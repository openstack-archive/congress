# $ANTLR 3.5 /Users/thinrichs/Code/congress/congress/datalog/Congress.g 2015-04-14 16:46:46

import sys
from antlr3 import *
from antlr3.compat import set, frozenset

from antlr3.tree import *




# for convenience in actions
HIDDEN = BaseRecognizer.HIDDEN

# token types
EOF=-1
T__52=52
T__53=53
T__54=54
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
EXPONENT=18
FLOAT=19
FLOAT_EXP=20
FLOAT_NO_EXP=21
FLOAT_OBJ=22
FRAC_PART=23
HEX_DIGIT=24
ID=25
INT=26
INTEGER_OBJ=27
INT_PART=28
LBRACKET=29
LITERAL=30
LPAREN=31
MODAL=32
NAMED_PARAM=33
NEGATION=34
NOT=35
PROG=36
RBRACKET=37
RPAREN=38
RULE=39
SIGN=40
SLBYTESTRING=41
SLSTRING=42
STRING=43
STRING_ESC=44
STRING_OBJ=45
STRPREFIX=46
STRUCTURED_NAME=47
SYMBOL_OBJ=48
THEORY=49
VARIABLE=50
WS=51

# token names
tokenNames = [
    "<invalid>", "<EOR>", "<DOWN>", "<UP>",
    "AND", "ATOM", "BYTESTRPREFIX", "BYTES_CHAR_DQ", "BYTES_CHAR_SQ", "BYTES_ESC", 
    "BYTES_TESC", "COLONMINUS", "COLUMN_NAME", "COLUMN_NUMBER", "COMMA", 
    "COMMENT", "DIGIT", "EQUAL", "EXPONENT", "FLOAT", "FLOAT_EXP", "FLOAT_NO_EXP", 
    "FLOAT_OBJ", "FRAC_PART", "HEX_DIGIT", "ID", "INT", "INTEGER_OBJ", "INT_PART", 
    "LBRACKET", "LITERAL", "LPAREN", "MODAL", "NAMED_PARAM", "NEGATION", 
    "NOT", "PROG", "RBRACKET", "RPAREN", "RULE", "SIGN", "SLBYTESTRING", 
    "SLSTRING", "STRING", "STRING_ESC", "STRING_OBJ", "STRPREFIX", "STRUCTURED_NAME", 
    "SYMBOL_OBJ", "THEORY", "VARIABLE", "WS", "'.'", "':'", "';'"
]




