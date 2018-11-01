# Copyright (c) 2013 VMware, Inc. All rights reserved.
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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

try:
    # For Python 3
    import http.client as httplib
except ImportError:
    import httplib
import re

from oslo_config import cfg
from oslo_db import exception as db_exc
from oslo_log import log as logging
from oslo_serialization import jsonutils as json
from oslo_utils import uuidutils
import six
import webob
import webob.dec

from congress.api import error_codes
from congress.common import policy
from congress import exception


LOG = logging.getLogger(__name__)


def error_response(status, error_code, description, data=None):
    """Construct and return an error response.

    Args:
        status: The HTTP status code of the response.
        error_code: The application-specific error code.
        description: Friendly G11N-enabled string corresponding to error_code.
        data: Additional data (not G11N-enabled) for the API consumer.
    """
    raw_body = {'error': {
        'message': description,
        'error_code': error_code,
        'error_data': data
        }
    }
    body = '%s\n' % json.dumps(raw_body)
    return webob.Response(body=body, status=status,
                          content_type='application/json',
                          charset='UTF-8')


NOT_FOUND_RESPONSE = error_response(httplib.NOT_FOUND,
                                    httplib.NOT_FOUND,
                                    "The resource could not be found.")
NOT_SUPPORTED_RESPONSE = error_response(httplib.NOT_IMPLEMENTED,
                                        httplib.NOT_IMPLEMENTED,
                                        "Method not supported")
INTERNAL_ERROR_RESPONSE = error_response(httplib.INTERNAL_SERVER_ERROR,
                                         httplib.INTERNAL_SERVER_ERROR,
                                         "Internal server error")


def original_msg(e):
    '''Undo oslo-messaging added traceback to return original exception msg'''
    msg = e.args[0].split('\nTraceback (most recent call last):')[0]
    if len(msg) != len(e.args[0]):
        if len(msg) > 0 and msg[-1] in ("'", '"'):
            msg = msg[:-1]
        if len(msg) > 1 and msg[0:2] in ('u"', "u'"):
            msg = msg[2:]
        elif len(msg) > 0 and msg[0] in ("'", '"'):
            msg = msg[1:]
        return msg
    else:  # return untouched message is format not as expected
        return e.args[0]


class DataModelException(Exception):
    """Congress API Data Model Exception

    Custom exception raised by API Data Model methods to communicate errors to
    the API framework.
    """

    def __init__(self, error_code, description, data=None,
                 http_status_code=httplib.BAD_REQUEST):
        super(DataModelException, self).__init__(description)
        self.error_code = error_code
        self.description = description
        self.data = data
        self.http_status_code = http_status_code

    @classmethod
    def create(cls, error):
        """Generate a DataModelException from an existing CongressException.

        :param: error: has a 'name' field corresponding to an error_codes
            error-name.  It may also have a 'data' field.
        :returns: a DataModelException properly populated.
        """
        name = getattr(error, "name", None)
        if name:
            error_code = error_codes.get_num(name)
            description = error_codes.get_desc(name)
            http_status_code = error_codes.get_http(name)
        else:
            # Check if it's default http error or else return 'Unknown error'
            error_code = error.code or httplib.BAD_REQUEST
            if error_code not in httplib.responses:
                error_code = httplib.BAD_REQUEST
            description = httplib.responses.get(error_code, "Unknown error")
            http_status_code = error_code

        if str(error):
            description += "::" + original_msg(error)
        return cls(error_code=error_code,
                   description=description,
                   data=getattr(error, 'data', None),
                   http_status_code=http_status_code)

    def rest_response(self):
        return error_response(self.http_status_code, self.error_code,
                              self.description, self.data)


