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

from oslo_config import cfg

from congress import harness
from congress.tests import fake_datasource
from congress.tests import helper


def setup_config(with_fake_datasource=True):
    """Setup DseNode for testing.

    :param services is an array of DataServices
    :param api is a dictionary mapping api name to API model instance
    """

    cfg.CONF.set_override('distributed_architecture', True)
    # Load the fake driver.
    cfg.CONF.set_override(
        'drivers',
        ['congress.tests.fake_datasource.FakeDataSource'])

    node = helper.make_dsenode_new_partition("testnode")
    services = harness.create2(node=node)

    # Always register engine and fake datasource
    # engine = Dse2Runtime('engine')
    # node.register_service(engine)
    data = None
    if with_fake_datasource:
        data = fake_datasource.FakeDataSource('data')
        node.register_service(data)

    # Register provided apis (and no others)
    # (ResourceManager inherits from DataService)
    # api_map = {a.name: a for a in api}
    # api_resource_mgr = application.ResourceManager()
    # router.APIRouterV1(api_resource_mgr, api)
    # node.register_service(api_resource_mgr)

    engine = services[harness.ENGINE_SERVICE_NAME]
    api = services['api']
    return {'node': node, 'engine': engine, 'data': data, 'api': api}
