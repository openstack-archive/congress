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

try:
    # For Python 3
    import http.client as httplib
except ImportError:
    import httplib
import json
import uuid

import mock
import webob

from congress.api import webservice
from congress.tests import base


class TestSimpleDataModel(base.TestCase):
    # if random ID matches, go to Vegas or file a uuid library bug
    UNADDED_ID = str(uuid.uuid4())
    CONTEXTS = [None, {'a': 'ctxt1'}, {'b': 'ctxt2', 'c': 'ctxt3'}]

    def test_get_items(self):
        """Test API DataModel get_items functionality."""
        model = webservice.SimpleDataModel("test")
        for context in self.CONTEXTS:
            ret = model.get_items({}, context=context)
            self.assertEqual(
                ret.keys(), ['results'],
                "get_items returns dict with single 'results' key")
            self.assertEqual(
                tuple(ret['results']), tuple(),
                "get_items of empty model returns empty results list")
            items = [{"i1": "%s/foo" % context}, {"i2": "%s/bar" % context}]
            for item in items:
                model.add_item(item, {}, context=context)
            ret2 = model.get_items({}, context=context)
            self.assertEqual(sorted(ret2['results']), sorted(items),
                             "get_items() returns all items added to model")

    def test_add_item(self):
        """Test API DataModel add_item functionality."""
        model = webservice.SimpleDataModel("test")
        assigned_ids = set()
        for context in self.CONTEXTS:
            items = ["%s/foo" % context, "%s/bar" % context]
            ret = model.add_item(items[0], {}, context=context)
            self.assertIsInstance(ret, tuple, "add_item returns a tuple")
            self.assertEqual(len(ret), 2,
                             "add_item returns tuple of length 2")
            self.assertNotIn(ret[0], assigned_ids,
                             "add_item assigned unique ID")
            assigned_ids.add(ret[0])
            self.assertEqual(ret[1], items[0], "add_item returned added item")

            ret = model.add_item(items[1], {}, 'myid', context=context)
            self.assertEqual(ret[0], 'myid',
                             "add_item returned provided ID")
            self.assertEqual(ret[1], items[1], "add_item returned added item")

    def test_get_item(self):
        """Test API DataModel get_item functionality."""
        model = webservice.SimpleDataModel("test")
        for context in self.CONTEXTS:
            items = ["%s/foo" % context, "%s/bar" % context]
            id_ = model.add_item(items[0], {}, context=context)[0]
            ret = model.get_item(id_, {}, context=context)
            self.assertEqual(ret, items[0],
                             "get_item(assigned_id) returns proper item")

            id_ = 'myid'
            ret = model.get_item(id_, {}, context=context)
            self.assertIsNone(ret,
                              "get_item(unadded_provided_id) returns None")
            model.add_item(items[1], {}, id_, context=context)
            ret = model.get_item(id_, {}, context=context)
            self.assertEqual(ret, items[1],
                             "get_item(provided_id) returned added item")

            ret = model.get_item(self.UNADDED_ID, {}, context=context)
            self.assertIsNone(ret, "get_item(unadded_id) returns None")

    def test_update_item(self):
        """Test API DataModel update_item functionality."""
        model = webservice.SimpleDataModel("test")
        for context in self.CONTEXTS:
            items = ["%s/foo%d" % (context, i) for i in [0, 1, 2]]
            id_, item = model.add_item(items[0], {}, context=context)
            self.assertNotEqual(item, items[1], "item not yet updated")
            ret = model.update_item(id_, items[1], {}, context=context)
            self.assertEqual(ret, items[1],
                             "update_item returned updated item")
            ret = model.get_item(id_, {}, context=context)
            self.assertEqual(ret, items[1],
                             "get_item(updated_item_id) returns updated item")

            self.assertNotEqual(item, items[2], "item not yet reupdated")
            ret = model.update_item(id_, items[2], {}, context=context)
            self.assertEqual(ret, items[2],
                             "update_item returned reupdated item")
            ret = model.get_item(id_, {}, context=context)
            self.assertEqual(
                ret, items[2],
                "get_item(reupdated_item_id) returns reupdated item")

            self.assertRaises(KeyError, model.update_item,
                              self.UNADDED_ID, 'blah', {}, context)

    def test_delete_item(self):
        """Test API DataModel delete_item functionality."""
        model = webservice.SimpleDataModel("test")

        for context in self.CONTEXTS:
            item_ids = []
            items = ["%s/foo%d" % (context, i) for i in [0, 1, 2]]
            for i in range(len(items)):
                id_, item = model.add_item(items[i], {}, context=context)
                item_ids.append(id_)

            for i in range(len(items)):
                ret = model.delete_item(item_ids[i], {}, context=context)
                self.assertEqual(ret, items[i],
                                 "delete_item returned deleted item")
                self.assertRaises(KeyError, model.delete_item, item_ids[i],
                                  {}, context)
            self.assertEqual(
                len(model.get_items({}, context=context)['results']), 0,
                "all items deleted")

            self.assertRaises(KeyError, model.delete_item, self.UNADDED_ID,
                              {}, context)


