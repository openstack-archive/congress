# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
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

"""Congress base exception handling."""

import sys

from oslo_config import cfg

from congress.openstack.common import log as logging
from congress.utils import Location


LOG = logging.getLogger(__name__)

exc_log_opts = [
    cfg.BoolOpt('fatal_exception_format_errors',
                default=False,
                help='Make exception message format errors fatal'),
]

CONF = cfg.CONF
CONF.register_opts(exc_log_opts)


class CongressException(Exception):
    """Base Congress Exception

    To correctly use this class, inherit from it and define
    a 'msg_fmt' property. That msg_fmt will get printf'd
    with the keyword arguments provided to the constructor.

    """
    msg_fmt = _("An unknown exception occurred.")
    # FIXME(arosen) the http_code should not live in the base exception class!
    code = 500
    headers = {}
    safe = False

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs

        if 'code' not in self.kwargs:
            try:
                self.kwargs['code'] = self.code
            except AttributeError:
                pass

        if not message:
            try:
                message = self.msg_fmt % kwargs

            except Exception:
                exc_info = sys.exc_info()
                # kwargs doesn't match a variable in the message
                # log the issue and the kwargs
                LOG.exception(_('Exception in string format operation'))
                for name, value in kwargs.iteritems():
                    LOG.error("%s: %s", name, value)    # noqa

                if CONF.fatal_exception_format_errors:
                    raise exc_info[0], exc_info[1], exc_info[2]
                else:
                    # at least get the core message out if something happened
                    message = self.msg_fmt

        super(CongressException, self).__init__(message)

    def format_message(self):
        # NOTE(mrodden): use the first argument to the python Exception object
        # which should be our full CongressException message, (see __init__)
        return self.args[0]


class Forbidden(CongressException):
    msg_fmt = _("Not authorized.")
    code = 403


class Conflict(CongressException):
    msg_fmt = _("Conflict")
    code = 409


class BadRequest(CongressException):
    msg_fmt = _("Bad request")
    code = 400


class NotFound(CongressException):
    msg_fmt = _("Resource not found.")
    code = 404


class PolicyNotAuthorized(Forbidden):
    msg_fmt = _("Policy doesn't allow %(action)s to be performed.")


# FIXME(arosen) This should probably inherit from CongresException
class InvalidParamException(Exception):
    pass


class DataSourceConfigException(Exception):
    pass


class DuplicateTableName(Exception):
    pass


class InvalidTranslationType(Exception):
    pass


class DanglingReference(Conflict):
    pass


class PolicyException(CongressException):
    def __init__(self, msg, obj=None, line=None, col=None):
        CongressException.__init__(self, msg)
        self.obj = obj
        self.location = Location(line=line, col=col, obj=obj)

    def __str__(self):
        s = str(self.location)
        if len(s) > 0:
            s = " at" + s
        return CongressException.__str__(self) + s


class PolicyRuntimeException(CongressException):
    pass
