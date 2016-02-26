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
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import sys

from oslo_config import cfg
from oslo_log import log as logging
import six

from congress import utils


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
    # FIXME(thinrichs): this exception is overly complex and should
    #  not include HTTP codes at all.  Proper fix needs to touch
    #  too many files that others are currently working on.
    code = 500
    headers = {}
    safe = False

    def __init__(self, message=None, **kwargs):
        """FIXME(thinrichs):

        We just want name and data as fields.
        :param name will be a name from error_codes, which includes the basic
        message.
        :param data will contain specifics for this instance of the
        exception, e.g. a description error message.
        """
        self.data = kwargs.get('data', None)
        self.name = kwargs.get('name', None)

        # TODO(thinrichs): remove the rest of this (except the call to super)
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
                for name, value in kwargs.items():
                    LOG.error("%s: %s", name, value)    # noqa

                if CONF.fatal_exception_format_errors:
                    six.reraise(exc_info[0], exc_info[1], exc_info[2])
                else:
                    # at least get the core message out if something happened
                    message = self.msg_fmt

        super(CongressException, self).__init__(message)

    def format_message(self):
        # NOTE(mrodden): use the first argument to the python Exception object
        # which should be our full CongressException message, (see __init__)
        return self.args[0]

# FIXME(thinrichs): Get rid of the ones below and instead create exception
#   classes to represent the parts of the code that generated the exception,
#   e.g. datasources versus policy compiler versus policy runtime.


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


# NOTE(thinrichs): The following represent different kinds of
#   exceptions: the policy compiler and the policy runtime, respectively.
class PolicyException(CongressException):
    def __init__(self, msg=None, obj=None, line=None, col=None,
                 name=None, data=None, **kwargs):
        CongressException.__init__(self, message=msg, name=name, data=data)
        self.obj = obj
        self.location = utils.Location(line=line, col=col, obj=obj)

    def __str__(self):
        s = str(self.location)
        if len(s) > 0:
            s = " at" + s
        return CongressException.__str__(self) + s


class PolicyRuntimeException(CongressException):
    pass


class IncompleteSchemaException(CongressException):
    pass


class DataServiceError (Exception):
    pass


class BadConfig(BadRequest):
    pass


class DatasourceDriverException(CongressException):
    pass


class MissingRequiredConfigOptions(BadConfig):
    msg_fmt = _("Missing required config options: %(missing_options)s")


class InvalidDriver(BadConfig):
    msg_fmt = _("Invalid driver: %(driver)s")


class InvalidDriverOption(BadConfig):
    msg_fmt = _("Invalid driver options: %(invalid_options)s")


class DatasourceNameInUse(Conflict):
    msg_fmt = _("Datasource already in use with name %(value)s")


class DatasourceNotFound(NotFound):
    msg_fmt = _("Datasource not found %(id)s")


class DriverNotFound(NotFound):
    msg_fmt = _("Driver not found %(id)s")


class DatasourceCreationError(BadConfig):
    msg_fmt = _("Datasource could not be created on the DSE: %(value)s")
