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
import subprocess
import time

from oslo_log import log as logging
import pulp

from congress.datalog import arithmetic_solvers
from congress.datalog import base
from congress.datalog import compile
from congress.datalog import nonrecursive
from congress import exception
from congress.policy_engines import base_driver

LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    """This method is called by d6cage to create a dataservice instance."""
    return ComputePlacementEngine(name, keys, inbox, datapath, args)


# TODO(thinrichs): Figure out what to move to the base class PolicyEngineDriver
#  Could also pull out the Datalog-to-LP conversion, potentially.
class ComputePlacementEngine(base_driver.PolicyEngineDriver):
    def __init__(self, name='', keys='', inbox=None, datapath=None, args=None):
        super(ComputePlacementEngine, self).__init__(
            name, keys, inbox, datapath)
        self.policy = nonrecursive.MultiModuleNonrecursiveRuleTheory(name=name)
        self.initialized = True
        self.guest_host_assignment = {}
        self.lplang = arithmetic_solvers.PulpLpLang()
        self.vm_migrator = VmMigrator()

    ###########################
    # Policy engine interface

    def insert(self, formula):
        return self.policy.insert(self.parse1(formula))

    def delete(self, formula):
        return self.policy.delete(self.parse1(formula))

    def select(self, query):
        ans = self.policy.select(self.parse1(query))
        return " ".join(str(x) for x in ans)

    def set_policy(self, policy):
        LOG.info("%s:: setting policy to %s", str(self.name), str(policy))
        # empty out current policy
        external = [compile.Tablename.build_service_table(service, name)
                    for service, name in self._current_external_tables()]
        self.policy.empty(tablenames=external, invert=True)

        # insert new policy and subscribe to the tablenames referencing a
        #    datasource driver
        for rule in self.parse(policy):
            self.policy.insert(rule)
        LOG.info("new policy: %s", self.policy.content_string())

        # initialize table subscriptions
        self.initialize_table_subscriptions()

        # enforce policy
        self.enforce_policy()

    def initialize_table_subscriptions(self):
        """Initialize table subscription.

        Once policies have all been loaded, this function subscribes to
        all the necessary tables.  See UPDATE_TABLE_SUBSCRIPTIONS as well.
        """
        tablenames = self.policy.tablenames()
        tablenames = [compile.Tablename.parse_service_table(table)
                      for table in tablenames]
        tablenames = [(service, name) for (service, name) in tablenames
                      if service is not None]
        self._set_subscriptions(tablenames)

    def _set_subscriptions(self, tablenames):
        """Update subscriptions on DSE to be exactly @tablenames."""
        subscriptions = set(self._current_external_tables())
        tablenames = set(tablenames)
        toadd = tablenames - subscriptions
        torem = subscriptions - tablenames
        for service, tablename in toadd:
            if service is not None:
                LOG.info("%s:: subscribing to (%s, %s)",
                         self.name, service, tablename)
                self.subscribe(service, tablename,
                               callback=self.receive_data)

        for service, tablename in torem:
            if service is not None:
                LOG.info("%s:: unsubscribing from (%s, %s)",
                         self.name, service, tablename)
                self.unsubscribe(service, tablename)
                relevant_tables = [compile.Tablename.build_service_table(
                                   service, tablename)]
                self.policy.empty(relevant_tables)

    def _current_external_tables(self):
        """Return list of tables engine is currently subscribed to."""
        return [(value.key, value.dataindex)
                for value in self.subdata.values()]

    ################################################################
    # Receiving data published on the DSE by other services
    # For PoC, assuming all data already present and no pubs.
    #   So we're ignoring this for now.

    def receive_data(self, msg):
        """Event handler for when a dataservice publishes data.

        That data can either be the full table (as a list of tuples)
        or a delta (a list of Events).
        """
        LOG.info("%s:: received data msg %s", self.name, msg)
        # if empty data, assume it is an init msg, since noop otherwise
        if len(msg.body.data) == 0:
            self.receive_data_full(msg)
        else:
            # grab an item from any iterable
            dataelem = next(iter(msg.body.data))
            if isinstance(dataelem, compile.Event):
                self.receive_data_update(msg)
            else:
                self.receive_data_full(msg)
        self.enforce_policy()

    def receive_data_full(self, msg):
        """Handler for when dataservice publishes full table."""
        LOG.info("%s:: received full data msg for %s: %s",
                 self.name, msg.header['dataindex'],
                 ";".join(str(x) for x in msg.body.data))
        tablename = compile.Tablename.build_service_table(
            msg.replyTo, msg.header['dataindex'])

        # Use a generator to avoid instantiating all these Facts at once.
        #   Don't print out 'literals' since that will eat the generator
        literals = (compile.Fact(tablename, row) for row in msg.body.data)

        LOG.info("%s:: begin initialize_tables %s", self.name, tablename)
        self.policy.initialize_tables([tablename], literals)
        LOG.info("%s:: end initialize data msg for %s", self.name, tablename)
        select = [str(x) for x in self.select('p(x)')]
        LOG.info("%s:: select('p(x)'): %s ENDED", self.name, " ".join(select))

    def receive_data_update(self, msg):
        """Handler for when dataservice publishes a delta."""
        LOG.info("%s:: received update data msg for %s: %s",
                 self.name, msg.header['dataindex'],
                 ";".join(str(x) for x in msg.body.data))
        new_events = []
        for event in msg.body.data:
            assert compile.is_atom(event.formula), (
                "receive_data_update received non-atom: " +
                str(event.formula))
            # prefix tablename with data source
            actual_table = compile.Tablename.build_service_table(
                msg.replyTo, event.formula.table.table)
            values = [term.name for term in event.formula.arguments]
            newevent = compile.Event(compile.Fact(actual_table, values),
                                     insert=event.insert)
            new_events.append(newevent)
        (permitted, changes) = self.policy.update(new_events)
        if not permitted:
            raise exception.CongressException(
                "Update not permitted." + '\n'.join(str(x) for x in changes))
        else:
            tablename = msg.header['dataindex']
            service = msg.replyTo
            LOG.debug("update data msg for %s from %s caused %d "
                      "changes: %s", tablename, service, len(changes),
                      ";".join(str(x) for x in changes))

    #######################################
    # Policy enforcement

    def enforce_policy(self):
        """Enforce policy by migrating VMs to minimize warnings.

        Raises LpProblemUnsolvable if the LP cannot solve the
        given problem.

        Raises LpConversionFailure if self.policy cannot be converted
        into an LP problem.
        """
        LOG.info("Enforcing policy")
        ans = self.policy.select(self.parse1('warning(x)'), True)
        if len(ans) == 0:
            return
        # grab assignment
        g_h_assignment = self.calculate_vm_assignment()
        self.guest_host_assignment = dict(g_h_assignment)
        # migrate
        for guest in g_h_assignment:
            g_h_assignment[guest] = [g_h_assignment[guest], 0]
        self.vm_migrator.do_migrations(g_h_assignment)

    def calculate_vm_assignment(self):
        """Calculate where VMs should be located in order to minimize warnings.

        Returns a dictionary from guest ID to host ID where that guest should
        be located.

        Raises LpProblemUnsolvable if the LP cannot solve the
        given problem.

        Raises LpConversionFailure if self.policy cannot be converted
        into an LP problem.
        """

        g_h_assignment = {}
        LOG.info("* Calculating VM assignment for Datalog policy: *")
        LOG.info(self.policy.content_string())
        migproblem, value_mapping = self.policy_to_lp_problem()
        LOG.info("* Converted to PuLP program: *")
        LOG.info("problem: %s", migproblem)
        migproblem.solve()
        LOG.info("problem status: %s", migproblem.status)
        if pulp.LpStatus[migproblem.status] == 'Optimal':
            LOG.info("value-mapping: %s", value_mapping)
            for var in migproblem.variables():
                LOG.info("var: %s = %s", var.name, var.varValue)
                if var.name.startswith('assign'):
                    g, h = var.name.lstrip('assign').lstrip('_').split('_')
                    g = value_mapping.get(int(g), g)
                    h = value_mapping.get(int(h), h)
                    LOG.info("guest %s, host %s has value %s",
                             g, h, var.varValue)
                    if var.varValue == 1.0:
                        # add correct old host
                        g_h_assignment[g] = h

            return g_h_assignment
        raise LpProblemUnsolvable(str(migproblem))

    #######################################
    # Toplevel conversion of Datalog to LP

    # mapping Datalog tables to LP decision variables

    def policy_to_lp_problem(self):
        """Return an LP problem representing the state of this engine.

        Returns an instance of self.lplang.problem representing the policy
        and the current data of this engine.
        """
        opt, hard = self.policy_to_lp()
        LOG.info("* Converted Datalog policy to DatalogLP *")
        LOG.info("optimization:\n%s", opt)
        LOG.info("constraints:\n%s", "\n".join(str(x) for x in hard))
        bounds = {}
        for exp in hard:
            self.set_bounds(exp, bounds)
        return self.lplang.problem(opt, hard, bounds)

    def policy_to_lp(self):
        """Transform self.policy into a (non-)linear programming problem.

        Returns (<optimization criteria>, <hard constraints>) where
        each are represented using expressions constructed by self.lplang.
        """
        # soft constraints. optimization criteria: minimize number of warnings
        # LOG.info("* Converting warning(x) to DatalogLP *")
        wquery = self.parse1('warning(x)')
        warnings, wvars = self.datalog_to_lp(wquery, [])
        opt = self.lplang.makeOr(*wvars)
        # hard constraints.  all must be false
        # LOG.info("* Converting error(x) to DatalogLP *")
        equery = self.parse1('error(x)')
        errors, evars = self.datalog_to_lp(equery, [])
        hard = [self.lplang.makeNotEqual(var, 1) for var in evars]
        # domain-specific axioms, e.g. sum of guest memory util = host mem util
        # LOG.info("* Constructing domain-specific axioms *")
        axioms = self.domain_axioms()
        return opt, warnings + errors + hard + axioms

    def set_bounds(self, expr, bounds):
        """Find upper bounds on all variables occurring in expr.

        :param expr is a LpLang.Expression
        :param bounds is a dictionary mapping an Expression's tuple() to a
            number.

        Modifies bounds to include values for all variables occurring inside
        expr.
        """
        # LOG.info("set_bounds(%s)", expr)
        variables = self.lplang.variables(expr)
        for var in variables:
            tup = var.tuple()
            if tup not in bounds:
                bounds[tup] = 10

    ##########################
    # Domain-specific axioms

    def domain_axioms(self):
        """Return a list of all the domain-specific axioms as strings.

        Axioms define relationships between LP decision variables that we
        would not expect the user to write.
        """
        # TODO(thinrichs): just defining relationship between mem-usage for
        #   guests and hosts.  Add rest of axioms.
        hosts = self.get_hosts()
        guests = self.get_guests()
        memusage = self.get_memusage()

        memusage_ax = self._domain_axiom_memusage(hosts, guests, memusage)
        assign_ax = self._domain_axiom_assignment(hosts, guests)
        return memusage_ax + assign_ax

    def _domain_axiom_assignment(self, hosts, guests):
        """Return axioms for assignment variables.

        :param hosts is the list of host IDs
        :param guests is the list of guest IDs

        assign[h1,g] + ... + assign[hn, g] = 1
        """
        axioms = []
        for g in guests:
            hostvars = [self._construct_assign(h, g) for h in hosts]
            axioms.append(self.lplang.makeEqual(
                1, self.lplang.makeArith('plus', *hostvars)))
        return axioms

    def _construct_assign(self, host, guest):
        return self.lplang.makeBoolVariable('assign', guest, host)

    def _domain_axiom_memusage(self, hosts, guests, memusage):
        """Return a list of LP axioms defining guest/host mem-usage.

        :param hosts is the list of host IDs
        :param guests is the list of guest IDs

        Axiom: sum of all guest mem-usage for those guests deployed on a host
        gives the mem-usage for that host:

        hMemUse[h] = assign[1][h]*gMemUse[1] + ... + assign[G][h]*gMemUse[G].

        Returns a list of LpLang expressions.
        Raises NotEnoughData if it does not have guest memory usage.
        """
        axioms = []

        for h in hosts:
            guest_terms = []
            for guest in guests:
                if guest not in memusage:
                    raise NotEnoughData(
                        "could not find guest mem usage: %s" % guest)
                guest_terms.append(
                    self.lplang.makeArith(
                        'times',
                        self._construct_assign(h, guest),
                        memusage[guest]))
            axioms.append(
                self.lplang.makeEqual(
                    self.lplang.makeIntVariable('hMemUse', h),
                    self.lplang.makeArith('plus', *guest_terms)))
        return axioms

    def get_hosts(self):
        query = self.parse1('nova:host(id, zone, memory_capacity)')
        host_rows = self.policy.select(query)
        return set([lit.arguments[0].name for lit in host_rows])

    def get_guests(self):
        query = self.parse1('nova:server(id, name, host)')
        guest_rows = self.policy.select(query)
        return set([lit.arguments[0].name for lit in guest_rows])

    def get_memusage(self):
        query = self.parse1('ceilometer:mem_consumption(id, mem)')
        rows = self.policy.select(query)
        return {lit.arguments[0].name: lit.arguments[1].name
                for lit in rows}

    #########################
    # Convert datalog to LP

    unknowns = ['ceilometer:mem_consumption']
    rewrites = ['ceilometer:mem_consumption(x, y) :- '
                'var("hMemUse", x), output(y)']

    def datalog_to_lp(self, query, unknown_table_possibilities):
        """Convert rules defining QUERY in self.policy into a linear program.

        @unknowns is the list of tablenames that should become
        decision variables.  @unknown_table_possibilities is the list
        of all possible instances of the decision variable tables.
        """
        # TODO(thinrichs): figure out if/when negation is handled properly

        # a list of rules, each of which has an instance of QUERY in the head
        #   and whose bodies are drawn from unknowns.
        rules = self.policy.abduce(query, self.unknowns)
        # LOG.info("interpolates:\n%s", "\n".join(str(x) for x in rules))
        if len(unknown_table_possibilities):
            rules = self.policy.instances(query, unknown_table_possibilities)
            # LOG.info("instances:\n%s", "\n".join(str(x) for x in rules))
        equalities, variables = self._to_lp(rules)
        # LOG.info("LP rules: \n%s", "\n".join(str(x) for x in equalities))
        # LOG.info("LP variables: %s", ", ".join(str(x) for x in variables))
        return equalities, variables

    def _to_lp(self, rules):
        """Compute an LP program equivalent to the given Datalog rules.

        :param rules: a list of Rule instances, all of which are ground
                      except for variables representing LP variables
        """
        # TODO(thinrichs): need type analysis to ensure we differentiate
        #    hosts from guests within ceilometer:mem_consumption
        act = nonrecursive.MultiModuleNonrecursiveRuleTheory()
        for var_rewrite_rule in self.rewrites:
            changes = act.insert(self.parse1(var_rewrite_rule))
            assert(changes)
        LOG.debug("action theory: %s", act.content_string())
        act.set_tracer(self.policy.tracer)
        definitions = {}
        for rule in rules:
            equalities, newrule = self._extract_lp_variable_equalities(
                rule, act)
            LOG.debug("equalities: %s", equalities)
            LOG.debug("newrule: %s", newrule)
            LOG.debug("newrule.body: %s", str(newrule.body))
            head = self._lit_to_lp_variable(newrule.head)
            LOG.debug("head: %s", str(head))
            LOG.debug("newrule.body: %s", newrule.body)
            body = []
            for lit in newrule.body:
                LOG.debug("processing %s", lit)
                body.append(self._lit_to_lp_arithmetic(lit, equalities))
            LOG.debug("new body: %s", ";".join(str(x) for x in body))
            conjunction = self.lplang.makeAnd(*body)
            LOG.debug("conjunct: %s", conjunction)
            if head not in definitions:
                definitions[head] = set([conjunction])
            else:
                definitions[head].add(conjunction)

        equalities = [self.lplang.makeEqual(h, self.lplang.makeOr(*bodies))
                      for h, bodies in definitions.items()]
        return equalities, definitions.keys()

    def _extract_lp_variable_equalities(self, rule, rewrite_theory):
        """Extract values for LP variables and slightly modify rule.

        :param rule: an instance of Rule
        :param rewrite_theory: reference to a theory that contains rules
               describing how tables correspond to LP variable inputs and
               outputs.

        Returns (i) dictionary mapping Datalog variable name (a string) to
        the set of LP variables to which it is equal and (ii) a rewriting
        of the rule that is the same as the original except some
        elements have been removed from the body.
        """
        newbody = []
        varnames = {}
        for lit in rule.body:
            result = self._extract_lp_variable_equality_lit(
                lit, rewrite_theory)
            if result is None:
                newbody.append(lit)
            else:
                datalogvar, lpvar = result
                if datalogvar not in varnames:
                    varnames[datalogvar] = set([lpvar])
                else:
                    varnames[datalogvar].add(lpvar)
        return varnames, compile.Rule(rule.head, newbody)

    def _extract_lp_variable_equality_lit(self, lit, rewrite_theory):
        """Identify datalog variable representing an LP-variable.

        :param lit: an instance of Literal
        :param rewrite_theory: reference to a theory that contains rules
               describing how tables correspond to LP variable inputs and
               outputs.
        Returns None, signifying literal does not include any datalog
        variable that maps to an LP variable, or (datalogvar, lpvar).
        """
        if lit.is_builtin():
            return
        # LOG.info("_extract_lp_var_eq_lit %s", lit)
        rewrites = rewrite_theory.abduce(lit, ['var', 'output'])
        # LOG.info("lit rewriting: %s", ";".join(str(x) for x in rewrites))
        if not rewrites:
            return
        assert(len(rewrites) == 1)
        varlit = next(lit for lit in rewrites[0].body
                      if lit.table.table == 'var')
        # LOG.info("varlit: %s", varlit)
        lpvar = self._varlit_to_lp_variable(varlit)
        outlit = next(lit for lit in rewrites[0].body
                      if lit.table.table == 'output')
        outvar = outlit.arguments[0].name
        # LOG.info("lpvar: %s; outvar: %s", lpvar, outvar)
        return outvar, lpvar

    def _lit_to_lp_arithmetic(self, lit, varnames):
        """Translates Datalog literal into an LP arithmetic statement.

        :param lit is a Literal instance and may include Datalog variables
        :param varnames is a dictionary from datalog variables to a set of
        LP variables

        Returns an LP arithmetic statement.

        Raises LpConversion if one of the Datalog variables appearing in
        lit has other than 1 value in varnames.
        Raises LpException if the arithmetic operator is not supported.
        """
        # TODO(thinrichs) translate to infix and use standard operators
        newargs = [self._term_to_lp_term(arg, varnames)
                   for arg in lit.arguments]
        return self.lplang.makeArith(lit.tablename(), *newargs)

    def _lit_to_lp_variable(self, lit):
        """Translates ground Datalog literal into an LP variable.

        :param lit is a Literal instance without variables
        Returns an LP variable.
        Raises LpConversionFailure if lit includes any Datalog variables.
        """
        if any(arg.is_variable() for arg in lit.arguments):
            raise self.lplang.LpConversionFailure(
                "Tried to convert literal %s into LP variable but "
                "found a Datalog variable" % lit)
        args = [arg.name for arg in lit.arguments]
        return self.lplang.makeVariable(lit.table.table, *args, type='bool')

    def _term_to_lp_term(self, term, varnames):
        """Translates Datalog term into an LP variable or a constant.

        :param term is an instance of Term
        :param varnames is a dictionary from varname to a set of LP variables

        Returns an LP variable, a number, or a string.

        Raises LpConversionFailure if Datalog variable appears without a
        corresponding LP variable or if multiple LP variables for a given
        Datalog variable.  (The latter condition could probably be handled
        without raising an error, but this is good for now.)
        """
        if term.is_variable():
            if term.name not in varnames:
                raise self.lplang.LpConversionFailure(
                    "Residual variable not assigned a value: %s" % term.name)
            if len(varnames[term.name]) > 1:
                raise self.lplang.LpConversionFailure(
                    "Variable name assigned to 2 different values: "
                    "%s assigned %s" % (term.name, varnames[term.name]))
            return next(iter(varnames[term.name]))
        return term.name

    def _varlit_to_lp_variable(self, lit):
        args = [x.name for x in lit.arguments[1:]]
        return self.lplang.makeVariable(lit.arguments[0].name, *args)

    #################
    # Miscellaneous

    def debug_mode(self):
        tracer = base.Tracer()
        tracer.trace('*')
        self.policy.set_tracer(tracer)

    def production_mode(self):
        tracer = base.Tracer()
        self.policy.set_tracer(tracer)

    def parse(self, policy):
        return compile.parse(policy, use_modules=False)

    def parse1(self, policy):
        return compile.parse1(policy, use_modules=False)


