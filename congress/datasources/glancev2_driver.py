# Copyright (c) 2014 VMware, Inc. All rights reserved.
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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import glanceclient.v2.client as glclient
from keystoneauth1.identity import v2
from keystoneauth1 import session
from oslo_log import log as logging

from congress.datasources import datasource_driver
from congress.datasources import datasource_utils as ds_utils

LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    """This method is called by d6cage to create a dataservice instance."""
    return GlanceV2Driver(name, keys, inbox, datapath, args)


class GlanceV2Driver(datasource_driver.PollingDataSourceDriver,
                     datasource_driver.ExecutionDriver):

    IMAGES = "images"
    TAGS = "tags"

    value_trans = {'translation-type': 'VALUE'}
    images_translator = {
        'translation-type': 'HDICT',
        'table-name': IMAGES,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'status', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'container_format', 'translator': value_trans},
             {'fieldname': 'created_at', 'translator': value_trans},
             {'fieldname': 'updated_at', 'translator': value_trans},
             {'fieldname': 'disk_format', 'translator': value_trans},
             {'fieldname': 'owner', 'translator': value_trans},
             {'fieldname': 'protected', 'translator': value_trans},
             {'fieldname': 'min_ram', 'translator': value_trans},
             {'fieldname': 'min_disk', 'translator': value_trans},
             {'fieldname': 'checksum', 'translator': value_trans},
             {'fieldname': 'size', 'translator': value_trans},
             {'fieldname': 'file', 'translator': value_trans},
             {'fieldname': 'kernel_id', 'translator': value_trans},
             {'fieldname': 'ramdisk_id', 'translator': value_trans},
             {'fieldname': 'schema', 'translator': value_trans},
             {'fieldname': 'visibility', 'translator': value_trans},
             {'fieldname': 'tags',
              'translator': {'translation-type': 'LIST',
                             'table-name': TAGS,
                             'val-col': 'tag',
                             'parent-key': 'id',
                             'parent-col-name': 'image_id',
                             'translator': value_trans}})}

    TRANSLATORS = [images_translator]

    def __init__(self, name='', keys='', inbox=None, datapath=None, args=None):
        super(GlanceV2Driver, self).__init__(name, keys, inbox, datapath, args)
        datasource_driver.ExecutionDriver.__init__(self)
        self.creds = args
        auth = v2.Password(auth_url=self.creds['auth_url'],
                           username=self.creds['username'],
                           password=self.creds['password'],
                           tenant_name=self.creds['tenant_name'])
        sess = session.Session(auth=auth)
        self.glance = glclient.Client(session=sess)
        self.add_executable_client_methods(self.glance, 'glanceclient.v2.')
        self._init_end_start_poll()

    @staticmethod
    def get_datasource_info():
        result = {}
        result['id'] = 'glancev2'
        result['description'] = ('Datasource driver that interfaces with '
                                 'OpenStack Images aka Glance.')
        result['config'] = ds_utils.get_openstack_required_config()
        result['secret'] = ['password']
        return result

    def update_from_datasource(self):
        """Called when it is time to pull new data from this datasource."""
        LOG.debug("Grabbing Glance Images")
        try:
            images = {'images': self.glance.images.list()}
            self._translate_images(images)
        except Exception as e:
            raise e

    @ds_utils.update_state_on_changed(IMAGES)
    def _translate_images(self, obj):
        """Translate the images represented by OBJ into tables."""
        LOG.debug("IMAGES: %s", str(dict(obj)))
        row_data = GlanceV2Driver.convert_objs(
            obj['images'], GlanceV2Driver.images_translator)
        return row_data

    def execute(self, action, action_args):
        """Overwrite ExecutionDriver.execute()."""
        # action can be written as a method or an API call.
        func = getattr(self, action, None)
        if func and self.is_executable(func):
            func(action_args)
        else:
            self._execute_api(self.glance, action, action_args)
