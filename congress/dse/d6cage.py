#!/usr/bin/env python
#Copyright 2014 Plexxi, Inc.
#
#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.
#
#	Main entrypoint for the DSE
#
#	Configuration in d6cage.ini
#
#	Prerequisites:
#	- Plexxi API libraries (there is an RPM)
#	- Python dependencies (see readme elsewhere, or capture RPM)
#
#
#
import amqprouter
#from configobj import ConfigObj
from d6message import d6msg
from deepsix import deepSix
import imp
import logging
import pprint
from Queue import Queue
import sys
import threading


class d6Cage(deepSix):
    def __init__(self):

        # cfgObj = ConfigObj("d6cage.ini")
        # self.config = cfgObj.dict()
        self.config = {}
        self.config['modules'] = {}
        self.config['services'] = {}
        # Dictionary mapping service name to a dict of arguments.
        # Those arguments are only passed to d6service by createservice if they
        #   are not alreay present in the ARGS argument given to createservice.
        self.default_service_args = {}

        # cageKeys = self.config["d6cage"]['keys']
        cageKeys = ['python.d6cage']
        # cageDesc = self.config["d6cage"]['description']
        cageDesc = 'deepsix python cage'
        name = "d6cage"

        deepSix.__init__(self, name, cageKeys)

        self.inbox = Queue()
        self.dataPath = Queue()

        self.table = amqprouter.routeTable()
        self.table.add("local.router", self.inbox)
        self.table.add(self.name, self.inbox)
        self.table.add("router", self.inbox)
        localname = "local." + self.name
        self.table.add(localname, self.inbox)

        self.modules = {}
        self.services = {}

        self.unloadingServices = {}
        self.reloadingServices = set()

        self.services[self.name] = {}
        self.services[self.name]['service'] = self
        self.services[self.name]['name'] = self.name
        self.services[self.name]['description'] = cageDesc
        self.services[self.name]['inbox'] = self.inbox
        self.services[self.name]['keys'] = self.keys

        self.subscribe(
            "local.d6cage",
            "routeKeys",
            callback=self.updateRoutes,
            interval=5)

        self.load_modules_from_config()
        self.load_services_from_config()
        # set of service names that we deem special
        self.system_service_names = set([self.name])

    def newConfig(self, msg):

        newConfig = msg.body.data

        if type(newConfig) == dict and newConfig:

            if "modules" in newConfig:

                for module in newConfig["modules"]:

                    if module not in sys.modules:

                        self.loadModule(
                            module,
                            newConfig['modules'][module]['filename'])

            if "services" in newConfig:

                for service in newConfig['services']:

                    if service not in self.services:

                        self.createservice(
                            service,
                            **newConfig['services'][service])

            self.config = newConfig

    def reloadStoppedService(self, service):

        moduleName = self.config['services'][service]['moduleName']

        try:
            reload(sys.modules[moduleName])
        except Exception, errmsg:
            self.log(
                "Unable to reload module '%s': %s", moduleName, errmsg)
            return

        self.createservice(service, **self.config['services'][service])

    def waitForServiceToStop(
            self,
            service,
            attemptsLeft=20,
            callback=None,
            cbkwargs={}):

        if attemptsLeft > 0:

            if self.services[service]['object'].isActive():

                self.timerThreads.append(
                    threading.Timer(
                        10,
                        self.waitForServiceToStop,
                        [service, attemptsLeft - 1]).start())

            else:

                del self.services[service]

                if callback:
                    callback(**cbkwargs)

        else:
            self.log("Unable to stop service '%s'", service)

    def loadModule(self, name, filename):
        if name in sys.modules:
            self.log(
                "error loading module '%s': module already exists"
                % (name))
            return
        try:
            self.log("loading module: %s" % (name))
            imp.load_source(name, filename)
        except Exception, errmsg:
            self.log(
                "error loading module '%s' from '%s': %s" %
                (name, filename, errmsg))

    def load_modules_from_config(self):
        for section in self.config['modules'].keys():
            filename = self.config['modules'][section]["filename"]

            self.loadModule(section, filename)

    def createservice(
            self,
            name="",
            keys="",
            description="",
            moduleName="",
            args={}):

        if moduleName not in sys.modules:
            self.log(
                "error loading service" + name +
                ": module " + moduleName + " does not exist")

            return

        if name in self.services:
            self.log(
                "error loading service '%s': name already in use"
                % (name))
            return

        inbox = Queue()
        module = sys.modules[moduleName]

        # set args to default values, as necessary
        if name in self.default_service_args:
            global_args = self.default_service_args[name]
            for key, value in global_args.items():
                if key not in args:
                    args[key] = value

        try:
            # self.log("loading service: " + name)
            svcObject = module.d6service(
                name,
                keys,
                inbox,
                self.dataPath,
                args)
        except Exception, errmsg:
            logging.exception(
                "D6CAGE: error loading service '%s' of module '%s': %s"
                % (name, module, errmsg))

        if svcObject:
            self.log("created service: {}".format(name))
            self.services[name] = {}
            self.services[name]['name'] = name
            self.services[name]['description'] = description
            self.services[name]['moduleName'] = moduleName
            self.services[name]['keys'] = keys
            self.services[name]['args'] = args
            self.services[name]['object'] = svcObject
            self.services[name]['inbox'] = inbox

            try:
                self.services[name]['object'].daemon = True
                self.services[name]['object'].start()
                self.table.add(name, inbox)
                localname = "local." + name
                self.table.add(localname, inbox)
                self.subscribe(
                    name,
                    'routeKeys',
                    callback=self.updateRoutes,
                    interval=5)
                self.publish('services', self.services)
            except Exception, errmsg:
                self.log(
                    "error starting service '%s': %s" % (name, errmsg))
                del self.services[name]

    def updateRoutes(self, msg):
        keyData = self.getSubData(msg.correlationId, sender=msg.replyTo)
        currentKeys = set(keyData.data)
        self.log("updateRoutes msgbody: %s" % str(msg.body.data))
        pubKeys = set(msg.body.data['keys'])

        if currentKeys != pubKeys:

            newKeys = pubKeys - currentKeys

            if newKeys:
                self.table.add(
                    list(newKeys), self.services[msg.replyTo]['inbox'])

            oldKeys = currentKeys - pubKeys

            if oldKeys:
                self.table.remove(
                    list(oldKeys), self.services[msg.replyTo]['inbox'])

            return msg.body

    def load_services_from_config(self):

        for section in self.config['services'].keys():

            self.createservice(section, **self.config['services'][section])

    def routemsg(self, msg):

        # logging.debug(
        #     "Message lookup %s from %s" % (msg.key, msg.replyTo))

        destinations = self.table.lookup(msg.key)

        if destinations:
            for destination in destinations:
                destination.put_nowait(msg)
                # logging.debug(
                #     "Message sent to %s from %s"
                #     % (msg.key, msg.replyTo))

    def d6reload(self, msg):

        inargs = msg.body.data

        service = inargs['service']

        newmsg = d6msg(key=service, replyTo=self.name, type="shut")

        self.send(newmsg)
        cbkwargs = {}

        cbkwargs['service'] = service

        self.waitForServiceToStop(
            service,
            callback=self.reloadStoppedService,
            cbkwargs=cbkwargs)

    def cmdhandler(self, msg):

        command = msg.header['dataindex']

        if command == "reload":
            self.d6reload(msg)

    def d6run(self):
        # logging.debug("d6cage running d6run()")
        if not self.dataPath.empty():
            # logging.debug("{} has non-empty dataPath: {}".format(
            #     self.name, str(self.dataPath)))
            msg = self.dataPath.get()
            self.routemsg(msg)
            self.dataPath.task_done()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(format='%(asctime)s %(message)s')
    pp = pprint.PrettyPrinter(indent=1)
    main = d6Cage()
    main.start()
    main.join()