class NotEnoughData(exception.CongressException):
    pass


class LpProblemUnsolvable(exception.CongressException):
    pass


class VmMigrator(object):
    """Code for migrating VMs once we have a LP problem solution."""
    @classmethod
    def migrate(cls, guest, host):
        try:
            call = ["nova", "live-migration", str(guest), str(host)]
            LOG.info("migrating: %s", call)
            ret = subprocess.check_output(call, stderr=subprocess.STDOUT)
            if ret == 0:
                return True
        except Exception:
            pass

    @classmethod
    def check_status(cls, guest, host, status):
        g = subprocess.check_output(["nova", "list"])
        g = g.replace("-", "").replace("+", "").lstrip("[").rstrip("]")
        elems = g.split('\n')
        for elem in elems:
            e = elem.split("|")
            el = [x.strip() for x in e]
            try:
                if status == el[2]:
                    return True
            except Exception:
                pass

    @classmethod
    def do_migration(cls, guest, newh, oldh):
        if (newh == oldh):
            return True
        try:
            done = cls.migrate(guest, newh)
            if done:
                for i in range(3):
                    if cls.check_migrate(guest, newh, "ACTIVE"):
                        return True
                    else:
                        time.sleep(2)
        except Exception:
            pass
        return False

    # status: -1 if migration done
    @classmethod
    def getnext(cls, mapping, status):
        hi = max(status.values())
        if hi > 0:
            i = status.values().index(hi)
            return status.keys()[i]

    @classmethod
    def do_migrations(cls, g_h_mapping):
        max_attempts = 10
        guest_mig_status = dict.fromkeys(g_h_mapping.keys(), max_attempts)
        g = cls.getnext(g_h_mapping, guest_mig_status)
        while g:
            newh, oldh = g_h_mapping[g]
            if cls.do_migration(g, newh, oldh):
                guest_mig_status[g] = -1
            else:
                guest_mig_status[g] -= 1
            g = cls.getnext(g_h_mapping, guest_mig_status)
        return guest_mig_status
