# Copyright (c) 2015 Hewlett-Packard. All rights reserved.
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

logger = logging.getLogger(__name__)


class IOMuranoObject(object):
    name = 'io.murano.Object'

    @classmethod
    def is_class_type(cls, name):
        if name == cls.name:
            return True
        else:
            return False

    @classmethod
    def get_parent_types(cls, class_name=None):
        if class_name and not cls.is_class_type(class_name):
            return []
        return [cls.name]


class IOMuranoEnvironment(IOMuranoObject):
    name = 'io.murano.Environment'

    @classmethod
    def get_parent_types(cls, class_name=None):
        if class_name and not cls.is_class_type(class_name):
            return []
        types = IOMuranoObject.get_parent_types()
        types.append(cls.name)
        return types


class IOMuranoResourcesInstance(IOMuranoObject):
    name = 'io.murano.resources.Instance'

    @classmethod
    def get_parent_types(cls, class_name=None):
        if class_name and not cls.is_class_type(class_name):
            return []
        types = IOMuranoObject.get_parent_types()
        types.append(cls.name)
        return types


class IOMuranoResourcesLinuxInstance(IOMuranoResourcesInstance):
    name = 'io.murano.resources.LinuxInstance'

    @classmethod
    def get_parent_types(cls, class_name=None):
        if class_name and not cls.is_class_type(class_name):
            return []
        types = IOMuranoResourcesInstance.get_parent_types()
        types.append(cls.name)
        return types


class IOMuranoResourcesLinuxMuranoInstance(IOMuranoResourcesLinuxInstance):
    name = 'io.murano.resources.LinuxMuranoInstance'

    @classmethod
    def get_parent_types(cls, class_name=None):
        if class_name and not cls.is_class_type(class_name):
            return []
        types = IOMuranoResourcesLinuxInstance.get_parent_types()
        types.append(cls.name)
        return types


class IOMuranoResourcesWindowsInstance(IOMuranoResourcesInstance):
    name = 'io.murano.resources.WindowsInstance'

    @classmethod
    def get_parent_types(cls, class_name=None):
        if class_name and not cls.is_class_type(class_name):
            return []
        types = IOMuranoResourcesInstance.get_parent_types()
        types.append(cls.name)
        return types


class IOMuranoResourcesNetwork(IOMuranoObject):
    name = 'io.murano.resources.Network'

    @classmethod
    def get_parent_types(cls, class_name=None):
        if class_name and not cls.is_class_type(class_name):
            return []
        types = IOMuranoObject.get_parent_types()
        types.append(cls.name)
        return types


class IOMuranoResourcesNeutronNetwork(IOMuranoResourcesNetwork):
    name = 'io.murano.resources.NeutronNetwork'

    @classmethod
    def get_parent_types(cls, class_name=None):
        if class_name and not cls.is_class_type(class_name):
            return []
        types = IOMuranoResourcesNetwork.get_parent_types()
        types.append(cls.name)
        return types


class IOMuranoApplication(IOMuranoObject):
    name = 'io.murano.Application'

    @classmethod
    def get_parent_types(cls, class_name=None):
        if class_name and not cls.is_class_type(class_name):
            return []
        types = IOMuranoObject.get_parent_types()
        types.append(cls.name)
        return types


class IOMuranoApps(IOMuranoApplication):
    # This is a common class for all applications
    # name should be set to actual apps type before use
    # (e.g io.murano.apps.apache.ApacheHttpServer)
    name = None

    @classmethod
    def get_parent_types(cls, class_name=None):
        if class_name and not cls.is_class_type(class_name):
            return []
        types = IOMuranoApplication.get_parent_types()
        types.append(cls.name)
        return types