class AbstractApiHandler(object):
    """Abstract handler for API requests.

    Attributes:
        path_regex: The regular expression matching paths supported by this
            handler.
    """

    def __init__(self, path_regex):
        if path_regex[-1] != '$':
            path_regex += "$"
        # we only use 'match' so no need to mark the beginning of string
        self.path_regex = path_regex
        self.path_re = re.compile(path_regex)

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self.path_re.pattern)

    def _get_context(self, request):
        """Return dict of variables in request path."""
        m = self.path_re.match(request.path)
        # remove all the None values before returning
        return dict([(k, v) for k, v in m.groupdict().items()
                     if v is not None])

    def _parse_json_body(self, request):
        content_type = (request.content_type or "application/json").lower()
        if content_type != 'application/json':
            raise DataModelException(
                400, "Unsupported Content-Type; must be 'application/json'")
        if request.charset != 'UTF-8':
            raise DataModelException(
                400, "Unsupported charset: must be 'UTF-8'")
        try:
            request.parsed_body = json.loads(request.body.decode('utf-8'))
        except ValueError as e:
            msg = "Failed to parse body as %s: %s" % (content_type, e)
            raise DataModelException(400, msg)
        return request.parsed_body

    def handles_request(self, request):
        """Return true iff handler supports the request."""
        m = self.path_re.match(request.path)
        return m is not None

    def handle_request(self, request):
        """Handle a REST request.

        :param: request: A webob request object.

        :returns: A webob response object.
        """
        return NOT_SUPPORTED_RESPONSE


