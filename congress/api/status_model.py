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

from oslo_log import log as logging

from congress.api import webservice
from congress.dse import d6cage
from congress.dse import deepsix
from congress import exception


LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    return StatusModel(name, keys, inbox=inbox, dataPath=datapath, **args)


class StatusModel(deepsix.deepSix):
    """Model for handling API requests about Statuses."""
    def __init__(self, name, keys, inbox=None, dataPath=None,
                 policy_engine=None):
        super(StatusModel, self).__init__(name, keys, inbox=inbox,
                                          dataPath=dataPath)
        self.cage = d6cage.d6Cage()
        self.engine = self.cage.service_object('engine')

    def _get_policy(self, context):
        if 'policy_id' in context:
            return self.engine.policy_object(id=context['policy_id'])
        else:
            return self.engine.policy_object(name=context['policy_name'])

    def _get_policy_specifier(self, context):
        if 'policy_id' in context:
            return context['policy_id']
        else:
            return context['policy_name']

    def get_item(self, id_, params, context=None):
        """Retrieve item with id id_ from model.

        Args:
            id_: The ID of the item to retrieve
            params: A dict-like object containing parameters
                    from the request query string and body.
            context: Key-values providing frame of reference of request

        Returns:
             The matching item or None if item with id_ does not exist.
        """
        # FIXME(arosen): we need better API validation in congress
        if 'ds_id' in context:
            service = self.cage.getservice(id_=context['ds_id'],
                                           type_='datasource_driver')
            if service:
                return service['object'].get_status()

            raise webservice.DataModelException(
                exception.NotFound.code,
                'Could not find service %s' % id_,
                http_status_code=exception.NotFound.code)

        elif (('policy_id' in context or 'policy_name' in context)
              and 'rule_id' in context):
            try:
                policy = self._get_policy(context)
                rule = policy.get_rule(str(context['rule_id']))
                if rule:
                    return {'name': rule.name,
                            'id': str(rule.id),
                            'comment': rule.comment,
                            'original_str': rule.original_str}
            except KeyError:
                pass
            policy_str = 'policy: ' + str(self._get_policy_specifier(context))
            raise webservice.DataModelException(
                exception.NotFound.code,
                'Could not find %s rule %s'
                % (policy_str, context['rule_id']),
                http_status_code=exception.NotFound.code)

        elif 'policy_id' in context or 'policy_name' in context:
            try:
                policy = self._get_policy(context)
                return {'name': policy.name, 'id': str(policy.id)}
            except KeyError:
                pass
            policy_str = 'policy: ' + str(self._get_policy_specifier(context))
            raise webservice.DataModelException(
                exception.NotFound.code,
                'Could not find policy %s' % policy_str,
                http_status_code=exception.NotFound.code)

        raise Exception("Could not find expected parameters for status call. "
                        "Context: " + str(context))
