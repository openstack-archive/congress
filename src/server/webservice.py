#!/usr/bin/env python
# Copyright (c) 2013 VMware, Inc. All rights reserved.

import httplib
import json
import re
import uuid
import webob
import webob.dec

import ovs.vlog
vlog = ovs.vlog.Vlog(__name__)


NOT_SUPPORTED_RESPONSE = webob.Response(body="Method not supported",
                                        status=httplib.NOT_IMPLEMENTED)


def errorResponse(status, error_code, description, data=None):
    """Construct and return an error response.

    Args:
        status: The HTTP status code of the response.
        error_code: The application-specific error code.
        description: Friendly G11N-enabled string corresponding ot error_code.
        data: Additional data (not G11N-enabled) for the API consumer.
    """
    data = {
        'error_code': error_code,
        'descripton': description,
        'error_data': data
    }
    body = '%s\n' % json.dumps(data)
    return webob.Response(body=body, status=status,
                          content_type='application/json')


class ApiApplication(object):
    def __init__(self):
        self.handlers = []

    @webob.dec.wsgify(RequestClass=webob.Request)
    def __call__(self, request):
        handler = self.get_handler(request)
        if handler:
            vlog.dbg("Handling request '%s %s' with %s"
                     % (request.method, request.path, str(handler)))
            return handler.handle_request(request)
        else:
            return NOT_SUPPORTED_RESPONSE

    def register_handler(self, handler, search_index=None):
        if search_index is not None:
            self.handlers.insert(search_index, handler)
        else:
            self.handlers.append(handler)

    def get_handler(self, request):
        """Find a handler for a REST request.

        Args:
           request: A webob request object.

        Returns:
            A handler instance or None.
        """
        for h in self.handlers:
            if h.handles_request(request):
                return h
        return None


class AbstractApiHandler(object):
    def __init__(self, path_regex):
        self.parent_handler = None
        self.child_handlers = []

        if path_regex[-1] != '$':
            path_regex += "$"
        # we only use 'match' so no need to mark the beginning of string
        self.path_regex = path_regex
        self.path_re = re.compile(path_regex)

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self.path_re.pattern)

    def handles_request(self, request):
        m = self.path_re.match(request.path)
        return m is not None

    def handle_request(self, request):
        """Handle a REST request.

        Args:
           request: A webob request object.

        Returns:
            A webob response object.
        """
        return NOT_SUPPORTED_RESPONSE


class ElementHandler(AbstractApiHandler):
    """API handler for REST element resources.
    """
    #TODO: validation

    def __init__(self, path_regex, model, collection_handler=None):
        """Initialize an element handler.

        Args:
            path_regex: A regular expression that matches the full path
                to the element.  If multiple handlers match a request path,
                the handler with the highhest registration search_index wins.
            model: A resource data model instance
            collection_handler: The collection handler this elemeent
                is a member of or None if the element is not a member of a
                collection.

        """
        super(ElementHandler, self).__init__(path_regex)
        self.model = model
        self.collection_handler = collection_handler

    def _get_element_id(self, request):
        m = self.path_re.match(request.path)
        if m.groups():
            return m.groups()[-1]  #TODO: make robust
        return None

    def handle_request(self, request):
        """Handle a REST request.

        Args:
           request: A webob request object.

        Returns:
            A webob response object.
        """
        if request.method == 'GET':
            return self.read(request)
        #TODO(pjb): POST for controller semantics
        elif request.method == 'PUT':
            return self.replace(request)
        elif request.method == 'PATCH':
            return self.update(request)
        elif request.method == 'DELETE':
            return self.delete(request)
        return NOT_SUPPORTED_RESPONSE

    def read(self, request):
        if not hasattr(self.model, 'get_item'):
            return NOT_SUPPORTED_RESPONSE

        id_ = self._get_element_id(request)
        item = self.model.get_item(id_)
        if item is None:
            return errorResponse(httplib.NOT_FOUND, 404, 'Not found')
        return webob.Response(body=json.dumps(item), status=httplib.OK,
                              content_type='application/json')

    def replace(self, request):
        if not hasattr(self.model, 'update_item'):
            return NOT_SUPPORTED_RESPONSE

        id_ = self._get_element_id(request)
        try:
            item = json.loads(request.body)
            self.model.update_item(id_, item)
        except KeyError:
            if (self.collection_handler and
                getattr(self.collection_handler, 'allow_named_create', False)):
                return self.collection_handler.create_member(request, id_=id_)
            return errorResponse(httplib.NOT_FOUND, 404, 'Not found')
        return webob.Response(body=json.dumps(item), status=httplib.OK,
                              content_type='application/json')

    def update(self, request):
        if not (hasattr(self.model, 'update_item') or
                hasattr(self.model, 'get_tiem')):
            return NOT_SUPPORTED_RESPONSE

        id_ = self._get_element_id(request)
        item = self.model.get_item(id_)
        if item is None:
            return errorResponse(httplib.NOT_FOUND, 404, 'Not found')

        updates = json.loads(request.body)
        item.update(updates)
        self.model.update_item(id_, item)
        return webob.Response(body=json.dumps(item), status=httplib.OK,
                              content_type='application/json')

    def delete(self, request):
        if not hasattr(self.model, 'delete_item'):
            return NOT_SUPPORTED_RESPONSE

        id_ = self._get_element_id(request)
        try:
            item = self.model.delete_item(id_)
            return webob.Response(body=json.dumps(item), status=httplib.OK,
                                  content_type='application/json')
        except KeyError:
            return errorResponse(httplib.NOT_FOUND, 404, 'Not found')