class ElementHandler(AbstractApiHandler):
    """API handler for REST element resources.

    REST elements represent individual entities in the data model, and often
    support the following operations:
    - Read a representation of the element
    - Update (replace) the entire element with a new version
    - Update (patch) parts of the element with new values
    - Delete the element

    Elements may also exhibit 'controller' semantics for RPC-style method
    invocation, however this is not currently supported.
    """

    def __init__(self, path_regex, model,
                 collection_handler=None, allow_read=True, allow_actions=True,
                 allow_replace=True, allow_update=True, allow_delete=True):
        """Initialize an element handler.

        :param: path_regex: A regular expression that matches the full path
                to the element.  If multiple handlers match a request path,
                the handler with the highest registration search_index wins.
        :param: model: A resource data model instance
        :param: collection_handler: The collection handler this element
                is a member of or None if the element is not a member of a
                collection.  (Used for named creation of elements)
        :param: allow_read: True if element supports read
        :param: allow_replace: True if element supports replace
        :param: allow_update: True if element supports update
        :param: allow_delete: True if element supports delete

        """
        super(ElementHandler, self).__init__(path_regex)
        self.model = model
        self.collection_handler = collection_handler
        self.allow_read = allow_read
        self.allow_actions = allow_actions
        self.allow_replace = allow_replace
        self.allow_update = allow_update
        self.allow_delete = allow_delete

    def _get_element_id(self, request):
        m = self.path_re.match(request.path)
        if m.groups():
            return m.groups()[-1]  # TODO(pballand): make robust
        return None

    def handle_request(self, request):
        """Handle a REST request.

        :param: request: A webob request object.

        :returns: A webob response object.
        """
        try:
            if request.method == 'GET' and self.allow_read:
                return self.read(request)
            elif request.method == 'POST' and self.allow_actions:
                return self.action(request)
            elif request.method == 'PUT' and self.allow_replace:
                return self.replace(request)
            elif request.method == 'PATCH' and self.allow_update:
                return self.update(request)
            elif request.method == 'DELETE' and self.allow_delete:
                return self.delete(request)
            return NOT_SUPPORTED_RESPONSE
        except db_exc.DBError:
            LOG.exception('Database backend experienced an unknown error.')
            raise exception.DatabaseError

    def read(self, request):
        if not hasattr(self.model, 'get_item'):
            return NOT_SUPPORTED_RESPONSE

        id_ = self._get_element_id(request)
        item = self.model.get_item(id_, request.params,
                                   context=self._get_context(request))
        if item is None:
            return error_response(httplib.NOT_FOUND, 404, 'Not found')
        return webob.Response(body="%s\n" % json.dumps(item),
                              status=httplib.OK,
                              content_type='application/json',
                              charset='UTF-8')

    def action(self, request):
        # Non-CRUD operations must specify an 'action' parameter
        action = request.params.getall('action')
        if len(action) != 1:
            if len(action) > 1:
                errstr = "Action parameter may not be provided multiple times."
            else:
                errstr = "Missing required action parameter."
            return error_response(httplib.BAD_REQUEST, 400, errstr)
        model_method = "%s_action" % action[0].replace('-', '_')
        f = getattr(self.model, model_method, None)
        if f is None:
            return NOT_SUPPORTED_RESPONSE
        try:
            response = f(request.params, context=self._get_context(request),
                         request=request)
            if isinstance(response, webob.Response):
                return response
            return webob.Response(body="%s\n" % json.dumps(response),
                                  status=httplib.OK,
                                  content_type='application/json',
                                  charset='UTF-8')
        except TypeError:
            LOG.exception("Error occurred")
            return NOT_SUPPORTED_RESPONSE

    def replace(self, request):
        if not hasattr(self.model, 'update_item'):
            return NOT_SUPPORTED_RESPONSE

        id_ = self._get_element_id(request)
        try:
            item = self._parse_json_body(request)
            self.model.replace_item(id_, item, request.params,
                                    context=self._get_context(request))
        except KeyError as e:
            if (self.collection_handler and
                    getattr(self.collection_handler, 'allow_named_create',
                            False)):
                return self.collection_handler.create_member(request, id_=id_)
            return error_response(httplib.NOT_FOUND, 404,
                                  original_msg(e) or 'Not found')
        return webob.Response(body="%s\n" % json.dumps(item),
                              status=httplib.OK,
                              content_type='application/json',
                              charset='UTF-8')

    def update(self, request):
        if not (hasattr(self.model, 'update_item') or
                hasattr(self.model, 'get_item')):
            return NOT_SUPPORTED_RESPONSE

        context = self._get_context(request)
        id_ = self._get_element_id(request)
        item = self.model.get_item(id_, request.params, context=context)
        if item is None:
            return error_response(httplib.NOT_FOUND, 404, 'Not found')

        updates = self._parse_json_body(request)
        item.update(updates)
        self.model.replace_item(id_, item, request.params, context=context)
        return webob.Response(body="%s\n" % json.dumps(item),
                              status=httplib.OK,
                              content_type='application/json',
                              charset='UTF-8')

    def delete(self, request):
        if not hasattr(self.model, 'delete_item'):
            return NOT_SUPPORTED_RESPONSE

        id_ = self._get_element_id(request)
        try:
            item = self.model.delete_item(
                id_, request.params, context=self._get_context(request))
            return webob.Response(body="%s\n" % json.dumps(item),
                                  status=httplib.OK,
                                  content_type='application/json',
                                  charset='UTF-8')
        except KeyError as e:
            LOG.exception("Error occurred")
            return error_response(httplib.NOT_FOUND, 404,
                                  original_msg(e) or 'Not found')


