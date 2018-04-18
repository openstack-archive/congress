# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2011 Justin Santa Barbara
# All Rights Reserved.
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

"""Utilities and helper functions."""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import contextlib
import json
import os
import shutil
import tempfile

from oslo_config import cfg
from oslo_log import log as logging
import six

LOG = logging.getLogger(__name__)

utils_opts = [
    cfg.StrOpt('tempdir',
               help='Explicitly specify the temporary working directory'),
]
CONF = cfg.CONF
CONF.register_opts(utils_opts)


# Note(thread-safety): blocking function
@contextlib.contextmanager
def tempdir(**kwargs):
    argdict = kwargs.copy()
    if 'dir' not in argdict:
        argdict['dir'] = CONF.tempdir
    tmpdir = tempfile.mkdtemp(**argdict)
    try:
        yield tmpdir
    finally:
        try:
            shutil.rmtree(tmpdir)
        except OSError as e:
            LOG.error(('Could not remove tmpdir: %s'), e)


def value_to_congress(value):
    if isinstance(value, six.string_types):
        # TODO(ayip): This throws away high unicode data because congress does
        # not have full support for unicode yet.  We'll need to fix this to
        # handle unicode coming from datasources.
        try:
            six.text_type(value).encode('ascii')
        except UnicodeEncodeError:
            LOG.warning('Ignoring non-ascii characters')
        # Py3: decode back into str for compat (bytes != str)
        return six.text_type(value).encode('ascii', 'ignore').decode('ascii')
    # Check for bool before int, because True and False are also ints.
    elif isinstance(value, bool):
        return str(value)
    elif (isinstance(value, six.integer_types) or
          isinstance(value, float)):
        return value
    return str(value)


def tuple_to_congress(value_tuple):
    return tuple(value_to_congress(v) for v in value_tuple)


# Note(thread-safety): blocking function
def create_datasource_policy(bus, datasource, engine):
    # Get the schema for the datasource using
    # Note(thread-safety): blocking call
    schema = bus.rpc(datasource, 'get_datasource_schema',
                     {'source_id': datasource})
    # Create policy and sets the schema once datasource is created.
    args = {'name': datasource, 'schema': schema}
    # Note(thread-safety): blocking call
    bus.rpc(engine, 'initialize_datasource', args)


def get_root_path():
    return os.path.dirname(os.path.dirname(__file__))


class Location (object):
    """A location in the program source code."""

    __slots__ = ['line', 'col']

    def __init__(self, line=None, col=None, obj=None):
        try:
            self.line = obj.location.line
            self.col = obj.location.col
        except AttributeError:
            pass
        self.col = col
        self.line = line

    def __str__(self):
        s = ""
        if self.line is not None:
            s += " line: {}".format(self.line)
        if self.col is not None:
            s += " col: {}".format(self.col)
        return s

    def __repr__(self):
        return "Location(line={}, col={})".format(
            repr(self.line), repr(self.col))

    def __hash__(self):
        return hash(('Location', hash(self.line), hash(self.col)))


def pretty_json(data):
    print(json.dumps(data, sort_keys=True,
                     indent=4, separators=(',', ': ')))


def pretty_rule(rule_str):
    # remove line breaks
    rule_str = ''.join(
        [line.strip() for line in rule_str.strip().splitlines()])

    head_and_body = rule_str.split(':-')

    # drop empty body
    head_and_body = [item.strip()
                     for item in head_and_body if len(item.strip()) > 0]

    head = head_and_body[0]
    if len(head_and_body) == 1:
        return head
    else:
        body = head_and_body[1]
        # split the literal by spliting on ')'
        body_list = body.split(')')
        body_list = body_list[:-1]  # drop part behind the final ')'

        new_body_list = []
        for literal in body_list:
            # remove commas between literals
            if literal[0] == ',':
                literal = literal[1:]
            # add back the ')', also add an indent
            new_body_list.append('  ' + literal.strip() + ')')

        pretty_rule_str = head + " :-\n" + ",\n".join(new_body_list)
        return pretty_rule_str
