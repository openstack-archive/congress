# Copyright (c) 2014 Montavista Software, LLC.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
from oslo_log import log as logging
import swiftclient.service

from congress.datasources import datasource_driver

LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    """This method is called by d6cage to create a dataservice instance."""
    return SwiftDriver(name, keys, inbox, datapath, args)


class SwiftDriver(datasource_driver.DataSourceDriver):
    CONTAINERS = "containers"
    OBJECTS = "objects"

    value_trans = {'translation-type': 'VALUE'}

    containers_translator = {
        'translation-type': 'HDICT',
        'table-name': CONTAINERS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'count', 'translator': value_trans},
             {'fieldname': 'bytes', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans})}

    objects_translator = {
        'translation-type': 'HDICT',
        'table-name': OBJECTS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'bytes', 'translator': value_trans},
             {'fieldname': 'last_modified', 'translator': value_trans},
             {'fieldname': 'hash', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'content_type', 'translator': value_trans},
             {'fieldname': 'container_name', 'translator': value_trans})}

    TRANSLATORS = [containers_translator, objects_translator]

    def __init__(self, name='', keys='', inbox=None, datapath=None, args=None):
        if args is None:
            args = self.empty_credentials()
        super(SwiftDriver, self).__init__(name, keys, inbox, datapath, args)
        self.swift_service = swiftclient.service.SwiftService()

        self.raw_state = {}
        self.initialized = True

    @staticmethod
    def get_datasource_info():
        # FIXME(arosen): Figure out how swift actually does auth?
        result = {}
        result['id'] = 'swift'
        result['description'] = ('Datasource driver that interfaces with '
                                 'swift.')
        result['config'] = {}
        return result

    def update_from_datasource(self):
        '''Read and populate.

        Read data from swift and populate the policy engine
        tables with current state as specified by translators
        '''
        container_list = self.swift_service.list()
        object_list = []
        self.obj_list = []
        cont_list = []
        objects = []
        containers = []

        LOG.debug("Swift obtaining containers List")
        for stats in container_list:
            containers = stats['listing']
            for item in containers:
                cont_list.append(item['name'])

        LOG.debug("Swift obtaining objects List")
        for container in cont_list:
            object_list = self.swift_service.list(container)
            for items in object_list:
                item_list = items['listing']
                for obj in item_list:
                    obj['container_name'] = container
                for obj in item_list:
                    objects.append(obj)

        LOG.debug("Containers Lists--->: %s" % containers)
        LOG.debug("Object Lists--->: %s " % objects)

        if ('containers' not in self.raw_state or containers !=
                self.raw_state['containers']):
            self.raw_state['containers'] = containers
            self._translate_containers(containers)

        if ('objects' not in self.raw_state or objects !=
                self.raw_state['objects']):
            self.raw_state['objects'] = objects
            self._translate_objects(objects)

    def _translate_containers(self, obj):
        """Translate the containers represented by OBJ into tables.

        Assign self.state[tablename] for the table names
        generated from OBJ: CONTAINERS.
        """
        row_data = SwiftDriver.convert_objs(obj,
                                            self.containers_translator)

        container_tables = (self.CONTAINERS)
        self.state[container_tables] = set()
        for table, row in row_data:
            assert table in container_tables
            self.state[table].add(row)

        LOG.debug("CONTAINERS: %s" % str(self.state[self.CONTAINERS]))
        return tuple(self.state[self.CONTAINERS])

    def _translate_objects(self, obj):
        """Translate the objects represented by OBJ into tables.

        Assign self.state[tablename] for the table names
        generated from OBJ: OBJECTS.
        """
        row_data = SwiftDriver.convert_objs(obj,
                                            self.objects_translator)

        object_tables = (self.OBJECTS)
        self.state[object_tables] = set()
        for table, row in row_data:
            assert table in object_tables
            self.state[table].add(row)

        LOG.debug("OBJECTS: %s" % str(self.state[self.OBJECTS]))
        return tuple(self.state[self.OBJECTS])
