# Copyright (c) 2018 VMware, Inc. All rights reserved.
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

"""
Mistral Driver for Congress

This driver allows the creation of Congress datasources that interfaces with
Mistral workflows service. The Congress datasource reflects as Congress tables
the Mistral data on workflows, workflow executions, actions, and action
executions. The datasource also supports the triggering of Mistral APIs such as
initiation of a workflows or actions. The triggering of workflows or actions is
especially useful for creating Congress policies that take remedial action.

Datasource creation CLI example:
$ openstack congress datasource create mistral mistral_datasource \
  --config username=admin \
  --config tenant_name=admin \
  --config auth_url=http://127.0.0.1/identity \
  --config password=password
"""

from mistralclient.api.v2 import client as mistral_client

from congress.datasources import constants
from congress.datasources import datasource_driver
from congress.datasources import datasource_utils as ds_utils


class MistralDriver(datasource_driver.PollingDataSourceDriver,
                    datasource_driver.ExecutionDriver):
    WORKFLOWS = 'workflows'
    ACTIONS = 'actions'

    WORKFLOW_EXECUTIONS = 'workflow_executions'
    ACTION_EXECUTIONS = 'action_executions'

    value_trans = {'translation-type': 'VALUE'}

    workflows_translator = {
        'translation-type': 'HDICT',
        'table-name': WORKFLOWS,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'scope', 'translator': value_trans},
             {'fieldname': 'input', 'translator': value_trans},
             {'fieldname': 'namespace', 'translator': value_trans},
             {'fieldname': 'project_id', 'translator': value_trans},
             {'fieldname': 'created_at', 'translator': value_trans},
             {'fieldname': 'updated_at', 'translator': value_trans},
             {'fieldname': 'definition', 'translator': value_trans},
             {'fieldname': 'description', 'translator': value_trans},
             # TODO(ekcs): maybe enable tags in the future
             )}

    actions_translator = {
        'translation-type': 'HDICT',
        'table-name': ACTIONS,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'input', 'translator': value_trans},
             {'fieldname': 'created_at', 'translator': value_trans},
             {'fieldname': 'updated_at', 'translator': value_trans},
             {'fieldname': 'is_system', 'translator': value_trans},
             {'fieldname': 'definition', 'translator': value_trans},
             {'fieldname': 'description', 'translator': value_trans},
             {'fieldname': 'scope', 'translator': value_trans},
             # TODO(ekcs): maybe enable tags in the future
             )}

    workflow_executions_translator = {
        'translation-type': 'HDICT',
        'table-name': WORKFLOW_EXECUTIONS,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'workflow_name', 'translator': value_trans},
             {'fieldname': 'input', 'translator': value_trans},
             {'fieldname': 'created_at', 'translator': value_trans},
             {'fieldname': 'updated_at', 'translator': value_trans},
             {'fieldname': 'state', 'translator': value_trans},
             {'fieldname': 'state_info', 'translator': value_trans},
             {'fieldname': 'description', 'translator': value_trans},
             {'fieldname': 'workflow_id', 'translator': value_trans},
             {'fieldname': 'workflow_namespace', 'translator': value_trans},
             {'fieldname': 'params', 'translator': value_trans},
             # TODO(ekcs): maybe add task_execution_ids table
             )}

    action_executions_translator = {
        'translation-type': 'HDICT',
        'table-name': ACTION_EXECUTIONS,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'state_info', 'translator': value_trans},
             {'fieldname': 'workflow_name', 'translator': value_trans},
             {'fieldname': 'task_execution_id', 'translator': value_trans},
             {'fieldname': 'task_name', 'translator': value_trans},
             {'fieldname': 'description', 'translator': value_trans},
             {'fieldname': 'input', 'translator': value_trans},
             {'fieldname': 'created_at', 'translator': value_trans},
             {'fieldname': 'updated_at', 'translator': value_trans},
             {'fieldname': 'accepted', 'translator': value_trans},
             {'fieldname': 'state', 'translator': value_trans},
             {'fieldname': 'workflow_namespace', 'translator': value_trans},
             # TODO(ekcs): maybe add action execution tags
             )}

    TRANSLATORS = [
        workflows_translator, actions_translator,
        workflow_executions_translator, action_executions_translator]

    def __init__(self, name='', args=None):
        super(MistralDriver, self).__init__(name, args=args)
        datasource_driver.ExecutionDriver.__init__(self)
        session = ds_utils.get_keystone_session(args)
        self.mistral_client = mistral_client.Client(session=session)

        self.add_executable_client_methods(
            self.mistral_client, 'mistralclient.api.v2.')
        self.initialize_update_method()
        self._init_end_start_poll()

    @staticmethod
    def get_datasource_info():
        result = {}
        result['id'] = 'mistral'
        result['description'] = ('Datasource driver that interfaces with '
                                 'Mistral.')
        result['config'] = ds_utils.get_openstack_required_config()
        result['config']['lazy_tables'] = constants.OPTIONAL
        result['secret'] = ['password']
        return result

    def initialize_update_method(self):
        workflows_method = lambda: self._translate_workflows(
            self.mistral_client.workflows.list())
        self.add_update_method(workflows_method, self.workflows_translator)

        workflow_executions_method = (
            lambda: self._translate_workflow_executions(
                self.mistral_client.executions.list()))
        self.add_update_method(workflow_executions_method,
                               self.workflow_executions_translator)

        actions_method = lambda: self._translate_actions(
            self.mistral_client.actions.list())
        self.add_update_method(actions_method, self.actions_translator)

        action_executions_method = lambda: self._translate_action_executions(
            self.mistral_client.action_executions.list())
        self.add_update_method(action_executions_method,
                               self.action_executions_translator)

    @ds_utils.update_state_on_changed(WORKFLOWS)
    def _translate_workflows(self, obj):
        """Translate the workflows represented by OBJ into tables."""
        row_data = MistralDriver.convert_objs(obj, self.workflows_translator)
        return row_data

    @ds_utils.update_state_on_changed(ACTIONS)
    def _translate_actions(self, obj):
        """Translate the workflows represented by OBJ into tables."""
        row_data = MistralDriver.convert_objs(obj, self.actions_translator)
        return row_data

    @ds_utils.update_state_on_changed(WORKFLOW_EXECUTIONS)
    def _translate_workflow_executions(self, obj):
        """Translate the workflow_executions represented by OBJ into tables."""
        row_data = MistralDriver.convert_objs(
            obj, self.workflow_executions_translator)
        return row_data

    @ds_utils.update_state_on_changed(ACTION_EXECUTIONS)
    def _translate_action_executions(self, obj):
        """Translate the action_executions represented by OBJ into tables."""
        row_data = MistralDriver.convert_objs(
            obj, self.action_executions_translator)
        return row_data

    def execute(self, action, action_args):
        """Overwrite ExecutionDriver.execute()."""
        # action can be written as a method or an API call.
        func = getattr(self, action, None)
        if func and self.is_executable(func):
            func(action_args)
        else:
            self._execute_api(self.mistral_client, action, action_args)
