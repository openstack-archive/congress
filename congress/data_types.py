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

import abc
import collections
import ipaddress
import json

from oslo_utils import uuidutils
import six


TypeNullabilityTuple = collections.namedtuple(
    'TypeNullabilityTuple', 'type nullable')


def nullable(marshal):
    '''decorator to make marshal function accept None value'''
    def func(cls, value):
        if value is None:
            return None
        else:
            return marshal(cls, value)
    return func


class UnqualifiedNameStr(abc.ABCMeta):
    '''metaclass to make str(Type) == Type'''
    def __str__(self):
        return self.__name__


@six.add_metaclass(UnqualifiedNameStr)
class CongressDataType(object):
    @classmethod
    @abc.abstractmethod
    def marshal(cls, value):
        '''Validate a value as valid for this type.

        :Raises ValueError: if the value is not valid for this type
        '''
        raise NotImplementedError

    @classmethod
    def least_ancestor(cls, target_types):
        '''Find this type's least ancestor among target_types

        This method helps a data consumer find the least common ancestor of
        this type among the types the data consumer supports.

        :param supported_types: iterable collection of types
        :returns: the subclass of CongressDataType which is the least ancestor
        '''
        target_types = frozenset(target_types)
        current_class = cls
        try:
            while current_class not in target_types:
                current_class = current_class._get_parent()
            return current_class
        except cls.CongressDataTypeNoParent:
            return None

    @classmethod
    def convert_to_ancestor(cls, value, ancestor_type):
        '''Convert this type's exchange value to ancestor_type's exchange value

        Generally there is no actual conversion because descendant type value
        is directly interpretable as ancestor type value. The only exception
        is the conversion from non-string descendents to string. This
        conversion is needed by Agnostic engine does not support boolean.

        .. warning:: undefined behavior if ancestor_type is not an ancestor of
                     this type.
        '''
        if ancestor_type == Str:
            return json.dumps(value)
        else:
            if cls.least_ancestor([ancestor_type]) is None:
                raise cls.CongressDataTypeHierarchyError
            else:
                return value

    @classmethod
    def _get_parent(cls):
        congress_parents = [parent for parent in cls.__bases__
                            if issubclass(parent, CongressDataType)]
        if len(congress_parents) == 1:
            return congress_parents[0]
        elif len(congress_parents) == 0:
            raise cls.CongressDataTypeNoParent(
                'No parent type found for {0}'.format(cls))
        else:
            raise cls.CongressDataTypeHierarchyError(
                'More than one parent type found for {0}: {1}'
                .format(cls, congress_parents))

    class CongressDataTypeNoParent(TypeError):
        pass

    class CongressDataTypeHierarchyError(TypeError):
        pass


class Scalar(CongressDataType):
    '''Most general type, emcompassing all JSON scalar values'''

    ACCEPTED_VALUE_TYPES = [
        six.string_types, six.text_type, six.integer_types, float, bool]

    @classmethod
    @nullable
    def marshal(cls, value):
        for type in cls.ACCEPTED_VALUE_TYPES:
            if isinstance(value, type):
                return value
        raise ValueError('Input value (%s) is of %s instead of one of the '
                         'expected types %s'
                         % (value, type(value), cls.ACCEPTED_VALUE_TYPES))


class Str(Scalar):

    @classmethod
    @nullable
    def marshal(cls, value):
        if not isinstance(value, six.string_types):
            raise ValueError('Input value (%s) is of %s instead of expected %s'
                             % (value, type(value), six.string_types))
        return value


class Bool(Scalar):

    @classmethod
    @nullable
    def marshal(cls, value):
        if not isinstance(value, bool):
            raise ValueError('Input value (%s) is of %s instead of expected %s'
                             % (value, type(value), bool))
        return value


class Int(Scalar):

    @classmethod
    @nullable
    def marshal(cls, value):
        if isinstance(value, int):
            return value
        elif isinstance(value, float) and value.is_integer():
            return int(value)
        else:
            raise ValueError('Input value (%s) is of %s instead of expected %s'
                             ' or %s' % (value, type(value), int, float))


