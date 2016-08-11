
# need to run at least 1 test or tox fails

from congress.tests import base


class TestRuntime(base.TestCase):
    def test_noop(self):
        pass