class CollectionHandler(AbstractApiHandler):
    """API handler for REST collection resources.

    REST collections represent collections of entities in the data model, and
    often support the following operations:
    - List elements in the collection
    - Create new element in the collection

    The following less-common collection operations are NOT SUPPORTED:
    - Replace all elements in the collection
    - Delete all elements in the collection
    """

    def __init__(self, path_regex, model,
                 allow_named_create=True, allow_list=True, allow_create=True,
                 allow_replace=False):
        """Initialize a collection handler.

        :param: path_regex: A regular expression matching the collection base
            path.
        :param: model: A resource data model instance
            allow_named_create: True if caller can specify ID of new items.
            allow_list: True if collection supports listing elements.
            allow_create: True if collection supports creating elements.
        """
        super(CollectionHandler, self).__init__(path_regex)
        self.model = model
        self.allow_named_create = allow_named_create
        self.allow_list = allow_list
        self.allow_create = allow_create
        self.allow_replace = allow_replace

    def handle_request(self, request):
        """Handle a REST request.

        :param: request: A webob request object.

        :returns: A webob response object.
        """
        # NOTE(arosen): only do policy.json if keystone is used for now.
        if cfg.CONF.auth_strategy == "keystone":
            context = request.environ['congress.context']
            target = {
                'project_id': context.project_id,
                'user_id': context.user_id
            }
            # NOTE(arosen): today congress only enforces API policy on which
            # API calls we allow tenants to make with their given roles.
            action_type = self._get_action_type(request.method)
            # FIXME(arosen): There should be a cleaner way to do this.
            model_name = self.path_regex.split('/')[1]
            action = "%s_%s" % (action_type, model_name)
            # TODO(arosen): we should handle serializing the
            # response in one place
            try:
                policy.enforce(context, action, target)
            except exception.PolicyNotAuthorized as e:
                LOG.info(e)
                return webob.Response(body=six.text_type(e), status=e.code,
                                      content_type='application/json',
                                      charset='UTF-8')
        if request.method == 'GET' and self.allow_list:
            return self.list_members(request)
        elif request.method == 'POST' and self.allow_create:
            return self.create_member(request)
        elif request.method == 'PUT' and self.allow_replace:
            return self.replace_members(request)
        return NOT_SUPPORTED_RESPONSE

    def _get_action_type(self, method):
        if method == 'GET':
            return 'get'
        elif method == 'POST':
            return 'create'
        elif method == 'DELETE':
            return 'delete'
        elif method == 'PUT' or method == 'PATCH':
            return 'update'
        else:
            # should never get here but just in case ;)
            # FIXME(arosen) raise NotImplemented instead and
            # make sure we return that as an http code.
            raise TypeError("Invalid HTTP Method")

    def list_members(self, request):
        if not hasattr(self.model, 'get_items'):
            return NOT_SUPPORTED_RESPONSE
        items = self.model.get_items(request.params,
                                     context=self._get_context(request))
        if items is None:
            return error_response(httplib.NOT_FOUND, 404, 'Not found')
        elif 'results' not in items:
            return error_response(httplib.NOT_FOUND, 404, 'Not found')

        body = "%s\n" % json.dumps(items, indent=2)
        return webob.Response(body=body, status=httplib.OK,
                              content_type='application/json',
                              charset='UTF-8')

    def create_member(self, request, id_=None):
        if not hasattr(self.model, 'add_item'):
            return NOT_SUPPORTED_RESPONSE
        item = self._parse_json_body(request)
        context = self._get_context(request)
        try:
            model_return_value = self.model.add_item(
                item, request.params, id_, context=context)
        except KeyError as e:
            LOG.exception("Error occurred")
            return error_response(httplib.CONFLICT, httplib.CONFLICT,
                                  original_msg(e) or 'Element already exists')
        if model_return_value is None:  # webhook request
            return webob.Response(body={},
                                  status=httplib.OK,
                                  content_type='application/json',
                                  charset='UTF-8')
        else:
            id_, item = model_return_value
            item['id'] = id_
            return webob.Response(body="%s\n" % json.dumps(item),
                                  status=httplib.CREATED,
                                  content_type='application/json',
                                  location="%s/%s" % (request.path, id_),
                                  charset='UTF-8')

    def replace_members(self, request):
        if not hasattr(self.model, 'replace_items'):
            return NOT_SUPPORTED_RESPONSE
        items = self._parse_json_body(request)
        context = self._get_context(request)
        try:
            self.model.replace_items(items, request.params, context)
        except KeyError as e:
            LOG.exception("Error occurred")
            return error_response(httplib.BAD_REQUEST, httplib.BAD_REQUEST,
                                  original_msg(e) or
                                  'Update %s Failed' % context['table_id'])
        return webob.Response(body="", status=httplib.OK,
                              content_type='application/json',
                              charset='UTF-8')


