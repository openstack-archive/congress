# Copyright 2015 Symantec.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
Congress Policy Middleware.

"""
import json

from nova.i18n import _
from nova import wsgi
from oslo_config import cfg
from oslo_log import log as logging
import webob.dec
import webob.exc

# policy enforcement flow
from congressclient.v1 import client
import keystoneclient
from keystoneclient.v3 import client as ksv3client
from novaclient import client as nova

LOG = logging.getLogger(__name__)


class Congress(wsgi.Middleware):
    """Make a request context from keystone headers."""

    @webob.dec.wsgify(RequestClass=wsgi.Request)
    def __call__(self, req):

        if req.environ['REQUEST_METHOD'] != 'POST':
            return self.application

        raw_path = req.environ['RAW_PATH_INFO']

        if "metadata" in raw_path:
            return self.application

        if "servers/action" in raw_path:
            return self.application

        flavor_ref = json.loads(req.body)['server']['flavorRef']

        token = req.environ['HTTP_X_AUTH_TOKEN']

        tenant_name = req.environ['HTTP_X_TENANT_NAME']

        CONF = cfg.CONF

        # obtain identity endpoint url
        url = CONF.keystone_authtoken.auth_url

        # obtain one of support keystone api versions
        raw_versions = keystoneclient.discover.available_versions(url,
                                                                  session=None)
        version = raw_versions[-1]['id']

        # assemble auth_url
        auth_url = url + '/' + version

        auth = keystoneclient.auth.identity.v2.Token(
            auth_url=auth_url,
            token=token, tenant_name=tenant_name)

        session = keystoneclient.session.Session(auth=auth)
        congress = client.Client(session=session,
                                 auth=None,
                                 interface='publicURL',
                                 service_type='policy')

        # Aggregating resource usage within domain level
        domain = req.environ['HTTP_X_PROJECT_DOMAIN_NAME']

        # obtain list of projects under this domain
        k3_client = ksv3client.Client(session=session)

        projects = k3_client.projects.list(domain=domain)
        # obtain list of hosts under each of these projects

        nova_c = nova.Client("2", session=session)
        ram_p = 0
        disk_p = 0
        cpus_p = 0
        for project in projects:

            search_opts = {
                'all_tenants': 1,
                'tenant_id': project.id,
            }

            servers_p = nova_c.servers.list(search_opts=search_opts)

            # locate flavor of each host
            for server in servers_p:

                info = nova_c.servers.get(server=server)
                flavor_id = info._info['flavor']['id']
                fd = nova_c.flavors.get(flavor=flavor_id)
                ram_p += fd.ram
                disk_p += fd.disk
                disk_p += fd.ephemeral
                cpus_p += fd.vcpus

        # incrementally add each type of resource
        # assemble query policy based on the data-usage
        # with memory_p, disk_p and cpus_p

        fd = nova_c.flavors.get(flavor=flavor_ref)
        ram_p += fd.ram
        disk_p += fd.disk
        disk_p += fd.ephemeral
        cpus_p += fd.vcpus
        domain_resource = ("(" + domain + "," + str(ram_p) + "," +
                           str(disk_p) + "," + str(cpus_p) + ")")

        validation_result = congress.execute_policy_action(
            "classification",
            "simulate",
            False,
            True,
            {'query': 'domain_resource_usage_exceeded (domain)',
             # this needs to be defined in congress server
             'action_policy': 'nova_quota_action',
             'sequence': 'domain_resource+'+domain_resource})

        if validation_result["result"]:

            messages = validation_result["result"]

            if messages:
                result_str = "\n  ".join(map(str, messages))
                msg = _(
                    "quota is not sufficient for this VM deployment").format(
                    "\n  " + result_str)
                LOG.error(msg)

            LOG.debug(messages)
            return webob.exc.HTTPUnauthorized(explanation=msg)
        else:
            LOG.info('Model valid')

        return self.application
