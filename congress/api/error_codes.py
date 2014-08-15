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

errors = {}
errors['add_item_id'] = (1001, "Add item does not support user-chosen ID.")
errors['rule_syntax'] = (1002, "Syntax error for rule")


def get(name):
    if name not in errors:
        return (1000, "Unknown error")
    return errors[name]
