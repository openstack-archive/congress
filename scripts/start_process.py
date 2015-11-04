# Copyright (c) 2015 VMware, Inc. All rights reserved.
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
# This script starts a number of children processes defined in a config file.
# If restart_delay is not None, this will restart a crashed process after
# restart_delay seconds.  The config file content should look like this:
# {
#     "datasource_drivers":
#       [
#           { "cmd": "ls",
#             "args": ["-l"],
#             "restart_delay": 5,
#             "name": "foo"
#           },
#
#           { "cmd": "watch",
#             "args": ["ls", "-l", "/tmp"],
#             "name": "bar"
#           }
#       ],
#     "output_directory": "/tmp/runner"
# }
#
# Config file requirements: the "name" fields must be unique within a config
# file.
#
import json
import os
import signal
import subprocess
import sys
import time

from oslo_log import log as logging


LOG = logging.getLogger(__name__)

children = []


class ProcessEntry(object):
    def __init__(self, process, cmd, args, restart_delay, name):
        self.process = process
        self.cmd = cmd
        self.args = args
        self.restart_delay = restart_delay
        self.time_of_death = None
        self.name = name


def _pid_file_name(name):
    return name + '.pid'


def stop_process(name, output_dir):
    filename = _pid_file_name(name)
    if os.path.isfile(os.path.join(output_dir, filename)):
        try:
            f = open(os.path.join(output_dir, filename))
            pid = int(f.read().strip())
            LOG.debug("Killing process %s, pid %d", name, pid)
            os.kill(pid, signal.SIGKILL)
            f.close()
            os.unlink(filename)
        except ValueError:
            LOG.debug("Could not parse pid file: %s (process %s)", filename,
                      name)
        except OSError:
            LOG.debug("No such process %s, pid %d", pid)
        except IOError:
            LOG.debug("Failed to stop process %s, pid %d", name, pid)


def start_process(cmd, args, restart_delay, name, output_dir):
    out = open(os.path.join(output_dir, name + '.stdout'), 'w')
    err = open(os.path.join(output_dir, name + '.stderr'), 'w')

    LOG.debug("Starting process (" + name + "): " + cmd + ' ' + ' '.join(args))
    p = subprocess.Popen([cmd] + args, stdout=out, stderr=err)
    LOG.debug("Started as pid %d", p.pid)
    f = open(os.path.join(output_dir, _pid_file_name(name)), 'w')
    f.write('%d\n' % p.pid)
    f.close()
    children.append(ProcessEntry(p, cmd, args, restart_delay, name))


def wait_all(output_dir, poll_interval_ms):
    LOG.debug("Monitoring %d children", len(children))
    while(True):
        for c in children:
            c.process.poll()
            if c.process.returncode is not None:
                if c.time_of_death is None:
                    LOG.debug("pid %d ended at %s with return code %d, "
                              "process %s", c.process.pid, c.time_of_death,
                              c.process.returncode,
                              c.name)
                    c.time_of_death = time.time()
                if c.restart_delay is not None:
                    if c.time_of_death + c.restart_delay < time.time():
                        LOG.debug("Restarting " + c.cmd + ' ' +
                                  ' '.join(c.args))
                        children.remove(c)
                        start_process(c.cmd, c.args, c.restart_delay,
                                      c.name, output_dir)
                else:
                    children.remove(c)

        if not children:
            break
        time.sleep(poll_interval_ms/1000)


def main():
    if len(sys.argv) != 2:
        sys.stderr.write("usage: start_process.py config_file\n")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        txt = f.read()
        f.close()
        config = json.loads(txt)

        if os.path.exists(config['output_directory']):
            if os.path.isfile(config['output_directory']):
                sys.stderr.write('output_directory %s already exists as '
                                 'a file\n', config['output_directory'])
                sys.exit(1)
        else:
            os.makedirs(config['output_directory'])

        names = set()
        for driver in config['datasource_drivers']:
            if driver['name'] in names:
                sys.stderr.write("Duplicate name '%s' in config file\n"
                                 % driver['name'])
                sys.exit(1)
            names.add(driver['name'])
            stop_process(driver['name'], config['output_directory'])

        for driver in config['datasource_drivers']:
            start_process(driver['cmd'], driver['args'],
                          driver.get('restart_delay'), driver['name'],
                          config['output_directory'])
        wait_all(config['output_directory'], config['poll_interval_ms'])


if __name__ == '__main__':
    main()
