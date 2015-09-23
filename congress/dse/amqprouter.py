# Copyright 2014 Plexxi, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import six


class Node(object):
    def __init__(self, rPath=[], results=set()):
        self.destinations = set()

        self.results = results
        self.children = {}
        self.rPath = rPath

    def _remove(self, patternList, destination):

        word = patternList[0]

        if word in self.children:

            if len(patternList) == 1:
                if destination in self.children[word].destinations:
                    self.children[word].destinations.remove(destination)

                    if (len(self.children[word].destinations) == 0 and
                            len(self.children[word].children) == 0):

                        del self.children[word]

            else:
                self.children[word]._remove(patternList[1:], destination)

                if (len(self.children[word].destinations) == 0 and
                        len(self.children[word].children) == 0):

                    del self.children[word]

    def _add(self, patternList, destination):

        word = patternList[0]

        if word not in self.children:

            if word == "#":
                self.children['#'] = hashNode(
                    rPath=self.rPath + ['#'],
                    results=self.results)

            else:
                self.children[word] = Node(
                    rPath=self.rPath + [word],
                    results=self.results)

        if len(patternList) == 1:
            self.children[word].destinations.add(destination)

        else:
            self.children[word]._add(patternList[1:], destination)

    def update_results(self):
        if '#' in self.children:
            self.children['#'].update_results()

        self.results.update(self.destinations)

    def _lookup(self, keyList):
        word = keyList[0]

        if len(keyList) == 1:
            if word in self.children:
                self.children[word].update_results()

            if '*' in self.children:
                if word:
                    self.children['*'].update_results()

        else:
            if word in self.children:
                self.children[word]._lookup(keyList[1:])

            if '*' in self.children:
                if word:
                    self.children['*']._lookup(keyList[1:])

        if '#' in self.children:
            self.children['#']._lookup(keyList[:])
            self.children['#'].update_results()


class hashNode(Node):
    def _lookup(self, keyList):
        for i in range(len(keyList)):
            if keyList[i] in self.children:
                self.children[keyList[i]]._lookup(keyList[i:])

            if '*' in self.children:
                if keyList[i]:
                    self.children['*']._lookup(keyList[i:])

            if '#' in self.children:
                self.children['#']._lookup(keyList[i:])

        if keyList[-1] in self.children:
            self.children[keyList[-1]].update_results()

        if '*' in self.children:
            if keyList[-1]:
                self.children['*'].update_results()


class routeTable(Node):
    def add(self, pattern, destination):
        if type(pattern) == list:
            for p in pattern:
                wordList = p.split('.')
                self._add(wordList, destination)
        elif isinstance(pattern, six.string_types):
            wordList = pattern.split('.')
            self._add(wordList, destination)

    def remove(self, pattern, destination):
        if type(pattern) == list:
            for p in pattern:
                wordList = p.split('.')
                self._remove(wordList, destination)
        elif isinstance(pattern, six.string_types):
            wordList = pattern.split('.')
            self._remove(wordList, destination)

    def lookup(self, key):
        self.results.clear()

        wordList = key.split('.')

        self._lookup(wordList)

        return self.results
