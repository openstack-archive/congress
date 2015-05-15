# -*- coding: utf-8 -*-

# Copyright 2010-2011 OpenStack Foundation
# Copyright (c) 2013 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os

import fixtures
import mock
import mox
from oslo_config import cfg
import testtools

from congress.common import config
from congress.db import api as db_api
# Import all data models
from congress.db.migration.models import head  # noqa
from congress.db import model_base
from congress.dse import d6cage
from congress.tests import helper
from congress.tests import policy_fixture

_TRUE_VALUES = ('true', '1', 'yes')


class TestCase(testtools.TestCase):

    """Test case base class for all unit tests."""

    def setUp(self):
        """Run before each test method to initialize test environment."""

        super(TestCase, self).setUp()

        self.mox = mox.Mox()
        self.setup_config()
        self.addCleanup(cfg.CONF.reset)
        config.setup_logging()

        test_timeout = os.environ.get('OS_TEST_TIMEOUT', 0)
        try:
            test_timeout = int(test_timeout)
        except ValueError:
            # If timeout value is invalid do not set a timeout.
            test_timeout = 0
        if test_timeout > 0:
            self.useFixture(fixtures.Timeout(test_timeout, gentle=True))

        self.useFixture(fixtures.NestedTempfile())
        self.useFixture(fixtures.TempHomeDir())
        self.addCleanup(mock.patch.stopall)

        if os.environ.get('OS_STDOUT_CAPTURE') in _TRUE_VALUES:
            stdout = self.useFixture(fixtures.StringStream('stdout')).stream
            self.useFixture(fixtures.MonkeyPatch('sys.stdout', stdout))
        if os.environ.get('OS_STDERR_CAPTURE') in _TRUE_VALUES:
            stderr = self.useFixture(fixtures.StringStream('stderr')).stream
            self.useFixture(fixtures.MonkeyPatch('sys.stderr', stderr))

        self.log_fixture = self.useFixture(fixtures.FakeLogger())
        self.policy = self.useFixture(policy_fixture.PolicyFixture())
        # cage is a singleton so we delete it here and
        # recreate it after each test
        self.addCleanup(d6cage.delete_cage)

    def setup_config(self):
        """Tests that need a non-default config can override this method."""
        config.init([], default_config_files=[])

    def tearDown(self):
        super(TestCase, self).tearDown()
        self.mox.UnsetStubs()
        self.mox = None


class SqlTestCase(TestCase):

    # flag to indicate that the models have been loaded
    _TABLES_ESTABLISHED = False

    def setUp(self):
        super(SqlTestCase, self).setUp()
        # Register all data models
        engine = db_api.get_engine()
        if not SqlTestCase._TABLES_ESTABLISHED:
            model_base.BASE.metadata.create_all(engine)
            SqlTestCase._TABLES_ESTABLISHED = True

        def clear_tables():
            with engine.begin() as conn:
                for table in reversed(
                        model_base.BASE.metadata.sorted_tables):
                    conn.execute(table.delete())

        self.addCleanup(clear_tables)

    def setup_config(self):
        """Tests that need a non-default config can override this method."""
        args = ['--config-file', helper.etcdir('congress.conf.test')]
        config.init(args)


class Benchmark(SqlTestCase):
    def setUp(self):
        if os.getenv("TEST_BENCHMARK") != "true":
            self.skipTest("Skipping slow benchmark tests")
        super(Benchmark, self).setUp()
