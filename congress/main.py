#! /usr/bin/python
#
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

import dse.d6cage
import logging
import optparse
import os.path
import sys
import time

# global variable so that we can test
cage = None


def start(rootdir, statedir):
    """Get Congress up and running when src is installed in rootdir,
    i.e. ROOTDIR=/path/to/congress/congress.
    """
    logging.debug("Starting Congress with rootdir={} and statedir={}".format(
        rootdir, statedir))

    # create message bus
    cage = dse.d6cage.d6Cage()
    cage.daemon = True
    cage.start()

    # add policy engine
    engine_path = os.path.join(rootdir, "policy/dsepolicy.py")
    logging.info("main::start() engine_path: " + str(engine_path))
    cage.loadModule("PolicyEngine", engine_path)
    cage.createservice(name="engine", moduleName="PolicyEngine",
                       description="Policy Engine (DseRuntime instance)",
                       args={'d6cage': cage, 'rootdir': rootdir})
    engine = cage.services['engine']['object']
    if statedir is not None:
        engine.load_dir(statedir)
    engine.initialize_table_subscriptions()

    # add api
    # TODO(thinrichs): change to real API path.
    api_path = os.path.join(rootdir, "datasources/test_driver.py")
    logging.info("main::start() api_path: " + str(api_path))
    cage.loadModule("API", api_path)
    cage.createservice(name="api", moduleName="API",
                       description="API DSE instance")

    # have policy-engine subscribe to api calls
    engine.subscribe('api', 'policy-update',
                     callback=engine.receive_policy_update)
    return cage


def main():
    # call as: "python main.py"
    parser = optparse.OptionParser()
    parser.add_option("-s", "--state", dest="statedir",
                      default=None,
                      help="absolute path for directory of policies")
    parser.add_option("-r", "--root", dest="rootdir",
                      default=None,
                      help="absolute path to root of Congress dir")
    (options, args) = parser.parse_args
    if options.rootdir is None:
        options.rootdir = os.path.realpath(sys.argv[1])
    assert os.path.isdir(options.root), "Root must be existing directory"
    assert (options.statedir is None or os.path.isdir(options.statedir)), \
        "State must be existing directory or be None"
    start(options.rootdir, options.statedir)

    # cooperative threading
    while True:
        time.sleep(1)


if __name__ == '__main__':
    main()
