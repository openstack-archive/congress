# Copyright (c) 2014 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import json

from oslo_config import cfg
from oslo_db import exception as db_exc
from oslo_log import log as logging
from oslo_utils import importutils
from oslo_utils import uuidutils
import six

from congress.datalog import base
from congress.datasources import constants
from congress.db import api as db
from congress.db import datasources as datasources_db
from congress.dse import d6cage
from congress import exception

import sys
import traceback


LOG = logging.getLogger(__name__)


class DataServiceError (Exception):
    pass


class DataSourceManager(object):

    loaded_drivers = {}
    dseNode = None

    @classmethod
    def set_dseNode(cls, dseNode):
        cls.dseNode = dseNode

    @classmethod
    def add_datasource(cls, item, deleted=False, update_db=True):
        req = cls.make_datasource_dict(item)
        # If update_db is True, new_id will get a new value from the db.
        new_id = req['id']
        driver_info = cls.get_driver_info(item['driver'])
        session = db.get_session()
        try:
            with session.begin(subtransactions=True):
                LOG.debug("adding datasource %s", req['name'])
                if update_db:
                    LOG.debug("updating db")
                    datasource = datasources_db.add_datasource(
                        id_=req['id'],
                        name=req['name'],
                        driver=req['driver'],
                        config=req['config'],
                        description=req['description'],
                        enabled=req['enabled'],
                        session=session)
                    new_id = datasource['id']

                cls.validate_create_datasource(req)
                cage = cls.dseNode or d6cage.d6Cage()
                engine = cage.service_object('engine')
                try:
                    LOG.debug("creating policy %s", req['name'])
                    engine.create_policy(req['name'],
                                         kind=base.DATASOURCE_POLICY_TYPE)
                except KeyError:
                    # FIXME(arosen): we need a better exception then
                    # key error being raised here
                    raise exception.DatasourceNameInUse(value=req['name'])
                try:
                    if cls.dseNode:
                        cls.createservice(name=req['name'],
                                          moduleName=driver_info['module'],
                                          args=item['config'],
                                          module_driver=True,
                                          type_='datasource_driver',
                                          id_=new_id)
                    else:
                        cage.createservice(name=req['name'],
                                           moduleName=driver_info['module'],
                                           args=item['config'],
                                           module_driver=True,
                                           type_='datasource_driver',
                                           id_=new_id)
                    service = cage.service_object(req['name'])
                    engine.set_schema(req['name'], service.get_schema())
                except Exception:
                    engine.delete_policy(req['name'])
                    raise exception.DatasourceCreationError(value=req['name'])

        except db_exc.DBDuplicateEntry:
            raise exception.DatasourceNameInUse(value=req['name'])
        new_item = dict(item)
        new_item['id'] = new_id
        return cls.make_datasource_dict(new_item)

    @classmethod
    def validate_configured_drivers(cls):
        """load all configured drivers and check no name conflict"""
        result = {}
        for driver_path in cfg.CONF.drivers:
            obj = importutils.import_class(driver_path)
            driver = obj.get_datasource_info()
            if driver['id'] in result:
                raise exception.BadConfig(_("There is a driver loaded already"
                                          "with the driver name of %s") %
                                          driver['id'])
            driver['module'] = driver_path
            result[driver['id']] = driver
        cls.loaded_drivers = result

    @classmethod
    def make_datasource_dict(cls, req, fields=None):
        result = {'id': req.get('id') or uuidutils.generate_uuid(),
                  'name': req.get('name'),
                  'driver': req.get('driver'),
                  'description': req.get('description'),
                  'type': None,
                  'enabled': req.get('enabled', True)}
        # NOTE(arosen): we store the config as a string in the db so
        # here we serialize it back when returning it.
        if isinstance(req.get('config'), six.string_types):
            result['config'] = json.loads(req['config'])
        else:
            result['config'] = req.get('config')

        return cls._fields(result, fields)

    @classmethod
    def _fields(cls, resource, fields):
        if fields:
            return dict(((key, item) for key, item in resource.items()
                         if key in fields))
        return resource

    @classmethod
    def get_datasources(cls, filter_secret=False):
        """Return the created datasources.

        This returns what datasources the database contains, not the
        datasources that this server instance is running.
        """

        results = []
        for datasouce_driver in datasources_db.get_datasources():
            result = cls.make_datasource_dict(datasouce_driver)
            if filter_secret:
                # secret field may be not provided while creating datasource
                try:
                    hides = cls.get_driver_info(result['driver'])['secret']
                    for hide_field in hides:
                        result['config'][hide_field] = "<hidden>"
                except KeyError:
                    pass
            results.append(result)
        return results

    @classmethod
    def get_datasource(cls, id_):
        """Return the created datasource."""
        result = datasources_db.get_datasource(id_)
        if not result:
            raise exception.DatasourceNotFound(id=id_)
        return cls.make_datasource_dict(result)

    @classmethod
    def get_driver_info(cls, driver):
        driver = cls.loaded_drivers.get(driver)
        if not driver:
            raise exception.DriverNotFound(id=driver)
        return driver

    @classmethod
    def get_driver_schema(cls, datasource_id):
        driver = cls.get_driver_info(datasource_id)
        obj = importutils.import_class(driver['module'])
        return obj.get_schema()

    @classmethod
    def get_datasource_schema(cls, source_id):
        datasource = datasources_db.get_datasource(source_id)
        if not datasource:
            raise exception.DatasourceNotFound(id=source_id)
        driver = cls.get_driver_info(datasource.driver)
        if driver:
            # NOTE(arosen): raises if not found
            driver = cls.get_driver_info(
                driver['id'])
            obj = importutils.import_class(driver['module'])
            return obj.get_schema()

    @classmethod
    def load_module_object(cls, datasource_id_or_name):
        datasource = datasources_db.get_datasource(datasource_id_or_name)
        # Ideally speaking, it should change datasource_db.get_datasource() to
        # be able to retrieve datasource info from db at once. The datasource
        # table and the method, however, will be removed in the new
        # architecture, so it use this way. Supporting both name and id is
        # a backward compatibility.
        if not datasource:
            datasource = (datasources_db.
                          get_datasource_by_name(datasource_id_or_name))
        if not datasource:
            return None

        driver = cls.get_driver_info(datasource.driver)
        obj = importutils.import_class(driver['module'])

        return obj

    @classmethod
    def get_row_data(cls, table_id, source_id, **kwargs):
        datasource = cls.get_datasource(source_id)
        cage = cls.dseNode or d6cage.d6Cage()
        datasource_obj = cage.service_object(datasource['name'])
        return datasource_obj.get_row_data(table_id)

    @classmethod
    def update_entire_data(cls, table_id, source_id, objs):
        datasource = cls.get_datasource(source_id)
        cage = d6cage.d6Cage()
        datasource_obj = cage.service_object(datasource['name'])
        return datasource_obj.update_entire_data(table_id, objs)

    @classmethod
    def get_tablename(cls, source_id, table_id):
        obj = cls.load_module_object(source_id)
        if obj:
            return obj.get_tablename(table_id)
        else:
            return None

    @classmethod
    def get_tablenames(cls, source_id):
        '''The method to get datasource tablename.'''
        # In the new architecture, table model would call datasource_driver's
        # get_tablenames() directly using RPC
        obj = cls.load_module_object(source_id)

        if obj:
            return obj.get_tablenames()
        else:
            return None

    @classmethod
    def delete_datasource(cls, datasource_id, update_db=True):
        datasource = cls.get_datasource(datasource_id)
        session = db.get_session()
        with session.begin(subtransactions=True):
            cage = cls.dseNode or d6cage.d6Cage()
            engine = cage.service_object('engine')
            try:
                engine.delete_policy(datasource['name'],
                                     disallow_dangling_refs=True)
            except exception.DanglingReference as e:
                raise e
            except KeyError:
                raise exception.DatasourceNotFound(id=datasource_id)
            if update_db:
                result = datasources_db.delete_datasource(
                    datasource_id, session)
                if not result:
                    raise exception.DatasourceNotFound(id=datasource_id)
            if cls.dseNode:
                cls.dseNode.unregister_service(
                    cls.dseNode.service_object(datasource['name']))
            else:
                cage.deleteservice(datasource['name'])

    @classmethod
    def get_status(cls, source_id=None, params=None):
        cage = d6cage.d6Cage()
        driver = cage.getservice(id_=source_id, type_='datasource_driver')
        if not driver:
            raise exception.NotFound('Could not find datasource %s' %
                                     source_id)
        return driver['object'].get_status()

    @classmethod
    def get_actions(cls, source_id=None):
        cage = d6cage.d6Cage()
        driver = cage.getservice(id_=source_id, type_='datasource_driver')
        if not driver:
            raise exception.NotFound('Could not find datasource %s' %
                                     source_id)
        return driver['object'].get_actions()

    @classmethod
    def get_drivers_info(cls):
        return [driver for driver in cls.loaded_drivers.values()]

    @classmethod
    def validate_create_datasource(cls, req):
        driver = req['driver']
        config = req['config'] or {}
        for loaded_driver in cls.loaded_drivers.values():
            if loaded_driver['id'] == driver:
                specified_options = set(config.keys())
                valid_options = set(loaded_driver['config'].keys())
                # Check that all the specified options passed in are
                # valid configuration options that the driver exposes.
                invalid_options = specified_options - valid_options
                if invalid_options:
                    raise exception.InvalidDriverOption(
                        invalid_options=invalid_options)

                # check that all the required options are passed in
                required_options = set(
                    [k for k, v in loaded_driver['config'].items()
                     if v == constants.REQUIRED])
                missing_options = required_options - specified_options
                if missing_options:
                    missing_options = ', '.join(missing_options)
                    raise exception.MissingRequiredConfigOptions(
                        missing_options=missing_options)
                return loaded_driver

        # If we get here no datasource driver match was found.
        raise exception.InvalidDriver(driver=req)

    @classmethod
    def request_refresh(cls, source_id):
        datasource = cls.get_datasource(source_id)
        cage = cls.dseNode or d6cage.d6Cage()
        datasource = cage.service_object(datasource['name'])
        datasource.request_refresh()

    @classmethod
    def createservice(
            cls,
            name="",
            keys="",
            description="",
            moduleName="",
            args={},
            module_driver=False,
            type_=None,
            id_=None):
        # copied from d6cage. It's not clear where this code should reside LT

        # self.log_info("creating service %s with module %s and args %s",
        #               name, moduleName, strutils.mask_password(args, "****"))

        # FIXME(arosen) This will be refactored out in the next patchset
        # this is only done because existing imports from d6service
        # instead of the module.
        if module_driver:
            congress_expected_module_path = ""
            for entry in range(len(moduleName.split(".")) - 1):
                congress_expected_module_path += (
                    moduleName.split(".")[entry] + ".")
            congress_expected_module_path = congress_expected_module_path[:-1]
            module = importutils.import_module(congress_expected_module_path)

        if not module_driver and moduleName not in sys.modules:
            # self.log_error(
            #     "error loading service %s: module %s does not exist",
            #     name,
            #     moduleName)
            raise exception.DataServiceError(
                "error loading service %s: module %s does not exist" %
                (name, moduleName))

        # if not module_driver and name in self.services:
        #     self.log_error("error loading service '%s': name already in use",
        #                         name)
        #     raise DataServiceError(
        #         "error loading service '%s': name already in use"
        #         % name)

        if not module_driver:
            module = sys.modules[moduleName]

        try:
            svcObject = module.d6service(name, keys, None, None,
                                         args)
            cls.dseNode.register_service(svcObject)
        except Exception:
            # self.log_error(
            #            "Error loading service '%s' of module '%s':: \n%s",
            #            name, module, traceback.format_exc())
            raise exception.DataServiceError(
                "Error loading service '%s' of module '%s':: \n%s"
                % (name, module, traceback.format_exc()))
