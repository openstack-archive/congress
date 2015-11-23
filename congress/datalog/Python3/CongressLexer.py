# $ANTLR 3.5.2 Congress.g 2015-11-02 17:04:43

import sys
from antlr3 import *



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

class CongressLexer(Lexer):

    grammarFileName = "Congress.g"
    api_version = 1

    def __init__(self, input=None, state=None):
        if state is None:
            state = RecognizerSharedState()
        super().__init__(input, state)

        self.delegates = []

        self.dfa8 = self.DFA8(
            self, 8,
            eot = self.DFA8_eot,
            eof = self.DFA8_eof,
            min = self.DFA8_min,
            max = self.DFA8_max,
            accept = self.DFA8_accept,
            special = self.DFA8_special,
            transition = self.DFA8_transition
            )

        self.dfa23 = self.DFA23(
            self, 23,
            eot = self.DFA23_eot,
            eof = self.DFA23_eof,
            min = self.DFA23_min,
            max = self.DFA23_max,
            accept = self.DFA23_accept,
            special = self.DFA23_special,
            transition = self.DFA23_transition
            )

        self.dfa24 = self.DFA24(
            self, 24,
            eot = self.DFA24_eot,
            eof = self.DFA24_eof,
            min = self.DFA24_min,
            max = self.DFA24_max,
            accept = self.DFA24_accept,
            special = self.DFA24_special,
            transition = self.DFA24_transition
            )

        self.dfa38 = self.DFA38(
            self, 38,
            eot = self.DFA38_eot,
            eof = self.DFA38_eof,
            min = self.DFA38_min,
            max = self.DFA38_max,
            accept = self.DFA38_accept,
            special = self.DFA38_special,
            transition = self.DFA38_transition
            )






    # $ANTLR start "COLONMINUS"
    def mCOLONMINUS(self, ):
        try:
            _type = COLONMINUS
            _channel = DEFAULT_CHANNEL

            # Congress.g:7:12: ( ':-' )
            # Congress.g:7:14: ':-'
            pass 
            self.match(":-")




            self._state.type = _type
            self._state.channel = _channel
        finally:
            pass

    # $ANTLR end "COLONMINUS"



    # $ANTLR start "COMMA"
    def mCOMMA(self, ):
        try:
            _type = COMMA
            _channel = DEFAULT_CHANNEL

            # Congress.g:8:7: ( ',' )
            # Congress.g:8:9: ','
            pass 
            self.match(44)



            self._state.type = _type
            self._state.channel = _channel
        finally:
            pass

    # $ANTLR end "COMMA"



    # $ANTLR start "LBRACKET"
    def mLBRACKET(self, ):
        try:
            _type = LBRACKET
            _channel = DEFAULT_CHANNEL

            # Congress.g:9:10: ( '[' )
            # Congress.g:9:12: '['
            pass 
            self.match(91)



            self._state.type = _type
            self._state.channel = _channel
        finally:
            pass

    # $ANTLR end "LBRACKET"



    # $ANTLR start "LPAREN"
    def mLPAREN(self, ):
        try:
            _type = LPAREN
            _channel = DEFAULT_CHANNEL

            # Congress.g:10:8: ( '(' )
            # Congress.g:10:10: '('
            pass 
            self.match(40)



            self._state.type = _type
            self._state.channel = _channel
        finally:
            pass

    # $ANTLR end "LPAREN"



    # $ANTLR start "RBRACKET"
    def mRBRACKET(self, ):
        try:
            _type = RBRACKET
            _channel = DEFAULT_CHANNEL

            # Congress.g:11:10: ( ']' )
            # Congress.g:11:12: ']'
            pass 
            self.match(93)



            self._state.type = _type
            self._state.channel = _channel
        finally:
            pass

    # $ANTLR end "RBRACKET"



    # $ANTLR start "RPAREN"
    def mRPAREN(self, ):
        try:
            _type = RPAREN
            _channel = DEFAULT_CHANNEL

            # Congress.g:12:8: ( ')' )
            # Congress.g:12:10: ')'
            pass 
            self.match(41)



            self._state.type = _type
            self._state.channel = _channel
        finally:
            pass

    # $ANTLR end "RPAREN"



    # $ANTLR start "T__53"
    def mT__53(self, ):
        try:
            _type = T__53
            _channel = DEFAULT_CHANNEL

            # Congress.g:13:7: ( '.' )
            # Congress.g:13:9: '.'
            pass 
            self.match(46)



            self._state.type = _type
            self._state.channel = _channel
        finally:
            pass

    # $ANTLR end "T__53"



    # $ANTLR start "T__54"
    def mT__54(self, ):
        try:
            _type = T__54
            _channel = DEFAULT_CHANNEL

            # Congress.g:14:7: ( ':' )
            # Congress.g:14:9: ':'
            pass 
            self.match(58)



            self._state.type = _type
            self._state.channel = _channel
        finally:
            pass

    # $ANTLR end "T__54"



    # $ANTLR start "T__55"
    def mT__55(self, ):
        try:
            _type = T__55
            _channel = DEFAULT_CHANNEL

            # Congress.g:15:7: ( ';' )
            # Congress.g:15:9: ';'
            pass 
            self.match(59)



            self._state.type = _type
            self._state.channel = _channel
        finally:
            pass

    # $ANTLR end "T__55"



    # $ANTLR start "T__56"
    def mT__56(self, ):
        try:
            _type = T__56
            _channel = DEFAULT_CHANNEL

            # Congress.g:16:7: ( 'delete' )
            # Congress.g:16:9: 'delete'
            pass 
            self.match("delete")




            self._state.type = _type
            self._state.channel = _channel
        finally:
            pass

    # $ANTLR end "T__56"



    # $ANTLR start "T__57"
    def mT__57(self, ):
        try:
            _type = T__57
            _channel = DEFAULT_CHANNEL

            # Congress.g:17:7: ( 'execute' )
            # Congress.g:17:9: 'execute'
            pass 
            self.match("execute")




            self._state.type = _type
            self._state.channel = _channel
        finally:
            pass

    # $ANTLR end "T__57"



    # $ANTLR start "T__58"
    def mT__58(self, ):
        try:
            _type = T__58
            _channel = DEFAULT_CHANNEL

            # Congress.g:18:7: ( 'insert' )
            # Congress.g:18:9: 'insert'
            pass 
            self.match("insert")




            self._state.type = _type
            self._state.channel = _channel
        finally:
            pass

    # $ANTLR end "T__58"



    # $ANTLR start "NEGATION"
    def mNEGATION(self, ):
        try:
            _type = NEGATION
            _channel = DEFAULT_CHANNEL

            # Congress.g:167:5: ( 'not' | 'NOT' | '!' )
            alt1 = 3
            LA1 = self.input.LA(1)
            if LA1 in {110}:
                alt1 = 1
            elif LA1 in {78}:
                alt1 = 2
            elif LA1 in {33}:
                alt1 = 3
            else:
                nvae = NoViableAltException("", 1, 0, self.input)

                raise nvae


            if alt1 == 1:
                # Congress.g:167:7: 'not'
                pass 
                self.match("not")



            elif alt1 == 2:
                # Congress.g:168:7: 'NOT'
                pass 
                self.match("NOT")



            elif alt1 == 3:
                # Congress.g:169:7: '!'
                pass 
                self.match(33)


            self._state.type = _type
            self._state.channel = _channel
        finally:
            pass

    # $ANTLR end "NEGATION"



    # $ANTLR start "EQUAL"
    def mEQUAL(self, ):
        try:
            _type = EQUAL
            _channel = DEFAULT_CHANNEL

            # Congress.g:173:5: ( '=' )
            # Congress.g:173:8: '='
            pass 
            self.match(61)



            self._state.type = _type
            self._state.channel = _channel
        finally:
            pass

    # $ANTLR end "EQUAL"



    # $ANTLR start "SIGN"
    def mSIGN(self, ):
        try:
            _type = SIGN
            _channel = DEFAULT_CHANNEL

            # Congress.g:177:5: ( '+' | '-' )
            # Congress.g:
            pass 
            if self.input.LA(1) in {43, 45}:
                self.input.consume()
            else:
                mse = MismatchedSetException(None, self.input)
                self.recover(mse)
                raise mse





            self._state.type = _type
            self._state.channel = _channel
        finally:
            pass

    # $ANTLR end "SIGN"



    # $ANTLR start "INT"
    def mINT(self, ):
        try:
            _type = INT
            _channel = DEFAULT_CHANNEL

            # Congress.g:184:5: ( '1' .. '9' ( '0' .. '9' )* | ( '0' )+ | '0' ( 'o' | 'O' ) ( '0' .. '7' )+ | '0' ( 'x' | 'X' ) ( HEX_DIGIT )+ | '0' ( 'b' | 'B' ) ( '0' | '1' )+ )
            alt7 = 5
            LA7_0 = self.input.LA(1)

            if ((49 <= LA7_0 <= 57) or LA7_0 in {}) :
                alt7 = 1
            elif (LA7_0 == 48) :
                LA7 = self.input.LA(2)
                if LA7 in {79, 111}:
                    alt7 = 3
                elif LA7 in {88, 120}:
                    alt7 = 4
                elif LA7 in {66, 98}:
                    alt7 = 5
                else:
                    alt7 = 2

            else:
                nvae = NoViableAltException("", 7, 0, self.input)

                raise nvae


            if alt7 == 1:
                # Congress.g:184:7: '1' .. '9' ( '0' .. '9' )*
                pass 
                self.matchRange(49, 57)

                # Congress.g:184:16: ( '0' .. '9' )*
                while True: #loop2
                    alt2 = 2
                    LA2_0 = self.input.LA(1)

                    if ((48 <= LA2_0 <= 57) or LA2_0 in {}) :
                        alt2 = 1


                    if alt2 == 1:
                        # Congress.g:
                        pass 
                        if (48 <= self.input.LA(1) <= 57) or self.input.LA(1) in {}:
                            self.input.consume()
                        else:
                            mse = MismatchedSetException(None, self.input)
                            self.recover(mse)
                            raise mse




                    else:
                        break #loop2



            elif alt7 == 2:
                # Congress.g:185:7: ( '0' )+
                pass 
                # Congress.g:185:7: ( '0' )+
                cnt3 = 0
                while True: #loop3
                    alt3 = 2
                    LA3_0 = self.input.LA(1)

                    if (LA3_0 == 48) :
                        alt3 = 1


                    if alt3 == 1:
                        # Congress.g:185:7: '0'
                        pass 
                        self.match(48)


                    else:
                        if cnt3 >= 1:
                            break #loop3

                        eee = EarlyExitException(3, self.input)
                        raise eee

                    cnt3 += 1



            elif alt7 == 3:
                # Congress.g:186:7: '0' ( 'o' | 'O' ) ( '0' .. '7' )+
                pass 
                self.match(48)

                if self.input.LA(1) in {79, 111}:
                    self.input.consume()
                else:
                    mse = MismatchedSetException(None, self.input)
                    self.recover(mse)
                    raise mse



                # Congress.g:186:23: ( '0' .. '7' )+
                cnt4 = 0
                while True: #loop4
                    alt4 = 2
                    LA4_0 = self.input.LA(1)

                    if ((48 <= LA4_0 <= 55) or LA4_0 in {}) :
                        alt4 = 1


                    if alt4 == 1:
                        # Congress.g:
                        pass 
                        if (48 <= self.input.LA(1) <= 55) or self.input.LA(1) in {}:
                            self.input.consume()
                        else:
                            mse = MismatchedSetException(None, self.input)
                            self.recover(mse)
                            raise mse




                    else:
                        if cnt4 >= 1:
                            break #loop4

                        eee = EarlyExitException(4, self.input)
                        raise eee

                    cnt4 += 1



            elif alt7 == 4:
                # Congress.g:187:7: '0' ( 'x' | 'X' ) ( HEX_DIGIT )+
                pass 
                self.match(48)

                if self.input.LA(1) in {88, 120}:
                    self.input.consume()
                else:
                    mse = MismatchedSetException(None, self.input)
                    self.recover(mse)
                    raise mse



                # Congress.g:187:23: ( HEX_DIGIT )+
                cnt5 = 0
                while True: #loop5
                    alt5 = 2
                    LA5_0 = self.input.LA(1)

                    if ((48 <= LA5_0 <= 57) or (65 <= LA5_0 <= 70) or (97 <= LA5_0 <= 102) or LA5_0 in {}) :
                        alt5 = 1


                    if alt5 == 1:
                        # Congress.g:
                        pass 
                        if (48 <= self.input.LA(1) <= 57) or (65 <= self.input.LA(1) <= 70) or (97 <= self.input.LA(1) <= 102) or self.input.LA(1) in {}:
                            self.input.consume()
                        else:
                            mse = MismatchedSetException(None, self.input)
                            self.recover(mse)
                            raise mse




                    else:
                        if cnt5 >= 1:
                            break #loop5

                        eee = EarlyExitException(5, self.input)
                        raise eee

                    cnt5 += 1



            elif alt7 == 5:
                # Congress.g:188:7: '0' ( 'b' | 'B' ) ( '0' | '1' )+
                pass 
                self.match(48)

                if self.input.LA(1) in {66, 98}:
                    self.input.consume()
                else:
                    mse = MismatchedSetException(None, self.input)
                    self.recover(mse)
                    raise mse



                # Congress.g:188:23: ( '0' | '1' )+
                cnt6 = 0
                while True: #loop6
                    alt6 = 2
                    LA6_0 = self.input.LA(1)

                    if (LA6_0 in {48, 49}) :
                        alt6 = 1


                    if alt6 == 1:
                        # Congress.g:
                        pass 
                        if self.input.LA(1) in {48, 49}:
                            self.input.consume()
                        else:
                            mse = MismatchedSetException(None, self.input)
                            self.recover(mse)
                            raise mse




                    else:
                        if cnt6 >= 1:
                            break #loop6

                        eee = EarlyExitException(6, self.input)
                        raise eee

                    cnt6 += 1



            self._state.type = _type
            self._state.channel = _channel
        finally:
            pass

    # $ANTLR end "INT"



    # $ANTLR start "FLOAT"
    def mFLOAT(self, ):
        try:
            _type = FLOAT
            _channel = DEFAULT_CHANNEL

            # Congress.g:194:5: ( FLOAT_NO_EXP | FLOAT_EXP )
            alt8 = 2
            alt8 = self.dfa8.predict(self.input)
            if alt8 == 1:
                # Congress.g:194:7: FLOAT_NO_EXP
                pass 
                self.mFLOAT_NO_EXP()



            elif alt8 == 2:
                # Congress.g:195:7: FLOAT_EXP
                pass 
                self.mFLOAT_EXP()



            self._state.type = _type
            self._state.channel = _channel
        finally:
            pass

    # $ANTLR end "FLOAT"



    # $ANTLR start "STRING"
    def mSTRING(self, ):
        try:
            _type = STRING
            _channel = DEFAULT_CHANNEL

            # Congress.g:218:5: ( ( STRPREFIX )? ( SLSTRING )+ | ( BYTESTRPREFIX ) ( SLBYTESTRING )+ )
            alt12 = 2
            LA12 = self.input.LA(1)
            if LA12 in {114}:
                LA12_1 = self.input.LA(2)

                if (LA12_1 in {66, 98}) :
                    alt12 = 2
                elif (LA12_1 in {34, 39}) :
                    alt12 = 1
                else:
                    nvae = NoViableAltException("", 12, 1, self.input)

                    raise nvae


            elif LA12 in {34, 39, 85, 117}:
                alt12 = 1
            elif LA12 in {66, 98}:
                alt12 = 2
            elif LA12 in {82}:
                LA12_4 = self.input.LA(2)

                if (LA12_4 in {66, 98}) :
                    alt12 = 2
                elif (LA12_4 in {34, 39}) :
                    alt12 = 1
                else:
                    nvae = NoViableAltException("", 12, 4, self.input)

                    raise nvae


            else:
                nvae = NoViableAltException("", 12, 0, self.input)

                raise nvae


            if alt12 == 1:
                # Congress.g:218:7: ( STRPREFIX )? ( SLSTRING )+
                pass 
                # Congress.g:218:7: ( STRPREFIX )?
                alt9 = 2
                LA9_0 = self.input.LA(1)

                if (LA9_0 in {82, 85, 114, 117}) :
                    alt9 = 1
                if alt9 == 1:
                    # Congress.g:
                    pass 
                    if self.input.LA(1) in {82, 85, 114, 117}:
                        self.input.consume()
                    else:
                        mse = MismatchedSetException(None, self.input)
                        self.recover(mse)
                        raise mse






                # Congress.g:218:20: ( SLSTRING )+
                cnt10 = 0
                while True: #loop10
                    alt10 = 2
                    LA10_0 = self.input.LA(1)

                    if (LA10_0 in {34, 39}) :
                        alt10 = 1


                    if alt10 == 1:
                        # Congress.g:218:21: SLSTRING
                        pass 
                        self.mSLSTRING()



                    else:
                        if cnt10 >= 1:
                            break #loop10

                        eee = EarlyExitException(10, self.input)
                        raise eee

                    cnt10 += 1



            elif alt12 == 2:
                # Congress.g:219:7: ( BYTESTRPREFIX ) ( SLBYTESTRING )+
                pass 
                # Congress.g:219:7: ( BYTESTRPREFIX )
                # Congress.g:219:8: BYTESTRPREFIX
                pass 
                self.mBYTESTRPREFIX()





                # Congress.g:219:23: ( SLBYTESTRING )+
                cnt11 = 0
                while True: #loop11
                    alt11 = 2
                    LA11_0 = self.input.LA(1)

                    if (LA11_0 in {34, 39}) :
                        alt11 = 1


                    if alt11 == 1:
                        # Congress.g:219:24: SLBYTESTRING
                        pass 
                        self.mSLBYTESTRING()



                    else:
                        if cnt11 >= 1:
                            break #loop11

                        eee = EarlyExitException(11, self.input)
                        raise eee

                    cnt11 += 1



            self._state.type = _type
            self._state.channel = _channel
        finally:
            pass

    # $ANTLR end "STRING"



    # $ANTLR start "ID"
    def mID(self, ):
        try:
            _type = ID
            _channel = DEFAULT_CHANNEL

            # Congress.g:225:5: ( ( 'a' .. 'z' | 'A' .. 'Z' | '_' | '.' ) ( 'a' .. 'z' | 'A' .. 'Z' | '0' .. '9' | '_' | '.' )* )
            # Congress.g:225:7: ( 'a' .. 'z' | 'A' .. 'Z' | '_' | '.' ) ( 'a' .. 'z' | 'A' .. 'Z' | '0' .. '9' | '_' | '.' )*
            pass 
            if (65 <= self.input.LA(1) <= 90) or (97 <= self.input.LA(1) <= 122) or self.input.LA(1) in {46, 95}:
                self.input.consume()
            else:
                mse = MismatchedSetException(None, self.input)
                self.recover(mse)
                raise mse



            # Congress.g:225:35: ( 'a' .. 'z' | 'A' .. 'Z' | '0' .. '9' | '_' | '.' )*
            while True: #loop13
                alt13 = 2
                LA13_0 = self.input.LA(1)

                if ((48 <= LA13_0 <= 57) or (65 <= LA13_0 <= 90) or (97 <= LA13_0 <= 122) or LA13_0 in {46, 95}) :
                    alt13 = 1


                if alt13 == 1:
                    # Congress.g:
                    pass 
                    if (48 <= self.input.LA(1) <= 57) or (65 <= self.input.LA(1) <= 90) or (97 <= self.input.LA(1) <= 122) or self.input.LA(1) in {46, 95}:
                        self.input.consume()
                    else:
                        mse = MismatchedSetException(None, self.input)
                        self.recover(mse)
                        raise mse




                else:
                    break #loop13




            self._state.type = _type
            self._state.channel = _channel
        finally:
            pass

    # $ANTLR end "ID"



    # $ANTLR start "COMMENT"
    def mCOMMENT(self, ):
        try:
            _type = COMMENT
            _channel = DEFAULT_CHANNEL

            # Congress.g:230:5: ( '//' (~ ( '\\n' | '\\r' ) )* ( '\\r' )? '\\n' | '/*' ( options {greedy=false; } : . )* '*/' | '#' (~ ( '\\n' | '\\r' ) )* ( '\\r' )? '\\n' )
            alt19 = 3
            LA19_0 = self.input.LA(1)

            if (LA19_0 == 47) :
                LA19_1 = self.input.LA(2)

                if (LA19_1 == 47) :
                    alt19 = 1
                elif (LA19_1 == 42) :
                    alt19 = 2
                else:
                    nvae = NoViableAltException("", 19, 1, self.input)

                    raise nvae


            elif (LA19_0 == 35) :
                alt19 = 3
            else:
                nvae = NoViableAltException("", 19, 0, self.input)

                raise nvae


            if alt19 == 1:
                # Congress.g:230:7: '//' (~ ( '\\n' | '\\r' ) )* ( '\\r' )? '\\n'
                pass 
                self.match("//")


                # Congress.g:230:12: (~ ( '\\n' | '\\r' ) )*
                while True: #loop14
                    alt14 = 2
                    LA14_0 = self.input.LA(1)

                    if ((0 <= LA14_0 <= 9) or (14 <= LA14_0 <= 65535) or LA14_0 in {11, 12}) :
                        alt14 = 1


                    if alt14 == 1:
                        # Congress.g:
                        pass 
                        if (0 <= self.input.LA(1) <= 9) or (14 <= self.input.LA(1) <= 65535) or self.input.LA(1) in {11, 12}:
                            self.input.consume()
                        else:
                            mse = MismatchedSetException(None, self.input)
                            self.recover(mse)
                            raise mse




                    else:
                        break #loop14


                # Congress.g:230:26: ( '\\r' )?
                alt15 = 2
                LA15_0 = self.input.LA(1)

                if (LA15_0 == 13) :
                    alt15 = 1
                if alt15 == 1:
                    # Congress.g:230:26: '\\r'
                    pass 
                    self.match(13)




                self.match(10)

                #action start
                _channel=HIDDEN;
                #action end



            elif alt19 == 2:
                # Congress.g:231:7: '/*' ( options {greedy=false; } : . )* '*/'
                pass 
                self.match("/*")


                # Congress.g:231:12: ( options {greedy=false; } : . )*
                while True: #loop16
                    alt16 = 2
                    LA16_0 = self.input.LA(1)

                    if (LA16_0 == 42) :
                        LA16_1 = self.input.LA(2)

                        if (LA16_1 == 47) :
                            alt16 = 2
                        elif ((0 <= LA16_1 <= 46) or (48 <= LA16_1 <= 65535) or LA16_1 in {}) :
                            alt16 = 1


                    elif ((0 <= LA16_0 <= 41) or (43 <= LA16_0 <= 65535) or LA16_0 in {}) :
                        alt16 = 1


                    if alt16 == 1:
                        # Congress.g:231:40: .
                        pass 
                        self.matchAny()


                    else:
                        break #loop16


                self.match("*/")


                #action start
                _channel=HIDDEN;
                #action end



            elif alt19 == 3:
                # Congress.g:232:7: '#' (~ ( '\\n' | '\\r' ) )* ( '\\r' )? '\\n'
                pass 
                self.match(35)

                # Congress.g:232:11: (~ ( '\\n' | '\\r' ) )*
                while True: #loop17
                    alt17 = 2
                    LA17_0 = self.input.LA(1)

                    if ((0 <= LA17_0 <= 9) or (14 <= LA17_0 <= 65535) or LA17_0 in {11, 12}) :
                        alt17 = 1


                    if alt17 == 1:
                        # Congress.g:
                        pass 
                        if (0 <= self.input.LA(1) <= 9) or (14 <= self.input.LA(1) <= 65535) or self.input.LA(1) in {11, 12}:
                            self.input.consume()
                        else:
                            mse = MismatchedSetException(None, self.input)
                            self.recover(mse)
                            raise mse




                    else:
                        break #loop17


                # Congress.g:232:25: ( '\\r' )?
                alt18 = 2
                LA18_0 = self.input.LA(1)

                if (LA18_0 == 13) :
                    alt18 = 1
                if alt18 == 1:
                    # Congress.g:232:25: '\\r'
                    pass 
                    self.match(13)




                self.match(10)

                #action start
                _channel=HIDDEN;
                #action end



            self._state.type = _type
            self._state.channel = _channel
        finally:
            pass

    # $ANTLR end "COMMENT"



    # $ANTLR start "WS"
    def mWS(self, ):
        try:
            _type = WS
            _channel = DEFAULT_CHANNEL

            # Congress.g:236:5: ( ( ' ' | '\\t' | '\\r' | '\\n' ) )
            # Congress.g:236:7: ( ' ' | '\\t' | '\\r' | '\\n' )
            pass 
            if self.input.LA(1) in {9, 10, 13, 32}:
                self.input.consume()
            else:
                mse = MismatchedSetException(None, self.input)
                self.recover(mse)
                raise mse



            #action start
            _channel=HIDDEN;
            #action end




            self._state.type = _type
            self._state.channel = _channel
        finally:
            pass

    # $ANTLR end "WS"



    # $ANTLR start "EXPONENT"
    def mEXPONENT(self, ):
        try:
            # Congress.g:250:5: ( ( 'e' | 'E' ) ( '+' | '-' )? ( '0' .. '9' )+ )
            # Congress.g:250:7: ( 'e' | 'E' ) ( '+' | '-' )? ( '0' .. '9' )+
            pass 
            if self.input.LA(1) in {69, 101}:
                self.input.consume()
            else:
                mse = MismatchedSetException(None, self.input)
                self.recover(mse)
                raise mse



            # Congress.g:250:17: ( '+' | '-' )?
            alt20 = 2
            LA20_0 = self.input.LA(1)

            if (LA20_0 in {43, 45}) :
                alt20 = 1
            if alt20 == 1:
                # Congress.g:
                pass 
                if self.input.LA(1) in {43, 45}:
                    self.input.consume()
                else:
                    mse = MismatchedSetException(None, self.input)
                    self.recover(mse)
                    raise mse






            # Congress.g:250:28: ( '0' .. '9' )+
            cnt21 = 0
            while True: #loop21
                alt21 = 2
                LA21_0 = self.input.LA(1)

                if ((48 <= LA21_0 <= 57) or LA21_0 in {}) :
                    alt21 = 1


                if alt21 == 1:
                    # Congress.g:
                    pass 
                    if (48 <= self.input.LA(1) <= 57) or self.input.LA(1) in {}:
                        self.input.consume()
                    else:
                        mse = MismatchedSetException(None, self.input)
                        self.recover(mse)
                        raise mse




                else:
                    if cnt21 >= 1:
                        break #loop21

                    eee = EarlyExitException(21, self.input)
                    raise eee

                cnt21 += 1





        finally:
            pass

    # $ANTLR end "EXPONENT"



    # $ANTLR start "HEX_DIGIT"
    def mHEX_DIGIT(self, ):
        try:
            # Congress.g:255:5: ( ( '0' .. '9' | 'a' .. 'f' | 'A' .. 'F' ) )
            # Congress.g:
            pass 
            if (48 <= self.input.LA(1) <= 57) or (65 <= self.input.LA(1) <= 70) or (97 <= self.input.LA(1) <= 102) or self.input.LA(1) in {}:
                self.input.consume()
            else:
                mse = MismatchedSetException(None, self.input)
                self.recover(mse)
                raise mse






        finally:
            pass

    # $ANTLR end "HEX_DIGIT"



    # $ANTLR start "DIGIT"
    def mDIGIT(self, ):
        try:
            # Congress.g:260:5: ( ( '0' .. '9' ) )
            # Congress.g:
            pass 
            if (48 <= self.input.LA(1) <= 57) or self.input.LA(1) in {}:
                self.input.consume()
            else:
                mse = MismatchedSetException(None, self.input)
                self.recover(mse)
                raise mse






        finally:
            pass

    # $ANTLR end "DIGIT"



    # $ANTLR start "FLOAT_NO_EXP"
    def mFLOAT_NO_EXP(self, ):
        try:
            # Congress.g:265:5: ( ( INT_PART )? FRAC_PART | INT_PART '.' )
            alt23 = 2
            alt23 = self.dfa23.predict(self.input)
            if alt23 == 1:
                # Congress.g:265:7: ( INT_PART )? FRAC_PART
                pass 
                # Congress.g:265:7: ( INT_PART )?
                alt22 = 2
                LA22_0 = self.input.LA(1)

                if ((48 <= LA22_0 <= 57) or LA22_0 in {}) :
                    alt22 = 1
                if alt22 == 1:
                    # Congress.g:265:7: INT_PART
                    pass 
                    self.mINT_PART()





                self.mFRAC_PART()



            elif alt23 == 2:
                # Congress.g:266:7: INT_PART '.'
                pass 
                self.mINT_PART()


                self.match(46)



        finally:
            pass

    # $ANTLR end "FLOAT_NO_EXP"



    # $ANTLR start "FLOAT_EXP"
    def mFLOAT_EXP(self, ):
        try:
            # Congress.g:271:5: ( ( INT_PART | FLOAT_NO_EXP ) EXPONENT )
            # Congress.g:271:7: ( INT_PART | FLOAT_NO_EXP ) EXPONENT
            pass 
            # Congress.g:271:7: ( INT_PART | FLOAT_NO_EXP )
            alt24 = 2
            alt24 = self.dfa24.predict(self.input)
            if alt24 == 1:
                # Congress.g:271:9: INT_PART
                pass 
                self.mINT_PART()



            elif alt24 == 2:
                # Congress.g:271:20: FLOAT_NO_EXP
                pass 
                self.mFLOAT_NO_EXP()





            self.mEXPONENT()





        finally:
            pass

    # $ANTLR end "FLOAT_EXP"



    # $ANTLR start "INT_PART"
    def mINT_PART(self, ):
        try:
            # Congress.g:276:5: ( ( DIGIT )+ )
            # Congress.g:276:7: ( DIGIT )+
            pass 
            # Congress.g:276:7: ( DIGIT )+
            cnt25 = 0
            while True: #loop25
                alt25 = 2
                LA25_0 = self.input.LA(1)

                if ((48 <= LA25_0 <= 57) or LA25_0 in {}) :
                    alt25 = 1


                if alt25 == 1:
                    # Congress.g:
                    pass 
                    if (48 <= self.input.LA(1) <= 57) or self.input.LA(1) in {}:
                        self.input.consume()
                    else:
                        mse = MismatchedSetException(None, self.input)
                        self.recover(mse)
                        raise mse




                else:
                    if cnt25 >= 1:
                        break #loop25

                    eee = EarlyExitException(25, self.input)
                    raise eee

                cnt25 += 1





        finally:
            pass

    # $ANTLR end "INT_PART"



    # $ANTLR start "FRAC_PART"
    def mFRAC_PART(self, ):
        try:
            # Congress.g:281:5: ( '.' ( DIGIT )+ )
            # Congress.g:281:7: '.' ( DIGIT )+
            pass 
            self.match(46)

            # Congress.g:281:11: ( DIGIT )+
            cnt26 = 0
            while True: #loop26
                alt26 = 2
                LA26_0 = self.input.LA(1)

                if ((48 <= LA26_0 <= 57) or LA26_0 in {}) :
                    alt26 = 1


                if alt26 == 1:
                    # Congress.g:
                    pass 
                    if (48 <= self.input.LA(1) <= 57) or self.input.LA(1) in {}:
                        self.input.consume()
                    else:
                        mse = MismatchedSetException(None, self.input)
                        self.recover(mse)
                        raise mse




                else:
                    if cnt26 >= 1:
                        break #loop26

                    eee = EarlyExitException(26, self.input)
                    raise eee

                cnt26 += 1





        finally:
            pass

    # $ANTLR end "FRAC_PART"



    # $ANTLR start "STRPREFIX"
    def mSTRPREFIX(self, ):
        try:
            # Congress.g:289:5: ( 'r' | 'R' | 'u' | 'U' )
            # Congress.g:
            pass 
            if self.input.LA(1) in {82, 85, 114, 117}:
                self.input.consume()
            else:
                mse = MismatchedSetException(None, self.input)
                self.recover(mse)
                raise mse






        finally:
            pass

    # $ANTLR end "STRPREFIX"



    # $ANTLR start "STRING_ESC"
    def mSTRING_ESC(self, ):
        try:
            # Congress.g:294:5: ( '\\\\' . )
            # Congress.g:294:7: '\\\\' .
            pass 
            self.match(92)

            self.matchAny()




        finally:
            pass

    # $ANTLR end "STRING_ESC"



    # $ANTLR start "SLSTRING"
    def mSLSTRING(self, ):
        try:
            # Congress.g:301:5: ( '\\'' ( STRING_ESC |~ ( '\\\\' | '\\r' | '\\n' | '\\'' ) )* '\\'' | '\"' ( STRING_ESC |~ ( '\\\\' | '\\r' | '\\n' | '\"' ) )* '\"' | '\\'\\'\\'' ( STRING_ESC |~ ( '\\\\' ) )* '\\'\\'\\'' | '\"\"\"' ( STRING_ESC |~ ( '\\\\' ) )* '\"\"\"' )
            alt31 = 4
            LA31_0 = self.input.LA(1)

            if (LA31_0 == 39) :
                LA31_1 = self.input.LA(2)

                if (LA31_1 == 39) :
                    LA31_3 = self.input.LA(3)

                    if (LA31_3 == 39) :
                        alt31 = 3
                    else:
                        alt31 = 1

                elif ((0 <= LA31_1 <= 9) or (14 <= LA31_1 <= 38) or (40 <= LA31_1 <= 65535) or LA31_1 in {11, 12}) :
                    alt31 = 1
                else:
                    nvae = NoViableAltException("", 31, 1, self.input)

                    raise nvae


            elif (LA31_0 == 34) :
                LA31_2 = self.input.LA(2)

                if (LA31_2 == 34) :
                    LA31_5 = self.input.LA(3)

                    if (LA31_5 == 34) :
                        alt31 = 4
                    else:
                        alt31 = 2

                elif ((0 <= LA31_2 <= 9) or (14 <= LA31_2 <= 33) or (35 <= LA31_2 <= 65535) or LA31_2 in {11, 12}) :
                    alt31 = 2
                else:
                    nvae = NoViableAltException("", 31, 2, self.input)

                    raise nvae


            else:
                nvae = NoViableAltException("", 31, 0, self.input)

                raise nvae


            if alt31 == 1:
                # Congress.g:301:7: '\\'' ( STRING_ESC |~ ( '\\\\' | '\\r' | '\\n' | '\\'' ) )* '\\''
                pass 
                self.match(39)

                # Congress.g:301:12: ( STRING_ESC |~ ( '\\\\' | '\\r' | '\\n' | '\\'' ) )*
                while True: #loop27
                    alt27 = 3
                    LA27_0 = self.input.LA(1)

                    if (LA27_0 == 92) :
                        alt27 = 1
                    elif ((0 <= LA27_0 <= 9) or (14 <= LA27_0 <= 38) or (40 <= LA27_0 <= 91) or (93 <= LA27_0 <= 65535) or LA27_0 in {11, 12}) :
                        alt27 = 2


                    if alt27 == 1:
                        # Congress.g:301:13: STRING_ESC
                        pass 
                        self.mSTRING_ESC()



                    elif alt27 == 2:
                        # Congress.g:301:26: ~ ( '\\\\' | '\\r' | '\\n' | '\\'' )
                        pass 
                        if (0 <= self.input.LA(1) <= 9) or (14 <= self.input.LA(1) <= 38) or (40 <= self.input.LA(1) <= 91) or (93 <= self.input.LA(1) <= 65535) or self.input.LA(1) in {11, 12}:
                            self.input.consume()
                        else:
                            mse = MismatchedSetException(None, self.input)
                            self.recover(mse)
                            raise mse




                    else:
                        break #loop27


                self.match(39)


            elif alt31 == 2:
                # Congress.g:302:7: '\"' ( STRING_ESC |~ ( '\\\\' | '\\r' | '\\n' | '\"' ) )* '\"'
                pass 
                self.match(34)

                # Congress.g:302:11: ( STRING_ESC |~ ( '\\\\' | '\\r' | '\\n' | '\"' ) )*
                while True: #loop28
                    alt28 = 3
                    LA28_0 = self.input.LA(1)

                    if (LA28_0 == 92) :
                        alt28 = 1
                    elif ((0 <= LA28_0 <= 9) or (14 <= LA28_0 <= 33) or (35 <= LA28_0 <= 91) or (93 <= LA28_0 <= 65535) or LA28_0 in {11, 12}) :
                        alt28 = 2


                    if alt28 == 1:
                        # Congress.g:302:12: STRING_ESC
                        pass 
                        self.mSTRING_ESC()



                    elif alt28 == 2:
                        # Congress.g:302:25: ~ ( '\\\\' | '\\r' | '\\n' | '\"' )
                        pass 
                        if (0 <= self.input.LA(1) <= 9) or (14 <= self.input.LA(1) <= 33) or (35 <= self.input.LA(1) <= 91) or (93 <= self.input.LA(1) <= 65535) or self.input.LA(1) in {11, 12}:
                            self.input.consume()
                        else:
                            mse = MismatchedSetException(None, self.input)
                            self.recover(mse)
                            raise mse




                    else:
                        break #loop28


                self.match(34)


            elif alt31 == 3:
                # Congress.g:303:7: '\\'\\'\\'' ( STRING_ESC |~ ( '\\\\' ) )* '\\'\\'\\''
                pass 
                self.match("'''")


                # Congress.g:303:16: ( STRING_ESC |~ ( '\\\\' ) )*
                while True: #loop29
                    alt29 = 3
                    LA29_0 = self.input.LA(1)

                    if (LA29_0 == 39) :
                        LA29_1 = self.input.LA(2)

                        if (LA29_1 == 39) :
                            LA29_4 = self.input.LA(3)

                            if (LA29_4 == 39) :
                                LA29_5 = self.input.LA(4)

                                if ((0 <= LA29_5 <= 65535) or LA29_5 in {}) :
                                    alt29 = 2


                            elif ((0 <= LA29_4 <= 38) or (40 <= LA29_4 <= 65535) or LA29_4 in {}) :
                                alt29 = 2


                        elif ((0 <= LA29_1 <= 38) or (40 <= LA29_1 <= 65535) or LA29_1 in {}) :
                            alt29 = 2


                    elif (LA29_0 == 92) :
                        alt29 = 1
                    elif ((0 <= LA29_0 <= 38) or (40 <= LA29_0 <= 91) or (93 <= LA29_0 <= 65535) or LA29_0 in {}) :
                        alt29 = 2


                    if alt29 == 1:
                        # Congress.g:303:17: STRING_ESC
                        pass 
                        self.mSTRING_ESC()



                    elif alt29 == 2:
                        # Congress.g:303:30: ~ ( '\\\\' )
                        pass 
                        if (0 <= self.input.LA(1) <= 91) or (93 <= self.input.LA(1) <= 65535) or self.input.LA(1) in {}:
                            self.input.consume()
                        else:
                            mse = MismatchedSetException(None, self.input)
                            self.recover(mse)
                            raise mse




                    else:
                        break #loop29


                self.match("'''")



            elif alt31 == 4:
                # Congress.g:304:7: '\"\"\"' ( STRING_ESC |~ ( '\\\\' ) )* '\"\"\"'
                pass 
                self.match("\"\"\"")


                # Congress.g:304:13: ( STRING_ESC |~ ( '\\\\' ) )*
                while True: #loop30
                    alt30 = 3
                    LA30_0 = self.input.LA(1)

                    if (LA30_0 == 34) :
                        LA30_1 = self.input.LA(2)

                        if (LA30_1 == 34) :
                            LA30_4 = self.input.LA(3)

                            if (LA30_4 == 34) :
                                LA30_5 = self.input.LA(4)

                                if ((0 <= LA30_5 <= 65535) or LA30_5 in {}) :
                                    alt30 = 2


                            elif ((0 <= LA30_4 <= 33) or (35 <= LA30_4 <= 65535) or LA30_4 in {}) :
                                alt30 = 2


                        elif ((0 <= LA30_1 <= 33) or (35 <= LA30_1 <= 65535) or LA30_1 in {}) :
                            alt30 = 2


                    elif (LA30_0 == 92) :
                        alt30 = 1
                    elif ((0 <= LA30_0 <= 33) or (35 <= LA30_0 <= 91) or (93 <= LA30_0 <= 65535) or LA30_0 in {}) :
                        alt30 = 2


                    if alt30 == 1:
                        # Congress.g:304:14: STRING_ESC
                        pass 
                        self.mSTRING_ESC()



                    elif alt30 == 2:
                        # Congress.g:304:27: ~ ( '\\\\' )
                        pass 
                        if (0 <= self.input.LA(1) <= 91) or (93 <= self.input.LA(1) <= 65535) or self.input.LA(1) in {}:
                            self.input.consume()
                        else:
                            mse = MismatchedSetException(None, self.input)
                            self.recover(mse)
                            raise mse




                    else:
                        break #loop30


                self.match("\"\"\"")




        finally:
            pass

    # $ANTLR end "SLSTRING"



    # $ANTLR start "BYTESTRPREFIX"
    def mBYTESTRPREFIX(self, ):
        try:
            # Congress.g:315:5: ( 'b' | 'B' | 'br' | 'Br' | 'bR' | 'BR' | 'rb' | 'rB' | 'Rb' | 'RB' )
            alt32 = 10
            LA32 = self.input.LA(1)
            if LA32 in {98}:
                LA32 = self.input.LA(2)
                if LA32 in {114}:
                    alt32 = 3
                elif LA32 in {82}:
                    alt32 = 5
                else:
                    alt32 = 1

            elif LA32 in {66}:
                LA32 = self.input.LA(2)
                if LA32 in {114}:
                    alt32 = 4
                elif LA32 in {82}:
                    alt32 = 6
                else:
                    alt32 = 2

            elif LA32 in {114}:
                LA32_3 = self.input.LA(2)

                if (LA32_3 == 98) :
                    alt32 = 7
                elif (LA32_3 == 66) :
                    alt32 = 8
                else:
                    nvae = NoViableAltException("", 32, 3, self.input)

                    raise nvae


            elif LA32 in {82}:
                LA32_4 = self.input.LA(2)

                if (LA32_4 == 98) :
                    alt32 = 9
                elif (LA32_4 == 66) :
                    alt32 = 10
                else:
                    nvae = NoViableAltException("", 32, 4, self.input)

                    raise nvae


            else:
                nvae = NoViableAltException("", 32, 0, self.input)

                raise nvae


            if alt32 == 1:
                # Congress.g:315:7: 'b'
                pass 
                self.match(98)


            elif alt32 == 2:
                # Congress.g:315:13: 'B'
                pass 
                self.match(66)


            elif alt32 == 3:
                # Congress.g:315:19: 'br'
                pass 
                self.match("br")



            elif alt32 == 4:
                # Congress.g:315:26: 'Br'
                pass 
                self.match("Br")



            elif alt32 == 5:
                # Congress.g:315:33: 'bR'
                pass 
                self.match("bR")



            elif alt32 == 6:
                # Congress.g:315:40: 'BR'
                pass 
                self.match("BR")



            elif alt32 == 7:
                # Congress.g:315:47: 'rb'
                pass 
                self.match("rb")



            elif alt32 == 8:
                # Congress.g:315:54: 'rB'
                pass 
                self.match("rB")



            elif alt32 == 9:
                # Congress.g:315:61: 'Rb'
                pass 
                self.match("Rb")



            elif alt32 == 10:
                # Congress.g:315:68: 'RB'
                pass 
                self.match("RB")




        finally:
            pass

    # $ANTLR end "BYTESTRPREFIX"



    # $ANTLR start "SLBYTESTRING"
    def mSLBYTESTRING(self, ):
        try:
            # Congress.g:320:5: ( '\\'' ( BYTES_CHAR_SQ | BYTES_ESC )* '\\'' | '\"' ( BYTES_CHAR_DQ | BYTES_ESC )* '\"' | '\\'\\'\\'' ( BYTES_CHAR_SQ | BYTES_TESC )* '\\'\\'\\'' | '\"\"\"' ( BYTES_CHAR_DQ | BYTES_TESC )* '\"\"\"' )
            alt37 = 4
            LA37_0 = self.input.LA(1)

            if (LA37_0 == 39) :
                LA37_1 = self.input.LA(2)

                if (LA37_1 == 39) :
                    LA37_3 = self.input.LA(3)

                    if (LA37_3 == 39) :
                        alt37 = 3
                    else:
                        alt37 = 1

                elif ((0 <= LA37_1 <= 9) or (14 <= LA37_1 <= 38) or (40 <= LA37_1 <= 127) or LA37_1 in {11, 12}) :
                    alt37 = 1
                else:
                    nvae = NoViableAltException("", 37, 1, self.input)

                    raise nvae


            elif (LA37_0 == 34) :
                LA37_2 = self.input.LA(2)

                if (LA37_2 == 34) :
                    LA37_5 = self.input.LA(3)

                    if (LA37_5 == 34) :
                        alt37 = 4
                    else:
                        alt37 = 2

                elif ((0 <= LA37_2 <= 9) or (14 <= LA37_2 <= 33) or (35 <= LA37_2 <= 127) or LA37_2 in {11, 12}) :
                    alt37 = 2
                else:
                    nvae = NoViableAltException("", 37, 2, self.input)

                    raise nvae


            else:
                nvae = NoViableAltException("", 37, 0, self.input)

                raise nvae


            if alt37 == 1:
                # Congress.g:320:7: '\\'' ( BYTES_CHAR_SQ | BYTES_ESC )* '\\''
                pass 
                self.match(39)

                # Congress.g:320:12: ( BYTES_CHAR_SQ | BYTES_ESC )*
                while True: #loop33
                    alt33 = 3
                    LA33_0 = self.input.LA(1)

                    if ((0 <= LA33_0 <= 9) or (14 <= LA33_0 <= 38) or (40 <= LA33_0 <= 91) or (93 <= LA33_0 <= 127) or LA33_0 in {11, 12}) :
                        alt33 = 1
                    elif (LA33_0 == 92) :
                        alt33 = 2


                    if alt33 == 1:
                        # Congress.g:320:13: BYTES_CHAR_SQ
                        pass 
                        self.mBYTES_CHAR_SQ()



                    elif alt33 == 2:
                        # Congress.g:320:29: BYTES_ESC
                        pass 
                        self.mBYTES_ESC()



                    else:
                        break #loop33


                self.match(39)


            elif alt37 == 2:
                # Congress.g:321:7: '\"' ( BYTES_CHAR_DQ | BYTES_ESC )* '\"'
                pass 
                self.match(34)

                # Congress.g:321:11: ( BYTES_CHAR_DQ | BYTES_ESC )*
                while True: #loop34
                    alt34 = 3
                    LA34_0 = self.input.LA(1)

                    if ((0 <= LA34_0 <= 9) or (14 <= LA34_0 <= 33) or (35 <= LA34_0 <= 91) or (93 <= LA34_0 <= 127) or LA34_0 in {11, 12}) :
                        alt34 = 1
                    elif (LA34_0 == 92) :
                        alt34 = 2


                    if alt34 == 1:
                        # Congress.g:321:12: BYTES_CHAR_DQ
                        pass 
                        self.mBYTES_CHAR_DQ()



                    elif alt34 == 2:
                        # Congress.g:321:28: BYTES_ESC
                        pass 
                        self.mBYTES_ESC()



                    else:
                        break #loop34


                self.match(34)


            elif alt37 == 3:
                # Congress.g:322:7: '\\'\\'\\'' ( BYTES_CHAR_SQ | BYTES_TESC )* '\\'\\'\\''
                pass 
                self.match("'''")


                # Congress.g:322:16: ( BYTES_CHAR_SQ | BYTES_TESC )*
                while True: #loop35
                    alt35 = 2
                    LA35_0 = self.input.LA(1)

                    if (LA35_0 == 39) :
                        LA35_1 = self.input.LA(2)

                        if (LA35_1 == 39) :
                            LA35_3 = self.input.LA(3)

                            if (LA35_3 == 39) :
                                LA35_4 = self.input.LA(4)

                                if ((0 <= LA35_4 <= 91) or (93 <= LA35_4 <= 127) or LA35_4 in {}) :
                                    alt35 = 1


                            elif ((0 <= LA35_3 <= 38) or (40 <= LA35_3 <= 91) or (93 <= LA35_3 <= 127) or LA35_3 in {}) :
                                alt35 = 1


                        elif ((0 <= LA35_1 <= 38) or (40 <= LA35_1 <= 91) or (93 <= LA35_1 <= 127) or LA35_1 in {}) :
                            alt35 = 1


                    elif ((0 <= LA35_0 <= 38) or (40 <= LA35_0 <= 91) or (93 <= LA35_0 <= 127) or LA35_0 in {}) :
                        alt35 = 1


                    if alt35 == 1:
                        # Congress.g:
                        pass 
                        if (0 <= self.input.LA(1) <= 91) or (93 <= self.input.LA(1) <= 127) or self.input.LA(1) in {}:
                            self.input.consume()
                        else:
                            mse = MismatchedSetException(None, self.input)
                            self.recover(mse)
                            raise mse




                    else:
                        break #loop35


                self.match("'''")



            elif alt37 == 4:
                # Congress.g:323:7: '\"\"\"' ( BYTES_CHAR_DQ | BYTES_TESC )* '\"\"\"'
                pass 
                self.match("\"\"\"")


                # Congress.g:323:13: ( BYTES_CHAR_DQ | BYTES_TESC )*
                while True: #loop36
                    alt36 = 2
                    LA36_0 = self.input.LA(1)

                    if (LA36_0 == 34) :
                        LA36_1 = self.input.LA(2)

                        if (LA36_1 == 34) :
                            LA36_3 = self.input.LA(3)

                            if (LA36_3 == 34) :
                                LA36_4 = self.input.LA(4)

                                if ((0 <= LA36_4 <= 91) or (93 <= LA36_4 <= 127) or LA36_4 in {}) :
                                    alt36 = 1


                            elif ((0 <= LA36_3 <= 33) or (35 <= LA36_3 <= 91) or (93 <= LA36_3 <= 127) or LA36_3 in {}) :
                                alt36 = 1


                        elif ((0 <= LA36_1 <= 33) or (35 <= LA36_1 <= 91) or (93 <= LA36_1 <= 127) or LA36_1 in {}) :
                            alt36 = 1


                    elif ((0 <= LA36_0 <= 33) or (35 <= LA36_0 <= 91) or (93 <= LA36_0 <= 127) or LA36_0 in {}) :
                        alt36 = 1


                    if alt36 == 1:
                        # Congress.g:
                        pass 
                        if (0 <= self.input.LA(1) <= 91) or (93 <= self.input.LA(1) <= 127) or self.input.LA(1) in {}:
                            self.input.consume()
                        else:
                            mse = MismatchedSetException(None, self.input)
                            self.recover(mse)
                            raise mse




                    else:
                        break #loop36


                self.match("\"\"\"")




        finally:
            pass

    # $ANTLR end "SLBYTESTRING"



    # $ANTLR start "BYTES_CHAR_SQ"
    def mBYTES_CHAR_SQ(self, ):
        try:
            # Congress.g:328:5: ( '\\u0000' .. '\\u0009' | '\\u000B' .. '\\u000C' | '\\u000E' .. '\\u0026' | '\\u0028' .. '\\u005B' | '\\u005D' .. '\\u007F' )
            # Congress.g:
            pass 
            if (0 <= self.input.LA(1) <= 9) or (14 <= self.input.LA(1) <= 38) or (40 <= self.input.LA(1) <= 91) or (93 <= self.input.LA(1) <= 127) or self.input.LA(1) in {11, 12}:
                self.input.consume()
            else:
                mse = MismatchedSetException(None, self.input)
                self.recover(mse)
                raise mse






        finally:
            pass

    # $ANTLR end "BYTES_CHAR_SQ"



    # $ANTLR start "BYTES_CHAR_DQ"
    def mBYTES_CHAR_DQ(self, ):
        try:
            # Congress.g:337:5: ( '\\u0000' .. '\\u0009' | '\\u000B' .. '\\u000C' | '\\u000E' .. '\\u0021' | '\\u0023' .. '\\u005B' | '\\u005D' .. '\\u007F' )
            # Congress.g:
            pass 
            if (0 <= self.input.LA(1) <= 9) or (14 <= self.input.LA(1) <= 33) or (35 <= self.input.LA(1) <= 91) or (93 <= self.input.LA(1) <= 127) or self.input.LA(1) in {11, 12}:
                self.input.consume()
            else:
                mse = MismatchedSetException(None, self.input)
                self.recover(mse)
                raise mse






        finally:
            pass

    # $ANTLR end "BYTES_CHAR_DQ"



    # $ANTLR start "BYTES_ESC"
    def mBYTES_ESC(self, ):
        try:
            # Congress.g:346:5: ( '\\\\' '\\u0000' .. '\\u007F' )
            # Congress.g:346:7: '\\\\' '\\u0000' .. '\\u007F'
            pass 
            self.match(92)

            self.matchRange(0, 127)




        finally:
            pass

    # $ANTLR end "BYTES_ESC"



    # $ANTLR start "BYTES_TESC"
    def mBYTES_TESC(self, ):
        try:
            # Congress.g:352:5: ( '\\u0000' .. '\\u005B' | '\\u005D' .. '\\u007F' )
            # Congress.g:
            pass 
            if (0 <= self.input.LA(1) <= 91) or (93 <= self.input.LA(1) <= 127) or self.input.LA(1) in {}:
                self.input.consume()
            else:
                mse = MismatchedSetException(None, self.input)
                self.recover(mse)
                raise mse






        finally:
            pass

    # $ANTLR end "BYTES_TESC"



    def mTokens(self):
        # Congress.g:1:8: ( COLONMINUS | COMMA | LBRACKET | LPAREN | RBRACKET | RPAREN | T__53 | T__54 | T__55 | T__56 | T__57 | T__58 | NEGATION | EQUAL | SIGN | INT | FLOAT | STRING | ID | COMMENT | WS )
        alt38 = 21
        alt38 = self.dfa38.predict(self.input)
        if alt38 == 1:
            # Congress.g:1:10: COLONMINUS
            pass 
            self.mCOLONMINUS()



        elif alt38 == 2:
            # Congress.g:1:21: COMMA
            pass 
            self.mCOMMA()



        elif alt38 == 3:
            # Congress.g:1:27: LBRACKET
            pass 
            self.mLBRACKET()



        elif alt38 == 4:
            # Congress.g:1:36: LPAREN
            pass 
            self.mLPAREN()



        elif alt38 == 5:
            # Congress.g:1:43: RBRACKET
            pass 
            self.mRBRACKET()



        elif alt38 == 6:
            # Congress.g:1:52: RPAREN
            pass 
            self.mRPAREN()



        elif alt38 == 7:
            # Congress.g:1:59: T__53
            pass 
            self.mT__53()



        elif alt38 == 8:
            # Congress.g:1:65: T__54
            pass 
            self.mT__54()



        elif alt38 == 9:
            # Congress.g:1:71: T__55
            pass 
            self.mT__55()



        elif alt38 == 10:
            # Congress.g:1:77: T__56
            pass 
            self.mT__56()



        elif alt38 == 11:
            # Congress.g:1:83: T__57
            pass 
            self.mT__57()



        elif alt38 == 12:
            # Congress.g:1:89: T__58
            pass 
            self.mT__58()



        elif alt38 == 13:
            # Congress.g:1:95: NEGATION
            pass 
            self.mNEGATION()



        elif alt38 == 14:
            # Congress.g:1:104: EQUAL
            pass 
            self.mEQUAL()



        elif alt38 == 15:
            # Congress.g:1:110: SIGN
            pass 
            self.mSIGN()



        elif alt38 == 16:
            # Congress.g:1:115: INT
            pass 
            self.mINT()



        elif alt38 == 17:
            # Congress.g:1:119: FLOAT
            pass 
            self.mFLOAT()



        elif alt38 == 18:
            # Congress.g:1:125: STRING
            pass 
            self.mSTRING()



        elif alt38 == 19:
            # Congress.g:1:132: ID
            pass 
            self.mID()



        elif alt38 == 20:
            # Congress.g:1:135: COMMENT
            pass 
            self.mCOMMENT()



        elif alt38 == 21:
            # Congress.g:1:143: WS
            pass 
            self.mWS()








    # lookup tables for DFA #8

    DFA8_eot = DFA.unpack(
        "\3\uffff\1\6\1\uffff\1\6\1\uffff"
        )

    DFA8_eof = DFA.unpack(
        "\7\uffff"
        )

    DFA8_min = DFA.unpack(
        "\2\56\2\60\1\uffff\1\60\1\uffff"
        )

    DFA8_max = DFA.unpack(
        "\1\71\1\145\1\71\1\145\1\uffff\1\145\1\uffff"
        )

    DFA8_accept = DFA.unpack(
        "\4\uffff\1\2\1\uffff\1\1"
        )

    DFA8_special = DFA.unpack(
        "\7\uffff"
        )


    DFA8_transition = [
        DFA.unpack("\1\2\1\uffff\12\1"),
        DFA.unpack("\1\3\1\uffff\12\1\13\uffff\1\4\37\uffff\1\4"),
        DFA.unpack("\12\5"),
        DFA.unpack("\12\5\13\uffff\1\4\37\uffff\1\4"),
        DFA.unpack(""),
        DFA.unpack("\12\5\13\uffff\1\4\37\uffff\1\4"),
        DFA.unpack("")
    ]

    # class definition for DFA #8

    class DFA8(DFA):
        pass


    # lookup tables for DFA #23

    DFA23_eot = DFA.unpack(
        "\3\uffff\1\4\1\uffff"
        )

    DFA23_eof = DFA.unpack(
        "\5\uffff"
        )

    DFA23_min = DFA.unpack(
        "\2\56\1\uffff\1\60\1\uffff"
        )

    DFA23_max = DFA.unpack(
        "\2\71\1\uffff\1\71\1\uffff"
        )

    DFA23_accept = DFA.unpack(
        "\2\uffff\1\1\1\uffff\1\2"
        )

    DFA23_special = DFA.unpack(
        "\5\uffff"
        )


    DFA23_transition = [
        DFA.unpack("\1\2\1\uffff\12\1"),
        DFA.unpack("\1\3\1\uffff\12\1"),
        DFA.unpack(""),
        DFA.unpack("\12\2"),
        DFA.unpack("")
    ]

    # class definition for DFA #23

    class DFA23(DFA):
        pass


    # lookup tables for DFA #24

    DFA24_eot = DFA.unpack(
        "\4\uffff"
        )

    DFA24_eof = DFA.unpack(
        "\4\uffff"
        )

    DFA24_min = DFA.unpack(
        "\2\56\2\uffff"
        )

    DFA24_max = DFA.unpack(
        "\1\71\1\145\2\uffff"
        )

    DFA24_accept = DFA.unpack(
        "\2\uffff\1\2\1\1"
        )

    DFA24_special = DFA.unpack(
        "\4\uffff"
        )


    DFA24_transition = [
        DFA.unpack("\1\2\1\uffff\12\1"),
        DFA.unpack("\1\2\1\uffff\12\1\13\uffff\1\3\37\uffff\1\3"),
        DFA.unpack(""),
        DFA.unpack("")
    ]

    # class definition for DFA #24

    class DFA24(DFA):
        pass


    # lookup tables for DFA #38

    DFA38_eot = DFA.unpack(
        "\1\uffff\1\35\5\uffff\1\36\1\uffff\5\31\3\uffff\2\46\1\31\1\uffff"
        "\4\31\6\uffff\1\47\5\31\1\46\2\uffff\1\46\14\31\2\16\1\47\6\31\1"
        "\101\1\31\1\103\1\uffff\1\104\2\uffff"
        )

    DFA38_eof = DFA.unpack(
        "\105\uffff"
        )

    DFA38_min = DFA.unpack(
        "\1\11\1\55\5\uffff\1\56\1\uffff\1\145\1\170\1\156\1\157\1\117\3"
        "\uffff\2\56\1\42\1\uffff\4\42\6\uffff\1\56\1\154\1\145\1\163\1\164"
        "\1\124\1\56\2\uffff\1\56\10\42\1\53\1\145\1\143\1\145\3\56\1\164"
        "\1\165\1\162\1\145\2\164\1\56\1\145\1\56\1\uffff\1\56\2\uffff"
        )

    DFA38_max = DFA.unpack(
        "\1\172\1\55\5\uffff\1\172\1\uffff\1\145\1\170\1\156\1\157\1\117"
        "\3\uffff\2\145\1\142\1\uffff\2\162\1\142\1\47\6\uffff\1\172\1\154"
        "\1\145\1\163\1\164\1\124\1\145\2\uffff\1\145\10\47\1\71\1\145\1"
        "\143\1\145\3\172\1\164\1\165\1\162\1\145\2\164\1\172\1\145\1\172"
        "\1\uffff\1\172\2\uffff"
        )

    DFA38_accept = DFA.unpack(
        "\2\uffff\1\2\1\3\1\4\1\5\1\6\1\uffff\1\11\5\uffff\1\15\1\16\1\17"
        "\3\uffff\1\22\4\uffff\1\23\1\24\1\25\1\1\1\10\1\7\7\uffff\1\20\1"
        "\21\31\uffff\1\12\1\uffff\1\14\1\13"
        )

    DFA38_special = DFA.unpack(
        "\105\uffff"
        )


    DFA38_transition = [
        DFA.unpack("\2\33\2\uffff\1\33\22\uffff\1\33\1\16\1\24\1\32\3\uffff"
        "\1\24\1\4\1\6\1\uffff\1\20\1\2\1\20\1\7\1\32\1\22\11\21\1\1\1\10"
        "\1\uffff\1\17\3\uffff\1\31\1\26\13\31\1\15\3\31\1\27\2\31\1\30\5"
        "\31\1\3\1\uffff\1\5\1\uffff\1\31\1\uffff\1\31\1\25\1\31\1\11\1\12"
        "\3\31\1\13\4\31\1\14\3\31\1\23\2\31\1\30\5\31"),
        DFA.unpack("\1\34"),
        DFA.unpack(""),
        DFA.unpack(""),
        DFA.unpack(""),
        DFA.unpack(""),
        DFA.unpack(""),
        DFA.unpack("\1\31\1\uffff\12\37\7\uffff\32\31\4\uffff\1\31\1\uffff"
        "\32\31"),
        DFA.unpack(""),
        DFA.unpack("\1\40"),
        DFA.unpack("\1\41"),
        DFA.unpack("\1\42"),
        DFA.unpack("\1\43"),
        DFA.unpack("\1\44"),
        DFA.unpack(""),
        DFA.unpack(""),
        DFA.unpack(""),
        DFA.unpack("\1\47\1\uffff\12\45\13\uffff\1\47\37\uffff\1\47"),
        DFA.unpack("\1\47\1\uffff\1\50\11\47\13\uffff\1\47\37\uffff\1\47"),
        DFA.unpack("\1\24\4\uffff\1\24\32\uffff\1\52\37\uffff\1\51"),
        DFA.unpack(""),
        DFA.unpack("\1\24\4\uffff\1\24\52\uffff\1\54\37\uffff\1\53"),
        DFA.unpack("\1\24\4\uffff\1\24\52\uffff\1\56\37\uffff\1\55"),
        DFA.unpack("\1\24\4\uffff\1\24\32\uffff\1\60\37\uffff\1\57"),
        DFA.unpack("\1\24\4\uffff\1\24"),
        DFA.unpack(""),
        DFA.unpack(""),
        DFA.unpack(""),
        DFA.unpack(""),
        DFA.unpack(""),
        DFA.unpack(""),
        DFA.unpack("\1\31\1\uffff\12\37\7\uffff\4\31\1\61\25\31\4\uffff"
        "\1\31\1\uffff\4\31\1\61\25\31"),
        DFA.unpack("\1\62"),
        DFA.unpack("\1\63"),
        DFA.unpack("\1\64"),
        DFA.unpack("\1\65"),
        DFA.unpack("\1\66"),
        DFA.unpack("\1\47\1\uffff\12\45\13\uffff\1\47\37\uffff\1\47"),
        DFA.unpack(""),
        DFA.unpack(""),
        DFA.unpack("\1\47\1\uffff\1\50\11\47\13\uffff\1\47\37\uffff\1\47"),
        DFA.unpack("\1\24\4\uffff\1\24"),
        DFA.unpack("\1\24\4\uffff\1\24"),
        DFA.unpack("\1\24\4\uffff\1\24"),
        DFA.unpack("\1\24\4\uffff\1\24"),
        DFA.unpack("\1\24\4\uffff\1\24"),
        DFA.unpack("\1\24\4\uffff\1\24"),
        DFA.unpack("\1\24\4\uffff\1\24"),
        DFA.unpack("\1\24\4\uffff\1\24"),
        DFA.unpack("\1\47\1\uffff\1\47\2\uffff\12\67"),
        DFA.unpack("\1\70"),
        DFA.unpack("\1\71"),
        DFA.unpack("\1\72"),
        DFA.unpack("\1\31\1\uffff\12\31\7\uffff\32\31\4\uffff\1\31\1\uffff"
        "\32\31"),
        DFA.unpack("\1\31\1\uffff\12\31\7\uffff\32\31\4\uffff\1\31\1\uffff"
        "\32\31"),
        DFA.unpack("\1\31\1\uffff\12\67\7\uffff\32\31\4\uffff\1\31\1\uffff"
        "\32\31"),
        DFA.unpack("\1\73"),
        DFA.unpack("\1\74"),
        DFA.unpack("\1\75"),
        DFA.unpack("\1\76"),
        DFA.unpack("\1\77"),
        DFA.unpack("\1\100"),
        DFA.unpack("\1\31\1\uffff\12\31\7\uffff\32\31\4\uffff\1\31\1\uffff"
        "\32\31"),
        DFA.unpack("\1\102"),
        DFA.unpack("\1\31\1\uffff\12\31\7\uffff\32\31\4\uffff\1\31\1\uffff"
        "\32\31"),
        DFA.unpack(""),
        DFA.unpack("\1\31\1\uffff\12\31\7\uffff\32\31\4\uffff\1\31\1\uffff"
        "\32\31"),
        DFA.unpack(""),
        DFA.unpack("")
    ]

    # class definition for DFA #38

    class DFA38(DFA):
        pass


 



def main(argv, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr):
    from antlr3.main import LexerMain
    main = LexerMain(CongressLexer)

    main.stdin = stdin
    main.stdout = stdout
    main.stderr = stderr
    main.execute(argv)



if __name__ == '__main__':
    main(sys.argv)
