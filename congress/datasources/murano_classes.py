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
import inspect

from congress.openstack.common import log as logging

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
    def get_parent_types(cls):
        return [cls.name]


class IOMuranoResourcesInstance(IOMuranoObject):
    name = 'io.murano.resources.Instance'

    @classmethod
    def get_parent_types(cls):
        types = IOMuranoObject.get_parent_types()
        types.append(cls.name)
        return types


class IOMuranoResourcesLinuxInstance(IOMuranoResourcesInstance):
    name = 'io.murano.resources.LinuxInstance'

    @classmethod
    def get_parent_types(cls):
        types = IOMuranoResourcesInstance.get_parent_types()
        types.append(cls.name)
        return types


class IOMuranoResourcesLinuxMuranoInstance(IOMuranoResourcesLinuxInstance):
    name = 'io.murano.resources.LinuxMuranoInstance'

    @classmethod
    def get_parent_types(cls):
        types = IOMuranoResourcesLinuxInstance.get_parent_types()
        types.append(cls.name)
        return types


class IOMuranoResourcesWindowsInstance(IOMuranoResourcesInstance):
    name = 'io.murano.resources.WindowsInstance'

    @classmethod
    def get_parent_types(cls):
        types = IOMuranoResourcesInstance.get_parent_types()
        types.append(cls.name)
        return types


class IOMuranoResourcesNetwork(IOMuranoObject):
    name = 'io.murano.resources.Network'

    @classmethod
    def get_parent_types(cls):
        types = IOMuranoObject.get_parent_types()
        types.append(cls.name)
        return types


class IOMuranoResourcesNeutronNetwork(IOMuranoResourcesNetwork):
    name = 'io.murano.resources.NeutronNetwork'

    @classmethod
    def get_parent_types(cls):
        types = IOMuranoResourcesNetwork.get_parent_types()
        types.append(cls.name)
        return types


class IOMuranoApplication(IOMuranoObject):
    name = 'io.murano.Application'

    @classmethod
    def get_parent_types(cls):
        types = IOMuranoObject.get_parent_types()
        types.append(cls.name)
        return types


class IOMuranoApps(IOMuranoApplication):
    # This is a common class for all apps with prefix
    # 'io.murano.apps'.
    # name should be set to actual apps type before use
    # (e.g io.murano.apps.apache.ApacheHttpServer)
    name = ""

    @classmethod
    def get_parent_types(cls):
        types = IOMuranoApplication.get_parent_types()
        types.append(cls.name)
        return types

    @classmethod
    def is_class_type(cls, name):
        if "io.murano.apps" in name:
            return True
        else:
            return False


def get_parent_types(obj_type):
    """Get class types of all OBJ_TYPE's parents including itself.

    Look up the hierachy of OBJ_TYPE and return types of all its
    ancestor including its own type.
    :param obj_type: string
    """
    class_types = []
    g = globals().copy()
    for name, cls in g.iteritems():
        logger.debug("%s: %s" % (name, cls))
        if (inspect.isclass(cls) and 'is_class_type' in dir(cls) and
                cls.is_class_type(obj_type)):
            if "io.murano.apps" in obj_type:
                cls.name = obj_type
            class_types = cls.get_parent_types()
            if len(class_types) > 0:
                break
    return class_types
