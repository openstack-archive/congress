# Copyright (c) 2016 Styra, Inc. All rights reserved.
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

from oslo_config import cfg
cfg.CONF.distributed_architecture = True

from congress.tests.datalog import test_compiler
from congress.tests.datalog import test_factset
from congress.tests.datalog import test_materialized
from congress.tests.datalog import test_nonrecur
from congress.tests.datalog import test_ordered_set
from congress.tests.datalog import test_ruleset
from congress.tests.datalog import test_unify
from congress.tests.datalog import test_utility


class TestCompilerParser(test_compiler.TestParser):
    pass


class TestCompilerColumn(test_compiler.TestColumnReferences):
    pass


class TestCompilerCompiler(test_compiler.TestCompiler):
    pass


class TestCompilerGraph(test_compiler.TestDependencyGraph):
    pass


class TestFact(test_factset.TestFactSet):
    pass


class TestMaterialized(test_materialized.TestRuntime):
    pass


class TestNonrecurRuntime(test_nonrecur.TestRuntime):
    pass


class TestNonrecurNegation(test_nonrecur.TestSelectNegation):
    pass


class TestNonrecurArity(test_nonrecur.TestArity):
    pass


class TestNonrecurInstances(test_nonrecur.TestInstances):
    pass


class TestOrdered(test_ordered_set.TestOrderedSet):
    pass


class TestRuleSet(test_ruleset.TestRuleSet):
    pass


class TestUnifyUnify(test_unify.TestUnify):
    pass


class TestUnifyMatch(test_unify.TestMatch):
    pass


class TestUtilityGraph(test_utility.TestGraph):
    pass


class TestUtilityBagGraph(test_utility.TestBagGraph):
    pass


class TestUtilityIterstr(test_utility.TestIterstr):
    pass
