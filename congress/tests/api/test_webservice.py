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

import unittest
import uuid

from congress.api import webservice
from congress.tests import base


class TestSimpleDataModel(unittest.TestCase):
    # if random ID matches, go to Vegas or file a uuid library bug
    UNADDED_ID = str(uuid.uuid4())
    CONTEXTS = [None, {'a': 'ctxt1'}, {'b': 'ctxt2', 'c': 'ctxt3'}]

    def setUp(self):
        pass

    def test_get_items(self):
        """Test API DataModel get_items functionality."""
        model = webservice.SimpleDataModel("test")
        for context in self.CONTEXTS:
            ret = model.get_items(context=context)
            self.assertEqual(
                ret.keys(), ['results'],
                "get_items returns dict with single 'results' key")
            self.assertEqual(
                tuple(ret['results']), tuple(),
                "get_items of empty model returns empty results list")
            items = [{"i1": "%s/foo" % context}, {"i2": "%s/bar" % context}]
            for item in items:
                model.add_item(item, context=context)
            ret2 = model.get_items(context=context)
            self.assertEqual(sorted(ret2['results']), sorted(items),
                             "get_items() returns all items added to model")

    def test_add_item(self):
        """Test API DataModel add_item functionality."""
        model = webservice.SimpleDataModel("test")
        assigned_ids = set()
        for context in self.CONTEXTS:
            items = ["%s/foo" % context, "%s/bar" % context]
            ret = model.add_item(items[0], context=context)
            self.assertIsInstance(ret, tuple, "add_item returns a tuple")
            self.assertEqual(len(ret), 2,
                             "add_item returns tuple of length 2")
            self.assertNotIn(ret[0], assigned_ids,
                             "add_item assigned unique ID")
            assigned_ids.add(ret[0])
            self.assertEqual(ret[1], items[0], "add_item returned added item")

            ret = model.add_item(items[1], 'myid', context=context)
            self.assertEqual(ret[0], 'myid',
                             "add_item returned provided ID")
            self.assertEqual(ret[1], items[1], "add_item returned added item")

    def test_get_item(self):
        """Test API DataModel get_item functionality."""
        model = webservice.SimpleDataModel("test")
        for context in self.CONTEXTS:
            items = ["%s/foo" % context, "%s/bar" % context]
            id_ = model.add_item(items[0], context=context)[0]
            ret = model.get_item(id_, context=context)
            self.assertEqual(ret, items[0],
                             "get_item(assigned_id) returns proper item")

            id_ = 'myid'
            ret = model.get_item(id_, context=context)
            self.assertIsNone(ret,
                              "get_item(unadded_provided_id) returns None")
            model.add_item(items[1], id_, context=context)
            ret = model.get_item(id_, context=context)
            self.assertEqual(ret, items[1],
                             "get_item(provided_id) returned added item")

            ret = model.get_item(self.UNADDED_ID, context=context)
            self.assertIsNone(ret, "get_item(unadded_id) returns None")

    def test_update_item(self):
        """Test API DataModel update_item functionality."""
        model = webservice.SimpleDataModel("test")
        for context in self.CONTEXTS:
            items = ["%s/foo%d" % (context, i) for i in [0, 1, 2]]
            id_, item = model.add_item(items[0], context=context)
            self.assertNotEqual(item, items[1], "item not yet updated")
            ret = model.update_item(id_, items[1], context=context)
            self.assertEqual(ret, items[1],
                             "update_item returned updated item")
            ret = model.get_item(id_, context=context)
            self.assertEqual(ret, items[1],
                             "get_item(updated_item_id) returns updated item")

            self.assertNotEqual(item, items[2], "item not yet reupdated")
            ret = model.update_item(id_, items[2], context=context)
            self.assertEqual(ret, items[2],
                             "update_item returned reupdated item")
            ret = model.get_item(id_, context=context)
            self.assertEqual(
                ret, items[2],
                "get_item(reupdated_item_id) returns reupdated item")

            with self.assertRaises(
                    KeyError, msg="update_item(unadded_id) raises KeyError"):
                model.update_item(self.UNADDED_ID, 'blah', context=context),

    def test_delete_item(self):
        """Test API DataModel delete_item functionality."""
        model = webservice.SimpleDataModel("test")

        for context in self.CONTEXTS:
            item_ids = []
            items = ["%s/foo%d" % (context, i) for i in [0, 1, 2]]
            for i in range(len(items)):
                id_, item = model.add_item(items[i], context=context)
                item_ids.append(id_)

            for i in range(len(items)):
                ret = model.delete_item(item_ids[i], context=context)
                self.assertEqual(ret, items[i],
                                 "delete_item returned deleted item")
                with self.assertRaises(
                        KeyError,
                        msg="delete_item(deleted_id) raises KeyError"):
                    model.delete_item(item_ids[i], context=context),
            self.assertEqual(len(model.get_items()['results']), 0,
                             "all items deleted")

            with self.assertRaises(
                    KeyError, msg="delete_item(unadded_id) raises KeyError"):
                model.delete_item(self.UNADDED_ID, context=context),


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
