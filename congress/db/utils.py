# Copyright 2018 - VMware Inc
# Copyright 2016 - Nokia Networks
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import functools

from oslo_db import exception as db_exc
from oslo_log import log as logging
import tenacity

LOG = logging.getLogger(__name__)

_RETRY_ERRORS = (db_exc.DBDeadlock,)


def retry_on_db_error(func):
    """Decorates the given function so that it retries on DB deadlock errors.

    :param func: Function to decorate.
    :return: Decorated function.
    """
    @functools.wraps(func)
    @tenacity.retry(
        reraise=True,
        retry=tenacity.retry_if_exception_type(_RETRY_ERRORS),
        stop=tenacity.stop_after_attempt(10),
        wait=tenacity.wait_incrementing(start=0, increment=0.1, max=2)
    )
    def decorate(*args, **kw):
        try:
            return func(*args, **kw)
        except db_exc.DBDeadlock:
            LOG.exception(
                "DB error detected, operation will be retried: %s", func)
            raise
    return decorate
