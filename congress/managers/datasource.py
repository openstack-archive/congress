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


LOG = logging.getLogger(__name__)


class DataSourceManager(object):

    loaded_drivers = {}

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
                cage = d6cage.d6Cage()
                engine = cage.service_object('engine')
                try:
                    LOG.debug("creating policy %s", req['name'])
                    engine.create_policy(req['name'],
                                         kind=base.DATASOURCE_POLICY_TYPE)
                except KeyError:
                    # FIXME(arosen): we need a better exception then
                    # key error being raised here
                    raise DatasourceNameInUse(value=req['name'])
                try:
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
                    raise DatasourceCreationError(value=req['name'])

        except db_exc.DBDuplicateEntry:
            raise DatasourceNameInUse(value=req['name'])
        new_item = dict(item)
        new_item['id'] = new_id
        return cls.make_datasource_dict(new_item)

    @classmethod
    def validate_configured_drivers(cls):
        result = {}
        for driver_path in cfg.CONF.drivers:
            obj = importutils.import_class(driver_path)
            driver = obj.get_datasource_info()
            if driver['id'] in result:
                raise BadConfig(_("There is a driver loaded already with the"
                                  "driver name of %s")
                                % driver['id'])
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
            raise DatasourceNotFound(id=id_)
        return cls.make_datasource_dict(result)

    @classmethod
    def get_driver_info(cls, driver):
        driver = cls.loaded_drivers.get(driver)
        if not driver:
            raise DriverNotFound(id=driver)
        return driver

    @classmethod
    def get_driver_schema(cls, datasource_id):
        driver = cls.get_driver_info(datasource_id)
        obj = importutils.import_class(driver['module'])
        return obj.get_schema()

    @classmethod
    def get_datasource_schema(cls, datasource_id):
        datasource = datasources_db.get_datasource(datasource_id)
        if not datasource:
            raise DatasourceNotFound(id=datasource_id)
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
    def get_row_data(cls, table_id, datasource_id, **kwargs):
        datasource = cls.get_datasource(datasource_id)
        cage = d6cage.d6Cage()
        datasource_obj = cage.service_object(datasource['name'])
        return datasource_obj.get_row_data(table_id)

    @classmethod
    def get_tablename(cls, datasource_id_or_name, table_id):
        obj = cls.load_module_object(datasource_id_or_name)
        if obj:
            return obj.get_tablename(table_id)
        else:
            return None

    @classmethod
    def get_tablenames(cls, datasource_id_or_name):
        '''The method to get datasource tablename.'''
        # In the new architecture, table model would call datasource_driver's
        # get_tablenames() directly using RPC
        obj = cls.load_module_object(datasource_id_or_name)

        if obj:
            return obj.get_tablenames()
        else:
            return None

    @classmethod
    def delete_datasource(cls, datasource_id, update_db=True):
        datasource = cls.get_datasource(datasource_id)
        session = db.get_session()
        with session.begin(subtransactions=True):
            cage = d6cage.d6Cage()
            engine = cage.service_object('engine')
            try:
                engine.delete_policy(datasource['name'],
                                     disallow_dangling_refs=True)
            except exception.DanglingReference as e:
                raise e
            except KeyError:
                raise DatasourceNotFound(id=datasource_id)
            if update_db:
                result = datasources_db.delete_datasource(
                    datasource_id, session)
                if not result:
                    raise DatasourceNotFound(id=datasource_id)
            cage.deleteservice(datasource['name'])

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
                    raise InvalidDriverOption(invalid_options=invalid_options)

                # check that all the required options are passed in
                required_options = set(
                    [k for k, v in loaded_driver['config'].items()
                     if v == constants.REQUIRED])
                missing_options = required_options - specified_options
                if missing_options:
                    missing_options = ', '.join(missing_options)
                    raise MissingRequiredConfigOptions(
                        missing_options=missing_options)
                return loaded_driver

        # If we get here no datasource driver match was found.
        raise InvalidDriver(driver=req)

    @classmethod
    def request_refresh(cls, datasource_id):
        datasource = cls.get_datasource(datasource_id)
        cage = d6cage.d6Cage()
        datasource = cage.service_object(datasource['name'])
        datasource.request_refresh()


class BadConfig(exception.BadRequest):
    pass


class DatasourceDriverException(exception.CongressException):
    pass


class MissingRequiredConfigOptions(BadConfig):
    msg_fmt = _("Missing required config options: %(missing_options)s")


class InvalidDriver(BadConfig):
    msg_fmt = _("Invalid driver: %(driver)s")


class InvalidDriverOption(BadConfig):
    msg_fmt = _("Invalid driver options: %(invalid_options)s")


class DatasourceNameInUse(exception.Conflict):
    msg_fmt = _("Datasource already in use with name %(value)s")


class DatasourceNotFound(exception.NotFound):
    msg_fmt = _("Datasource not found %(id)s")


class DriverNotFound(exception.NotFound):
    msg_fmt = _("Driver not found %(id)s")


class DatasourceCreationError(BadConfig):
    msg_fmt = _("Datasource could not be created on the DSE: %(value)s")
