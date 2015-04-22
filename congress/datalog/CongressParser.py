# $ANTLR 3.5 C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g 2015-04-22 14:17:23

import sys
from antlr3 import *
from antlr3.compat import set, frozenset

from antlr3.tree import *




# for convenience in actions
HIDDEN = BaseRecognizer.HIDDEN

# token types
EOF=-1
T__54=54
T__55=55
T__56=56
AND=4
ATOM=5
BYTESTRPREFIX=6
BYTES_CHAR_DQ=7
BYTES_CHAR_SQ=8
BYTES_ESC=9
BYTES_TESC=10
COLONMINUS=11
COLUMN_NAME=12
COLUMN_NUMBER=13
COMMA=14
COMMENT=15
DELETE=16
DIGIT=17
EQUAL=18
EXPONENT=19
FLOAT=20
FLOAT_EXP=21
FLOAT_NO_EXP=22
FLOAT_OBJ=23
FRAC_PART=24
HEX_DIGIT=25
ID=26
INSERT=27
INT=28
INTEGER_OBJ=29
INT_PART=30
LBRACKET=31
LITERAL=32
LPAREN=33
MODAL=34
NAMED_PARAM=35
NEGATION=36
NOT=37
PROG=38
RBRACKET=39
RPAREN=40
RULE=41
SIGN=42
SLBYTESTRING=43
SLSTRING=44
STRING=45
STRING_ESC=46
STRING_OBJ=47
STRPREFIX=48
STRUCTURED_NAME=49
SYMBOL_OBJ=50
THEORY=51
VARIABLE=52
WS=53

# token names
tokenNames = [
    "<invalid>", "<EOR>", "<DOWN>", "<UP>",
    "AND", "ATOM", "BYTESTRPREFIX", "BYTES_CHAR_DQ", "BYTES_CHAR_SQ", "BYTES_ESC", 
    "BYTES_TESC", "COLONMINUS", "COLUMN_NAME", "COLUMN_NUMBER", "COMMA", 
    "COMMENT", "DELETE", "DIGIT", "EQUAL", "EXPONENT", "FLOAT", "FLOAT_EXP", 
    "FLOAT_NO_EXP", "FLOAT_OBJ", "FRAC_PART", "HEX_DIGIT", "ID", "INSERT", 
    "INT", "INTEGER_OBJ", "INT_PART", "LBRACKET", "LITERAL", "LPAREN", "MODAL", 
    "NAMED_PARAM", "NEGATION", "NOT", "PROG", "RBRACKET", "RPAREN", "RULE", 
    "SIGN", "SLBYTESTRING", "SLSTRING", "STRING", "STRING_ESC", "STRING_OBJ", 
    "STRPREFIX", "STRUCTURED_NAME", "SYMBOL_OBJ", "THEORY", "VARIABLE", 
    "WS", "'.'", "':'", "';'"
]