class CollectionHandler(AbstractApiHandler):
    """API handler for REST collection resources.
    """
    #TODO: validation

    def __init__(self, path_regex, model, allow_named_create=True):
        """Initialize a collection handler.

        Args:
            path_regex: A regular expression matching the collection base path.
            model: TODO
            element_handler_factor: A callable that returns a new element
                handler.
        """
        super(CollectionHandler, self).__init__(path_regex)
        self.model = model
        self.allow_named_create = allow_named_create

    def handle_request(self, request):
        """Handle a REST request.

        Args:
           request: A webob request object.

        Returns:
            A webob response object.
        """
        if request.method == 'GET':
            return self.list_members(request)
        elif request.method == 'POST':
            return self.create_member(request)
        return NOT_SUPPORTED_RESPONSE

    def list_members(self, request):
        items = self.model.get_items().values()
        body = "%s\n" % json.dumps(items, indent=2)
        return webob.Response(body=body, status=httplib.OK,
                              content_type='application/json')

    def create_member(self, request, id_=None):
        item = json.loads(request.body)
        try:
            id_ = self.model.add_item(item, id_)
        except KeyError:
            return errorResponse(httplib.CONFLICT, httplib.CONFLICT,
                                 'Element already exists')
        item['id'] = id_

        return webob.Response(body=json.dumps(item), status=httplib.CREATED,
                              content_type='application/json',
                              location="%s/%s" %(request.path, id_))


class RowCollectionHandler(CollectionHandler):
    pass


class RowElementHandler(ElementHandler):
    """API handler for table row elements.
    """

    def _get_element_id(self, request):
        m = self.path_re.match(request.path)
        print 'groups', m.groups()
        if m.groups():
            return m.groups()[-1]  #TODO: make robust
        return None



class SimpleDataModel(object):
    """An in-memory data model.
    """

    def __init__(self):
        self.items = {}

    def get_items(self):
        """Get items in model.

        Returns: A dict of {id, item} for all items in model.
        """
        return self.items

    def add_item(self, item, id_=None):
        """Add item to model.

        Args:
            item: The item to add to the model.
            id_: The ID of the item, or None if an ID should be generated

        Returns:
             The ID of the newly added item.

        Raises:
            KeyError: ID already exists.
        """
        if id_ is None:
            id_ = str(uuid.uuid4())
        if id_ in self.items:
            raise KeyError("Cannot create item with ID '%s': "
                           "ID already exists")
        self.items[id_] = item
        return id_

    def get_item(self, id_):
        """Retrieve item with id id_ from model.

        Args:
            id_: The ID of the item to retrieve.

        Returns:
             The matching item or None if item with id_ does not exist.
        """
        return self.items.get(id_)

    def update_item(self, id_, item):
        """Update item with id_ with new data.

        Args:
            id_: The ID of the item to be updated.
            item: The new item.

        Returns:
             The updated item.

        Raises:
            KeyError: Item with specified id_ not present.
        """
        if id_ not in self.items:
            raise KeyError("Cannot update item with ID '%s': "
                           "ID does not exist")
        self.items[id_] = item
        return item

    def delete_item(self, id_):
        """Remove item from model.

        Args:
            id_: The ID of the item to be removed.

        Returns:
             The removed item.

        Raises:
            KeyError: Item with specified id_ not present.
        """
        ret = self.items[id_]
        del self.items[id_]
        return ret




class PolicyDataModel(object):
    """An in-memory policy data model.
    """

    def __init__(self):
        self.rules = []

    def get_item(self, id_):
        return {'rules': self.rules}

    def update_item(self, id_, item):
        self.rules = item['rules']
        return self.get_item(None)