class Float(Scalar):

    @classmethod
    @nullable
    def marshal(cls, value):
        if isinstance(value, float):
            return value
        elif isinstance(value, int):
            return float(value)
        else:
            raise ValueError('Input value (%s) is of %s instead of expected %s'
                             ' or %s' % (value, type(value), int, float))


class UUID(Str):

    @classmethod
    @nullable
    def marshal(cls, value):
        if uuidutils.is_uuid_like(value):
            return value
        else:
            raise ValueError('Input value (%s) is not an UUID' % value)


class IPAddress(Str):

    @classmethod
    @nullable
    def marshal(cls, value):
        try:
            return str(ipaddress.IPv4Address(six.text_type(value)))
        except ipaddress.AddressValueError:
            try:
                ipv6 = ipaddress.IPv6Address(six.text_type(value))
                if ipv6.ipv4_mapped:
                    return str(ipv6.ipv4_mapped)
                else:
                    return str(ipv6)
            except ipaddress.AddressValueError:
                raise ValueError('Input value (%s) is not interprable '
                                 'as an IP address' % value)


class IPNetwork(Str):

    @classmethod
    @nullable
    def marshal(cls, value):
        try:
            return str(ipaddress.ip_network(six.text_type(value)))
        except ValueError:
            raise ValueError('Input value (%s) is not interprable '
                             'as an IP network' % value)


@six.add_metaclass(abc.ABCMeta)
class CongressTypeFiniteDomain(object):
    '''Abstract base class for a Congress type of bounded domain.

    Each type inheriting from this class must have a class variable DOMAIN
    which is a frozenset of the set of values allowed in the type.
    '''
    pass


def create_congress_enum_type(class_name, enum_items, base_type,
                              catch_all_default_value=None):
    '''Return a sub-type of base_type

    representing a value of type base_type from a fixed, finite domain.
    :param enum_items: collection of items forming the domain
    :param catch_all_default_value: value to use for any value outside the
    domain. Defaults to None to disallow any avy value outside the domain.
    '''
    domain = set(enum_items)
    if catch_all_default_value is not None:
        domain.add(catch_all_default_value)

    for item in domain:
        if not base_type.marshal(item) == item:
            raise ValueError

    class NewType(base_type, CongressTypeFiniteDomain):
        DOMAIN = domain
        CATCH_ALL_DEFAULT_VALUE = catch_all_default_value

        @classmethod
        @nullable
        def marshal(cls, value):
            if value not in cls.DOMAIN:
                if cls.CATCH_ALL_DEFAULT_VALUE is None:
                    raise ValueError(
                        'Input value (%s) is not in the expected domain of '
                        'values %s' % (value, cls.DOMAIN))
                else:
                    return cls.CATCH_ALL_DEFAULT_VALUE
            return value

    NewType.__name__ = class_name
    return NewType


class TypesRegistry(object):
    _type_name_to_type_class = {}

    @classmethod
    def register(cls, type_class):
        # skip if type already registered
        if not issubclass(type_class, Scalar):
            raise TypeError('Attempted to register a type which is not a '
                            'subclass of the top type %s.' % Scalar)
        elif str(type_class) in cls._type_name_to_type_class:
            if type_class == cls._type_name_to_type_class[str(type_class)]:
                pass  # type already registered
            else:  # conflicting types with same name
                raise Exception('Attempted to register new type with the same '
                                'name \'%s\' as previously registered type.' %
                                type_class)
        else:  # register new type
            cls._type_name_to_type_class[str(type_class)] = type_class

    @classmethod
    def type_class(cls, type_name):
        return cls._type_name_to_type_class[type_name]


TYPES = [Scalar, Str, Bool, Int, Float, IPAddress, IPNetwork]

for type_class in TYPES:
    TypesRegistry.register((type_class))