class CongressParser(Parser):
    grammarFileName = "C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g"
    api_version = 1
    tokenNames = tokenNames

    def __init__(self, input, state=None, *args, **kwargs):
        if state is None:
            state = RecognizerSharedState()

        super(CongressParser, self).__init__(input, state, *args, **kwargs)

        self.dfa5 = self.DFA5(
            self, 5,
            eot = self.DFA5_eot,
            eof = self.DFA5_eof,
            min = self.DFA5_min,
            max = self.DFA5_max,
            accept = self.DFA5_accept,
            special = self.DFA5_special,
            transition = self.DFA5_transition
            )

        self.dfa7 = self.DFA7(
            self, 7,
            eot = self.DFA7_eot,
            eof = self.DFA7_eof,
            min = self.DFA7_min,
            max = self.DFA7_max,
            accept = self.DFA7_accept,
            special = self.DFA7_special,
            transition = self.DFA7_transition
            )




        self.delegates = []

	self._adaptor = None
	self.adaptor = CommonTreeAdaptor()



    def getTreeAdaptor(self):
        return self._adaptor

    def setTreeAdaptor(self, adaptor):
        self._adaptor = adaptor

    adaptor = property(getTreeAdaptor, setTreeAdaptor)


    class prog_return(ParserRuleReturnScope):
        def __init__(self):
            super(CongressParser.prog_return, self).__init__()

            self.tree = None





    # $ANTLR start "prog"
    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:57:1: prog : ( ( statement )+ EOF -> ^( THEORY ( statement )+ ) | EOF );
    def prog(self, ):
        retval = self.prog_return()
        retval.start = self.input.LT(1)


        root_0 = None

        EOF2 = None
        EOF3 = None
        statement1 = None

        EOF2_tree = None
        EOF3_tree = None
        stream_EOF = RewriteRuleTokenStream(self._adaptor, "token EOF")
        stream_statement = RewriteRuleSubtreeStream(self._adaptor, "rule statement")
        try:
            try:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:58:5: ( ( statement )+ EOF -> ^( THEORY ( statement )+ ) | EOF )
                alt2 = 2
                LA2_0 = self.input.LA(1)

                if ((COMMENT <= LA2_0 <= DELETE) or (ID <= LA2_0 <= INSERT) or LA2_0 == NEGATION) :
                    alt2 = 1
                elif (LA2_0 == EOF) :
                    alt2 = 2
                else:
                    nvae = NoViableAltException("", 2, 0, self.input)

                    raise nvae


                if alt2 == 1:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:58:7: ( statement )+ EOF
                    pass 
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:58:7: ( statement )+
                    cnt1 = 0
                    while True: #loop1
                        alt1 = 2
                        LA1_0 = self.input.LA(1)

                        if ((COMMENT <= LA1_0 <= DELETE) or (ID <= LA1_0 <= INSERT) or LA1_0 == NEGATION) :
                            alt1 = 1


                        if alt1 == 1:
                            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:58:7: statement
                            pass 
                            self._state.following.append(self.FOLLOW_statement_in_prog258)
                            statement1 = self.statement()

                            self._state.following.pop()
                            stream_statement.add(statement1.tree)



                        else:
                            if cnt1 >= 1:
                                break #loop1

                            eee = EarlyExitException(1, self.input)
                            raise eee

                        cnt1 += 1


                    EOF2 = self.match(self.input, EOF, self.FOLLOW_EOF_in_prog261) 
                    stream_EOF.add(EOF2)


                    # AST Rewrite
                    # elements: statement
                    # token labels: 
                    # rule labels: retval
                    # token list labels: 
                    # rule list labels: 
                    # wildcard labels: 
                    retval.tree = root_0
                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "rule retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()
                    # 58:22: -> ^( THEORY ( statement )+ )
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:58:25: ^( THEORY ( statement )+ )
                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(
                    self._adaptor.createFromType(THEORY, "THEORY")
                    , root_1)

                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:58:34: ( statement )+
                    if not (stream_statement.hasNext()):
                        raise RewriteEarlyExitException()

                    while stream_statement.hasNext():
                        self._adaptor.addChild(root_1, stream_statement.nextTree())


                    stream_statement.reset()

                    self._adaptor.addChild(root_0, root_1)




                    retval.tree = root_0




                elif alt2 == 2:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:59:7: EOF
                    pass 
                    root_0 = self._adaptor.nil()


                    EOF3 = self.match(self.input, EOF, self.FOLLOW_EOF_in_prog278)
                    EOF3_tree = self._adaptor.createWithPayload(EOF3)
                    self._adaptor.addChild(root_0, EOF3_tree)




                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "prog"


    class statement_return(ParserRuleReturnScope):
        def __init__(self):
            super(CongressParser.statement_return, self).__init__()

            self.tree = None





    # $ANTLR start "statement"
    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:64:1: statement : ( bare_formula ( formula_terminator )? -> bare_formula | COMMENT );
    def statement(self, ):
        retval = self.statement_return()
        retval.start = self.input.LT(1)


        root_0 = None

        COMMENT6 = None
        bare_formula4 = None
        formula_terminator5 = None

        COMMENT6_tree = None
        stream_bare_formula = RewriteRuleSubtreeStream(self._adaptor, "rule bare_formula")
        stream_formula_terminator = RewriteRuleSubtreeStream(self._adaptor, "rule formula_terminator")
        try:
            try:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:65:5: ( bare_formula ( formula_terminator )? -> bare_formula | COMMENT )
                alt4 = 2
                LA4_0 = self.input.LA(1)

                if (LA4_0 == DELETE or (ID <= LA4_0 <= INSERT) or LA4_0 == NEGATION) :
                    alt4 = 1
                elif (LA4_0 == COMMENT) :
                    alt4 = 2
                else:
                    nvae = NoViableAltException("", 4, 0, self.input)

                    raise nvae


                if alt4 == 1:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:65:7: bare_formula ( formula_terminator )?
                    pass 
                    self._state.following.append(self.FOLLOW_bare_formula_in_statement297)
                    bare_formula4 = self.bare_formula()

                    self._state.following.pop()
                    stream_bare_formula.add(bare_formula4.tree)


                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:65:20: ( formula_terminator )?
                    alt3 = 2
                    LA3_0 = self.input.LA(1)

                    if (LA3_0 == 54 or LA3_0 == 56) :
                        alt3 = 1
                    if alt3 == 1:
                        # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:65:20: formula_terminator
                        pass 
                        self._state.following.append(self.FOLLOW_formula_terminator_in_statement299)
                        formula_terminator5 = self.formula_terminator()

                        self._state.following.pop()
                        stream_formula_terminator.add(formula_terminator5.tree)





                    # AST Rewrite
                    # elements: bare_formula
                    # token labels: 
                    # rule labels: retval
                    # token list labels: 
                    # rule list labels: 
                    # wildcard labels: 
                    retval.tree = root_0
                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "rule retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()
                    # 65:40: -> bare_formula
                    self._adaptor.addChild(root_0, stream_bare_formula.nextTree())




                    retval.tree = root_0




                elif alt4 == 2:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:66:7: COMMENT
                    pass 
                    root_0 = self._adaptor.nil()


                    COMMENT6 = self.match(self.input, COMMENT, self.FOLLOW_COMMENT_in_statement312)
                    COMMENT6_tree = self._adaptor.createWithPayload(COMMENT6)
                    self._adaptor.addChild(root_0, COMMENT6_tree)




                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "statement"


    class bare_formula_return(ParserRuleReturnScope):
        def __init__(self):
            super(CongressParser.bare_formula_return, self).__init__()

            self.tree = None





    # $ANTLR start "bare_formula"
    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:71:1: bare_formula : ( rule | fact );
    def bare_formula(self, ):
        retval = self.bare_formula_return()
        retval.start = self.input.LT(1)


        root_0 = None

        rule7 = None
        fact8 = None


        try:
            try:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:72:5: ( rule | fact )
                alt5 = 2
                alt5 = self.dfa5.predict(self.input)
                if alt5 == 1:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:72:7: rule
                    pass 
                    root_0 = self._adaptor.nil()


                    self._state.following.append(self.FOLLOW_rule_in_bare_formula331)
                    rule7 = self.rule()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, rule7.tree)



                elif alt5 == 2:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:73:7: fact
                    pass 
                    root_0 = self._adaptor.nil()


                    self._state.following.append(self.FOLLOW_fact_in_bare_formula339)
                    fact8 = self.fact()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, fact8.tree)



                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "bare_formula"


    class formula_terminator_return(ParserRuleReturnScope):
        def __init__(self):
            super(CongressParser.formula_terminator_return, self).__init__()

            self.tree = None





    # $ANTLR start "formula_terminator"
    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:75:1: formula_terminator : ( ';' | '.' );
    def formula_terminator(self, ):
        retval = self.formula_terminator_return()
        retval.start = self.input.LT(1)


        root_0 = None

        set9 = None

        set9_tree = None

        try:
            try:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:76:5: ( ';' | '.' )
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:
                pass 
                root_0 = self._adaptor.nil()


                set9 = self.input.LT(1)

                if self.input.LA(1) == 54 or self.input.LA(1) == 56:
                    self.input.consume()
                    self._adaptor.addChild(root_0, self._adaptor.createWithPayload(set9))

                    self._state.errorRecovery = False


                else:
                    mse = MismatchedSetException(None, self.input)
                    raise mse





                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "formula_terminator"


    class rule_return(ParserRuleReturnScope):
        def __init__(self):
            super(CongressParser.rule_return, self).__init__()

            self.tree = None





    # $ANTLR start "rule"
    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:82:1: rule : ( modal_rule | rule_body );
    def rule(self, ):
        retval = self.rule_return()
        retval.start = self.input.LT(1)


        root_0 = None

        modal_rule10 = None
        rule_body11 = None


        try:
            try:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:83:5: ( modal_rule | rule_body )
                alt6 = 2
                LA6_0 = self.input.LA(1)

                if (LA6_0 == DELETE or LA6_0 == INSERT) :
                    alt6 = 1
                elif (LA6_0 == ID or LA6_0 == NEGATION) :
                    alt6 = 2
                else:
                    nvae = NoViableAltException("", 6, 0, self.input)

                    raise nvae


                if alt6 == 1:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:83:7: modal_rule
                    pass 
                    root_0 = self._adaptor.nil()


                    self._state.following.append(self.FOLLOW_modal_rule_in_rule382)
                    modal_rule10 = self.modal_rule()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, modal_rule10.tree)



                elif alt6 == 2:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:84:7: rule_body
                    pass 
                    root_0 = self._adaptor.nil()


                    self._state.following.append(self.FOLLOW_rule_body_in_rule390)
                    rule_body11 = self.rule_body()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, rule_body11.tree)



                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "rule"


    class modal_rule_return(ParserRuleReturnScope):
        def __init__(self):
            super(CongressParser.modal_rule_return, self).__init__()

            self.tree = None





    # $ANTLR start "modal_rule"
    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:88:1: modal_rule : ( modal_op LBRACKET rule_body policy_name RBRACKET | modal_op LBRACKET fact policy_name RBRACKET );
    def modal_rule(self, ):
        retval = self.modal_rule_return()
        retval.start = self.input.LT(1)


        root_0 = None

        LBRACKET13 = None
        RBRACKET16 = None
        LBRACKET18 = None
        RBRACKET21 = None
        modal_op12 = None
        rule_body14 = None
        policy_name15 = None
        modal_op17 = None
        fact19 = None
        policy_name20 = None

        LBRACKET13_tree = None
        RBRACKET16_tree = None
        LBRACKET18_tree = None
        RBRACKET21_tree = None

        try:
            try:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:89:5: ( modal_op LBRACKET rule_body policy_name RBRACKET | modal_op LBRACKET fact policy_name RBRACKET )
                alt7 = 2
                alt7 = self.dfa7.predict(self.input)
                if alt7 == 1:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:89:7: modal_op LBRACKET rule_body policy_name RBRACKET
                    pass 
                    root_0 = self._adaptor.nil()


                    self._state.following.append(self.FOLLOW_modal_op_in_modal_rule408)
                    modal_op12 = self.modal_op()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, modal_op12.tree)


                    LBRACKET13 = self.match(self.input, LBRACKET, self.FOLLOW_LBRACKET_in_modal_rule410)
                    LBRACKET13_tree = self._adaptor.createWithPayload(LBRACKET13)
                    self._adaptor.addChild(root_0, LBRACKET13_tree)



                    self._state.following.append(self.FOLLOW_rule_body_in_modal_rule412)
                    rule_body14 = self.rule_body()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, rule_body14.tree)


                    self._state.following.append(self.FOLLOW_policy_name_in_modal_rule414)
                    policy_name15 = self.policy_name()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, policy_name15.tree)


                    RBRACKET16 = self.match(self.input, RBRACKET, self.FOLLOW_RBRACKET_in_modal_rule416)
                    RBRACKET16_tree = self._adaptor.createWithPayload(RBRACKET16)
                    self._adaptor.addChild(root_0, RBRACKET16_tree)




                elif alt7 == 2:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:90:7: modal_op LBRACKET fact policy_name RBRACKET
                    pass 
                    root_0 = self._adaptor.nil()


                    self._state.following.append(self.FOLLOW_modal_op_in_modal_rule424)
                    modal_op17 = self.modal_op()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, modal_op17.tree)


                    LBRACKET18 = self.match(self.input, LBRACKET, self.FOLLOW_LBRACKET_in_modal_rule426)
                    LBRACKET18_tree = self._adaptor.createWithPayload(LBRACKET18)
                    self._adaptor.addChild(root_0, LBRACKET18_tree)



                    self._state.following.append(self.FOLLOW_fact_in_modal_rule428)
                    fact19 = self.fact()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, fact19.tree)


                    self._state.following.append(self.FOLLOW_policy_name_in_modal_rule430)
                    policy_name20 = self.policy_name()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, policy_name20.tree)


                    RBRACKET21 = self.match(self.input, RBRACKET, self.FOLLOW_RBRACKET_in_modal_rule432)
                    RBRACKET21_tree = self._adaptor.createWithPayload(RBRACKET21)
                    self._adaptor.addChild(root_0, RBRACKET21_tree)




                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "modal_rule"


    class modal_op_return(ParserRuleReturnScope):
        def __init__(self):
            super(CongressParser.modal_op_return, self).__init__()

            self.tree = None





    # $ANTLR start "modal_op"
    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:93:1: modal_op : ( INSERT | DELETE );
    def modal_op(self, ):
        retval = self.modal_op_return()
        retval.start = self.input.LT(1)


        root_0 = None

        set22 = None

        set22_tree = None

        try:
            try:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:94:5: ( INSERT | DELETE )
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:
                pass 
                root_0 = self._adaptor.nil()


                set22 = self.input.LT(1)

                if self.input.LA(1) == DELETE or self.input.LA(1) == INSERT:
                    self.input.consume()
                    self._adaptor.addChild(root_0, self._adaptor.createWithPayload(set22))

                    self._state.errorRecovery = False


                else:
                    mse = MismatchedSetException(None, self.input)
                    raise mse





                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "modal_op"


    class policy_name_return(ParserRuleReturnScope):
        def __init__(self):
            super(CongressParser.policy_name_return, self).__init__()

            self.tree = None





    # $ANTLR start "policy_name"
    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:99:1: policy_name : COMMA STRING ;
    def policy_name(self, ):
        retval = self.policy_name_return()
        retval.start = self.input.LT(1)


        root_0 = None

        COMMA23 = None
        STRING24 = None

        COMMA23_tree = None
        STRING24_tree = None

        try:
            try:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:100:5: ( COMMA STRING )
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:100:7: COMMA STRING
                pass 
                root_0 = self._adaptor.nil()


                COMMA23 = self.match(self.input, COMMA, self.FOLLOW_COMMA_in_policy_name475)
                COMMA23_tree = self._adaptor.createWithPayload(COMMA23)
                self._adaptor.addChild(root_0, COMMA23_tree)



                STRING24 = self.match(self.input, STRING, self.FOLLOW_STRING_in_policy_name477)
                STRING24_tree = self._adaptor.createWithPayload(STRING24)
                self._adaptor.addChild(root_0, STRING24_tree)





                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "policy_name"


    class rule_body_return(ParserRuleReturnScope):
        def __init__(self):
            super(CongressParser.rule_body_return, self).__init__()

            self.tree = None





    # $ANTLR start "rule_body"
    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:103:1: rule_body : literal_list COLONMINUS literal_list -> ^( RULE literal_list literal_list ) ;
    def rule_body(self, ):
        retval = self.rule_body_return()
        retval.start = self.input.LT(1)


        root_0 = None

        COLONMINUS26 = None
        literal_list25 = None
        literal_list27 = None

        COLONMINUS26_tree = None
        stream_COLONMINUS = RewriteRuleTokenStream(self._adaptor, "token COLONMINUS")
        stream_literal_list = RewriteRuleSubtreeStream(self._adaptor, "rule literal_list")
        try:
            try:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:104:5: ( literal_list COLONMINUS literal_list -> ^( RULE literal_list literal_list ) )
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:104:7: literal_list COLONMINUS literal_list
                pass 
                self._state.following.append(self.FOLLOW_literal_list_in_rule_body494)
                literal_list25 = self.literal_list()

                self._state.following.pop()
                stream_literal_list.add(literal_list25.tree)


                COLONMINUS26 = self.match(self.input, COLONMINUS, self.FOLLOW_COLONMINUS_in_rule_body496) 
                stream_COLONMINUS.add(COLONMINUS26)


                self._state.following.append(self.FOLLOW_literal_list_in_rule_body498)
                literal_list27 = self.literal_list()

                self._state.following.pop()
                stream_literal_list.add(literal_list27.tree)


                # AST Rewrite
                # elements: literal_list, literal_list
                # token labels: 
                # rule labels: retval
                # token list labels: 
                # rule list labels: 
                # wildcard labels: 
                retval.tree = root_0
                if retval is not None:
                    stream_retval = RewriteRuleSubtreeStream(self._adaptor, "rule retval", retval.tree)
                else:
                    stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                root_0 = self._adaptor.nil()
                # 104:44: -> ^( RULE literal_list literal_list )
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:104:47: ^( RULE literal_list literal_list )
                root_1 = self._adaptor.nil()
                root_1 = self._adaptor.becomeRoot(
                self._adaptor.createFromType(RULE, "RULE")
                , root_1)

                self._adaptor.addChild(root_1, stream_literal_list.nextTree())

                self._adaptor.addChild(root_1, stream_literal_list.nextTree())

                self._adaptor.addChild(root_0, root_1)




                retval.tree = root_0





                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "rule_body"


    class literal_list_return(ParserRuleReturnScope):
        def __init__(self):
            super(CongressParser.literal_list_return, self).__init__()

            self.tree = None





    # $ANTLR start "literal_list"
    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:107:1: literal_list : literal ( COMMA literal )* -> ^( AND ( literal )+ ) ;
    def literal_list(self, ):
        retval = self.literal_list_return()
        retval.start = self.input.LT(1)


        root_0 = None

        COMMA29 = None
        literal28 = None
        literal30 = None

        COMMA29_tree = None
        stream_COMMA = RewriteRuleTokenStream(self._adaptor, "token COMMA")
        stream_literal = RewriteRuleSubtreeStream(self._adaptor, "rule literal")
        try:
            try:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:108:5: ( literal ( COMMA literal )* -> ^( AND ( literal )+ ) )
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:108:7: literal ( COMMA literal )*
                pass 
                self._state.following.append(self.FOLLOW_literal_in_literal_list525)
                literal28 = self.literal()

                self._state.following.pop()
                stream_literal.add(literal28.tree)


                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:108:15: ( COMMA literal )*
                while True: #loop8
                    alt8 = 2
                    LA8_0 = self.input.LA(1)

                    if (LA8_0 == COMMA) :
                        LA8_2 = self.input.LA(2)

                        if (LA8_2 == ID or LA8_2 == NEGATION) :
                            alt8 = 1




                    if alt8 == 1:
                        # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:108:16: COMMA literal
                        pass 
                        COMMA29 = self.match(self.input, COMMA, self.FOLLOW_COMMA_in_literal_list528) 
                        stream_COMMA.add(COMMA29)


                        self._state.following.append(self.FOLLOW_literal_in_literal_list530)
                        literal30 = self.literal()

                        self._state.following.pop()
                        stream_literal.add(literal30.tree)



                    else:
                        break #loop8


                # AST Rewrite
                # elements: literal
                # token labels: 
                # rule labels: retval
                # token list labels: 
                # rule list labels: 
                # wildcard labels: 
                retval.tree = root_0
                if retval is not None:
                    stream_retval = RewriteRuleSubtreeStream(self._adaptor, "rule retval", retval.tree)
                else:
                    stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                root_0 = self._adaptor.nil()
                # 108:32: -> ^( AND ( literal )+ )
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:108:35: ^( AND ( literal )+ )
                root_1 = self._adaptor.nil()
                root_1 = self._adaptor.becomeRoot(
                self._adaptor.createFromType(AND, "AND")
                , root_1)

                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:108:41: ( literal )+
                if not (stream_literal.hasNext()):
                    raise RewriteEarlyExitException()

                while stream_literal.hasNext():
                    self._adaptor.addChild(root_1, stream_literal.nextTree())


                stream_literal.reset()

                self._adaptor.addChild(root_0, root_1)




                retval.tree = root_0





                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "literal_list"


    class literal_return(ParserRuleReturnScope):
        def __init__(self):
            super(CongressParser.literal_return, self).__init__()

            self.tree = None





    # $ANTLR start "literal"
    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:111:1: literal : ( fact -> fact | NEGATION fact -> ^( NOT fact ) );
    def literal(self, ):
        retval = self.literal_return()
        retval.start = self.input.LT(1)


        root_0 = None

        NEGATION32 = None
        fact31 = None
        fact33 = None

        NEGATION32_tree = None
        stream_NEGATION = RewriteRuleTokenStream(self._adaptor, "token NEGATION")
        stream_fact = RewriteRuleSubtreeStream(self._adaptor, "rule fact")
        try:
            try:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:112:5: ( fact -> fact | NEGATION fact -> ^( NOT fact ) )
                alt9 = 2
                LA9_0 = self.input.LA(1)

                if (LA9_0 == ID) :
                    alt9 = 1
                elif (LA9_0 == NEGATION) :
                    alt9 = 2
                else:
                    nvae = NoViableAltException("", 9, 0, self.input)

                    raise nvae


                if alt9 == 1:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:112:7: fact
                    pass 
                    self._state.following.append(self.FOLLOW_fact_in_literal558)
                    fact31 = self.fact()

                    self._state.following.pop()
                    stream_fact.add(fact31.tree)


                    # AST Rewrite
                    # elements: fact
                    # token labels: 
                    # rule labels: retval
                    # token list labels: 
                    # rule list labels: 
                    # wildcard labels: 
                    retval.tree = root_0
                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "rule retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()
                    # 112:23: -> fact
                    self._adaptor.addChild(root_0, stream_fact.nextTree())




                    retval.tree = root_0




                elif alt9 == 2:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:113:7: NEGATION fact
                    pass 
                    NEGATION32 = self.match(self.input, NEGATION, self.FOLLOW_NEGATION_in_literal581) 
                    stream_NEGATION.add(NEGATION32)


                    self._state.following.append(self.FOLLOW_fact_in_literal583)
                    fact33 = self.fact()

                    self._state.following.pop()
                    stream_fact.add(fact33.tree)


                    # AST Rewrite
                    # elements: fact
                    # token labels: 
                    # rule labels: retval
                    # token list labels: 
                    # rule list labels: 
                    # wildcard labels: 
                    retval.tree = root_0
                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "rule retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()
                    # 113:23: -> ^( NOT fact )
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:113:26: ^( NOT fact )
                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(
                    self._adaptor.createFromType(NOT, "NOT")
                    , root_1)

                    self._adaptor.addChild(root_1, stream_fact.nextTree())

                    self._adaptor.addChild(root_0, root_1)




                    retval.tree = root_0




                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "literal"


    class fact_return(ParserRuleReturnScope):
        def __init__(self):
            super(CongressParser.fact_return, self).__init__()

            self.tree = None





    # $ANTLR start "fact"
    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:116:1: fact : ( atom | ID LBRACKET atom RBRACKET -> ^( MODAL ID atom ) );
    def fact(self, ):
        retval = self.fact_return()
        retval.start = self.input.LT(1)


        root_0 = None

        ID35 = None
        LBRACKET36 = None
        RBRACKET38 = None
        atom34 = None
        atom37 = None

        ID35_tree = None
        LBRACKET36_tree = None
        RBRACKET38_tree = None
        stream_LBRACKET = RewriteRuleTokenStream(self._adaptor, "token LBRACKET")
        stream_RBRACKET = RewriteRuleTokenStream(self._adaptor, "token RBRACKET")
        stream_ID = RewriteRuleTokenStream(self._adaptor, "token ID")
        stream_atom = RewriteRuleSubtreeStream(self._adaptor, "rule atom")
        try:
            try:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:117:5: ( atom | ID LBRACKET atom RBRACKET -> ^( MODAL ID atom ) )
                alt10 = 2
                LA10_0 = self.input.LA(1)

                if (LA10_0 == ID) :
                    LA10_1 = self.input.LA(2)

                    if (LA10_1 == LBRACKET) :
                        alt10 = 2
                    elif (LA10_1 == EOF or LA10_1 == COLONMINUS or (COMMA <= LA10_1 <= DELETE) or (ID <= LA10_1 <= INSERT) or LA10_1 == LPAREN or LA10_1 == NEGATION or LA10_1 == SIGN or (54 <= LA10_1 <= 56)) :
                        alt10 = 1
                    else:
                        nvae = NoViableAltException("", 10, 1, self.input)

                        raise nvae


                else:
                    nvae = NoViableAltException("", 10, 0, self.input)

                    raise nvae


                if alt10 == 1:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:117:7: atom
                    pass 
                    root_0 = self._adaptor.nil()


                    self._state.following.append(self.FOLLOW_atom_in_fact610)
                    atom34 = self.atom()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, atom34.tree)



                elif alt10 == 2:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:118:7: ID LBRACKET atom RBRACKET
                    pass 
                    ID35 = self.match(self.input, ID, self.FOLLOW_ID_in_fact618) 
                    stream_ID.add(ID35)


                    LBRACKET36 = self.match(self.input, LBRACKET, self.FOLLOW_LBRACKET_in_fact620) 
                    stream_LBRACKET.add(LBRACKET36)


                    self._state.following.append(self.FOLLOW_atom_in_fact622)
                    atom37 = self.atom()

                    self._state.following.pop()
                    stream_atom.add(atom37.tree)


                    RBRACKET38 = self.match(self.input, RBRACKET, self.FOLLOW_RBRACKET_in_fact624) 
                    stream_RBRACKET.add(RBRACKET38)


                    # AST Rewrite
                    # elements: ID, atom
                    # token labels: 
                    # rule labels: retval
                    # token list labels: 
                    # rule list labels: 
                    # wildcard labels: 
                    retval.tree = root_0
                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "rule retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()
                    # 118:33: -> ^( MODAL ID atom )
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:118:36: ^( MODAL ID atom )
                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(
                    self._adaptor.createFromType(MODAL, "MODAL")
                    , root_1)

                    self._adaptor.addChild(root_1, 
                    stream_ID.nextNode()
                    )

                    self._adaptor.addChild(root_1, stream_atom.nextTree())

                    self._adaptor.addChild(root_0, root_1)




                    retval.tree = root_0




                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "fact"


    class atom_return(ParserRuleReturnScope):
        def __init__(self):
            super(CongressParser.atom_return, self).__init__()

            self.tree = None





    # $ANTLR start "atom"
    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:121:1: atom : relation_constant ( LPAREN ( parameter_list )? RPAREN )? -> ^( ATOM relation_constant ( parameter_list )? ) ;
    def atom(self, ):
        retval = self.atom_return()
        retval.start = self.input.LT(1)


        root_0 = None

        LPAREN40 = None
        RPAREN42 = None
        relation_constant39 = None
        parameter_list41 = None

        LPAREN40_tree = None
        RPAREN42_tree = None
        stream_LPAREN = RewriteRuleTokenStream(self._adaptor, "token LPAREN")
        stream_RPAREN = RewriteRuleTokenStream(self._adaptor, "token RPAREN")
        stream_relation_constant = RewriteRuleSubtreeStream(self._adaptor, "rule relation_constant")
        stream_parameter_list = RewriteRuleSubtreeStream(self._adaptor, "rule parameter_list")
        try:
            try:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:122:5: ( relation_constant ( LPAREN ( parameter_list )? RPAREN )? -> ^( ATOM relation_constant ( parameter_list )? ) )
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:122:7: relation_constant ( LPAREN ( parameter_list )? RPAREN )?
                pass 
                self._state.following.append(self.FOLLOW_relation_constant_in_atom651)
                relation_constant39 = self.relation_constant()

                self._state.following.pop()
                stream_relation_constant.add(relation_constant39.tree)


                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:122:25: ( LPAREN ( parameter_list )? RPAREN )?
                alt12 = 2
                LA12_0 = self.input.LA(1)

                if (LA12_0 == LPAREN) :
                    alt12 = 1
                if alt12 == 1:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:122:26: LPAREN ( parameter_list )? RPAREN
                    pass 
                    LPAREN40 = self.match(self.input, LPAREN, self.FOLLOW_LPAREN_in_atom654) 
                    stream_LPAREN.add(LPAREN40)


                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:122:33: ( parameter_list )?
                    alt11 = 2
                    LA11_0 = self.input.LA(1)

                    if (LA11_0 == FLOAT or LA11_0 == ID or LA11_0 == INT or LA11_0 == STRING) :
                        alt11 = 1
                    if alt11 == 1:
                        # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:122:33: parameter_list
                        pass 
                        self._state.following.append(self.FOLLOW_parameter_list_in_atom656)
                        parameter_list41 = self.parameter_list()

                        self._state.following.pop()
                        stream_parameter_list.add(parameter_list41.tree)





                    RPAREN42 = self.match(self.input, RPAREN, self.FOLLOW_RPAREN_in_atom659) 
                    stream_RPAREN.add(RPAREN42)





                # AST Rewrite
                # elements: parameter_list, relation_constant
                # token labels: 
                # rule labels: retval
                # token list labels: 
                # rule list labels: 
                # wildcard labels: 
                retval.tree = root_0
                if retval is not None:
                    stream_retval = RewriteRuleSubtreeStream(self._adaptor, "rule retval", retval.tree)
                else:
                    stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                root_0 = self._adaptor.nil()
                # 122:58: -> ^( ATOM relation_constant ( parameter_list )? )
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:122:61: ^( ATOM relation_constant ( parameter_list )? )
                root_1 = self._adaptor.nil()
                root_1 = self._adaptor.becomeRoot(
                self._adaptor.createFromType(ATOM, "ATOM")
                , root_1)

                self._adaptor.addChild(root_1, stream_relation_constant.nextTree())

                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:122:86: ( parameter_list )?
                if stream_parameter_list.hasNext():
                    self._adaptor.addChild(root_1, stream_parameter_list.nextTree())


                stream_parameter_list.reset();

                self._adaptor.addChild(root_0, root_1)




                retval.tree = root_0





                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "atom"


    class parameter_list_return(ParserRuleReturnScope):
        def __init__(self):
            super(CongressParser.parameter_list_return, self).__init__()

            self.tree = None





    # $ANTLR start "parameter_list"
    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:125:1: parameter_list : parameter ( COMMA parameter )* -> ( parameter )+ ;
    def parameter_list(self, ):
        retval = self.parameter_list_return()
        retval.start = self.input.LT(1)


        root_0 = None

        COMMA44 = None
        parameter43 = None
        parameter45 = None

        COMMA44_tree = None
        stream_COMMA = RewriteRuleTokenStream(self._adaptor, "token COMMA")
        stream_parameter = RewriteRuleSubtreeStream(self._adaptor, "rule parameter")
        try:
            try:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:126:5: ( parameter ( COMMA parameter )* -> ( parameter )+ )
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:126:7: parameter ( COMMA parameter )*
                pass 
                self._state.following.append(self.FOLLOW_parameter_in_parameter_list689)
                parameter43 = self.parameter()

                self._state.following.pop()
                stream_parameter.add(parameter43.tree)


                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:126:17: ( COMMA parameter )*
                while True: #loop13
                    alt13 = 2
                    LA13_0 = self.input.LA(1)

                    if (LA13_0 == COMMA) :
                        alt13 = 1


                    if alt13 == 1:
                        # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:126:18: COMMA parameter
                        pass 
                        COMMA44 = self.match(self.input, COMMA, self.FOLLOW_COMMA_in_parameter_list692) 
                        stream_COMMA.add(COMMA44)


                        self._state.following.append(self.FOLLOW_parameter_in_parameter_list694)
                        parameter45 = self.parameter()

                        self._state.following.pop()
                        stream_parameter.add(parameter45.tree)



                    else:
                        break #loop13


                # AST Rewrite
                # elements: parameter
                # token labels: 
                # rule labels: retval
                # token list labels: 
                # rule list labels: 
                # wildcard labels: 
                retval.tree = root_0
                if retval is not None:
                    stream_retval = RewriteRuleSubtreeStream(self._adaptor, "rule retval", retval.tree)
                else:
                    stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                root_0 = self._adaptor.nil()
                # 126:36: -> ( parameter )+
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:126:39: ( parameter )+
                if not (stream_parameter.hasNext()):
                    raise RewriteEarlyExitException()

                while stream_parameter.hasNext():
                    self._adaptor.addChild(root_0, stream_parameter.nextTree())


                stream_parameter.reset()




                retval.tree = root_0





                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "parameter_list"


    class parameter_return(ParserRuleReturnScope):
        def __init__(self):
            super(CongressParser.parameter_return, self).__init__()

            self.tree = None





    # $ANTLR start "parameter"
    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:129:1: parameter : ( term -> term | column_ref EQUAL term -> ^( NAMED_PARAM column_ref term ) );
    def parameter(self, ):
        retval = self.parameter_return()
        retval.start = self.input.LT(1)


        root_0 = None

        EQUAL48 = None
        term46 = None
        column_ref47 = None
        term49 = None

        EQUAL48_tree = None
        stream_EQUAL = RewriteRuleTokenStream(self._adaptor, "token EQUAL")
        stream_term = RewriteRuleSubtreeStream(self._adaptor, "rule term")
        stream_column_ref = RewriteRuleSubtreeStream(self._adaptor, "rule column_ref")
        try:
            try:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:130:5: ( term -> term | column_ref EQUAL term -> ^( NAMED_PARAM column_ref term ) )
                alt14 = 2
                LA14 = self.input.LA(1)
                if LA14 == INT:
                    LA14_1 = self.input.LA(2)

                    if (LA14_1 == COMMA or LA14_1 == RPAREN) :
                        alt14 = 1
                    elif (LA14_1 == EQUAL) :
                        alt14 = 2
                    else:
                        nvae = NoViableAltException("", 14, 1, self.input)

                        raise nvae


                elif LA14 == FLOAT or LA14 == STRING:
                    alt14 = 1
                elif LA14 == ID:
                    LA14_3 = self.input.LA(2)

                    if (LA14_3 == COMMA or LA14_3 == RPAREN) :
                        alt14 = 1
                    elif (LA14_3 == EQUAL) :
                        alt14 = 2
                    else:
                        nvae = NoViableAltException("", 14, 3, self.input)

                        raise nvae


                else:
                    nvae = NoViableAltException("", 14, 0, self.input)

                    raise nvae


                if alt14 == 1:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:130:7: term
                    pass 
                    self._state.following.append(self.FOLLOW_term_in_parameter718)
                    term46 = self.term()

                    self._state.following.pop()
                    stream_term.add(term46.tree)


                    # AST Rewrite
                    # elements: term
                    # token labels: 
                    # rule labels: retval
                    # token list labels: 
                    # rule list labels: 
                    # wildcard labels: 
                    retval.tree = root_0
                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "rule retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()
                    # 130:12: -> term
                    self._adaptor.addChild(root_0, stream_term.nextTree())




                    retval.tree = root_0




                elif alt14 == 2:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:131:7: column_ref EQUAL term
                    pass 
                    self._state.following.append(self.FOLLOW_column_ref_in_parameter730)
                    column_ref47 = self.column_ref()

                    self._state.following.pop()
                    stream_column_ref.add(column_ref47.tree)


                    EQUAL48 = self.match(self.input, EQUAL, self.FOLLOW_EQUAL_in_parameter732) 
                    stream_EQUAL.add(EQUAL48)


                    self._state.following.append(self.FOLLOW_term_in_parameter734)
                    term49 = self.term()

                    self._state.following.pop()
                    stream_term.add(term49.tree)


                    # AST Rewrite
                    # elements: column_ref, term
                    # token labels: 
                    # rule labels: retval
                    # token list labels: 
                    # rule list labels: 
                    # wildcard labels: 
                    retval.tree = root_0
                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "rule retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()
                    # 131:29: -> ^( NAMED_PARAM column_ref term )
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:131:32: ^( NAMED_PARAM column_ref term )
                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(
                    self._adaptor.createFromType(NAMED_PARAM, "NAMED_PARAM")
                    , root_1)

                    self._adaptor.addChild(root_1, stream_column_ref.nextTree())

                    self._adaptor.addChild(root_1, stream_term.nextTree())

                    self._adaptor.addChild(root_0, root_1)




                    retval.tree = root_0




                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "parameter"


    class column_ref_return(ParserRuleReturnScope):
        def __init__(self):
            super(CongressParser.column_ref_return, self).__init__()

            self.tree = None





    # $ANTLR start "column_ref"
    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:134:1: column_ref : ( ID -> ^( COLUMN_NAME ID ) | INT -> ^( COLUMN_NUMBER INT ) );
    def column_ref(self, ):
        retval = self.column_ref_return()
        retval.start = self.input.LT(1)


        root_0 = None

        ID50 = None
        INT51 = None

        ID50_tree = None
        INT51_tree = None
        stream_ID = RewriteRuleTokenStream(self._adaptor, "token ID")
        stream_INT = RewriteRuleTokenStream(self._adaptor, "token INT")

        try:
            try:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:135:5: ( ID -> ^( COLUMN_NAME ID ) | INT -> ^( COLUMN_NUMBER INT ) )
                alt15 = 2
                LA15_0 = self.input.LA(1)

                if (LA15_0 == ID) :
                    alt15 = 1
                elif (LA15_0 == INT) :
                    alt15 = 2
                else:
                    nvae = NoViableAltException("", 15, 0, self.input)

                    raise nvae


                if alt15 == 1:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:135:7: ID
                    pass 
                    ID50 = self.match(self.input, ID, self.FOLLOW_ID_in_column_ref761) 
                    stream_ID.add(ID50)


                    # AST Rewrite
                    # elements: ID
                    # token labels: 
                    # rule labels: retval
                    # token list labels: 
                    # rule list labels: 
                    # wildcard labels: 
                    retval.tree = root_0
                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "rule retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()
                    # 135:12: -> ^( COLUMN_NAME ID )
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:135:16: ^( COLUMN_NAME ID )
                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(
                    self._adaptor.createFromType(COLUMN_NAME, "COLUMN_NAME")
                    , root_1)

                    self._adaptor.addChild(root_1, 
                    stream_ID.nextNode()
                    )

                    self._adaptor.addChild(root_0, root_1)




                    retval.tree = root_0




                elif alt15 == 2:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:136:7: INT
                    pass 
                    INT51 = self.match(self.input, INT, self.FOLLOW_INT_in_column_ref780) 
                    stream_INT.add(INT51)


                    # AST Rewrite
                    # elements: INT
                    # token labels: 
                    # rule labels: retval
                    # token list labels: 
                    # rule list labels: 
                    # wildcard labels: 
                    retval.tree = root_0
                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "rule retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()
                    # 136:12: -> ^( COLUMN_NUMBER INT )
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:136:16: ^( COLUMN_NUMBER INT )
                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(
                    self._adaptor.createFromType(COLUMN_NUMBER, "COLUMN_NUMBER")
                    , root_1)

                    self._adaptor.addChild(root_1, 
                    stream_INT.nextNode()
                    )

                    self._adaptor.addChild(root_0, root_1)




                    retval.tree = root_0




                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "column_ref"


    class term_return(ParserRuleReturnScope):
        def __init__(self):
            super(CongressParser.term_return, self).__init__()

            self.tree = None





    # $ANTLR start "term"
    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:139:1: term : ( object_constant | variable );
    def term(self, ):
        retval = self.term_return()
        retval.start = self.input.LT(1)


        root_0 = None

        object_constant52 = None
        variable53 = None


        try:
            try:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:140:5: ( object_constant | variable )
                alt16 = 2
                LA16_0 = self.input.LA(1)

                if (LA16_0 == FLOAT or LA16_0 == INT or LA16_0 == STRING) :
                    alt16 = 1
                elif (LA16_0 == ID) :
                    alt16 = 2
                else:
                    nvae = NoViableAltException("", 16, 0, self.input)

                    raise nvae


                if alt16 == 1:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:140:7: object_constant
                    pass 
                    root_0 = self._adaptor.nil()


                    self._state.following.append(self.FOLLOW_object_constant_in_term807)
                    object_constant52 = self.object_constant()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, object_constant52.tree)



                elif alt16 == 2:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:141:7: variable
                    pass 
                    root_0 = self._adaptor.nil()


                    self._state.following.append(self.FOLLOW_variable_in_term815)
                    variable53 = self.variable()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, variable53.tree)



                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "term"


    class object_constant_return(ParserRuleReturnScope):
        def __init__(self):
            super(CongressParser.object_constant_return, self).__init__()

            self.tree = None





    # $ANTLR start "object_constant"
    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:144:1: object_constant : ( INT -> ^( INTEGER_OBJ INT ) | FLOAT -> ^( FLOAT_OBJ FLOAT ) | STRING -> ^( STRING_OBJ STRING ) );
    def object_constant(self, ):
        retval = self.object_constant_return()
        retval.start = self.input.LT(1)


        root_0 = None

        INT54 = None
        FLOAT55 = None
        STRING56 = None

        INT54_tree = None
        FLOAT55_tree = None
        STRING56_tree = None
        stream_FLOAT = RewriteRuleTokenStream(self._adaptor, "token FLOAT")
        stream_STRING = RewriteRuleTokenStream(self._adaptor, "token STRING")
        stream_INT = RewriteRuleTokenStream(self._adaptor, "token INT")

        try:
            try:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:145:5: ( INT -> ^( INTEGER_OBJ INT ) | FLOAT -> ^( FLOAT_OBJ FLOAT ) | STRING -> ^( STRING_OBJ STRING ) )
                alt17 = 3
                LA17 = self.input.LA(1)
                if LA17 == INT:
                    alt17 = 1
                elif LA17 == FLOAT:
                    alt17 = 2
                elif LA17 == STRING:
                    alt17 = 3
                else:
                    nvae = NoViableAltException("", 17, 0, self.input)

                    raise nvae


                if alt17 == 1:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:145:7: INT
                    pass 
                    INT54 = self.match(self.input, INT, self.FOLLOW_INT_in_object_constant832) 
                    stream_INT.add(INT54)


                    # AST Rewrite
                    # elements: INT
                    # token labels: 
                    # rule labels: retval
                    # token list labels: 
                    # rule list labels: 
                    # wildcard labels: 
                    retval.tree = root_0
                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "rule retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()
                    # 145:16: -> ^( INTEGER_OBJ INT )
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:145:19: ^( INTEGER_OBJ INT )
                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(
                    self._adaptor.createFromType(INTEGER_OBJ, "INTEGER_OBJ")
                    , root_1)

                    self._adaptor.addChild(root_1, 
                    stream_INT.nextNode()
                    )

                    self._adaptor.addChild(root_0, root_1)




                    retval.tree = root_0




                elif alt17 == 2:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:146:7: FLOAT
                    pass 
                    FLOAT55 = self.match(self.input, FLOAT, self.FOLLOW_FLOAT_in_object_constant853) 
                    stream_FLOAT.add(FLOAT55)


                    # AST Rewrite
                    # elements: FLOAT
                    # token labels: 
                    # rule labels: retval
                    # token list labels: 
                    # rule list labels: 
                    # wildcard labels: 
                    retval.tree = root_0
                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "rule retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()
                    # 146:16: -> ^( FLOAT_OBJ FLOAT )
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:146:19: ^( FLOAT_OBJ FLOAT )
                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(
                    self._adaptor.createFromType(FLOAT_OBJ, "FLOAT_OBJ")
                    , root_1)

                    self._adaptor.addChild(root_1, 
                    stream_FLOAT.nextNode()
                    )

                    self._adaptor.addChild(root_0, root_1)




                    retval.tree = root_0




                elif alt17 == 3:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:147:7: STRING
                    pass 
                    STRING56 = self.match(self.input, STRING, self.FOLLOW_STRING_in_object_constant872) 
                    stream_STRING.add(STRING56)


                    # AST Rewrite
                    # elements: STRING
                    # token labels: 
                    # rule labels: retval
                    # token list labels: 
                    # rule list labels: 
                    # wildcard labels: 
                    retval.tree = root_0
                    if retval is not None:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "rule retval", retval.tree)
                    else:
                        stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                    root_0 = self._adaptor.nil()
                    # 147:16: -> ^( STRING_OBJ STRING )
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:147:19: ^( STRING_OBJ STRING )
                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(
                    self._adaptor.createFromType(STRING_OBJ, "STRING_OBJ")
                    , root_1)

                    self._adaptor.addChild(root_1, 
                    stream_STRING.nextNode()
                    )

                    self._adaptor.addChild(root_0, root_1)




                    retval.tree = root_0




                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "object_constant"


    class variable_return(ParserRuleReturnScope):
        def __init__(self):
            super(CongressParser.variable_return, self).__init__()

            self.tree = None





    # $ANTLR start "variable"
    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:150:1: variable : ID -> ^( VARIABLE ID ) ;
    def variable(self, ):
        retval = self.variable_return()
        retval.start = self.input.LT(1)


        root_0 = None

        ID57 = None

        ID57_tree = None
        stream_ID = RewriteRuleTokenStream(self._adaptor, "token ID")

        try:
            try:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:151:5: ( ID -> ^( VARIABLE ID ) )
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:151:7: ID
                pass 
                ID57 = self.match(self.input, ID, self.FOLLOW_ID_in_variable899) 
                stream_ID.add(ID57)


                # AST Rewrite
                # elements: ID
                # token labels: 
                # rule labels: retval
                # token list labels: 
                # rule list labels: 
                # wildcard labels: 
                retval.tree = root_0
                if retval is not None:
                    stream_retval = RewriteRuleSubtreeStream(self._adaptor, "rule retval", retval.tree)
                else:
                    stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                root_0 = self._adaptor.nil()
                # 151:10: -> ^( VARIABLE ID )
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:151:13: ^( VARIABLE ID )
                root_1 = self._adaptor.nil()
                root_1 = self._adaptor.becomeRoot(
                self._adaptor.createFromType(VARIABLE, "VARIABLE")
                , root_1)

                self._adaptor.addChild(root_1, 
                stream_ID.nextNode()
                )

                self._adaptor.addChild(root_0, root_1)




                retval.tree = root_0





                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "variable"


    class relation_constant_return(ParserRuleReturnScope):
        def __init__(self):
            super(CongressParser.relation_constant_return, self).__init__()

            self.tree = None





    # $ANTLR start "relation_constant"
    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:154:1: relation_constant : ID ( ':' ID )* ( SIGN )? -> ^( STRUCTURED_NAME ( ID )+ ( SIGN )? ) ;
    def relation_constant(self, ):
        retval = self.relation_constant_return()
        retval.start = self.input.LT(1)


        root_0 = None

        ID58 = None
        char_literal59 = None
        ID60 = None
        SIGN61 = None

        ID58_tree = None
        char_literal59_tree = None
        ID60_tree = None
        SIGN61_tree = None
        stream_55 = RewriteRuleTokenStream(self._adaptor, "token 55")
        stream_ID = RewriteRuleTokenStream(self._adaptor, "token ID")
        stream_SIGN = RewriteRuleTokenStream(self._adaptor, "token SIGN")

        try:
            try:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:155:5: ( ID ( ':' ID )* ( SIGN )? -> ^( STRUCTURED_NAME ( ID )+ ( SIGN )? ) )
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:155:7: ID ( ':' ID )* ( SIGN )?
                pass 
                ID58 = self.match(self.input, ID, self.FOLLOW_ID_in_relation_constant924) 
                stream_ID.add(ID58)


                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:155:10: ( ':' ID )*
                while True: #loop18
                    alt18 = 2
                    LA18_0 = self.input.LA(1)

                    if (LA18_0 == 55) :
                        alt18 = 1


                    if alt18 == 1:
                        # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:155:11: ':' ID
                        pass 
                        char_literal59 = self.match(self.input, 55, self.FOLLOW_55_in_relation_constant927) 
                        stream_55.add(char_literal59)


                        ID60 = self.match(self.input, ID, self.FOLLOW_ID_in_relation_constant929) 
                        stream_ID.add(ID60)



                    else:
                        break #loop18


                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:155:20: ( SIGN )?
                alt19 = 2
                LA19_0 = self.input.LA(1)

                if (LA19_0 == SIGN) :
                    alt19 = 1
                if alt19 == 1:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:155:20: SIGN
                    pass 
                    SIGN61 = self.match(self.input, SIGN, self.FOLLOW_SIGN_in_relation_constant933) 
                    stream_SIGN.add(SIGN61)





                # AST Rewrite
                # elements: ID, SIGN
                # token labels: 
                # rule labels: retval
                # token list labels: 
                # rule list labels: 
                # wildcard labels: 
                retval.tree = root_0
                if retval is not None:
                    stream_retval = RewriteRuleSubtreeStream(self._adaptor, "rule retval", retval.tree)
                else:
                    stream_retval = RewriteRuleSubtreeStream(self._adaptor, "token retval", None)


                root_0 = self._adaptor.nil()
                # 155:26: -> ^( STRUCTURED_NAME ( ID )+ ( SIGN )? )
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:155:29: ^( STRUCTURED_NAME ( ID )+ ( SIGN )? )
                root_1 = self._adaptor.nil()
                root_1 = self._adaptor.becomeRoot(
                self._adaptor.createFromType(STRUCTURED_NAME, "STRUCTURED_NAME")
                , root_1)

                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:155:47: ( ID )+
                if not (stream_ID.hasNext()):
                    raise RewriteEarlyExitException()

                while stream_ID.hasNext():
                    self._adaptor.addChild(root_1, 
                    stream_ID.nextNode()
                    )


                stream_ID.reset()

                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:155:51: ( SIGN )?
                if stream_SIGN.hasNext():
                    self._adaptor.addChild(root_1, 
                    stream_SIGN.nextNode()
                    )


                stream_SIGN.reset();

                self._adaptor.addChild(root_0, root_1)




                retval.tree = root_0





                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException, re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "relation_constant"



    # lookup tables for DFA #5

    DFA5_eot = DFA.unpack(
        u"\67\uffff"
        )

    DFA5_eof = DFA.unpack(
        u"\2\uffff\1\7\2\uffff\1\7\3\uffff\1\7\4\uffff\1\7\3\uffff\1\7\44"
        u"\uffff"
        )

    DFA5_min = DFA.unpack(
        u"\1\20\1\uffff\1\13\2\32\1\13\1\24\1\uffff\1\41\1\13\4\16\1\13\1"
        u"\32\1\41\1\24\1\13\2\24\1\41\4\16\1\47\10\16\3\24\14\16\1\24\4"
        u"\16"
        )

    DFA5_max = DFA.unpack(
        u"\1\44\1\uffff\1\70\2\32\1\70\1\55\1\uffff\1\67\1\70\4\50\1\70\1"
        u"\32\1\47\1\55\1\70\2\55\1\67\4\50\1\47\10\50\3\55\14\50\1\55\4"
        u"\50"
        )

    DFA5_accept = DFA.unpack(
        u"\1\uffff\1\1\5\uffff\1\2\57\uffff"
        )

    DFA5_special = DFA.unpack(
        u"\67\uffff"
        )


    DFA5_transition = [
        DFA.unpack(u"\1\1\11\uffff\1\2\1\1\10\uffff\1\1"),
        DFA.unpack(u""),
        DFA.unpack(u"\1\1\2\uffff\1\1\2\7\11\uffff\2\7\3\uffff\1\3\1\uffff"
        u"\1\6\2\uffff\1\7\5\uffff\1\5\13\uffff\1\7\1\4\1\7"),
        DFA.unpack(u"\1\10"),
        DFA.unpack(u"\1\11"),
        DFA.unpack(u"\1\1\2\uffff\1\1\2\7\11\uffff\2\7\5\uffff\1\6\2\uffff"
        u"\1\7\21\uffff\1\7\1\uffff\1\7"),
        DFA.unpack(u"\1\13\5\uffff\1\15\1\uffff\1\12\13\uffff\1\16\4\uffff"
        u"\1\14"),
        DFA.unpack(u""),
        DFA.unpack(u"\1\21\5\uffff\1\22\2\uffff\1\20\14\uffff\1\17"),
        DFA.unpack(u"\1\1\2\uffff\1\1\2\7\11\uffff\2\7\5\uffff\1\6\2\uffff"
        u"\1\7\5\uffff\1\5\13\uffff\1\7\1\4\1\7"),
        DFA.unpack(u"\1\23\3\uffff\1\24\25\uffff\1\16"),
        DFA.unpack(u"\1\23\31\uffff\1\16"),
        DFA.unpack(u"\1\23\31\uffff\1\16"),
        DFA.unpack(u"\1\23\3\uffff\1\24\25\uffff\1\16"),
        DFA.unpack(u"\1\1\2\uffff\1\1\2\7\11\uffff\2\7\10\uffff\1\7\21\uffff"
        u"\1\7\1\uffff\1\7"),
        DFA.unpack(u"\1\25"),
        DFA.unpack(u"\1\21\5\uffff\1\22"),
        DFA.unpack(u"\1\27\5\uffff\1\31\1\uffff\1\26\13\uffff\1\32\4\uffff"
        u"\1\30"),
        DFA.unpack(u"\1\1\2\uffff\1\1\2\7\11\uffff\2\7\10\uffff\1\7\21\uffff"
        u"\1\7\1\uffff\1\7"),
        DFA.unpack(u"\1\34\5\uffff\1\36\1\uffff\1\33\20\uffff\1\35"),
        DFA.unpack(u"\1\40\5\uffff\1\42\1\uffff\1\37\20\uffff\1\41"),
        DFA.unpack(u"\1\21\5\uffff\1\22\2\uffff\1\20\14\uffff\1\17"),
        DFA.unpack(u"\1\43\3\uffff\1\44\25\uffff\1\32"),
        DFA.unpack(u"\1\43\31\uffff\1\32"),
        DFA.unpack(u"\1\43\31\uffff\1\32"),
        DFA.unpack(u"\1\43\3\uffff\1\44\25\uffff\1\32"),
        DFA.unpack(u"\1\22"),
        DFA.unpack(u"\1\23\3\uffff\1\45\25\uffff\1\16"),
        DFA.unpack(u"\1\23\31\uffff\1\16"),
        DFA.unpack(u"\1\23\31\uffff\1\16"),
        DFA.unpack(u"\1\23\3\uffff\1\45\25\uffff\1\16"),
        DFA.unpack(u"\1\23\31\uffff\1\16"),
        DFA.unpack(u"\1\23\31\uffff\1\16"),
        DFA.unpack(u"\1\23\31\uffff\1\16"),
        DFA.unpack(u"\1\23\31\uffff\1\16"),
        DFA.unpack(u"\1\47\5\uffff\1\51\1\uffff\1\46\20\uffff\1\50"),
        DFA.unpack(u"\1\53\5\uffff\1\55\1\uffff\1\52\20\uffff\1\54"),
        DFA.unpack(u"\1\57\5\uffff\1\61\1\uffff\1\56\20\uffff\1\60"),
        DFA.unpack(u"\1\43\3\uffff\1\62\25\uffff\1\32"),
        DFA.unpack(u"\1\43\31\uffff\1\32"),
        DFA.unpack(u"\1\43\31\uffff\1\32"),
        DFA.unpack(u"\1\43\3\uffff\1\62\25\uffff\1\32"),
        DFA.unpack(u"\1\43\31\uffff\1\32"),
        DFA.unpack(u"\1\43\31\uffff\1\32"),
        DFA.unpack(u"\1\43\31\uffff\1\32"),
        DFA.unpack(u"\1\43\31\uffff\1\32"),
        DFA.unpack(u"\1\23\31\uffff\1\16"),
        DFA.unpack(u"\1\23\31\uffff\1\16"),
        DFA.unpack(u"\1\23\31\uffff\1\16"),
        DFA.unpack(u"\1\23\31\uffff\1\16"),
        DFA.unpack(u"\1\64\5\uffff\1\66\1\uffff\1\63\20\uffff\1\65"),
        DFA.unpack(u"\1\43\31\uffff\1\32"),
        DFA.unpack(u"\1\43\31\uffff\1\32"),
        DFA.unpack(u"\1\43\31\uffff\1\32"),
        DFA.unpack(u"\1\43\31\uffff\1\32")
    ]

    # class definition for DFA #5

    class DFA5(DFA):
        pass


    # lookup tables for DFA #7

    DFA7_eot = DFA.unpack(
        u"\72\uffff"
        )

    DFA7_eof = DFA.unpack(
        u"\72\uffff"
        )

    DFA7_min = DFA.unpack(
        u"\1\20\1\37\1\32\1\13\1\uffff\2\32\1\13\1\24\1\32\1\41\1\13\4\16"
        u"\1\13\1\uffff\1\32\1\41\1\24\1\13\2\24\1\41\4\16\1\47\10\16\3\24"
        u"\14\16\1\24\4\16"
        )

    DFA7_max = DFA.unpack(
        u"\1\33\1\37\1\44\1\67\1\uffff\2\32\1\41\2\55\2\67\4\50\1\16\1\uffff"
        u"\1\32\1\47\1\55\1\16\2\55\1\67\4\50\1\47\10\50\3\55\14\50\1\55"
        u"\4\50"
        )

    DFA7_accept = DFA.unpack(
        u"\4\uffff\1\1\14\uffff\1\2\50\uffff"
        )

    DFA7_special = DFA.unpack(
        u"\72\uffff"
        )


    DFA7_transition = [
        DFA.unpack(u"\1\1\12\uffff\1\1"),
        DFA.unpack(u"\1\2"),
        DFA.unpack(u"\1\3\11\uffff\1\4"),
        DFA.unpack(u"\1\4\2\uffff\1\11\20\uffff\1\5\1\uffff\1\10\10\uffff"
        u"\1\7\14\uffff\1\6"),
        DFA.unpack(u""),
        DFA.unpack(u"\1\12"),
        DFA.unpack(u"\1\13"),
        DFA.unpack(u"\1\4\2\uffff\1\11\22\uffff\1\10"),
        DFA.unpack(u"\1\15\5\uffff\1\17\1\uffff\1\14\13\uffff\1\20\4\uffff"
        u"\1\16"),
        DFA.unpack(u"\1\4\11\uffff\1\4\10\uffff\1\21"),
        DFA.unpack(u"\1\24\5\uffff\1\25\2\uffff\1\23\14\uffff\1\22"),
        DFA.unpack(u"\1\4\2\uffff\1\11\22\uffff\1\10\10\uffff\1\7\14\uffff"
        u"\1\6"),
        DFA.unpack(u"\1\26\3\uffff\1\27\25\uffff\1\20"),
        DFA.unpack(u"\1\26\31\uffff\1\20"),
        DFA.unpack(u"\1\26\31\uffff\1\20"),
        DFA.unpack(u"\1\26\3\uffff\1\27\25\uffff\1\20"),
        DFA.unpack(u"\1\4\2\uffff\1\11"),
        DFA.unpack(u""),
        DFA.unpack(u"\1\30"),
        DFA.unpack(u"\1\24\5\uffff\1\25"),
        DFA.unpack(u"\1\32\5\uffff\1\34\1\uffff\1\31\13\uffff\1\35\4\uffff"
        u"\1\33"),
        DFA.unpack(u"\1\4\2\uffff\1\11"),
        DFA.unpack(u"\1\37\5\uffff\1\41\1\uffff\1\36\20\uffff\1\40"),
        DFA.unpack(u"\1\43\5\uffff\1\45\1\uffff\1\42\20\uffff\1\44"),
        DFA.unpack(u"\1\24\5\uffff\1\25\2\uffff\1\23\14\uffff\1\22"),
        DFA.unpack(u"\1\46\3\uffff\1\47\25\uffff\1\35"),
        DFA.unpack(u"\1\46\31\uffff\1\35"),
        DFA.unpack(u"\1\46\31\uffff\1\35"),
        DFA.unpack(u"\1\46\3\uffff\1\47\25\uffff\1\35"),
        DFA.unpack(u"\1\25"),
        DFA.unpack(u"\1\26\3\uffff\1\50\25\uffff\1\20"),
        DFA.unpack(u"\1\26\31\uffff\1\20"),
        DFA.unpack(u"\1\26\31\uffff\1\20"),
        DFA.unpack(u"\1\26\3\uffff\1\50\25\uffff\1\20"),
        DFA.unpack(u"\1\26\31\uffff\1\20"),
        DFA.unpack(u"\1\26\31\uffff\1\20"),
        DFA.unpack(u"\1\26\31\uffff\1\20"),
        DFA.unpack(u"\1\26\31\uffff\1\20"),
        DFA.unpack(u"\1\52\5\uffff\1\54\1\uffff\1\51\20\uffff\1\53"),
        DFA.unpack(u"\1\56\5\uffff\1\60\1\uffff\1\55\20\uffff\1\57"),
        DFA.unpack(u"\1\62\5\uffff\1\64\1\uffff\1\61\20\uffff\1\63"),
        DFA.unpack(u"\1\46\3\uffff\1\65\25\uffff\1\35"),
        DFA.unpack(u"\1\46\31\uffff\1\35"),
        DFA.unpack(u"\1\46\31\uffff\1\35"),
        DFA.unpack(u"\1\46\3\uffff\1\65\25\uffff\1\35"),
        DFA.unpack(u"\1\46\31\uffff\1\35"),
        DFA.unpack(u"\1\46\31\uffff\1\35"),
        DFA.unpack(u"\1\46\31\uffff\1\35"),
        DFA.unpack(u"\1\46\31\uffff\1\35"),
        DFA.unpack(u"\1\26\31\uffff\1\20"),
        DFA.unpack(u"\1\26\31\uffff\1\20"),
        DFA.unpack(u"\1\26\31\uffff\1\20"),
        DFA.unpack(u"\1\26\31\uffff\1\20"),
        DFA.unpack(u"\1\67\5\uffff\1\71\1\uffff\1\66\20\uffff\1\70"),
        DFA.unpack(u"\1\46\31\uffff\1\35"),
        DFA.unpack(u"\1\46\31\uffff\1\35"),
        DFA.unpack(u"\1\46\31\uffff\1\35"),
        DFA.unpack(u"\1\46\31\uffff\1\35")
    ]

    # class definition for DFA #7

    class DFA7(DFA):
        pass


 

    FOLLOW_statement_in_prog258 = frozenset([15, 16, 26, 27, 36])
    FOLLOW_EOF_in_prog261 = frozenset([1])
    FOLLOW_EOF_in_prog278 = frozenset([1])
    FOLLOW_bare_formula_in_statement297 = frozenset([1, 54, 56])
    FOLLOW_formula_terminator_in_statement299 = frozenset([1])
    FOLLOW_COMMENT_in_statement312 = frozenset([1])
    FOLLOW_rule_in_bare_formula331 = frozenset([1])
    FOLLOW_fact_in_bare_formula339 = frozenset([1])
    FOLLOW_modal_rule_in_rule382 = frozenset([1])
    FOLLOW_rule_body_in_rule390 = frozenset([1])
    FOLLOW_modal_op_in_modal_rule408 = frozenset([31])
    FOLLOW_LBRACKET_in_modal_rule410 = frozenset([26, 36])
    FOLLOW_rule_body_in_modal_rule412 = frozenset([14])
    FOLLOW_policy_name_in_modal_rule414 = frozenset([39])
    FOLLOW_RBRACKET_in_modal_rule416 = frozenset([1])
    FOLLOW_modal_op_in_modal_rule424 = frozenset([31])
    FOLLOW_LBRACKET_in_modal_rule426 = frozenset([26])
    FOLLOW_fact_in_modal_rule428 = frozenset([14])
    FOLLOW_policy_name_in_modal_rule430 = frozenset([39])
    FOLLOW_RBRACKET_in_modal_rule432 = frozenset([1])
    FOLLOW_COMMA_in_policy_name475 = frozenset([45])
    FOLLOW_STRING_in_policy_name477 = frozenset([1])
    FOLLOW_literal_list_in_rule_body494 = frozenset([11])
    FOLLOW_COLONMINUS_in_rule_body496 = frozenset([26, 36])
    FOLLOW_literal_list_in_rule_body498 = frozenset([1])
    FOLLOW_literal_in_literal_list525 = frozenset([1, 14])
    FOLLOW_COMMA_in_literal_list528 = frozenset([26, 36])
    FOLLOW_literal_in_literal_list530 = frozenset([1, 14])
    FOLLOW_fact_in_literal558 = frozenset([1])
    FOLLOW_NEGATION_in_literal581 = frozenset([26])
    FOLLOW_fact_in_literal583 = frozenset([1])
    FOLLOW_atom_in_fact610 = frozenset([1])
    FOLLOW_ID_in_fact618 = frozenset([31])
    FOLLOW_LBRACKET_in_fact620 = frozenset([26])
    FOLLOW_atom_in_fact622 = frozenset([39])
    FOLLOW_RBRACKET_in_fact624 = frozenset([1])
    FOLLOW_relation_constant_in_atom651 = frozenset([1, 33])
    FOLLOW_LPAREN_in_atom654 = frozenset([20, 26, 28, 40, 45])
    FOLLOW_parameter_list_in_atom656 = frozenset([40])
    FOLLOW_RPAREN_in_atom659 = frozenset([1])
    FOLLOW_parameter_in_parameter_list689 = frozenset([1, 14])
    FOLLOW_COMMA_in_parameter_list692 = frozenset([20, 26, 28, 45])
    FOLLOW_parameter_in_parameter_list694 = frozenset([1, 14])
    FOLLOW_term_in_parameter718 = frozenset([1])
    FOLLOW_column_ref_in_parameter730 = frozenset([18])
    FOLLOW_EQUAL_in_parameter732 = frozenset([20, 26, 28, 45])
    FOLLOW_term_in_parameter734 = frozenset([1])
    FOLLOW_ID_in_column_ref761 = frozenset([1])
    FOLLOW_INT_in_column_ref780 = frozenset([1])
    FOLLOW_object_constant_in_term807 = frozenset([1])
    FOLLOW_variable_in_term815 = frozenset([1])
    FOLLOW_INT_in_object_constant832 = frozenset([1])
    FOLLOW_FLOAT_in_object_constant853 = frozenset([1])
    FOLLOW_STRING_in_object_constant872 = frozenset([1])
    FOLLOW_ID_in_variable899 = frozenset([1])
    FOLLOW_ID_in_relation_constant924 = frozenset([1, 42, 55])
    FOLLOW_55_in_relation_constant927 = frozenset([26])
    FOLLOW_ID_in_relation_constant929 = frozenset([1, 42, 55])
    FOLLOW_SIGN_in_relation_constant933 = frozenset([1])



def main(argv, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr):
    from antlr3.main import ParserMain
    main = ParserMain("CongressLexer", CongressParser)

    main.stdin = stdin
    main.stdout = stdout
    main.stderr = stderr
    main.execute(argv)



if __name__ == '__main__':
    main(sys.argv)
