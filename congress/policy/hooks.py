# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
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
import subprocess


POLICY_PATH = os.path.dirname(os.path.realpath(__file__))
SRC_PATH = os.path.dirname(POLICY_PATH)
TOP_PATH = os.path.dirname(SRC_PATH)
ANTLR_JAR_PATH = os.path.join(TOP_PATH, 'thirdparty', 'antlr-3.5-complete.jar')
GRAMMAR_SPEC_PATH = os.path.join(POLICY_PATH, 'Congress.g')


def setup_hook(config):
    """Generate parser using antlr and associated spec."""
    antlr_args = ['java', '-jar', ANTLR_JAR_PATH, GRAMMAR_SPEC_PATH]
    subprocess.call(antlr_args)
