# Copyright (c) 2013,2014 VMware, Inc. All rights reserved.
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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import functools
import inspect
import re

from keystoneauth1 import loading as kaloading

from congress.datasources import constants


def typed_value_trans(type):
    return {'translation-type': 'VALUE', 'data-type': type}


def get_openstack_required_config():
    return {'auth_url': constants.REQUIRED,
            'endpoint': constants.OPTIONAL,
            'region': constants.OPTIONAL,
            'username': constants.REQUIRED,
            'password': constants.REQUIRED,
            'user_domain_name': constants.OPTIONAL,
            'project_domain_name': constants.OPTIONAL,
            'tenant_name': constants.OPTIONAL,
            'project_name': constants.REQUIRED,
            'poll_time': constants.OPTIONAL}


def update_state_on_changed(root_table_name):
    """Decorator to check raw data before retranslating.

    If raw data is same with cached self.raw_state,
    don't translate data, return empty list directly.
    If raw data is changed, translate it and update state.
    """

    def outer(f):
        @functools.wraps(f)
        def inner(self, raw_data, *args, **kw):
            if (root_table_name not in self.raw_state or
                    # TODO(RuiChen): workaround for oslo-incubator bug/1499369,
                    # enable self.raw_state cache, once the bug is resolved.
                    raw_data is not self.raw_state[root_table_name]):
                result = f(self, raw_data, *args, **kw)
                self._update_state(root_table_name, result)
                self.raw_state[root_table_name] = raw_data
            else:
                result = []
            return result
        return inner
    return outer


def add_column(colname, desc=None, type=None, nullable=True):
    """Adds column in the form of dict."""
    col_dict = {'name': colname, 'desc': desc}
    if type is not None:
        col_dict['type'] = str(type)
    if not nullable:
        col_dict['nullable'] = False
    return col_dict


def inspect_methods(client, api_prefix):
    """Inspect all callable methods from client for congress."""

    # some methods are referred multiple times, we should
    # save them here to avoid infinite loop
    obj_checked = []
    method_checked = []
    # For depth-first search
    obj_stack = []
    # save all inspected methods that will be returned
    allmethods = []

    obj_checked.append(client)
    obj_stack.append(client)
    while len(obj_stack) > 0:
        cur_obj = obj_stack.pop()
        # everything starts with '_' are considered as internal only
        for f in [f for f in dir(cur_obj) if not f.startswith('_')]:
            p = getattr(cur_obj, f, None)
            if inspect.ismethod(p):
                m_p = {}
                # to get a name that can be called by Congress, no need
                # to return the full path
                m_p['name'] = cur_obj.__module__.replace(api_prefix, '')
                if m_p['name'] == '':
                    m_p['name'] = p.__name__
                else:
                    m_p['name'] = m_p['name'] + '.' + p.__name__
                # skip checked methods
                if m_p['name'] in method_checked:
                    continue
                m_doc = inspect.getdoc(p)
                # not return deprecated methods
                if m_doc and "DEPRECATED:" in m_doc:
                    continue

                if m_doc:
                    m_doc = re.sub('\n|\s+', ' ', m_doc)
                    x = re.split(' :param ', m_doc)
                    m_p['desc'] = x.pop(0)
                    y = inspect.getargspec(p)
                    m_p['args'] = []
                    while len(y.args) > 0:
                        m_p_name = y.args.pop(0)
                        if m_p_name == 'self':
                            continue
                        if len(x) > 0:
                            m_p_desc = x.pop(0)
                        else:
                            m_p_desc = "None"
                        m_p['args'].append({'name': m_p_name,
                                            'desc': m_p_desc})
                else:
                    m_p['args'] = []
                    m_p['desc'] = ''
                allmethods.append(m_p)
                method_checked.append(m_p['name'])
            elif inspect.isfunction(p):
                m_p = {}
                m_p['name'] = cur_obj.__module__.replace(api_prefix, '')
                if m_p['name'] == '':
                    m_p['name'] = f
                else:
                    m_p['name'] = m_p['name'] + '.' + f
                # TODO(zhenzanz): Never see doc for function yet.
                # m_doc = inspect.getdoc(p)
                m_p['args'] = []
                m_p['desc'] = ''
                allmethods.append(m_p)
                method_checked.append(m_p['name'])
            elif isinstance(p, object) and hasattr(p, '__module__'):
                # avoid infinite loop by checking that p not in obj_checked.
                # don't use 'in' since that uses ==, and some clients err
                if ((not any(p is x for x in obj_checked)) and
                   (not inspect.isbuiltin(p))):
                    if re.match(api_prefix, p.__module__):
                        if (not inspect.isclass(p)):
                            obj_stack.append(p)

    return allmethods


# Note (thread-safety): blocking function
def get_keystone_session(creds, headers=None):

    auth_details = {}
    auth_details['auth_url'] = creds['auth_url']
    auth_details['username'] = creds['username']
    auth_details['password'] = creds['password']
    auth_details['project_name'] = (creds.get('project_name') or
                                    creds.get('tenant_name'))
    auth_details['tenant_name'] = creds.get('tenant_name')
    auth_details['user_domain_name'] = creds.get('user_domain_name', 'Default')
    auth_details['project_domain_name'] = creds.get('project_domain_name',
                                                    'Default')
    loader = kaloading.get_plugin_loader('password')
    auth_plugin = loader.load_from_options(**auth_details)
    if headers is None:
        session = kaloading.session.Session().load_from_options(
            auth=auth_plugin)
    else:
        session = kaloading.session.Session().load_from_options(
            auth=auth_plugin, additional_headers=headers)

    return session
