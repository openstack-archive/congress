# $ANTLR 3.5.2 Congress.g 2015-11-02 17:04:43

import sys
from antlr3 import *

from antlr3.tree import *




# for convenience in actions
HIDDEN = BaseRecognizer.HIDDEN

# token types
EOF=-1
T__53=53
T__54=54
T__55=55
T__56=56
T__57=57
T__58=58
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
DIGIT=16
EQUAL=17
EVENT=18
EXPONENT=19
FLOAT=20
FLOAT_EXP=21
FLOAT_NO_EXP=22
FLOAT_OBJ=23
FRAC_PART=24
HEX_DIGIT=25
ID=26
INT=27
INTEGER_OBJ=28
INT_PART=29
LBRACKET=30
LITERAL=31
LPAREN=32
MODAL=33
NAMED_PARAM=34
NEGATION=35
NOT=36
PROG=37
RBRACKET=38
RPAREN=39
RULE=40
SIGN=41
SLBYTESTRING=42
SLSTRING=43
STRING=44
STRING_ESC=45
STRING_OBJ=46
STRPREFIX=47
STRUCTURED_NAME=48
SYMBOL_OBJ=49
THEORY=50
VARIABLE=51
WS=52

# token names
tokenNamesMap = {
    0: "<invalid>", 1: "<EOR>", 2: "<DOWN>", 3: "<UP>",
    -1: "EOF", 53: "T__53", 54: "T__54", 55: "T__55", 56: "T__56", 57: "T__57", 
    58: "T__58", 4: "AND", 5: "ATOM", 6: "BYTESTRPREFIX", 7: "BYTES_CHAR_DQ", 
    8: "BYTES_CHAR_SQ", 9: "BYTES_ESC", 10: "BYTES_TESC", 11: "COLONMINUS", 
    12: "COLUMN_NAME", 13: "COLUMN_NUMBER", 14: "COMMA", 15: "COMMENT", 
    16: "DIGIT", 17: "EQUAL", 18: "EVENT", 19: "EXPONENT", 20: "FLOAT", 
    21: "FLOAT_EXP", 22: "FLOAT_NO_EXP", 23: "FLOAT_OBJ", 24: "FRAC_PART", 
    25: "HEX_DIGIT", 26: "ID", 27: "INT", 28: "INTEGER_OBJ", 29: "INT_PART", 
    30: "LBRACKET", 31: "LITERAL", 32: "LPAREN", 33: "MODAL", 34: "NAMED_PARAM", 
    35: "NEGATION", 36: "NOT", 37: "PROG", 38: "RBRACKET", 39: "RPAREN", 
    40: "RULE", 41: "SIGN", 42: "SLBYTESTRING", 43: "SLSTRING", 44: "STRING", 
    45: "STRING_ESC", 46: "STRING_OBJ", 47: "STRPREFIX", 48: "STRUCTURED_NAME", 
    49: "SYMBOL_OBJ", 50: "THEORY", 51: "VARIABLE", 52: "WS"
}
Token.registerTokenNamesMap(tokenNamesMap)

# token names
tokenNames = [
    "<invalid>", "<EOR>", "<DOWN>", "<UP>",
    "AND", "ATOM", "BYTESTRPREFIX", "BYTES_CHAR_DQ", "BYTES_CHAR_SQ", "BYTES_ESC", 
    "BYTES_TESC", "COLONMINUS", "COLUMN_NAME", "COLUMN_NUMBER", "COMMA", 
    "COMMENT", "DIGIT", "EQUAL", "EVENT", "EXPONENT", "FLOAT", "FLOAT_EXP", 
    "FLOAT_NO_EXP", "FLOAT_OBJ", "FRAC_PART", "HEX_DIGIT", "ID", "INT", 
    "INTEGER_OBJ", "INT_PART", "LBRACKET", "LITERAL", "LPAREN", "MODAL", 
    "NAMED_PARAM", "NEGATION", "NOT", "PROG", "RBRACKET", "RPAREN", "RULE", 
    "SIGN", "SLBYTESTRING", "SLSTRING", "STRING", "STRING_ESC", "STRING_OBJ", 
    "STRPREFIX", "STRUCTURED_NAME", "SYMBOL_OBJ", "THEORY", "VARIABLE", 
    "WS", "'.'", "':'", "';'", "'delete'", "'execute'", "'insert'"
]



