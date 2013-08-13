# Copyright (c) 2013 VMware, Inc. All rights reserved.
#

import unittest


class TestCompiler(unittest.TestCase):

    def setUp(self):
        pass

    def test_foo(self):
	self.assertTrue("a" in "abc", "'a' is a substring of 'abc'")


if __name__ == '__main__':
    unittest.main()