class CongressParser(Parser):
    grammarFileName = "/Users/thinrichs/Code/congress/congress/datalog/Congress.g"
    api_version = 1
    tokenNames = tokenNames

    def __init__(self, input, state=None, *args, **kwargs):
        if state is None:
            state = RecognizerSharedState()

        super(CongressParser, self).__init__(input, state, *args, **kwargs)

        self.dfa4 = self.DFA4(
            self, 4,
            eot = self.DFA4_eot,
            eof = self.DFA4_eof,
            min = self.DFA4_min,
            max = self.DFA4_max,
            accept = self.DFA4_accept,
            special = self.DFA4_special,
            transition = self.DFA4_transition
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
    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:56:1: prog : ( formula ( formula )* EOF -> ^( THEORY ( formula )+ ) | EOF );
    def prog(self, ):
        retval = self.prog_return()
        retval.start = self.input.LT(1)


        root_0 = None

        EOF3 = None
        EOF4 = None
        formula1 = None
        formula2 = None

        EOF3_tree = None
        EOF4_tree = None
        stream_EOF = RewriteRuleTokenStream(self._adaptor, "token EOF")
        stream_formula = RewriteRuleSubtreeStream(self._adaptor, "rule formula")
        try:
            try:
                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:57:5: ( formula ( formula )* EOF -> ^( THEORY ( formula )+ ) | EOF )
                alt2 = 2
                LA2_0 = self.input.LA(1)

                if (LA2_0 == ID or LA2_0 == NEGATION) :
                    alt2 = 1
                elif (LA2_0 == EOF) :
                    alt2 = 2
                else:
                    nvae = NoViableAltException("", 2, 0, self.input)

                    raise nvae


                if alt2 == 1:
                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:57:7: formula ( formula )* EOF
                    pass 
                    self._state.following.append(self.FOLLOW_formula_in_prog257)
                    formula1 = self.formula()

                    self._state.following.pop()
                    stream_formula.add(formula1.tree)


                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:57:15: ( formula )*
                    while True: #loop1
                        alt1 = 2
                        LA1_0 = self.input.LA(1)

                        if (LA1_0 == ID or LA1_0 == NEGATION) :
                            alt1 = 1


                        if alt1 == 1:
                            # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:57:15: formula
                            pass 
                            self._state.following.append(self.FOLLOW_formula_in_prog259)
                            formula2 = self.formula()

                            self._state.following.pop()
                            stream_formula.add(formula2.tree)



                        else:
                            break #loop1


                    EOF3 = self.match(self.input, EOF, self.FOLLOW_EOF_in_prog262) 
                    stream_EOF.add(EOF3)


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
                    # 57:28: -> ^( THEORY ( formula )+ )
                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:57:31: ^( THEORY ( formula )+ )
                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(
                    self._adaptor.createFromType(THEORY, "THEORY")
                    , root_1)

                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:57:40: ( formula )+
                    if not (stream_formula.hasNext()):
                        raise RewriteEarlyExitException()

                    while stream_formula.hasNext():
                        self._adaptor.addChild(root_1, stream_formula.nextTree())


                    stream_formula.reset()

                    self._adaptor.addChild(root_0, root_1)




                    retval.tree = root_0




                elif alt2 == 2:
                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:58:7: EOF
                    pass 
                    root_0 = self._adaptor.nil()


                    EOF4 = self.match(self.input, EOF, self.FOLLOW_EOF_in_prog279)
                    EOF4_tree = self._adaptor.createWithPayload(EOF4)
                    self._adaptor.addChild(root_0, EOF4_tree)




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


    class formula_return(ParserRuleReturnScope):
        def __init__(self):
            super(CongressParser.formula_return, self).__init__()

            self.tree = None





    # $ANTLR start "formula"
    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:61:1: formula : bare_formula ( formula_terminator )? -> bare_formula ;
    def formula(self, ):
        retval = self.formula_return()
        retval.start = self.input.LT(1)


        root_0 = None

        bare_formula5 = None
        formula_terminator6 = None

        stream_bare_formula = RewriteRuleSubtreeStream(self._adaptor, "rule bare_formula")
        stream_formula_terminator = RewriteRuleSubtreeStream(self._adaptor, "rule formula_terminator")
        try:
            try:
                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:62:5: ( bare_formula ( formula_terminator )? -> bare_formula )
                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:62:7: bare_formula ( formula_terminator )?
                pass 
                self._state.following.append(self.FOLLOW_bare_formula_in_formula296)
                bare_formula5 = self.bare_formula()

                self._state.following.pop()
                stream_bare_formula.add(bare_formula5.tree)


                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:62:20: ( formula_terminator )?
                alt3 = 2
                LA3_0 = self.input.LA(1)

                if (LA3_0 == 52 or LA3_0 == 54) :
                    alt3 = 1
                if alt3 == 1:
                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:62:20: formula_terminator
                    pass 
                    self._state.following.append(self.FOLLOW_formula_terminator_in_formula298)
                    formula_terminator6 = self.formula_terminator()

                    self._state.following.pop()
                    stream_formula_terminator.add(formula_terminator6.tree)





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
                # 62:40: -> bare_formula
                self._adaptor.addChild(root_0, stream_bare_formula.nextTree())




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

    # $ANTLR end "formula"


    class formula_terminator_return(ParserRuleReturnScope):
        def __init__(self):
            super(CongressParser.formula_terminator_return, self).__init__()

            self.tree = None





    # $ANTLR start "formula_terminator"
    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:65:1: formula_terminator : ( ';' | '.' );
    def formula_terminator(self, ):
        retval = self.formula_terminator_return()
        retval.start = self.input.LT(1)


        root_0 = None

        set7 = None

        set7_tree = None

        try:
            try:
                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:66:5: ( ';' | '.' )
                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:
                pass 
                root_0 = self._adaptor.nil()


                set7 = self.input.LT(1)

                if self.input.LA(1) == 52 or self.input.LA(1) == 54:
                    self.input.consume()
                    self._adaptor.addChild(root_0, self._adaptor.createWithPayload(set7))

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


    class bare_formula_return(ParserRuleReturnScope):
        def __init__(self):
            super(CongressParser.bare_formula_return, self).__init__()

            self.tree = None





    # $ANTLR start "bare_formula"
    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:70:1: bare_formula : ( rule | modal );
    def bare_formula(self, ):
        retval = self.bare_formula_return()
        retval.start = self.input.LT(1)


        root_0 = None

        rule8 = None
        modal9 = None


        try:
            try:
                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:71:5: ( rule | modal )
                alt4 = 2
                alt4 = self.dfa4.predict(self.input)
                if alt4 == 1:
                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:71:7: rule
                    pass 
                    root_0 = self._adaptor.nil()


                    self._state.following.append(self.FOLLOW_rule_in_bare_formula345)
                    rule8 = self.rule()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, rule8.tree)



                elif alt4 == 2:
                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:72:7: modal
                    pass 
                    root_0 = self._adaptor.nil()


                    self._state.following.append(self.FOLLOW_modal_in_bare_formula353)
                    modal9 = self.modal()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, modal9.tree)



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


    class rule_return(ParserRuleReturnScope):
        def __init__(self):
            super(CongressParser.rule_return, self).__init__()

            self.tree = None





    # $ANTLR start "rule"
    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:75:1: rule : literal_list COLONMINUS literal_list -> ^( RULE literal_list literal_list ) ;
    def rule(self, ):
        retval = self.rule_return()
        retval.start = self.input.LT(1)


        root_0 = None

        COLONMINUS11 = None
        literal_list10 = None
        literal_list12 = None

        COLONMINUS11_tree = None
        stream_COLONMINUS = RewriteRuleTokenStream(self._adaptor, "token COLONMINUS")
        stream_literal_list = RewriteRuleSubtreeStream(self._adaptor, "rule literal_list")
        try:
            try:
                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:76:5: ( literal_list COLONMINUS literal_list -> ^( RULE literal_list literal_list ) )
                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:76:7: literal_list COLONMINUS literal_list
                pass 
                self._state.following.append(self.FOLLOW_literal_list_in_rule370)
                literal_list10 = self.literal_list()

                self._state.following.pop()
                stream_literal_list.add(literal_list10.tree)


                COLONMINUS11 = self.match(self.input, COLONMINUS, self.FOLLOW_COLONMINUS_in_rule372) 
                stream_COLONMINUS.add(COLONMINUS11)


                self._state.following.append(self.FOLLOW_literal_list_in_rule374)
                literal_list12 = self.literal_list()

                self._state.following.pop()
                stream_literal_list.add(literal_list12.tree)


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
                # 76:44: -> ^( RULE literal_list literal_list )
                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:76:47: ^( RULE literal_list literal_list )
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

    # $ANTLR end "rule"


    class literal_list_return(ParserRuleReturnScope):
        def __init__(self):
            super(CongressParser.literal_list_return, self).__init__()

            self.tree = None





    # $ANTLR start "literal_list"
    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:79:1: literal_list : literal ( COMMA literal )* -> ^( AND ( literal )+ ) ;
    def literal_list(self, ):
        retval = self.literal_list_return()
        retval.start = self.input.LT(1)


        root_0 = None

        COMMA14 = None
        literal13 = None
        literal15 = None

        COMMA14_tree = None
        stream_COMMA = RewriteRuleTokenStream(self._adaptor, "token COMMA")
        stream_literal = RewriteRuleSubtreeStream(self._adaptor, "rule literal")
        try:
            try:
                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:80:5: ( literal ( COMMA literal )* -> ^( AND ( literal )+ ) )
                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:80:7: literal ( COMMA literal )*
                pass 
                self._state.following.append(self.FOLLOW_literal_in_literal_list401)
                literal13 = self.literal()

                self._state.following.pop()
                stream_literal.add(literal13.tree)


                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:80:15: ( COMMA literal )*
                while True: #loop5
                    alt5 = 2
                    LA5_0 = self.input.LA(1)

                    if (LA5_0 == COMMA) :
                        alt5 = 1


                    if alt5 == 1:
                        # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:80:16: COMMA literal
                        pass 
                        COMMA14 = self.match(self.input, COMMA, self.FOLLOW_COMMA_in_literal_list404) 
                        stream_COMMA.add(COMMA14)


                        self._state.following.append(self.FOLLOW_literal_in_literal_list406)
                        literal15 = self.literal()

                        self._state.following.pop()
                        stream_literal.add(literal15.tree)



                    else:
                        break #loop5


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
                # 80:32: -> ^( AND ( literal )+ )
                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:80:35: ^( AND ( literal )+ )
                root_1 = self._adaptor.nil()
                root_1 = self._adaptor.becomeRoot(
                self._adaptor.createFromType(AND, "AND")
                , root_1)

                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:80:41: ( literal )+
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
    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:83:1: literal : ( modal -> modal | NEGATION modal -> ^( NOT modal ) );
    def literal(self, ):
        retval = self.literal_return()
        retval.start = self.input.LT(1)


        root_0 = None

        NEGATION17 = None
        modal16 = None
        modal18 = None

        NEGATION17_tree = None
        stream_NEGATION = RewriteRuleTokenStream(self._adaptor, "token NEGATION")
        stream_modal = RewriteRuleSubtreeStream(self._adaptor, "rule modal")
        try:
            try:
                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:84:5: ( modal -> modal | NEGATION modal -> ^( NOT modal ) )
                alt6 = 2
                LA6_0 = self.input.LA(1)

                if (LA6_0 == ID) :
                    alt6 = 1
                elif (LA6_0 == NEGATION) :
                    alt6 = 2
                else:
                    nvae = NoViableAltException("", 6, 0, self.input)

                    raise nvae


                if alt6 == 1:
                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:84:7: modal
                    pass 
                    self._state.following.append(self.FOLLOW_modal_in_literal434)
                    modal16 = self.modal()

                    self._state.following.pop()
                    stream_modal.add(modal16.tree)


                    # AST Rewrite
                    # elements: modal
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
                    # 84:23: -> modal
                    self._adaptor.addChild(root_0, stream_modal.nextTree())




                    retval.tree = root_0




                elif alt6 == 2:
                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:85:7: NEGATION modal
                    pass 
                    NEGATION17 = self.match(self.input, NEGATION, self.FOLLOW_NEGATION_in_literal456) 
                    stream_NEGATION.add(NEGATION17)


                    self._state.following.append(self.FOLLOW_modal_in_literal458)
                    modal18 = self.modal()

                    self._state.following.pop()
                    stream_modal.add(modal18.tree)


                    # AST Rewrite
                    # elements: modal
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
                    # 85:23: -> ^( NOT modal )
                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:85:26: ^( NOT modal )
                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(
                    self._adaptor.createFromType(NOT, "NOT")
                    , root_1)

                    self._adaptor.addChild(root_1, stream_modal.nextTree())

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


    class modal_return(ParserRuleReturnScope):
        def __init__(self):
            super(CongressParser.modal_return, self).__init__()

            self.tree = None





    # $ANTLR start "modal"
    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:94:1: modal : ( atom | ID LBRACKET atom RBRACKET -> ^( MODAL ID atom ) );
    def modal(self, ):
        retval = self.modal_return()
        retval.start = self.input.LT(1)


        root_0 = None

        ID20 = None
        LBRACKET21 = None
        RBRACKET23 = None
        atom19 = None
        atom22 = None

        ID20_tree = None
        LBRACKET21_tree = None
        RBRACKET23_tree = None
        stream_LBRACKET = RewriteRuleTokenStream(self._adaptor, "token LBRACKET")
        stream_RBRACKET = RewriteRuleTokenStream(self._adaptor, "token RBRACKET")
        stream_ID = RewriteRuleTokenStream(self._adaptor, "token ID")
        stream_atom = RewriteRuleSubtreeStream(self._adaptor, "rule atom")
        try:
            try:
                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:95:5: ( atom | ID LBRACKET atom RBRACKET -> ^( MODAL ID atom ) )
                alt7 = 2
                LA7_0 = self.input.LA(1)

                if (LA7_0 == ID) :
                    LA7_1 = self.input.LA(2)

                    if (LA7_1 == LBRACKET) :
                        alt7 = 2
                    elif (LA7_1 == EOF or LA7_1 == COLONMINUS or LA7_1 == COMMA or LA7_1 == ID or LA7_1 == LPAREN or LA7_1 == NEGATION or LA7_1 == SIGN or (52 <= LA7_1 <= 54)) :
                        alt7 = 1
                    else:
                        nvae = NoViableAltException("", 7, 1, self.input)

                        raise nvae


                else:
                    nvae = NoViableAltException("", 7, 0, self.input)

                    raise nvae


                if alt7 == 1:
                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:95:7: atom
                    pass 
                    root_0 = self._adaptor.nil()


                    self._state.following.append(self.FOLLOW_atom_in_modal517)
                    atom19 = self.atom()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, atom19.tree)



                elif alt7 == 2:
                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:96:7: ID LBRACKET atom RBRACKET
                    pass 
                    ID20 = self.match(self.input, ID, self.FOLLOW_ID_in_modal525) 
                    stream_ID.add(ID20)


                    LBRACKET21 = self.match(self.input, LBRACKET, self.FOLLOW_LBRACKET_in_modal527) 
                    stream_LBRACKET.add(LBRACKET21)


                    self._state.following.append(self.FOLLOW_atom_in_modal529)
                    atom22 = self.atom()

                    self._state.following.pop()
                    stream_atom.add(atom22.tree)


                    RBRACKET23 = self.match(self.input, RBRACKET, self.FOLLOW_RBRACKET_in_modal531) 
                    stream_RBRACKET.add(RBRACKET23)


                    # AST Rewrite
                    # elements: atom, ID
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
                    # 96:33: -> ^( MODAL ID atom )
                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:96:36: ^( MODAL ID atom )
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

    # $ANTLR end "modal"


    class atom_return(ParserRuleReturnScope):
        def __init__(self):
            super(CongressParser.atom_return, self).__init__()

            self.tree = None





    # $ANTLR start "atom"
    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:99:1: atom : relation_constant ( LPAREN ( parameter_list )? RPAREN )? -> ^( ATOM relation_constant ( parameter_list )? ) ;
    def atom(self, ):
        retval = self.atom_return()
        retval.start = self.input.LT(1)


        root_0 = None

        LPAREN25 = None
        RPAREN27 = None
        relation_constant24 = None
        parameter_list26 = None

        LPAREN25_tree = None
        RPAREN27_tree = None
        stream_LPAREN = RewriteRuleTokenStream(self._adaptor, "token LPAREN")
        stream_RPAREN = RewriteRuleTokenStream(self._adaptor, "token RPAREN")
        stream_relation_constant = RewriteRuleSubtreeStream(self._adaptor, "rule relation_constant")
        stream_parameter_list = RewriteRuleSubtreeStream(self._adaptor, "rule parameter_list")
        try:
            try:
                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:100:5: ( relation_constant ( LPAREN ( parameter_list )? RPAREN )? -> ^( ATOM relation_constant ( parameter_list )? ) )
                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:100:7: relation_constant ( LPAREN ( parameter_list )? RPAREN )?
                pass 
                self._state.following.append(self.FOLLOW_relation_constant_in_atom558)
                relation_constant24 = self.relation_constant()

                self._state.following.pop()
                stream_relation_constant.add(relation_constant24.tree)


                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:100:25: ( LPAREN ( parameter_list )? RPAREN )?
                alt9 = 2
                LA9_0 = self.input.LA(1)

                if (LA9_0 == LPAREN) :
                    alt9 = 1
                if alt9 == 1:
                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:100:26: LPAREN ( parameter_list )? RPAREN
                    pass 
                    LPAREN25 = self.match(self.input, LPAREN, self.FOLLOW_LPAREN_in_atom561) 
                    stream_LPAREN.add(LPAREN25)


                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:100:33: ( parameter_list )?
                    alt8 = 2
                    LA8_0 = self.input.LA(1)

                    if (LA8_0 == FLOAT or (ID <= LA8_0 <= INT) or LA8_0 == STRING) :
                        alt8 = 1
                    if alt8 == 1:
                        # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:100:33: parameter_list
                        pass 
                        self._state.following.append(self.FOLLOW_parameter_list_in_atom563)
                        parameter_list26 = self.parameter_list()

                        self._state.following.pop()
                        stream_parameter_list.add(parameter_list26.tree)





                    RPAREN27 = self.match(self.input, RPAREN, self.FOLLOW_RPAREN_in_atom566) 
                    stream_RPAREN.add(RPAREN27)





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
                # 100:58: -> ^( ATOM relation_constant ( parameter_list )? )
                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:100:61: ^( ATOM relation_constant ( parameter_list )? )
                root_1 = self._adaptor.nil()
                root_1 = self._adaptor.becomeRoot(
                self._adaptor.createFromType(ATOM, "ATOM")
                , root_1)

                self._adaptor.addChild(root_1, stream_relation_constant.nextTree())

                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:100:86: ( parameter_list )?
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
    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:103:1: parameter_list : parameter ( COMMA parameter )* -> ( parameter )+ ;
    def parameter_list(self, ):
        retval = self.parameter_list_return()
        retval.start = self.input.LT(1)


        root_0 = None

        COMMA29 = None
        parameter28 = None
        parameter30 = None

        COMMA29_tree = None
        stream_COMMA = RewriteRuleTokenStream(self._adaptor, "token COMMA")
        stream_parameter = RewriteRuleSubtreeStream(self._adaptor, "rule parameter")
        try:
            try:
                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:104:5: ( parameter ( COMMA parameter )* -> ( parameter )+ )
                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:104:7: parameter ( COMMA parameter )*
                pass 
                self._state.following.append(self.FOLLOW_parameter_in_parameter_list596)
                parameter28 = self.parameter()

                self._state.following.pop()
                stream_parameter.add(parameter28.tree)


                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:104:17: ( COMMA parameter )*
                while True: #loop10
                    alt10 = 2
                    LA10_0 = self.input.LA(1)

                    if (LA10_0 == COMMA) :
                        alt10 = 1


                    if alt10 == 1:
                        # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:104:18: COMMA parameter
                        pass 
                        COMMA29 = self.match(self.input, COMMA, self.FOLLOW_COMMA_in_parameter_list599) 
                        stream_COMMA.add(COMMA29)


                        self._state.following.append(self.FOLLOW_parameter_in_parameter_list601)
                        parameter30 = self.parameter()

                        self._state.following.pop()
                        stream_parameter.add(parameter30.tree)



                    else:
                        break #loop10


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
                # 104:36: -> ( parameter )+
                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:104:39: ( parameter )+
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
    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:107:1: parameter : ( term -> term | column_ref EQUAL term -> ^( NAMED_PARAM column_ref term ) );
    def parameter(self, ):
        retval = self.parameter_return()
        retval.start = self.input.LT(1)


        root_0 = None

        EQUAL33 = None
        term31 = None
        column_ref32 = None
        term34 = None

        EQUAL33_tree = None
        stream_EQUAL = RewriteRuleTokenStream(self._adaptor, "token EQUAL")
        stream_term = RewriteRuleSubtreeStream(self._adaptor, "rule term")
        stream_column_ref = RewriteRuleSubtreeStream(self._adaptor, "rule column_ref")
        try:
            try:
                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:108:5: ( term -> term | column_ref EQUAL term -> ^( NAMED_PARAM column_ref term ) )
                alt11 = 2
                LA11 = self.input.LA(1)
                if LA11 == INT:
                    LA11_1 = self.input.LA(2)

                    if (LA11_1 == COMMA or LA11_1 == RPAREN) :
                        alt11 = 1
                    elif (LA11_1 == EQUAL) :
                        alt11 = 2
                    else:
                        nvae = NoViableAltException("", 11, 1, self.input)

                        raise nvae


                elif LA11 == FLOAT or LA11 == STRING:
                    alt11 = 1
                elif LA11 == ID:
                    LA11_3 = self.input.LA(2)

                    if (LA11_3 == COMMA or LA11_3 == RPAREN) :
                        alt11 = 1
                    elif (LA11_3 == EQUAL) :
                        alt11 = 2
                    else:
                        nvae = NoViableAltException("", 11, 3, self.input)

                        raise nvae


                else:
                    nvae = NoViableAltException("", 11, 0, self.input)

                    raise nvae


                if alt11 == 1:
                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:108:7: term
                    pass 
                    self._state.following.append(self.FOLLOW_term_in_parameter625)
                    term31 = self.term()

                    self._state.following.pop()
                    stream_term.add(term31.tree)


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
                    # 108:12: -> term
                    self._adaptor.addChild(root_0, stream_term.nextTree())




                    retval.tree = root_0




                elif alt11 == 2:
                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:109:7: column_ref EQUAL term
                    pass 
                    self._state.following.append(self.FOLLOW_column_ref_in_parameter637)
                    column_ref32 = self.column_ref()

                    self._state.following.pop()
                    stream_column_ref.add(column_ref32.tree)


                    EQUAL33 = self.match(self.input, EQUAL, self.FOLLOW_EQUAL_in_parameter639) 
                    stream_EQUAL.add(EQUAL33)


                    self._state.following.append(self.FOLLOW_term_in_parameter641)
                    term34 = self.term()

                    self._state.following.pop()
                    stream_term.add(term34.tree)


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
                    # 109:29: -> ^( NAMED_PARAM column_ref term )
                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:109:32: ^( NAMED_PARAM column_ref term )
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
    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:112:1: column_ref : ( ID -> ^( COLUMN_NAME ID ) | INT -> ^( COLUMN_NUMBER INT ) );
    def column_ref(self, ):
        retval = self.column_ref_return()
        retval.start = self.input.LT(1)


        root_0 = None

        ID35 = None
        INT36 = None

        ID35_tree = None
        INT36_tree = None
        stream_ID = RewriteRuleTokenStream(self._adaptor, "token ID")
        stream_INT = RewriteRuleTokenStream(self._adaptor, "token INT")

        try:
            try:
                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:113:5: ( ID -> ^( COLUMN_NAME ID ) | INT -> ^( COLUMN_NUMBER INT ) )
                alt12 = 2
                LA12_0 = self.input.LA(1)

                if (LA12_0 == ID) :
                    alt12 = 1
                elif (LA12_0 == INT) :
                    alt12 = 2
                else:
                    nvae = NoViableAltException("", 12, 0, self.input)

                    raise nvae


                if alt12 == 1:
                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:113:7: ID
                    pass 
                    ID35 = self.match(self.input, ID, self.FOLLOW_ID_in_column_ref668) 
                    stream_ID.add(ID35)


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
                    # 113:12: -> ^( COLUMN_NAME ID )
                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:113:16: ^( COLUMN_NAME ID )
                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(
                    self._adaptor.createFromType(COLUMN_NAME, "COLUMN_NAME")
                    , root_1)

                    self._adaptor.addChild(root_1, 
                    stream_ID.nextNode()
                    )

                    self._adaptor.addChild(root_0, root_1)




                    retval.tree = root_0




                elif alt12 == 2:
                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:114:7: INT
                    pass 
                    INT36 = self.match(self.input, INT, self.FOLLOW_INT_in_column_ref687) 
                    stream_INT.add(INT36)


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
                    # 114:12: -> ^( COLUMN_NUMBER INT )
                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:114:16: ^( COLUMN_NUMBER INT )
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
    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:117:1: term : ( object_constant | variable );
    def term(self, ):
        retval = self.term_return()
        retval.start = self.input.LT(1)


        root_0 = None

        object_constant37 = None
        variable38 = None


        try:
            try:
                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:118:5: ( object_constant | variable )
                alt13 = 2
                LA13_0 = self.input.LA(1)

                if (LA13_0 == FLOAT or LA13_0 == INT or LA13_0 == STRING) :
                    alt13 = 1
                elif (LA13_0 == ID) :
                    alt13 = 2
                else:
                    nvae = NoViableAltException("", 13, 0, self.input)

                    raise nvae


                if alt13 == 1:
                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:118:7: object_constant
                    pass 
                    root_0 = self._adaptor.nil()


                    self._state.following.append(self.FOLLOW_object_constant_in_term714)
                    object_constant37 = self.object_constant()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, object_constant37.tree)



                elif alt13 == 2:
                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:119:7: variable
                    pass 
                    root_0 = self._adaptor.nil()


                    self._state.following.append(self.FOLLOW_variable_in_term722)
                    variable38 = self.variable()

                    self._state.following.pop()
                    self._adaptor.addChild(root_0, variable38.tree)



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
    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:122:1: object_constant : ( INT -> ^( INTEGER_OBJ INT ) | FLOAT -> ^( FLOAT_OBJ FLOAT ) | STRING -> ^( STRING_OBJ STRING ) );
    def object_constant(self, ):
        retval = self.object_constant_return()
        retval.start = self.input.LT(1)


        root_0 = None

        INT39 = None
        FLOAT40 = None
        STRING41 = None

        INT39_tree = None
        FLOAT40_tree = None
        STRING41_tree = None
        stream_FLOAT = RewriteRuleTokenStream(self._adaptor, "token FLOAT")
        stream_STRING = RewriteRuleTokenStream(self._adaptor, "token STRING")
        stream_INT = RewriteRuleTokenStream(self._adaptor, "token INT")

        try:
            try:
                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:123:5: ( INT -> ^( INTEGER_OBJ INT ) | FLOAT -> ^( FLOAT_OBJ FLOAT ) | STRING -> ^( STRING_OBJ STRING ) )
                alt14 = 3
                LA14 = self.input.LA(1)
                if LA14 == INT:
                    alt14 = 1
                elif LA14 == FLOAT:
                    alt14 = 2
                elif LA14 == STRING:
                    alt14 = 3
                else:
                    nvae = NoViableAltException("", 14, 0, self.input)

                    raise nvae


                if alt14 == 1:
                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:123:7: INT
                    pass 
                    INT39 = self.match(self.input, INT, self.FOLLOW_INT_in_object_constant739) 
                    stream_INT.add(INT39)


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
                    # 123:16: -> ^( INTEGER_OBJ INT )
                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:123:19: ^( INTEGER_OBJ INT )
                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(
                    self._adaptor.createFromType(INTEGER_OBJ, "INTEGER_OBJ")
                    , root_1)

                    self._adaptor.addChild(root_1, 
                    stream_INT.nextNode()
                    )

                    self._adaptor.addChild(root_0, root_1)




                    retval.tree = root_0




                elif alt14 == 2:
                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:124:7: FLOAT
                    pass 
                    FLOAT40 = self.match(self.input, FLOAT, self.FOLLOW_FLOAT_in_object_constant760) 
                    stream_FLOAT.add(FLOAT40)


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
                    # 124:16: -> ^( FLOAT_OBJ FLOAT )
                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:124:19: ^( FLOAT_OBJ FLOAT )
                    root_1 = self._adaptor.nil()
                    root_1 = self._adaptor.becomeRoot(
                    self._adaptor.createFromType(FLOAT_OBJ, "FLOAT_OBJ")
                    , root_1)

                    self._adaptor.addChild(root_1, 
                    stream_FLOAT.nextNode()
                    )

                    self._adaptor.addChild(root_0, root_1)




                    retval.tree = root_0




                elif alt14 == 3:
                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:125:7: STRING
                    pass 
                    STRING41 = self.match(self.input, STRING, self.FOLLOW_STRING_in_object_constant779) 
                    stream_STRING.add(STRING41)


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
                    # 125:16: -> ^( STRING_OBJ STRING )
                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:125:19: ^( STRING_OBJ STRING )
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
    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:128:1: variable : ID -> ^( VARIABLE ID ) ;
    def variable(self, ):
        retval = self.variable_return()
        retval.start = self.input.LT(1)


        root_0 = None

        ID42 = None

        ID42_tree = None
        stream_ID = RewriteRuleTokenStream(self._adaptor, "token ID")

        try:
            try:
                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:129:5: ( ID -> ^( VARIABLE ID ) )
                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:129:7: ID
                pass 
                ID42 = self.match(self.input, ID, self.FOLLOW_ID_in_variable806) 
                stream_ID.add(ID42)


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
                # 129:10: -> ^( VARIABLE ID )
                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:129:13: ^( VARIABLE ID )
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
    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:132:1: relation_constant : ID ( ':' ID )* ( SIGN )? -> ^( STRUCTURED_NAME ( ID )+ ( SIGN )? ) ;
    def relation_constant(self, ):
        retval = self.relation_constant_return()
        retval.start = self.input.LT(1)


        root_0 = None

        ID43 = None
        char_literal44 = None
        ID45 = None
        SIGN46 = None

        ID43_tree = None
        char_literal44_tree = None
        ID45_tree = None
        SIGN46_tree = None
        stream_ID = RewriteRuleTokenStream(self._adaptor, "token ID")
        stream_SIGN = RewriteRuleTokenStream(self._adaptor, "token SIGN")
        stream_53 = RewriteRuleTokenStream(self._adaptor, "token 53")

        try:
            try:
                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:133:5: ( ID ( ':' ID )* ( SIGN )? -> ^( STRUCTURED_NAME ( ID )+ ( SIGN )? ) )
                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:133:7: ID ( ':' ID )* ( SIGN )?
                pass 
                ID43 = self.match(self.input, ID, self.FOLLOW_ID_in_relation_constant831) 
                stream_ID.add(ID43)


                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:133:10: ( ':' ID )*
                while True: #loop15
                    alt15 = 2
                    LA15_0 = self.input.LA(1)

                    if (LA15_0 == 53) :
                        alt15 = 1


                    if alt15 == 1:
                        # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:133:11: ':' ID
                        pass 
                        char_literal44 = self.match(self.input, 53, self.FOLLOW_53_in_relation_constant834) 
                        stream_53.add(char_literal44)


                        ID45 = self.match(self.input, ID, self.FOLLOW_ID_in_relation_constant836) 
                        stream_ID.add(ID45)



                    else:
                        break #loop15


                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:133:20: ( SIGN )?
                alt16 = 2
                LA16_0 = self.input.LA(1)

                if (LA16_0 == SIGN) :
                    alt16 = 1
                if alt16 == 1:
                    # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:133:20: SIGN
                    pass 
                    SIGN46 = self.match(self.input, SIGN, self.FOLLOW_SIGN_in_relation_constant840) 
                    stream_SIGN.add(SIGN46)





                # AST Rewrite
                # elements: SIGN, ID
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
                # 133:26: -> ^( STRUCTURED_NAME ( ID )+ ( SIGN )? )
                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:133:29: ^( STRUCTURED_NAME ( ID )+ ( SIGN )? )
                root_1 = self._adaptor.nil()
                root_1 = self._adaptor.becomeRoot(
                self._adaptor.createFromType(STRUCTURED_NAME, "STRUCTURED_NAME")
                , root_1)

                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:133:47: ( ID )+
                if not (stream_ID.hasNext()):
                    raise RewriteEarlyExitException()

                while stream_ID.hasNext():
                    self._adaptor.addChild(root_1, 
                    stream_ID.nextNode()
                    )


                stream_ID.reset()

                # /Users/thinrichs/Code/congress/congress/datalog/Congress.g:133:51: ( SIGN )?
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



    # lookup tables for DFA #4

    DFA4_eot = DFA.unpack(
        u"\67\uffff"
        )

    DFA4_eof = DFA.unpack(
        u"\1\uffff\1\7\3\uffff\1\7\3\uffff\1\7\4\uffff\1\7\3\uffff\1\7\44"
        u"\uffff"
        )

    DFA4_min = DFA.unpack(
        u"\1\31\1\13\1\uffff\2\31\1\13\1\23\1\uffff\1\37\1\13\4\16\1\13\1"
        u"\31\1\37\1\23\1\13\2\23\1\37\4\16\1\45\10\16\3\23\14\16\1\23\4"
        u"\16"
        )

    DFA4_max = DFA.unpack(
        u"\1\42\1\66\1\uffff\2\31\1\66\1\53\1\uffff\1\65\1\66\4\46\1\66\1"
        u"\31\1\45\1\53\1\66\2\53\1\65\4\46\1\45\10\46\3\53\14\46\1\53\4"
        u"\46"
        )

    DFA4_accept = DFA.unpack(
        u"\2\uffff\1\1\4\uffff\1\2\57\uffff"
        )

    DFA4_special = DFA.unpack(
        u"\67\uffff"
        )


    DFA4_transition = [
        DFA.unpack(u"\1\1\10\uffff\1\2"),
        DFA.unpack(u"\1\2\2\uffff\1\2\12\uffff\1\7\3\uffff\1\3\1\uffff\1"
        u"\6\2\uffff\1\7\5\uffff\1\5\13\uffff\1\7\1\4\1\7"),
        DFA.unpack(u""),
        DFA.unpack(u"\1\10"),
        DFA.unpack(u"\1\11"),
        DFA.unpack(u"\1\2\2\uffff\1\2\12\uffff\1\7\5\uffff\1\6\2\uffff\1"
        u"\7\21\uffff\1\7\1\uffff\1\7"),
        DFA.unpack(u"\1\13\5\uffff\1\15\1\12\13\uffff\1\16\4\uffff\1\14"),
        DFA.unpack(u""),
        DFA.unpack(u"\1\21\5\uffff\1\22\2\uffff\1\20\14\uffff\1\17"),
        DFA.unpack(u"\1\2\2\uffff\1\2\12\uffff\1\7\5\uffff\1\6\2\uffff\1"
        u"\7\5\uffff\1\5\13\uffff\1\7\1\4\1\7"),
        DFA.unpack(u"\1\23\2\uffff\1\24\24\uffff\1\16"),
        DFA.unpack(u"\1\23\27\uffff\1\16"),
        DFA.unpack(u"\1\23\27\uffff\1\16"),
        DFA.unpack(u"\1\23\2\uffff\1\24\24\uffff\1\16"),
        DFA.unpack(u"\1\2\2\uffff\1\2\12\uffff\1\7\10\uffff\1\7\21\uffff"
        u"\1\7\1\uffff\1\7"),
        DFA.unpack(u"\1\25"),
        DFA.unpack(u"\1\21\5\uffff\1\22"),
        DFA.unpack(u"\1\27\5\uffff\1\31\1\26\13\uffff\1\32\4\uffff\1\30"),
        DFA.unpack(u"\1\2\2\uffff\1\2\12\uffff\1\7\10\uffff\1\7\21\uffff"
        u"\1\7\1\uffff\1\7"),
        DFA.unpack(u"\1\34\5\uffff\1\36\1\33\20\uffff\1\35"),
        DFA.unpack(u"\1\40\5\uffff\1\42\1\37\20\uffff\1\41"),
        DFA.unpack(u"\1\21\5\uffff\1\22\2\uffff\1\20\14\uffff\1\17"),
        DFA.unpack(u"\1\43\2\uffff\1\44\24\uffff\1\32"),
        DFA.unpack(u"\1\43\27\uffff\1\32"),
        DFA.unpack(u"\1\43\27\uffff\1\32"),
        DFA.unpack(u"\1\43\2\uffff\1\44\24\uffff\1\32"),
        DFA.unpack(u"\1\22"),
        DFA.unpack(u"\1\23\2\uffff\1\45\24\uffff\1\16"),
        DFA.unpack(u"\1\23\27\uffff\1\16"),
        DFA.unpack(u"\1\23\27\uffff\1\16"),
        DFA.unpack(u"\1\23\2\uffff\1\45\24\uffff\1\16"),
        DFA.unpack(u"\1\23\27\uffff\1\16"),
        DFA.unpack(u"\1\23\27\uffff\1\16"),
        DFA.unpack(u"\1\23\27\uffff\1\16"),
        DFA.unpack(u"\1\23\27\uffff\1\16"),
        DFA.unpack(u"\1\47\5\uffff\1\51\1\46\20\uffff\1\50"),
        DFA.unpack(u"\1\53\5\uffff\1\55\1\52\20\uffff\1\54"),
        DFA.unpack(u"\1\57\5\uffff\1\61\1\56\20\uffff\1\60"),
        DFA.unpack(u"\1\43\2\uffff\1\62\24\uffff\1\32"),
        DFA.unpack(u"\1\43\27\uffff\1\32"),
        DFA.unpack(u"\1\43\27\uffff\1\32"),
        DFA.unpack(u"\1\43\2\uffff\1\62\24\uffff\1\32"),
        DFA.unpack(u"\1\43\27\uffff\1\32"),
        DFA.unpack(u"\1\43\27\uffff\1\32"),
        DFA.unpack(u"\1\43\27\uffff\1\32"),
        DFA.unpack(u"\1\43\27\uffff\1\32"),
        DFA.unpack(u"\1\23\27\uffff\1\16"),
        DFA.unpack(u"\1\23\27\uffff\1\16"),
        DFA.unpack(u"\1\23\27\uffff\1\16"),
        DFA.unpack(u"\1\23\27\uffff\1\16"),
        DFA.unpack(u"\1\64\5\uffff\1\66\1\63\20\uffff\1\65"),
        DFA.unpack(u"\1\43\27\uffff\1\32"),
        DFA.unpack(u"\1\43\27\uffff\1\32"),
        DFA.unpack(u"\1\43\27\uffff\1\32"),
        DFA.unpack(u"\1\43\27\uffff\1\32")
    ]

    # class definition for DFA #4

    class DFA4(DFA):
        pass


 

    FOLLOW_formula_in_prog257 = frozenset([25, 34])
    FOLLOW_formula_in_prog259 = frozenset([25, 34])
    FOLLOW_EOF_in_prog262 = frozenset([1])
    FOLLOW_EOF_in_prog279 = frozenset([1])
    FOLLOW_bare_formula_in_formula296 = frozenset([1, 52, 54])
    FOLLOW_formula_terminator_in_formula298 = frozenset([1])
    FOLLOW_rule_in_bare_formula345 = frozenset([1])
    FOLLOW_modal_in_bare_formula353 = frozenset([1])
    FOLLOW_literal_list_in_rule370 = frozenset([11])
    FOLLOW_COLONMINUS_in_rule372 = frozenset([25, 34])
    FOLLOW_literal_list_in_rule374 = frozenset([1])
    FOLLOW_literal_in_literal_list401 = frozenset([1, 14])
    FOLLOW_COMMA_in_literal_list404 = frozenset([25, 34])
    FOLLOW_literal_in_literal_list406 = frozenset([1, 14])
    FOLLOW_modal_in_literal434 = frozenset([1])
    FOLLOW_NEGATION_in_literal456 = frozenset([25])
    FOLLOW_modal_in_literal458 = frozenset([1])
    FOLLOW_atom_in_modal517 = frozenset([1])
    FOLLOW_ID_in_modal525 = frozenset([29])
    FOLLOW_LBRACKET_in_modal527 = frozenset([25])
    FOLLOW_atom_in_modal529 = frozenset([37])
    FOLLOW_RBRACKET_in_modal531 = frozenset([1])
    FOLLOW_relation_constant_in_atom558 = frozenset([1, 31])
    FOLLOW_LPAREN_in_atom561 = frozenset([19, 25, 26, 38, 43])
    FOLLOW_parameter_list_in_atom563 = frozenset([38])
    FOLLOW_RPAREN_in_atom566 = frozenset([1])
    FOLLOW_parameter_in_parameter_list596 = frozenset([1, 14])
    FOLLOW_COMMA_in_parameter_list599 = frozenset([19, 25, 26, 43])
    FOLLOW_parameter_in_parameter_list601 = frozenset([1, 14])
    FOLLOW_term_in_parameter625 = frozenset([1])
    FOLLOW_column_ref_in_parameter637 = frozenset([17])
    FOLLOW_EQUAL_in_parameter639 = frozenset([19, 25, 26, 43])
    FOLLOW_term_in_parameter641 = frozenset([1])
    FOLLOW_ID_in_column_ref668 = frozenset([1])
    FOLLOW_INT_in_column_ref687 = frozenset([1])
    FOLLOW_object_constant_in_term714 = frozenset([1])
    FOLLOW_variable_in_term722 = frozenset([1])
    FOLLOW_INT_in_object_constant739 = frozenset([1])
    FOLLOW_FLOAT_in_object_constant760 = frozenset([1])
    FOLLOW_STRING_in_object_constant779 = frozenset([1])
    FOLLOW_ID_in_variable806 = frozenset([1])
    FOLLOW_ID_in_relation_constant831 = frozenset([1, 40, 53])
    FOLLOW_53_in_relation_constant834 = frozenset([25])
    FOLLOW_ID_in_relation_constant836 = frozenset([1, 40, 53])
    FOLLOW_SIGN_in_relation_constant840 = frozenset([1])



def main(argv, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr):
    from antlr3.main import ParserMain
    main = ParserMain("CongressLexer", CongressParser)

    main.stdin = stdin
    main.stdout = stdout
    main.stderr = stderr
    main.execute(argv)



if __name__ == '__main__':
    main(sys.argv)
