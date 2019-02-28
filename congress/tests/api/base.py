# Copyright (c) 2016 NEC Corporation. All rights reserved.
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
from futurist import periodics
import mock
from oslo_config import cfg

from congress.api import base as api_base
from congress.common import config
from congress import harness
from congress.tests import fake_datasource
from congress.tests import helper


def setup_config(with_fake_datasource=True, node_id='testnode',
                 same_partition_as_node=None, api=True, policy=True,
                 datasources=True, with_fake_json_ingester=False):
    """Setup DseNode for testing.

    :param: services is an array of DataServices
    :param: api is a dictionary mapping api name to API model instance
    """
    config.set_config_defaults()
    # Load the fake driver.
    cfg.CONF.set_override(
        'drivers',
        ['congress.tests.fake_datasource.FakeDataSource'])

    if same_partition_as_node is None:
        node = helper.make_dsenode_new_partition(node_id)
    else:
        node = helper.make_dsenode_same_partition(
            same_partition_as_node, node_id)

    if datasources:
        cfg.CONF.set_override('datasources', True)

    with mock.patch.object(periodics, 'PeriodicWorker', autospec=True):
        services = harness.create2(
            existing_node=node, policy_engine=policy, api=api,
            datasources=datasources)

    data = None
    if with_fake_datasource:
        data = fake_datasource.FakeDataSource('data')
        # FIXME(ekcs): this is a hack to prevent the synchronizer from
        # attempting to delete this DSD because it's not in DB
        data.type = 'no_sync_datasource_driver'
        node.register_service(data)

    ingester = None
    if with_fake_json_ingester:
        ingester = fake_datasource.FakeJsonIngester()
        node.register_service(ingester)

    engine_service = None
    library_service = None
    api_service = None
    if policy:
        engine_service = services[api_base.ENGINE_SERVICE_ID]
        library_service = services[api_base.LIBRARY_SERVICE_ID]
    if api:
        api_service = services['api']
    if datasources:
        ds_manager = services['ds_manager']

    return {'node': node, 'engine': engine_service, 'library': library_service,
            'data': data, 'api': api_service, 'ds_manager': ds_manager,
            'json_ingester': ingester}