class TestAbstractHandler(base.TestCase):
    def test_parse_json_body(self):
        abstract_handler = webservice.AbstractApiHandler(r'/')
        request = mock.MagicMock()
        data = {"some": ["simple", "json"]}
        serialized_data = json.dumps({"some": ["simple", "json"]})
        invalid_json = 'this is not valid JSON'

        # correctly assume application/json when no content-type header
        request = webob.Request.blank('/')
        self.assertEqual(request.content_type, '')
        request.body = serialized_data
        ret = abstract_handler._parse_json_body(request)
        self.assertEqual(ret, data)

        # correctly validate valid content-type headers
        for ct in ['application/json',
                   'Application/jSoN',
                   'application/json; charset=utf-8',
                   'apPLICAtion/JSOn; charset=UtF-8',
                   'apPLICAtion/JSOn; CHARset=utf-8; IGnored=c',
                   'application/json; ignored_param=a; ignored2=b']:
            request = webob.Request.blank('/', content_type=ct)
            request.body = serialized_data
            try:
                ret = abstract_handler._parse_json_body(request)
            except Exception:
                self.fail("accepts content type '%s'" % ct)
            self.assertEqual(ret, data, "Accepts content type '%s'" % ct)

        # correctly fail on invalid content-type headers
        request = webob.Request.blank('/', content_type='text/json')
        request.body = serialized_data
        self.assertRaises(webservice.DataModelException,
                          abstract_handler._parse_json_body, request)

        # enforce unspecified or utf-8 charset
        # valid charset checked above, just need to check invalid
        request = webob.Request.blank(
            '/', content_type='application/json; charset=utf-16')
        request.body = serialized_data
        self.assertRaises(webservice.DataModelException,
                          abstract_handler._parse_json_body, request)

        # raise DataModelException on non-JSON body
        request = webob.Request.blank(
            '/', content_type='application/json; charset=utf-8')
        request.body = invalid_json
        self.assertRaises(webservice.DataModelException,
                          abstract_handler._parse_json_body, request)


class TestElementHandler(base.TestCase):
    def test_read(self):
        # TODO(pballand): write tests
        pass

    def test_action(self):
        element_handler = webservice.ElementHandler(r'/', '')
        element_handler.model = webservice.SimpleDataModel("test")
        request = mock.MagicMock()
        request.path = "/"

        response = element_handler.action(request)
        self.assertEqual(400, response.status_code)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(json.loads(response.body)['error']['message'],
                         "Missing required action parameter.")

        request.params = mock.MagicMock()
        request.params.getall.return_value = ['do_test']
        request.params["action"] = "do_test"
        request.path = "/"
        response = element_handler.action(request)
        self.assertEqual(501, response.status_code)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(json.loads(response.body)['error']['message'],
                         "Method not supported")

        # test action impl returning python primitives
        simple_data = [1, 2]
        element_handler.model.do_test_action = lambda *a, **kwa: simple_data
        response = element_handler.action(request)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(json.loads(response.body), simple_data)

        # test action impl returning custom webob response
        custom_data = webob.Response(body="test", status=599,
                                     content_type="custom/test")
        element_handler.model.do_test_action = lambda *a, **kwa: custom_data
        response = element_handler.action(request)
        self.assertEqual(599, response.status_code)
        self.assertEqual('custom/test', response.content_type)
        self.assertEqual(response.body, "test")

    def test_replace(self):
        # TODO(pballand): write tests
        pass

    def test_update(self):
        # TODO(pballand): write tests
        pass

    def test_delete(self):
        # TODO(pballand): write tests
        pass


class TestCollectionHandler(base.TestCase):
    def test_get_action_type(self):
        collection_handler = webservice.CollectionHandler(r'/', '')
        self.assertEqual('get',
                         collection_handler._get_action_type("GET"))
        self.assertEqual('create',
                         collection_handler._get_action_type("POST"))
        self.assertEqual('delete',
                         collection_handler._get_action_type("DELETE"))
        self.assertEqual('update',
                         collection_handler._get_action_type("PATCH"))
        self.assertEqual('update',
                         collection_handler._get_action_type("PUT"))
        self.assertRaises(TypeError, collection_handler._get_action_type,
                          'Wah!')

    def test_create_member(self):
        collection_handler = webservice.CollectionHandler(r'/', '')
        collection_handler.model = webservice.SimpleDataModel("test")
        request = webob.Request.blank('/')
        request.content_type = 'application/json'
        request.body = '{"key": "value"}'
        response = collection_handler.create_member(request, id_='123')
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(str(httplib.CREATED) + " Created", response.status)
        self.assertEqual("%s/%s" % (request.path, '123'), response.location)
        actual_response = json.loads(response.body)
        actual_id = actual_response.get("id")
        actual_value = actual_response.get("key")
        self.assertEqual('123', actual_id)
        self.assertEqual('value', actual_value)

    def test_list_members(self):
        collection_handler = webservice.CollectionHandler(r'/', '')
        collection_handler.model = webservice.SimpleDataModel("test")
        request = mock.MagicMock()
        request.body = '{"key": "value"}'
        request.params = mock.MagicMock()
        request.path = "/"
        response = collection_handler.list_members(request)
        items = collection_handler.model.get_items(
            request.params,
            context=collection_handler._get_context(request))

        expected_body = "%s\n" % json.dumps(items, indent=2)
        self.assertEqual('application/json', response.content_type)

        self.assertEqual(expected_body, response.body)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(str(httplib.OK) + " OK", response.status)