class SimpleDataModel(object):
    """A container providing access to a single type of data."""

    def __init__(self, model_name):
        self.model_name = model_name
        self.items = {}

    @staticmethod
    def _context_str(context):
        context = context or {}
        return ".".join(
            ["%s:%s" % (k, context[k]) for k in sorted(context.keys())])

    def get_items(self, params, context=None):
        """Get items in model.

        :param: params: A dict-like object containing parameters
                    from the request query string and body.
        :param: context: Key-values providing frame of reference of request

        :returns: A dict containing at least a 'results' key whose value is
                 a list of items in the model.  Additional keys set in the
                 dict will also be rendered for the user.
        """
        cstr = self._context_str(context)
        results = list(self.items.setdefault(cstr, {}).values())
        return {'results': results}

    def add_item(self, item, params, id_=None, context=None):
        """Add item to model.

        :param: item: The item to add to the model
        :param: params: A dict-like object containing parameters
                    from the request query string and body.
        :param: The ID of the item, or None if an ID should be generated
        :param: context: Key-values providing frame of reference of request

        :returns: Tuple of (ID, newly_created_item)

        :raises KeyError: ID already exists.
        :raises DataModelException: Addition cannot be performed.
        """
        cstr = self._context_str(context)
        if id_ is None:
            id_ = uuidutils.generate_uuid()
        if id_ in self.items.setdefault(cstr, {}):
            raise KeyError("Cannot create item with ID '%s': "
                           "ID already exists" % id_)
        self.items[cstr][id_] = item
        return (id_, item)

    def get_item(self, id_, params, context=None):
        """Retrieve item with id id\_ from model.

        :param: id\_: The ID of the item to retrieve
        :param: params: A dict-like object containing parameters
                    from the request query string and body.
        :param: context: Key-values providing frame of reference of request

        :returns: The matching item or None if item with id\_ does not exist.
        """
        cstr = self._context_str(context)
        return self.items.setdefault(cstr, {}).get(id_)

    def update_item(self, id_, item, params, context=None):
        """Update item with id\_ with new data.

        :param: id\_: The ID of the item to be updated
            item: The new item
        :param: params: A dict-like object containing parameters
                    from the request query string and body.
        :param: context: Key-values providing frame of reference of request

        :returns: The updated item.

        :raises KeyError: Item with specified id\_ not present.
        :raises DataModelException: Update cannot be performed.
        """
        cstr = self._context_str(context)
        if id_ not in self.items.setdefault(cstr, {}):
            raise KeyError("Cannot update item with ID '%s': "
                           "ID does not exist" % id_)
        self.items.setdefault(cstr, {})[id_] = item
        return item

    def replace_item(self, id_, item, params, context=None):
        """Replace item with id\_ with new data.

        :param: id\_: The ID of the item to be replaced
            item: The new item
        :param: params: A dict-like object containing parameters
                    from the request query string and body.
        :param: context: Key-values providing frame of reference of request

        :returns: The new item after replacement.

        :raises KeyError: Item with specified id\_ not present.
        :raises DataModelException: Replacement cannot be performed.
        """
        cstr = self._context_str(context)
        if id_ not in self.items.setdefault(cstr, {}):
            raise KeyError("Cannot replace item with ID '%s': "
                           "ID does not exist" % id_)
        self.items.setdefault(cstr, {})[id_] = item
        return item

    def delete_item(self, id_, params, context=None):
        """Remove item from model.

        :param: id\_: The ID of the item to be removed
        :param: params: A dict-like object containing parameters
                    from the request query string and body.
        :param: context: Key-values providing frame of reference of request

        :returns: The removed item.

        :raises KeyError: Item with specified id\_ not present.
        """
        cstr = self._context_str(context)
        ret = self.items.setdefault(cstr, {})[id_]
        del self.items[cstr][id_]
        return ret

    def replace_items(self, items, params, context=None):
        """Replace items in the model.

        :param: items: A dict-like object containing new data
        :param: params: A dict-like object containing parameters
        :param: context: Key-values providing frame of reference of request
        :returns: None
        """
        self.items = items