class CongressParser(Parser):
    grammarFileName = "Congress.g"
    api_version = 1
    tokenNames = tokenNames

    def __init__(self, input, state=None, *args, **kwargs):
        if state is None:
            state = RecognizerSharedState()

        super().__init__(input, state, *args, **kwargs)

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
            super().__init__()

            self.tree = None





    # $ANTLR start "prog"
    # Congress.g:58:1: prog : ( ( statement )+ EOF -> ^( THEORY ( statement )+ ) | EOF );
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
                # Congress.g:59:5: ( ( statement )+ EOF -> ^( THEORY ( statement )+ ) | EOF )
                alt2 = 2
                LA2_0 = self.input.LA(1)

                if (LA2_0 in {COMMENT, ID, NEGATION, 56, 57, 58}) :
                    alt2 = 1
                elif (LA2_0 == EOF) :
                    alt2 = 2
                else:
                    nvae = NoViableAltException("", 2, 0, self.input)

                    raise nvae


                if alt2 == 1:
                    # Congress.g:59:7: ( statement )+ EOF
                    pass 
                    # Congress.g:59:7: ( statement )+
                    cnt1 = 0
                    while True: #loop1
                        alt1 = 2
                        LA1_0 = self.input.LA(1)

                        if (LA1_0 in {COMMENT, ID, NEGATION, 56, 57, 58}) :
                            alt1 = 1


                        if alt1 == 1:
                            # Congress.g:59:7: statement
                            pass 
                            self._state.following.append(self.FOLLOW_statement_in_prog265)
                            statement1 = self.statement()

                            self._state.following.pop()
                            stream_statement.add(statement1.tree)



                        else:
                            if cnt1 >= 1:
                                break #loop1

                            eee = EarlyExitException(1, self.input)
                            raise eee

                        cnt1 += 1


                    EOF2 = self.match(self.input, EOF, self.FOLLOW_EOF_in_prog268) 
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
                    # 59:22: -> ^( THEORY ( statement )+ )
                    # Congress.g:59:25: ^( THEORY ( statement )+ )
                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(
                    self._adaptor.createFromType(THEORY, "THEORY")
                    , root_1)

                    # Congress.g:59:34: ( statement )+
                    if not (stream_statement.hasNext()):
                        raise RewriteEarlyExitException()

                    while stream_statement.hasNext():
                        self._adaptor.addChild(root_1, stream_statement.nextTree())


                    stream_statement.reset()

                    self._adaptor.addChild(root_0, root_1)




                    retval.tree = root_0




                elif alt2 == 2:
                    # Congress.g:60:7: EOF
                    pass 
                    root_0 = self._adaptor.nil()


                    EOF3 = self.match(self.input, EOF, self.FOLLOW_EOF_in_prog285)
                    EOF3_tree = self._adaptor.createWithPayload(EOF3)
                    self._adaptor.addChild(root_0, EOF3_tree)




                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException as re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "prog"


    class statement_return(ParserRuleReturnScope):
        def __init__(self):
            super().__init__()

            self.tree = None





    # $ANTLR start "statement"
    # Congress.g:65:1: statement : ( formula ( formula_terminator )? -> formula | COMMENT );
    def statement(self, ):
        retval = self.statement_return()
        retval.start = self.input.LT(1)


        root_0 = None

        COMMENT6 = None
        formula4 = None
        formula_terminator5 = None

        COMMENT6_tree = None
        stream_formula_terminator = RewriteRuleSubtreeStream(self._adaptor, "rule formula_terminator")
        stream_formula = RewriteRuleSubtreeStream(self._adaptor, "rule formula")
        try:
            try:
                # Congress.g:66:5: ( formula ( formula_terminator )? -> formula | COMMENT )
                alt4 = 2
                LA4_0 = self.input.LA(1)

                if (LA4_0 in {ID, NEGATION, 56, 57, 58}) :
                    alt4 = 1
                elif (LA4_0 == COMMENT) :
                    alt4 = 2
                else:
                    nvae = NoViableAltException("", 4, 0, self.input)

                    raise nvae


                if alt4 == 1:
                    # Congress.g:66:7: formula ( formula_terminator )?
                    pass 
                    self._state.following.append(self.FOLLOW_formula_in_statement304)
                    formula4 = self.formula()

                    self._state.following.pop()
                    stream_formula.add(formula4.tree)


                    # Congress.g:66:15: ( formula_terminator )?
                    alt3 = 2
                    LA3_0 = self.input.LA(1)

                    if (LA3_0 in {53, 55}) :
                        alt3 = 1
                    if alt3 == 1:
                        # Congress.g:66:15: formula_terminator
                        pass 
                        self._state.following.append(self.FOLLOW_formula_terminator_in_statement306)
                        formula_terminator5 = self.formula_terminator()

                        self._state.following.pop()
                        stream_formula_terminator.add(formula_terminator5.tree)





                    # AST Rewrite
                    # elements: formula
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
                    # 66:35: -> formula
                    self._adaptor.addChild(root_0, stream_formula.nextTree())




                    retval.tree = root_0




                elif alt4 == 2:
                    # Congress.g:67:7: COMMENT
                    pass 
                    root_0 = self._adaptor.nil()


                    COMMENT6 = self.match(self.input, COMMENT, self.FOLLOW_COMMENT_in_statement319)
                    COMMENT6_tree = self._adaptor.createWithPayload(COMMENT6)
                    self._adaptor.addChild(root_0, COMMENT6_tree)




                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException as re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "statement"


    class formula_return(ParserRuleReturnScope):
        def __init__(self):
            super().__init__()

            self.tree = None





    # $ANTLR start "formula"
    # Congress.g:70:1: formula : ( rule | fact | event );
    def formula(self, ):
        retval = self.formula_return()
        retval.start = self.input.LT(1)


        root_0 = None

        rule7 = None
        fact8 = None
        event9 = None


        try:
            try:
                # Congress.g:71:5: ( rule | fact | event )
                alt5 = 3
                alt5 = self.dfa5.predict(self.input)
                if alt5 == 1:
                    # Congress.g:71:7: rule
                    pass 
                    root_0 = self._adaptor.nil()


                    self._state.following.append(self.FOLLOW_rule_in_formula336)
                    rule7 = self.rule()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, rule7.tree)



                elif alt5 == 2:
                    # Congress.g:72:7: fact
                    pass 
                    root_0 = self._adaptor.nil()


                    self._state.following.append(self.FOLLOW_fact_in_formula344)
                    fact8 = self.fact()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, fact8.tree)



                elif alt5 == 3:
                    # Congress.g:73:7: event
                    pass 
                    root_0 = self._adaptor.nil()


                    self._state.following.append(self.FOLLOW_event_in_formula352)
                    event9 = self.event()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, event9.tree)



                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException as re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "formula"


    class event_return(ParserRuleReturnScope):
        def __init__(self):
            super().__init__()

            self.tree = None





    # $ANTLR start "event"
    # Congress.g:86:1: event : event_op LBRACKET rule ( formula_terminator STRING )? RBRACKET -> ^( EVENT event_op rule ( STRING )? ) ;
    def event(self, ):
        retval = self.event_return()
        retval.start = self.input.LT(1)


        root_0 = None

        LBRACKET11 = None
        STRING14 = None
        RBRACKET15 = None
        event_op10 = None
        rule12 = None
        formula_terminator13 = None

        LBRACKET11_tree = None
        STRING14_tree = None
        RBRACKET15_tree = None
        stream_LBRACKET = RewriteRuleTokenStream(self._adaptor, "token LBRACKET")
        stream_RBRACKET = RewriteRuleTokenStream(self._adaptor, "token RBRACKET")
        stream_STRING = RewriteRuleTokenStream(self._adaptor, "token STRING")
        stream_formula_terminator = RewriteRuleSubtreeStream(self._adaptor, "rule formula_terminator")
        stream_rule = RewriteRuleSubtreeStream(self._adaptor, "rule rule")
        stream_event_op = RewriteRuleSubtreeStream(self._adaptor, "rule event_op")
        try:
            try:
                # Congress.g:87:5: ( event_op LBRACKET rule ( formula_terminator STRING )? RBRACKET -> ^( EVENT event_op rule ( STRING )? ) )
                # Congress.g:87:7: event_op LBRACKET rule ( formula_terminator STRING )? RBRACKET
                pass 
                self._state.following.append(self.FOLLOW_event_op_in_event379)
                event_op10 = self.event_op()

                self._state.following.pop()
                stream_event_op.add(event_op10.tree)


                LBRACKET11 = self.match(self.input, LBRACKET, self.FOLLOW_LBRACKET_in_event381) 
                stream_LBRACKET.add(LBRACKET11)


                self._state.following.append(self.FOLLOW_rule_in_event383)
                rule12 = self.rule()

                self._state.following.pop()
                stream_rule.add(rule12.tree)


                # Congress.g:87:30: ( formula_terminator STRING )?
                alt6 = 2
                LA6_0 = self.input.LA(1)

                if (LA6_0 in {53, 55}) :
                    alt6 = 1
                if alt6 == 1:
                    # Congress.g:87:31: formula_terminator STRING
                    pass 
                    self._state.following.append(self.FOLLOW_formula_terminator_in_event386)
                    formula_terminator13 = self.formula_terminator()

                    self._state.following.pop()
                    stream_formula_terminator.add(formula_terminator13.tree)


                    STRING14 = self.match(self.input, STRING, self.FOLLOW_STRING_in_event388) 
                    stream_STRING.add(STRING14)





                RBRACKET15 = self.match(self.input, RBRACKET, self.FOLLOW_RBRACKET_in_event392) 
                stream_RBRACKET.add(RBRACKET15)


                # AST Rewrite
                # elements: STRING, rule, event_op
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
                # 87:68: -> ^( EVENT event_op rule ( STRING )? )
                # Congress.g:87:71: ^( EVENT event_op rule ( STRING )? )
                root_1 = self._adaptor.nil()
                root_1 = self._adaptor.becomeRoot(
                self._adaptor.createFromType(EVENT, "EVENT")
                , root_1)

                self._adaptor.addChild(root_1, stream_event_op.nextTree())

                self._adaptor.addChild(root_1, stream_rule.nextTree())

                # Congress.g:87:93: ( STRING )?
                if stream_STRING.hasNext():
                    self._adaptor.addChild(root_1, 
                    stream_STRING.nextNode()
                    )


                stream_STRING.reset();

                self._adaptor.addChild(root_0, root_1)




                retval.tree = root_0





                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException as re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "event"


    class event_op_return(ParserRuleReturnScope):
        def __init__(self):
            super().__init__()

            self.tree = None





    # $ANTLR start "event_op"
    # Congress.g:90:1: event_op : ( 'insert' | 'delete' );
    def event_op(self, ):
        retval = self.event_op_return()
        retval.start = self.input.LT(1)


        root_0 = None

        set16 = None

        set16_tree = None

        try:
            try:
                # Congress.g:91:5: ( 'insert' | 'delete' )
                # Congress.g:
                pass 
                root_0 = self._adaptor.nil()


                set16 = self.input.LT(1)

                if self.input.LA(1) in {56, 58}:
                    self.input.consume()
                    self._adaptor.addChild(root_0, self._adaptor.createWithPayload(set16))

                    self._state.errorRecovery = False


                else:
                    mse = MismatchedSetException(None, self.input)
                    raise mse





                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException as re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "event_op"


    class formula_terminator_return(ParserRuleReturnScope):
        def __init__(self):
            super().__init__()

            self.tree = None





    # $ANTLR start "formula_terminator"
    # Congress.g:95:1: formula_terminator : ( ';' | '.' );
    def formula_terminator(self, ):
        retval = self.formula_terminator_return()
        retval.start = self.input.LT(1)


        root_0 = None

        set17 = None

        set17_tree = None

        try:
            try:
                # Congress.g:96:5: ( ';' | '.' )
                # Congress.g:
                pass 
                root_0 = self._adaptor.nil()


                set17 = self.input.LT(1)

                if self.input.LA(1) in {53, 55}:
                    self.input.consume()
                    self._adaptor.addChild(root_0, self._adaptor.createWithPayload(set17))

                    self._state.errorRecovery = False


                else:
                    mse = MismatchedSetException(None, self.input)
                    raise mse





                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException as re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "formula_terminator"


    class rule_return(ParserRuleReturnScope):
        def __init__(self):
            super().__init__()

            self.tree = None





    # $ANTLR start "rule"
    # Congress.g:100:1: rule : literal_list COLONMINUS literal_list -> ^( RULE literal_list literal_list ) ;
    def rule(self, ):
        retval = self.rule_return()
        retval.start = self.input.LT(1)


        root_0 = None

        COLONMINUS19 = None
        literal_list18 = None
        literal_list20 = None

        COLONMINUS19_tree = None
        stream_COLONMINUS = RewriteRuleTokenStream(self._adaptor, "token COLONMINUS")
        stream_literal_list = RewriteRuleSubtreeStream(self._adaptor, "rule literal_list")
        try:
            try:
                # Congress.g:101:5: ( literal_list COLONMINUS literal_list -> ^( RULE literal_list literal_list ) )
                # Congress.g:101:7: literal_list COLONMINUS literal_list
                pass 
                self._state.following.append(self.FOLLOW_literal_list_in_rule472)
                literal_list18 = self.literal_list()

                self._state.following.pop()
                stream_literal_list.add(literal_list18.tree)


                COLONMINUS19 = self.match(self.input, COLONMINUS, self.FOLLOW_COLONMINUS_in_rule474) 
                stream_COLONMINUS.add(COLONMINUS19)


                self._state.following.append(self.FOLLOW_literal_list_in_rule476)
                literal_list20 = self.literal_list()

                self._state.following.pop()
                stream_literal_list.add(literal_list20.tree)


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
                # 101:44: -> ^( RULE literal_list literal_list )
                # Congress.g:101:47: ^( RULE literal_list literal_list )
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



            except RecognitionException as re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "rule"


    class literal_list_return(ParserRuleReturnScope):
        def __init__(self):
            super().__init__()

            self.tree = None





    # $ANTLR start "literal_list"
    # Congress.g:104:1: literal_list : literal ( COMMA literal )* -> ^( AND ( literal )+ ) ;
    def literal_list(self, ):
        retval = self.literal_list_return()
        retval.start = self.input.LT(1)


        root_0 = None

        COMMA22 = None
        literal21 = None
        literal23 = None

        COMMA22_tree = None
        stream_COMMA = RewriteRuleTokenStream(self._adaptor, "token COMMA")
        stream_literal = RewriteRuleSubtreeStream(self._adaptor, "rule literal")
        try:
            try:
                # Congress.g:105:5: ( literal ( COMMA literal )* -> ^( AND ( literal )+ ) )
                # Congress.g:105:7: literal ( COMMA literal )*
                pass 
                self._state.following.append(self.FOLLOW_literal_in_literal_list503)
                literal21 = self.literal()

                self._state.following.pop()
                stream_literal.add(literal21.tree)


                # Congress.g:105:15: ( COMMA literal )*
                while True: #loop7
                    alt7 = 2
                    LA7_0 = self.input.LA(1)

                    if (LA7_0 == COMMA) :
                        alt7 = 1


                    if alt7 == 1:
                        # Congress.g:105:16: COMMA literal
                        pass 
                        COMMA22 = self.match(self.input, COMMA, self.FOLLOW_COMMA_in_literal_list506) 
                        stream_COMMA.add(COMMA22)


                        self._state.following.append(self.FOLLOW_literal_in_literal_list508)
                        literal23 = self.literal()

                        self._state.following.pop()
                        stream_literal.add(literal23.tree)



                    else:
                        break #loop7


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
                # 105:32: -> ^( AND ( literal )+ )
                # Congress.g:105:35: ^( AND ( literal )+ )
                root_1 = self._adaptor.nil()
                root_1 = self._adaptor.becomeRoot(
                self._adaptor.createFromType(AND, "AND")
                , root_1)

                # Congress.g:105:41: ( literal )+
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



            except RecognitionException as re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "literal_list"


    class literal_return(ParserRuleReturnScope):
        def __init__(self):
            super().__init__()

            self.tree = None





    # $ANTLR start "literal"
    # Congress.g:108:1: literal : ( fact -> fact | NEGATION fact -> ^( NOT fact ) );
    def literal(self, ):
        retval = self.literal_return()
        retval.start = self.input.LT(1)


        root_0 = None

        NEGATION25 = None
        fact24 = None
        fact26 = None

        NEGATION25_tree = None
        stream_NEGATION = RewriteRuleTokenStream(self._adaptor, "token NEGATION")
        stream_fact = RewriteRuleSubtreeStream(self._adaptor, "rule fact")
        try:
            try:
                # Congress.g:109:5: ( fact -> fact | NEGATION fact -> ^( NOT fact ) )
                alt8 = 2
                LA8_0 = self.input.LA(1)

                if (LA8_0 in {ID, 56, 57, 58}) :
                    alt8 = 1
                elif (LA8_0 == NEGATION) :
                    alt8 = 2
                else:
                    nvae = NoViableAltException("", 8, 0, self.input)

                    raise nvae


                if alt8 == 1:
                    # Congress.g:109:7: fact
                    pass 
                    self._state.following.append(self.FOLLOW_fact_in_literal536)
                    fact24 = self.fact()

                    self._state.following.pop()
                    stream_fact.add(fact24.tree)


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
                    # 109:23: -> fact
                    self._adaptor.addChild(root_0, stream_fact.nextTree())




                    retval.tree = root_0




                elif alt8 == 2:
                    # Congress.g:110:7: NEGATION fact
                    pass 
                    NEGATION25 = self.match(self.input, NEGATION, self.FOLLOW_NEGATION_in_literal559) 
                    stream_NEGATION.add(NEGATION25)


                    self._state.following.append(self.FOLLOW_fact_in_literal561)
                    fact26 = self.fact()

                    self._state.following.pop()
                    stream_fact.add(fact26.tree)


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
                    # 110:23: -> ^( NOT fact )
                    # Congress.g:110:26: ^( NOT fact )
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



            except RecognitionException as re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "literal"


    class fact_return(ParserRuleReturnScope):
        def __init__(self):
            super().__init__()

            self.tree = None





    # $ANTLR start "fact"
    # Congress.g:115:1: fact : ( atom | modal_op LBRACKET atom RBRACKET -> ^( MODAL modal_op atom ) );
    def fact(self, ):
        retval = self.fact_return()
        retval.start = self.input.LT(1)


        root_0 = None

        LBRACKET29 = None
        RBRACKET31 = None
        atom27 = None
        modal_op28 = None
        atom30 = None

        LBRACKET29_tree = None
        RBRACKET31_tree = None
        stream_LBRACKET = RewriteRuleTokenStream(self._adaptor, "token LBRACKET")
        stream_RBRACKET = RewriteRuleTokenStream(self._adaptor, "token RBRACKET")
        stream_atom = RewriteRuleSubtreeStream(self._adaptor, "rule atom")
        stream_modal_op = RewriteRuleSubtreeStream(self._adaptor, "rule modal_op")
        try:
            try:
                # Congress.g:116:5: ( atom | modal_op LBRACKET atom RBRACKET -> ^( MODAL modal_op atom ) )
                alt9 = 2
                LA9_0 = self.input.LA(1)

                if (LA9_0 == ID) :
                    alt9 = 1
                elif (LA9_0 in {56, 57, 58}) :
                    alt9 = 2
                else:
                    nvae = NoViableAltException("", 9, 0, self.input)

                    raise nvae


                if alt9 == 1:
                    # Congress.g:116:7: atom
                    pass 
                    root_0 = self._adaptor.nil()


                    self._state.following.append(self.FOLLOW_atom_in_fact590)
                    atom27 = self.atom()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, atom27.tree)



                elif alt9 == 2:
                    # Congress.g:117:7: modal_op LBRACKET atom RBRACKET
                    pass 
                    self._state.following.append(self.FOLLOW_modal_op_in_fact598)
                    modal_op28 = self.modal_op()

                    self._state.following.pop()
                    stream_modal_op.add(modal_op28.tree)


                    LBRACKET29 = self.match(self.input, LBRACKET, self.FOLLOW_LBRACKET_in_fact600) 
                    stream_LBRACKET.add(LBRACKET29)


                    self._state.following.append(self.FOLLOW_atom_in_fact602)
                    atom30 = self.atom()

                    self._state.following.pop()
                    stream_atom.add(atom30.tree)


                    RBRACKET31 = self.match(self.input, RBRACKET, self.FOLLOW_RBRACKET_in_fact604) 
                    stream_RBRACKET.add(RBRACKET31)


                    # AST Rewrite
                    # elements: atom, modal_op
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
                    # 117:39: -> ^( MODAL modal_op atom )
                    # Congress.g:117:42: ^( MODAL modal_op atom )
                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(
                    self._adaptor.createFromType(MODAL, "MODAL")
                    , root_1)

                    self._adaptor.addChild(root_1, stream_modal_op.nextTree())

                    self._adaptor.addChild(root_1, stream_atom.nextTree())

                    self._adaptor.addChild(root_0, root_1)




                    retval.tree = root_0




                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException as re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "fact"


    class modal_op_return(ParserRuleReturnScope):
        def __init__(self):
            super().__init__()

            self.tree = None





    # $ANTLR start "modal_op"
    # Congress.g:120:1: modal_op : ( 'execute' | 'insert' | 'delete' );
    def modal_op(self, ):
        retval = self.modal_op_return()
        retval.start = self.input.LT(1)


        root_0 = None

        set32 = None

        set32_tree = None

        try:
            try:
                # Congress.g:121:5: ( 'execute' | 'insert' | 'delete' )
                # Congress.g:
                pass 
                root_0 = self._adaptor.nil()


                set32 = self.input.LT(1)

                if self.input.LA(1) in {56, 57, 58}:
                    self.input.consume()
                    self._adaptor.addChild(root_0, self._adaptor.createWithPayload(set32))

                    self._state.errorRecovery = False


                else:
                    mse = MismatchedSetException(None, self.input)
                    raise mse





                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException as re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "modal_op"


    class atom_return(ParserRuleReturnScope):
        def __init__(self):
            super().__init__()

            self.tree = None





    # $ANTLR start "atom"
    # Congress.g:126:1: atom : relation_constant ( LPAREN ( parameter_list )? RPAREN )? -> ^( ATOM relation_constant ( parameter_list )? ) ;
    def atom(self, ):
        retval = self.atom_return()
        retval.start = self.input.LT(1)


        root_0 = None

        LPAREN34 = None
        RPAREN36 = None
        relation_constant33 = None
        parameter_list35 = None

        LPAREN34_tree = None
        RPAREN36_tree = None
        stream_RPAREN = RewriteRuleTokenStream(self._adaptor, "token RPAREN")
        stream_LPAREN = RewriteRuleTokenStream(self._adaptor, "token LPAREN")
        stream_relation_constant = RewriteRuleSubtreeStream(self._adaptor, "rule relation_constant")
        stream_parameter_list = RewriteRuleSubtreeStream(self._adaptor, "rule parameter_list")
        try:
            try:
                # Congress.g:127:5: ( relation_constant ( LPAREN ( parameter_list )? RPAREN )? -> ^( ATOM relation_constant ( parameter_list )? ) )
                # Congress.g:127:7: relation_constant ( LPAREN ( parameter_list )? RPAREN )?
                pass 
                self._state.following.append(self.FOLLOW_relation_constant_in_atom664)
                relation_constant33 = self.relation_constant()

                self._state.following.pop()
                stream_relation_constant.add(relation_constant33.tree)


                # Congress.g:127:25: ( LPAREN ( parameter_list )? RPAREN )?
                alt11 = 2
                LA11_0 = self.input.LA(1)

                if (LA11_0 == LPAREN) :
                    alt11 = 1
                if alt11 == 1:
                    # Congress.g:127:26: LPAREN ( parameter_list )? RPAREN
                    pass 
                    LPAREN34 = self.match(self.input, LPAREN, self.FOLLOW_LPAREN_in_atom667) 
                    stream_LPAREN.add(LPAREN34)


                    # Congress.g:127:33: ( parameter_list )?
                    alt10 = 2
                    LA10_0 = self.input.LA(1)

                    if (LA10_0 in {FLOAT, ID, INT, STRING}) :
                        alt10 = 1
                    if alt10 == 1:
                        # Congress.g:127:33: parameter_list
                        pass 
                        self._state.following.append(self.FOLLOW_parameter_list_in_atom669)
                        parameter_list35 = self.parameter_list()

                        self._state.following.pop()
                        stream_parameter_list.add(parameter_list35.tree)





                    RPAREN36 = self.match(self.input, RPAREN, self.FOLLOW_RPAREN_in_atom672) 
                    stream_RPAREN.add(RPAREN36)





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
                # 127:58: -> ^( ATOM relation_constant ( parameter_list )? )
                # Congress.g:127:61: ^( ATOM relation_constant ( parameter_list )? )
                root_1 = self._adaptor.nil()
                root_1 = self._adaptor.becomeRoot(
                self._adaptor.createFromType(ATOM, "ATOM")
                , root_1)

                self._adaptor.addChild(root_1, stream_relation_constant.nextTree())

                # Congress.g:127:86: ( parameter_list )?
                if stream_parameter_list.hasNext():
                    self._adaptor.addChild(root_1, stream_parameter_list.nextTree())


                stream_parameter_list.reset();

                self._adaptor.addChild(root_0, root_1)




                retval.tree = root_0





                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException as re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "atom"


    class parameter_list_return(ParserRuleReturnScope):
        def __init__(self):
            super().__init__()

            self.tree = None





    # $ANTLR start "parameter_list"
    # Congress.g:130:1: parameter_list : parameter ( COMMA parameter )* -> ( parameter )+ ;
    def parameter_list(self, ):
        retval = self.parameter_list_return()
        retval.start = self.input.LT(1)


        root_0 = None

        COMMA38 = None
        parameter37 = None
        parameter39 = None

        COMMA38_tree = None
        stream_COMMA = RewriteRuleTokenStream(self._adaptor, "token COMMA")
        stream_parameter = RewriteRuleSubtreeStream(self._adaptor, "rule parameter")
        try:
            try:
                # Congress.g:131:5: ( parameter ( COMMA parameter )* -> ( parameter )+ )
                # Congress.g:131:7: parameter ( COMMA parameter )*
                pass 
                self._state.following.append(self.FOLLOW_parameter_in_parameter_list702)
                parameter37 = self.parameter()

                self._state.following.pop()
                stream_parameter.add(parameter37.tree)


                # Congress.g:131:17: ( COMMA parameter )*
                while True: #loop12
                    alt12 = 2
                    LA12_0 = self.input.LA(1)

                    if (LA12_0 == COMMA) :
                        alt12 = 1


                    if alt12 == 1:
                        # Congress.g:131:18: COMMA parameter
                        pass 
                        COMMA38 = self.match(self.input, COMMA, self.FOLLOW_COMMA_in_parameter_list705) 
                        stream_COMMA.add(COMMA38)


                        self._state.following.append(self.FOLLOW_parameter_in_parameter_list707)
                        parameter39 = self.parameter()

                        self._state.following.pop()
                        stream_parameter.add(parameter39.tree)



                    else:
                        break #loop12


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
                # 131:36: -> ( parameter )+
                # Congress.g:131:39: ( parameter )+
                if not (stream_parameter.hasNext()):
                    raise RewriteEarlyExitException()

                while stream_parameter.hasNext():
                    self._adaptor.addChild(root_0, stream_parameter.nextTree())


                stream_parameter.reset()




                retval.tree = root_0





                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException as re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "parameter_list"


    class parameter_return(ParserRuleReturnScope):
        def __init__(self):
            super().__init__()

            self.tree = None





    # $ANTLR start "parameter"
    # Congress.g:134:1: parameter : ( term -> term | column_ref EQUAL term -> ^( NAMED_PARAM column_ref term ) );
    def parameter(self, ):
        retval = self.parameter_return()
        retval.start = self.input.LT(1)


        root_0 = None

        EQUAL42 = None
        term40 = None
        column_ref41 = None
        term43 = None

        EQUAL42_tree = None
        stream_EQUAL = RewriteRuleTokenStream(self._adaptor, "token EQUAL")
        stream_term = RewriteRuleSubtreeStream(self._adaptor, "rule term")
        stream_column_ref = RewriteRuleSubtreeStream(self._adaptor, "rule column_ref")
        try:
            try:
                # Congress.g:135:5: ( term -> term | column_ref EQUAL term -> ^( NAMED_PARAM column_ref term ) )
                alt13 = 2
                LA13 = self.input.LA(1)
                if LA13 in {INT}:
                    LA13_1 = self.input.LA(2)

                    if (LA13_1 in {COMMA, RPAREN}) :
                        alt13 = 1
                    elif (LA13_1 == EQUAL) :
                        alt13 = 2
                    else:
                        nvae = NoViableAltException("", 13, 1, self.input)

                        raise nvae


                elif LA13 in {FLOAT, STRING}:
                    alt13 = 1
                elif LA13 in {ID}:
                    LA13_3 = self.input.LA(2)

                    if (LA13_3 in {COMMA, RPAREN}) :
                        alt13 = 1
                    elif (LA13_3 == EQUAL) :
                        alt13 = 2
                    else:
                        nvae = NoViableAltException("", 13, 3, self.input)

                        raise nvae


                else:
                    nvae = NoViableAltException("", 13, 0, self.input)

                    raise nvae


                if alt13 == 1:
                    # Congress.g:135:7: term
                    pass 
                    self._state.following.append(self.FOLLOW_term_in_parameter731)
                    term40 = self.term()

                    self._state.following.pop()
                    stream_term.add(term40.tree)


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
                    # 135:12: -> term
                    self._adaptor.addChild(root_0, stream_term.nextTree())




                    retval.tree = root_0




                elif alt13 == 2:
                    # Congress.g:136:7: column_ref EQUAL term
                    pass 
                    self._state.following.append(self.FOLLOW_column_ref_in_parameter743)
                    column_ref41 = self.column_ref()

                    self._state.following.pop()
                    stream_column_ref.add(column_ref41.tree)


                    EQUAL42 = self.match(self.input, EQUAL, self.FOLLOW_EQUAL_in_parameter745) 
                    stream_EQUAL.add(EQUAL42)


                    self._state.following.append(self.FOLLOW_term_in_parameter747)
                    term43 = self.term()

                    self._state.following.pop()
                    stream_term.add(term43.tree)


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
                    # 136:29: -> ^( NAMED_PARAM column_ref term )
                    # Congress.g:136:32: ^( NAMED_PARAM column_ref term )
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



            except RecognitionException as re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "parameter"


    class column_ref_return(ParserRuleReturnScope):
        def __init__(self):
            super().__init__()

            self.tree = None





    # $ANTLR start "column_ref"
    # Congress.g:139:1: column_ref : ( ID -> ^( COLUMN_NAME ID ) | INT -> ^( COLUMN_NUMBER INT ) );
    def column_ref(self, ):
        retval = self.column_ref_return()
        retval.start = self.input.LT(1)


        root_0 = None

        ID44 = None
        INT45 = None

        ID44_tree = None
        INT45_tree = None
        stream_INT = RewriteRuleTokenStream(self._adaptor, "token INT")
        stream_ID = RewriteRuleTokenStream(self._adaptor, "token ID")

        try:
            try:
                # Congress.g:140:5: ( ID -> ^( COLUMN_NAME ID ) | INT -> ^( COLUMN_NUMBER INT ) )
                alt14 = 2
                LA14_0 = self.input.LA(1)

                if (LA14_0 == ID) :
                    alt14 = 1
                elif (LA14_0 == INT) :
                    alt14 = 2
                else:
                    nvae = NoViableAltException("", 14, 0, self.input)

                    raise nvae


                if alt14 == 1:
                    # Congress.g:140:7: ID
                    pass 
                    ID44 = self.match(self.input, ID, self.FOLLOW_ID_in_column_ref774) 
                    stream_ID.add(ID44)


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
                    # 140:12: -> ^( COLUMN_NAME ID )
                    # Congress.g:140:16: ^( COLUMN_NAME ID )
                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(
                    self._adaptor.createFromType(COLUMN_NAME, "COLUMN_NAME")
                    , root_1)

                    self._adaptor.addChild(root_1, 
                    stream_ID.nextNode()
                    )

                    self._adaptor.addChild(root_0, root_1)




                    retval.tree = root_0




                elif alt14 == 2:
                    # Congress.g:141:7: INT
                    pass 
                    INT45 = self.match(self.input, INT, self.FOLLOW_INT_in_column_ref793) 
                    stream_INT.add(INT45)


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
                    # 141:12: -> ^( COLUMN_NUMBER INT )
                    # Congress.g:141:16: ^( COLUMN_NUMBER INT )
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



            except RecognitionException as re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "column_ref"


    class term_return(ParserRuleReturnScope):
        def __init__(self):
            super().__init__()

            self.tree = None





    # $ANTLR start "term"
    # Congress.g:144:1: term : ( object_constant | variable );
    def term(self, ):
        retval = self.term_return()
        retval.start = self.input.LT(1)


        root_0 = None

        object_constant46 = None
        variable47 = None


        try:
            try:
                # Congress.g:145:5: ( object_constant | variable )
                alt15 = 2
                LA15_0 = self.input.LA(1)

                if (LA15_0 in {FLOAT, INT, STRING}) :
                    alt15 = 1
                elif (LA15_0 == ID) :
                    alt15 = 2
                else:
                    nvae = NoViableAltException("", 15, 0, self.input)

                    raise nvae


                if alt15 == 1:
                    # Congress.g:145:7: object_constant
                    pass 
                    root_0 = self._adaptor.nil()


                    self._state.following.append(self.FOLLOW_object_constant_in_term820)
                    object_constant46 = self.object_constant()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, object_constant46.tree)



                elif alt15 == 2:
                    # Congress.g:146:7: variable
                    pass 
                    root_0 = self._adaptor.nil()


                    self._state.following.append(self.FOLLOW_variable_in_term828)
                    variable47 = self.variable()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, variable47.tree)



                retval.stop = self.input.LT(-1)


                retval.tree = self._adaptor.rulePostProcessing(root_0)
                self._adaptor.setTokenBoundaries(retval.tree, retval.start, retval.stop)



            except RecognitionException as re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "term"


    class object_constant_return(ParserRuleReturnScope):
        def __init__(self):
            super().__init__()

            self.tree = None





    # $ANTLR start "object_constant"
    # Congress.g:149:1: object_constant : ( INT -> ^( INTEGER_OBJ INT ) | FLOAT -> ^( FLOAT_OBJ FLOAT ) | STRING -> ^( STRING_OBJ STRING ) );
    def object_constant(self, ):
        retval = self.object_constant_return()
        retval.start = self.input.LT(1)


        root_0 = None

        INT48 = None
        FLOAT49 = None
        STRING50 = None

        INT48_tree = None
        FLOAT49_tree = None
        STRING50_tree = None
        stream_FLOAT = RewriteRuleTokenStream(self._adaptor, "token FLOAT")
        stream_INT = RewriteRuleTokenStream(self._adaptor, "token INT")
        stream_STRING = RewriteRuleTokenStream(self._adaptor, "token STRING")

        try:
            try:
                # Congress.g:150:5: ( INT -> ^( INTEGER_OBJ INT ) | FLOAT -> ^( FLOAT_OBJ FLOAT ) | STRING -> ^( STRING_OBJ STRING ) )
                alt16 = 3
                LA16 = self.input.LA(1)
                if LA16 in {INT}:
                    alt16 = 1
                elif LA16 in {FLOAT}:
                    alt16 = 2
                elif LA16 in {STRING}:
                    alt16 = 3
                else:
                    nvae = NoViableAltException("", 16, 0, self.input)

                    raise nvae


                if alt16 == 1:
                    # Congress.g:150:7: INT
                    pass 
                    INT48 = self.match(self.input, INT, self.FOLLOW_INT_in_object_constant845) 
                    stream_INT.add(INT48)


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
                    # 150:16: -> ^( INTEGER_OBJ INT )
                    # Congress.g:150:19: ^( INTEGER_OBJ INT )
                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(
                    self._adaptor.createFromType(INTEGER_OBJ, "INTEGER_OBJ")
                    , root_1)

                    self._adaptor.addChild(root_1, 
                    stream_INT.nextNode()
                    )

                    self._adaptor.addChild(root_0, root_1)




                    retval.tree = root_0




                elif alt16 == 2:
                    # Congress.g:151:7: FLOAT
                    pass 
                    FLOAT49 = self.match(self.input, FLOAT, self.FOLLOW_FLOAT_in_object_constant866) 
                    stream_FLOAT.add(FLOAT49)


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
                    # 151:16: -> ^( FLOAT_OBJ FLOAT )
                    # Congress.g:151:19: ^( FLOAT_OBJ FLOAT )
                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(
                    self._adaptor.createFromType(FLOAT_OBJ, "FLOAT_OBJ")
                    , root_1)

                    self._adaptor.addChild(root_1, 
                    stream_FLOAT.nextNode()
                    )

                    self._adaptor.addChild(root_0, root_1)




                    retval.tree = root_0




                elif alt16 == 3:
                    # Congress.g:152:7: STRING
                    pass 
                    STRING50 = self.match(self.input, STRING, self.FOLLOW_STRING_in_object_constant885) 
                    stream_STRING.add(STRING50)


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
                    # 152:16: -> ^( STRING_OBJ STRING )
                    # Congress.g:152:19: ^( STRING_OBJ STRING )
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



            except RecognitionException as re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "object_constant"


    class variable_return(ParserRuleReturnScope):
        def __init__(self):
            super().__init__()

            self.tree = None





    # $ANTLR start "variable"
    # Congress.g:155:1: variable : ID -> ^( VARIABLE ID ) ;
    def variable(self, ):
        retval = self.variable_return()
        retval.start = self.input.LT(1)


        root_0 = None

        ID51 = None

        ID51_tree = None
        stream_ID = RewriteRuleTokenStream(self._adaptor, "token ID")

        try:
            try:
                # Congress.g:156:5: ( ID -> ^( VARIABLE ID ) )
                # Congress.g:156:7: ID
                pass 
                ID51 = self.match(self.input, ID, self.FOLLOW_ID_in_variable912) 
                stream_ID.add(ID51)


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
                # 156:10: -> ^( VARIABLE ID )
                # Congress.g:156:13: ^( VARIABLE ID )
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



            except RecognitionException as re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "variable"


    class relation_constant_return(ParserRuleReturnScope):
        def __init__(self):
            super().__init__()

            self.tree = None





    # $ANTLR start "relation_constant"
    # Congress.g:159:1: relation_constant : ID ( ':' ID )* ( SIGN )? -> ^( STRUCTURED_NAME ( ID )+ ( SIGN )? ) ;
    def relation_constant(self, ):
        retval = self.relation_constant_return()
        retval.start = self.input.LT(1)


        root_0 = None

        ID52 = None
        char_literal53 = None
        ID54 = None
        SIGN55 = None

        ID52_tree = None
        char_literal53_tree = None
        ID54_tree = None
        SIGN55_tree = None
        stream_SIGN = RewriteRuleTokenStream(self._adaptor, "token SIGN")
        stream_ID = RewriteRuleTokenStream(self._adaptor, "token ID")
        stream_54 = RewriteRuleTokenStream(self._adaptor, "token 54")

        try:
            try:
                # Congress.g:160:5: ( ID ( ':' ID )* ( SIGN )? -> ^( STRUCTURED_NAME ( ID )+ ( SIGN )? ) )
                # Congress.g:160:7: ID ( ':' ID )* ( SIGN )?
                pass 
                ID52 = self.match(self.input, ID, self.FOLLOW_ID_in_relation_constant937) 
                stream_ID.add(ID52)


                # Congress.g:160:10: ( ':' ID )*
                while True: #loop17
                    alt17 = 2
                    LA17_0 = self.input.LA(1)

                    if (LA17_0 == 54) :
                        alt17 = 1


                    if alt17 == 1:
                        # Congress.g:160:11: ':' ID
                        pass 
                        char_literal53 = self.match(self.input, 54, self.FOLLOW_54_in_relation_constant940) 
                        stream_54.add(char_literal53)


                        ID54 = self.match(self.input, ID, self.FOLLOW_ID_in_relation_constant942) 
                        stream_ID.add(ID54)



                    else:
                        break #loop17


                # Congress.g:160:20: ( SIGN )?
                alt18 = 2
                LA18_0 = self.input.LA(1)

                if (LA18_0 == SIGN) :
                    alt18 = 1
                if alt18 == 1:
                    # Congress.g:160:20: SIGN
                    pass 
                    SIGN55 = self.match(self.input, SIGN, self.FOLLOW_SIGN_in_relation_constant946) 
                    stream_SIGN.add(SIGN55)





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
                # 160:26: -> ^( STRUCTURED_NAME ( ID )+ ( SIGN )? )
                # Congress.g:160:29: ^( STRUCTURED_NAME ( ID )+ ( SIGN )? )
                root_1 = self._adaptor.nil()
                root_1 = self._adaptor.becomeRoot(
                self._adaptor.createFromType(STRUCTURED_NAME, "STRUCTURED_NAME")
                , root_1)

                # Congress.g:160:47: ( ID )+
                if not (stream_ID.hasNext()):
                    raise RewriteEarlyExitException()

                while stream_ID.hasNext():
                    self._adaptor.addChild(root_1, 
                    stream_ID.nextNode()
                    )


                stream_ID.reset()

                # Congress.g:160:51: ( SIGN )?
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



            except RecognitionException as re:
                self.reportError(re)
                self.recover(self.input, re)
                retval.tree = self._adaptor.errorNode(self.input, retval.start, self.input.LT(-1), re)

        finally:
            pass
        return retval

    # $ANTLR end "relation_constant"



    # lookup tables for DFA #5

    DFA5_eot = DFA.unpack(
        "\124\uffff"
        )

    DFA5_eof = DFA.unpack(
        "\1\uffff\1\10\4\uffff\1\10\4\uffff\1\10\4\uffff\1\10\10\uffff\1"
        "\10\72\uffff"
        )

    DFA5_min = DFA.unpack(
        "\1\32\1\13\1\36\1\uffff\1\36\1\32\1\13\1\24\1\uffff\2\32\1\13\4"
        "\16\2\13\1\uffff\1\40\2\24\1\32\1\13\1\24\1\13\1\32\1\40\1\24\10"
        "\16\1\13\4\16\1\13\1\40\4\16\1\46\5\24\24\16\2\24\10\16"
        )

    DFA5_max = DFA.unpack(
        "\2\72\1\36\1\uffff\1\36\1\32\1\72\1\54\1\uffff\1\72\1\32\1\72\4"
        "\47\1\72\1\66\1\uffff\1\66\2\54\1\32\1\46\1\54\1\72\1\32\1\46\1"
        "\54\10\47\1\66\4\47\1\46\1\66\4\47\1\46\5\54\24\47\2\54\10\47"
        )

    DFA5_accept = DFA.unpack(
        "\3\uffff\1\1\4\uffff\1\2\11\uffff\1\3\101\uffff"
        )

    DFA5_special = DFA.unpack(
        "\124\uffff"
        )


    DFA5_transition = [
        DFA.unpack("\1\1\10\uffff\1\3\24\uffff\1\2\1\4\1\2"),
        DFA.unpack("\1\3\2\uffff\1\3\1\10\12\uffff\1\10\5\uffff\1\7\2\uffff"
        "\1\10\5\uffff\1\6\13\uffff\1\10\1\5\4\10"),
        DFA.unpack("\1\11"),
        DFA.unpack(""),
        DFA.unpack("\1\12"),
        DFA.unpack("\1\13"),
        DFA.unpack("\1\3\2\uffff\1\3\1\10\12\uffff\1\10\5\uffff\1\7\2\uffff"
        "\1\10\21\uffff\1\10\1\uffff\4\10"),
        DFA.unpack("\1\15\5\uffff\1\17\1\14\13\uffff\1\20\4\uffff\1\16"),
        DFA.unpack(""),
        DFA.unpack("\1\21\10\uffff\1\22\24\uffff\3\22"),
        DFA.unpack("\1\23"),
        DFA.unpack("\1\3\2\uffff\1\3\1\10\12\uffff\1\10\5\uffff\1\7\2\uffff"
        "\1\10\5\uffff\1\6\13\uffff\1\10\1\5\4\10"),
        DFA.unpack("\1\24\2\uffff\1\25\25\uffff\1\20"),
        DFA.unpack("\1\24\30\uffff\1\20"),
        DFA.unpack("\1\24\30\uffff\1\20"),
        DFA.unpack("\1\24\2\uffff\1\25\25\uffff\1\20"),
        DFA.unpack("\1\3\2\uffff\1\3\1\10\12\uffff\1\10\10\uffff\1\10\21"
        "\uffff\1\10\1\uffff\4\10"),
        DFA.unpack("\1\22\2\uffff\1\22\21\uffff\1\30\5\uffff\1\31\2\uffff"
        "\1\27\14\uffff\1\26"),
        DFA.unpack(""),
        DFA.unpack("\1\34\5\uffff\1\31\2\uffff\1\33\14\uffff\1\32"),
        DFA.unpack("\1\36\5\uffff\1\40\1\35\20\uffff\1\37"),
        DFA.unpack("\1\42\5\uffff\1\44\1\41\20\uffff\1\43"),
        DFA.unpack("\1\45"),
        DFA.unpack("\1\22\2\uffff\1\22\21\uffff\1\30\5\uffff\1\31"),
        DFA.unpack("\1\47\5\uffff\1\51\1\46\13\uffff\1\52\4\uffff\1\50"),
        DFA.unpack("\1\3\2\uffff\1\3\1\10\12\uffff\1\10\10\uffff\1\10\21"
        "\uffff\1\10\1\uffff\4\10"),
        DFA.unpack("\1\53"),
        DFA.unpack("\1\34\5\uffff\1\31"),
        DFA.unpack("\1\55\5\uffff\1\57\1\54\13\uffff\1\60\4\uffff\1\56"),
        DFA.unpack("\1\24\2\uffff\1\61\25\uffff\1\20"),
        DFA.unpack("\1\24\30\uffff\1\20"),
        DFA.unpack("\1\24\30\uffff\1\20"),
        DFA.unpack("\1\24\2\uffff\1\61\25\uffff\1\20"),
        DFA.unpack("\1\24\30\uffff\1\20"),
        DFA.unpack("\1\24\30\uffff\1\20"),
        DFA.unpack("\1\24\30\uffff\1\20"),
        DFA.unpack("\1\24\30\uffff\1\20"),
        DFA.unpack("\1\22\2\uffff\1\22\21\uffff\1\30\5\uffff\1\31\2\uffff"
        "\1\27\14\uffff\1\26"),
        DFA.unpack("\1\62\2\uffff\1\63\25\uffff\1\52"),
        DFA.unpack("\1\62\30\uffff\1\52"),
        DFA.unpack("\1\62\30\uffff\1\52"),
        DFA.unpack("\1\62\2\uffff\1\63\25\uffff\1\52"),
        DFA.unpack("\1\22\2\uffff\1\22\27\uffff\1\31"),
        DFA.unpack("\1\34\5\uffff\1\31\2\uffff\1\33\14\uffff\1\32"),
        DFA.unpack("\1\64\2\uffff\1\65\25\uffff\1\60"),
        DFA.unpack("\1\64\30\uffff\1\60"),
        DFA.unpack("\1\64\30\uffff\1\60"),
        DFA.unpack("\1\64\2\uffff\1\65\25\uffff\1\60"),
        DFA.unpack("\1\31"),
        DFA.unpack("\1\67\5\uffff\1\71\1\66\20\uffff\1\70"),
        DFA.unpack("\1\73\5\uffff\1\75\1\72\20\uffff\1\74"),
        DFA.unpack("\1\77\5\uffff\1\101\1\76\20\uffff\1\100"),
        DFA.unpack("\1\103\5\uffff\1\105\1\102\20\uffff\1\104"),
        DFA.unpack("\1\107\5\uffff\1\111\1\106\20\uffff\1\110"),
        DFA.unpack("\1\24\30\uffff\1\20"),
        DFA.unpack("\1\24\30\uffff\1\20"),
        DFA.unpack("\1\24\30\uffff\1\20"),
        DFA.unpack("\1\24\30\uffff\1\20"),
        DFA.unpack("\1\62\2\uffff\1\112\25\uffff\1\52"),
        DFA.unpack("\1\62\30\uffff\1\52"),
        DFA.unpack("\1\62\30\uffff\1\52"),
        DFA.unpack("\1\62\2\uffff\1\112\25\uffff\1\52"),
        DFA.unpack("\1\62\30\uffff\1\52"),
        DFA.unpack("\1\62\30\uffff\1\52"),
        DFA.unpack("\1\62\30\uffff\1\52"),
        DFA.unpack("\1\62\30\uffff\1\52"),
        DFA.unpack("\1\64\2\uffff\1\113\25\uffff\1\60"),
        DFA.unpack("\1\64\30\uffff\1\60"),
        DFA.unpack("\1\64\30\uffff\1\60"),
        DFA.unpack("\1\64\2\uffff\1\113\25\uffff\1\60"),
        DFA.unpack("\1\64\30\uffff\1\60"),
        DFA.unpack("\1\64\30\uffff\1\60"),
        DFA.unpack("\1\64\30\uffff\1\60"),
        DFA.unpack("\1\64\30\uffff\1\60"),
        DFA.unpack("\1\115\5\uffff\1\117\1\114\20\uffff\1\116"),
        DFA.unpack("\1\121\5\uffff\1\123\1\120\20\uffff\1\122"),
        DFA.unpack("\1\62\30\uffff\1\52"),
        DFA.unpack("\1\62\30\uffff\1\52"),
        DFA.unpack("\1\62\30\uffff\1\52"),
        DFA.unpack("\1\62\30\uffff\1\52"),
        DFA.unpack("\1\64\30\uffff\1\60"),
        DFA.unpack("\1\64\30\uffff\1\60"),
        DFA.unpack("\1\64\30\uffff\1\60"),
        DFA.unpack("\1\64\30\uffff\1\60")
    ]

    # class definition for DFA #5

    class DFA5(DFA):
        pass


 

    FOLLOW_statement_in_prog265 = frozenset([15, 26, 35, 56, 57, 58])
    FOLLOW_EOF_in_prog268 = frozenset([1])
    FOLLOW_EOF_in_prog285 = frozenset([1])
    FOLLOW_formula_in_statement304 = frozenset([1, 53, 55])
    FOLLOW_formula_terminator_in_statement306 = frozenset([1])
    FOLLOW_COMMENT_in_statement319 = frozenset([1])
    FOLLOW_rule_in_formula336 = frozenset([1])
    FOLLOW_fact_in_formula344 = frozenset([1])
    FOLLOW_event_in_formula352 = frozenset([1])
    FOLLOW_event_op_in_event379 = frozenset([30])
    FOLLOW_LBRACKET_in_event381 = frozenset([26, 35, 56, 57, 58])
    FOLLOW_rule_in_event383 = frozenset([38, 53, 55])
    FOLLOW_formula_terminator_in_event386 = frozenset([44])
    FOLLOW_STRING_in_event388 = frozenset([38])
    FOLLOW_RBRACKET_in_event392 = frozenset([1])
    FOLLOW_literal_list_in_rule472 = frozenset([11])
    FOLLOW_COLONMINUS_in_rule474 = frozenset([26, 35, 56, 57, 58])
    FOLLOW_literal_list_in_rule476 = frozenset([1])
    FOLLOW_literal_in_literal_list503 = frozenset([1, 14])
    FOLLOW_COMMA_in_literal_list506 = frozenset([26, 35, 56, 57, 58])
    FOLLOW_literal_in_literal_list508 = frozenset([1, 14])
    FOLLOW_fact_in_literal536 = frozenset([1])
    FOLLOW_NEGATION_in_literal559 = frozenset([26, 56, 57, 58])
    FOLLOW_fact_in_literal561 = frozenset([1])
    FOLLOW_atom_in_fact590 = frozenset([1])
    FOLLOW_modal_op_in_fact598 = frozenset([30])
    FOLLOW_LBRACKET_in_fact600 = frozenset([26])
    FOLLOW_atom_in_fact602 = frozenset([38])
    FOLLOW_RBRACKET_in_fact604 = frozenset([1])
    FOLLOW_relation_constant_in_atom664 = frozenset([1, 32])
    FOLLOW_LPAREN_in_atom667 = frozenset([20, 26, 27, 39, 44])
    FOLLOW_parameter_list_in_atom669 = frozenset([39])
    FOLLOW_RPAREN_in_atom672 = frozenset([1])
    FOLLOW_parameter_in_parameter_list702 = frozenset([1, 14])
    FOLLOW_COMMA_in_parameter_list705 = frozenset([20, 26, 27, 44])
    FOLLOW_parameter_in_parameter_list707 = frozenset([1, 14])
    FOLLOW_term_in_parameter731 = frozenset([1])
    FOLLOW_column_ref_in_parameter743 = frozenset([17])
    FOLLOW_EQUAL_in_parameter745 = frozenset([20, 26, 27, 44])
    FOLLOW_term_in_parameter747 = frozenset([1])
    FOLLOW_ID_in_column_ref774 = frozenset([1])
    FOLLOW_INT_in_column_ref793 = frozenset([1])
    FOLLOW_object_constant_in_term820 = frozenset([1])
    FOLLOW_variable_in_term828 = frozenset([1])
    FOLLOW_INT_in_object_constant845 = frozenset([1])
    FOLLOW_FLOAT_in_object_constant866 = frozenset([1])
    FOLLOW_STRING_in_object_constant885 = frozenset([1])
    FOLLOW_ID_in_variable912 = frozenset([1])
    FOLLOW_ID_in_relation_constant937 = frozenset([1, 41, 54])
    FOLLOW_54_in_relation_constant940 = frozenset([26])
    FOLLOW_ID_in_relation_constant942 = frozenset([1, 41, 54])
    FOLLOW_SIGN_in_relation_constant946 = frozenset([1])



def main(argv, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr):
    from antlr3.main import ParserMain
    main = ParserMain("CongressLexer", CongressParser)

    main.stdin = stdin
    main.stdout = stdout
    main.stderr = stderr
    main.execute(argv)



if __name__ == '__main__':
    main(sys.argv)
