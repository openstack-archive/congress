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

from congress.policy_engines.agnostic import Dse2Runtime
from congress.tests import fake_datasource
from congress.tests import helper


def setup_config(services=[]):
    cfg.CONF.set_override('distributed_architecture', True)
    # Load the fake driver.
    cfg.CONF.set_override(
        'drivers',
        ['congress.tests.fake_datasource.FakeDataSource'])

    node = helper.make_dsenode_new_partition("testnode")
    engine = Dse2Runtime('engine')
    data = fake_datasource.FakeDataSource('data')

    node.register_service(engine)
    node.register_service(data)

    for service in services:
        node.register_service(service)

    return {'node': node, 'engine': engine, 'data': data}
