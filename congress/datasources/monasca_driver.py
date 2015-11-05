# Copyright (c) 2015 Cisco.
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

import datetime

import keystoneclient.v3.client as ksclient
from monascaclient import client as monasca_client
from oslo_log import log as logging
from oslo_utils import timeutils

from congress.datasources import datasource_driver
from congress.datasources import datasource_utils as ds_utils

LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    """Create a dataservice instance.

    This method is called by d6cage to create a dataservice
    instance.  There are a couple of parameters we found useful
    to add to that call, so we included them here instead of
    modifying d6cage (and all the d6cage.createservice calls).
    """
    return MonascaDriver(name, keys, inbox, datapath, args)


# TODO(thinrichs): figure out how to move even more of this boilerplate
#   into DataSourceDriver.  E.g. change all the classes to Driver instead of
#   NeutronDriver, CeilometerDriver, etc. and move the d6instantiate function
#   to DataSourceDriver.
class MonascaDriver(datasource_driver.PollingDataSourceDriver,
                    datasource_driver.ExecutionDriver):

    METRICS = "metrics"
    DIMENSIONS = "dimensions"
    STATISTICS = "statistics"
    DATA = "statistics.data"
    # TODO(fabiog): add events and logs when fully supported in Monasca
    # EVENTS = "events"
    # LOGS = "logs"

    value_trans = {'translation-type': 'VALUE'}

    metric_translator = {
        'translation-type': 'HDICT',
        'table-name': METRICS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'dimensions',
              'translator': {'translation-type': 'VDICT',
                             'table-name': DIMENSIONS,
                             'id-col': 'id',
                             'key-col': 'key', 'val-col': 'value',
                             'translator': value_trans}})
    }

    statistics_translator = {
        'translation-type': 'HDICT',
        'table-name': STATISTICS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'statistics',
              'translator': {'translation-type': 'LIST',
                             'table-name': DATA,
                             'id-col': 'name',
                             'val-col': 'value_col',
                             'translator': value_trans}})
    }

    TRANSLATORS = [metric_translator, statistics_translator]

    def __init__(self,  name='', keys='', inbox=None, datapath=None,
                 args=None):
        super(MonascaDriver, self).__init__(name, keys, inbox, datapath, args)
        datasource_driver.ExecutionDriver.__init__(self)
        self.creds = args
        if not self.creds.get('project_name'):
            self.creds['project_name'] = self.creds['tenant_name']

        if not self.creds.get('poll_time'):
            # set default polling time to 1hr
            self.creds['poll_time'] = 3600

        # Monasca uses Keystone V3
        self.creds['auth_url'] = self.creds['auth_url'].replace("v2.0", "v3")
        self.keystone = ksclient.Client(**self.creds)
        self.creds['token'] = self.keystone.auth_token

        if not self.creds.get('endpoint'):
            # if the endpoint not defined retrieved it from keystone catalog
            self.creds['endpoint'] = self.keystone.service_catalog.url_for(
                service_type='monitoring', endpoint_type='publicURL')

        self.monasca = monasca_client.Client('2_0', **self.creds)
        self.add_executable_client_methods(self.monasca, 'monascaclient.')
        self._init_end_start_poll()

    @staticmethod
    def get_datasource_info():
        result = {}
        result['id'] = 'monasca'
        result['description'] = ('Datasource driver that interfaces with '
                                 'monasca.')
        result['config'] = ds_utils.get_openstack_required_config()
        result['secret'] = ['password']
        return result

    def update_from_datasource(self):
        """Read Data from Monasca datasource.

        And to fill up the current state of the policy engine.
        """

        try:
            LOG.debug("Monasca grabbing metrics")
            metrics = self.monasca.metrics.list()
            self._translate_metric(metrics)
            LOG.debug("METRICS: %s" % str(self.state[self.METRICS]))

            LOG.debug("Monasca grabbing statistics")
            # gather statistic for the last day
            today = datetime.datetime.now()
            yesterday = datetime.timedelta(hours=24)
            start_from = timeutils.isotime(today-yesterday)

            for metric in self.monasca.metrics.list_names():
                LOG.debug("Monasca statistics for metric %s", metric['name'])
                _query_args = dict(
                    start_time=start_from,
                    name=metric['name'],
                    statistics='avg',
                    period=int(self.creds['poll_time']),
                    merge_metrics='true')
                statistics = self.monasca.metrics.list_statistics(
                    **_query_args)
                self._translate_statistics(statistics)
                LOG.debug("STATISTICS: %s" % str(self.state[self.STATISTICS]))

        except Exception as e:
            raise e

    @ds_utils.update_state_on_changed(METRICS)
    def _translate_metric(self, obj):
        """Translate the metrics represented by OBJ into tables."""
        LOG.debug("METRIC: %s" % str(obj))

        row_data = MonascaDriver.convert_objs(obj,
                                              self.metric_translator)
        return row_data

    @ds_utils.update_state_on_changed(STATISTICS)
    def _translate_statistics(self, obj):
        """Translate the metrics represented by OBJ into tables."""

        LOG.debug("STATISTICS: %s" % str(obj))

        row_data = MonascaDriver.convert_objs(obj,
                                              self.statistics_translator)
        return row_data

    def execute(self, action, action_args):
        """Overwrite ExecutionDriver.execute()."""
        # action can be written as a method or an API call.
        func = getattr(self, action, None)
        if func and self.is_executable(func):
            func(action_args)
        else:
            self._execute_api(self.monasca, action, action_args)
