# $ANTLR 3.5 C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g 2015-04-22 14:17:24

import sys
from antlr3 import *
from antlr3.compat import set, frozenset



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


class CongressLexer(Lexer):

    grammarFileName = "C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g"
    api_version = 1

    def __init__(self, input=None, state=None):
        if state is None:
            state = RecognizerSharedState()
        super(CongressLexer, self).__init__(input, state)

        self.delegates = []

        self.dfa10 = self.DFA10(
            self, 10,
            eot = self.DFA10_eot,
            eof = self.DFA10_eof,
            min = self.DFA10_min,
            max = self.DFA10_max,
            accept = self.DFA10_accept,
            special = self.DFA10_special,
            transition = self.DFA10_transition
            )

        self.dfa25 = self.DFA25(
            self, 25,
            eot = self.DFA25_eot,
            eof = self.DFA25_eof,
            min = self.DFA25_min,
            max = self.DFA25_max,
            accept = self.DFA25_accept,
            special = self.DFA25_special,
            transition = self.DFA25_transition
            )

        self.dfa26 = self.DFA26(
            self, 26,
            eot = self.DFA26_eot,
            eof = self.DFA26_eof,
            min = self.DFA26_min,
            max = self.DFA26_max,
            accept = self.DFA26_accept,
            special = self.DFA26_special,
            transition = self.DFA26_transition
            )

        self.dfa40 = self.DFA40(
            self, 40,
            eot = self.DFA40_eot,
            eof = self.DFA40_eof,
            min = self.DFA40_min,
            max = self.DFA40_max,
            accept = self.DFA40_accept,
            special = self.DFA40_special,
            transition = self.DFA40_transition
            )






    # $ANTLR start "COLONMINUS"
    def mCOLONMINUS(self, ):
        try:
            _type = COLONMINUS
            _channel = DEFAULT_CHANNEL

            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:7:12: ( ':-' )
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:7:14: ':-'
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

            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:8:7: ( ',' )
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:8:9: ','
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

            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:9:10: ( '[' )
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:9:12: '['
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

            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:10:8: ( '(' )
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:10:10: '('
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

            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:11:10: ( ']' )
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:11:12: ']'
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

            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:12:8: ( ')' )
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:12:10: ')'
            pass 
            self.match(41)



            self._state.type = _type
            self._state.channel = _channel
        finally:
            pass

    # $ANTLR end "RPAREN"



    # $ANTLR start "T__54"
    def mT__54(self, ):
        try:
            _type = T__54
            _channel = DEFAULT_CHANNEL

            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:13:7: ( '.' )
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:13:9: '.'
            pass 
            self.match(46)



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

            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:14:7: ( ':' )
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:14:9: ':'
            pass 
            self.match(58)



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

            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:15:7: ( ';' )
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:15:9: ';'
            pass 
            self.match(59)



            self._state.type = _type
            self._state.channel = _channel
        finally:
            pass

    # $ANTLR end "T__56"



    # $ANTLR start "NEGATION"
    def mNEGATION(self, ):
        try:
            _type = NEGATION
            _channel = DEFAULT_CHANNEL

            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:162:5: ( 'not' | 'NOT' | '!' )
            alt1 = 3
            LA1 = self.input.LA(1)
            if LA1 == 110:
                alt1 = 1
            elif LA1 == 78:
                alt1 = 2
            elif LA1 == 33:
                alt1 = 3
            else:
                nvae = NoViableAltException("", 1, 0, self.input)

                raise nvae


            if alt1 == 1:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:162:7: 'not'
                pass 
                self.match("not")



            elif alt1 == 2:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:163:7: 'NOT'
                pass 
                self.match("NOT")



            elif alt1 == 3:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:164:7: '!'
                pass 
                self.match(33)


            self._state.type = _type
            self._state.channel = _channel
        finally:
            pass

    # $ANTLR end "NEGATION"



    # $ANTLR start "INSERT"
    def mINSERT(self, ):
        try:
            _type = INSERT
            _channel = DEFAULT_CHANNEL

            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:168:5: ( 'INSERT' | 'insert' )
            alt2 = 2
            LA2_0 = self.input.LA(1)

            if (LA2_0 == 73) :
                alt2 = 1
            elif (LA2_0 == 105) :
                alt2 = 2
            else:
                nvae = NoViableAltException("", 2, 0, self.input)

                raise nvae


            if alt2 == 1:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:168:7: 'INSERT'
                pass 
                self.match("INSERT")



            elif alt2 == 2:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:169:7: 'insert'
                pass 
                self.match("insert")



            self._state.type = _type
            self._state.channel = _channel
        finally:
            pass

    # $ANTLR end "INSERT"



    # $ANTLR start "DELETE"
    def mDELETE(self, ):
        try:
            _type = DELETE
            _channel = DEFAULT_CHANNEL

            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:173:5: ( 'DELETE' | 'delete' )
            alt3 = 2
            LA3_0 = self.input.LA(1)

            if (LA3_0 == 68) :
                alt3 = 1
            elif (LA3_0 == 100) :
                alt3 = 2
            else:
                nvae = NoViableAltException("", 3, 0, self.input)

                raise nvae


            if alt3 == 1:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:173:7: 'DELETE'
                pass 
                self.match("DELETE")



            elif alt3 == 2:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:174:7: 'delete'
                pass 
                self.match("delete")



            self._state.type = _type
            self._state.channel = _channel
        finally:
            pass

    # $ANTLR end "DELETE"



    # $ANTLR start "EQUAL"
    def mEQUAL(self, ):
        try:
            _type = EQUAL
            _channel = DEFAULT_CHANNEL

            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:178:5: ( '=' )
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:178:8: '='
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

            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:182:5: ( '+' | '-' )
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:
            pass 
            if self.input.LA(1) == 43 or self.input.LA(1) == 45:
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

            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:189:5: ( '1' .. '9' ( '0' .. '9' )* | ( '0' )+ | '0' ( 'o' | 'O' ) ( '0' .. '7' )+ | '0' ( 'x' | 'X' ) ( HEX_DIGIT )+ | '0' ( 'b' | 'B' ) ( '0' | '1' )+ )
            alt9 = 5
            LA9_0 = self.input.LA(1)

            if ((49 <= LA9_0 <= 57)) :
                alt9 = 1
            elif (LA9_0 == 48) :
                LA9 = self.input.LA(2)
                if LA9 == 79 or LA9 == 111:
                    alt9 = 3
                elif LA9 == 88 or LA9 == 120:
                    alt9 = 4
                elif LA9 == 66 or LA9 == 98:
                    alt9 = 5
                else:
                    alt9 = 2

            else:
                nvae = NoViableAltException("", 9, 0, self.input)

                raise nvae


            if alt9 == 1:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:189:7: '1' .. '9' ( '0' .. '9' )*
                pass 
                self.matchRange(49, 57)

                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:189:16: ( '0' .. '9' )*
                while True: #loop4
                    alt4 = 2
                    LA4_0 = self.input.LA(1)

                    if ((48 <= LA4_0 <= 57)) :
                        alt4 = 1


                    if alt4 == 1:
                        # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:
                        pass 
                        if (48 <= self.input.LA(1) <= 57):
                            self.input.consume()
                        else:
                            mse = MismatchedSetException(None, self.input)
                            self.recover(mse)
                            raise mse




                    else:
                        break #loop4



            elif alt9 == 2:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:190:7: ( '0' )+
                pass 
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:190:7: ( '0' )+
                cnt5 = 0
                while True: #loop5
                    alt5 = 2
                    LA5_0 = self.input.LA(1)

                    if (LA5_0 == 48) :
                        alt5 = 1


                    if alt5 == 1:
                        # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:190:7: '0'
                        pass 
                        self.match(48)


                    else:
                        if cnt5 >= 1:
                            break #loop5

                        eee = EarlyExitException(5, self.input)
                        raise eee

                    cnt5 += 1



            elif alt9 == 3:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:191:7: '0' ( 'o' | 'O' ) ( '0' .. '7' )+
                pass 
                self.match(48)

                if self.input.LA(1) == 79 or self.input.LA(1) == 111:
                    self.input.consume()
                else:
                    mse = MismatchedSetException(None, self.input)
                    self.recover(mse)
                    raise mse



                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:191:23: ( '0' .. '7' )+
                cnt6 = 0
                while True: #loop6
                    alt6 = 2
                    LA6_0 = self.input.LA(1)

                    if ((48 <= LA6_0 <= 55)) :
                        alt6 = 1


                    if alt6 == 1:
                        # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:
                        pass 
                        if (48 <= self.input.LA(1) <= 55):
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



            elif alt9 == 4:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:192:7: '0' ( 'x' | 'X' ) ( HEX_DIGIT )+
                pass 
                self.match(48)

                if self.input.LA(1) == 88 or self.input.LA(1) == 120:
                    self.input.consume()
                else:
                    mse = MismatchedSetException(None, self.input)
                    self.recover(mse)
                    raise mse



                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:192:23: ( HEX_DIGIT )+
                cnt7 = 0
                while True: #loop7
                    alt7 = 2
                    LA7_0 = self.input.LA(1)

                    if ((48 <= LA7_0 <= 57) or (65 <= LA7_0 <= 70) or (97 <= LA7_0 <= 102)) :
                        alt7 = 1


                    if alt7 == 1:
                        # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:
                        pass 
                        if (48 <= self.input.LA(1) <= 57) or (65 <= self.input.LA(1) <= 70) or (97 <= self.input.LA(1) <= 102):
                            self.input.consume()
                        else:
                            mse = MismatchedSetException(None, self.input)
                            self.recover(mse)
                            raise mse




                    else:
                        if cnt7 >= 1:
                            break #loop7

                        eee = EarlyExitException(7, self.input)
                        raise eee

                    cnt7 += 1



            elif alt9 == 5:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:193:7: '0' ( 'b' | 'B' ) ( '0' | '1' )+
                pass 
                self.match(48)

                if self.input.LA(1) == 66 or self.input.LA(1) == 98:
                    self.input.consume()
                else:
                    mse = MismatchedSetException(None, self.input)
                    self.recover(mse)
                    raise mse



                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:193:23: ( '0' | '1' )+
                cnt8 = 0
                while True: #loop8
                    alt8 = 2
                    LA8_0 = self.input.LA(1)

                    if ((48 <= LA8_0 <= 49)) :
                        alt8 = 1


                    if alt8 == 1:
                        # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:
                        pass 
                        if (48 <= self.input.LA(1) <= 49):
                            self.input.consume()
                        else:
                            mse = MismatchedSetException(None, self.input)
                            self.recover(mse)
                            raise mse




                    else:
                        if cnt8 >= 1:
                            break #loop8

                        eee = EarlyExitException(8, self.input)
                        raise eee

                    cnt8 += 1



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

            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:199:5: ( FLOAT_NO_EXP | FLOAT_EXP )
            alt10 = 2
            alt10 = self.dfa10.predict(self.input)
            if alt10 == 1:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:199:7: FLOAT_NO_EXP
                pass 
                self.mFLOAT_NO_EXP()



            elif alt10 == 2:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:200:7: FLOAT_EXP
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

            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:223:5: ( ( STRPREFIX )? ( SLSTRING )+ | ( BYTESTRPREFIX ) ( SLBYTESTRING )+ )
            alt14 = 2
            LA14 = self.input.LA(1)
            if LA14 == 114:
                LA14_1 = self.input.LA(2)

                if (LA14_1 == 66 or LA14_1 == 98) :
                    alt14 = 2
                elif (LA14_1 == 34 or LA14_1 == 39) :
                    alt14 = 1
                else:
                    nvae = NoViableAltException("", 14, 1, self.input)

                    raise nvae


            elif LA14 == 34 or LA14 == 39 or LA14 == 85 or LA14 == 117:
                alt14 = 1
            elif LA14 == 66 or LA14 == 98:
                alt14 = 2
            elif LA14 == 82:
                LA14_4 = self.input.LA(2)

                if (LA14_4 == 66 or LA14_4 == 98) :
                    alt14 = 2
                elif (LA14_4 == 34 or LA14_4 == 39) :
                    alt14 = 1
                else:
                    nvae = NoViableAltException("", 14, 4, self.input)

                    raise nvae


            else:
                nvae = NoViableAltException("", 14, 0, self.input)

                raise nvae


            if alt14 == 1:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:223:7: ( STRPREFIX )? ( SLSTRING )+
                pass 
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:223:7: ( STRPREFIX )?
                alt11 = 2
                LA11_0 = self.input.LA(1)

                if (LA11_0 == 82 or LA11_0 == 85 or LA11_0 == 114 or LA11_0 == 117) :
                    alt11 = 1
                if alt11 == 1:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:
                    pass 
                    if self.input.LA(1) == 82 or self.input.LA(1) == 85 or self.input.LA(1) == 114 or self.input.LA(1) == 117:
                        self.input.consume()
                    else:
                        mse = MismatchedSetException(None, self.input)
                        self.recover(mse)
                        raise mse






                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:223:20: ( SLSTRING )+
                cnt12 = 0
                while True: #loop12
                    alt12 = 2
                    LA12_0 = self.input.LA(1)

                    if (LA12_0 == 34 or LA12_0 == 39) :
                        alt12 = 1


                    if alt12 == 1:
                        # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:223:21: SLSTRING
                        pass 
                        self.mSLSTRING()



                    else:
                        if cnt12 >= 1:
                            break #loop12

                        eee = EarlyExitException(12, self.input)
                        raise eee

                    cnt12 += 1



            elif alt14 == 2:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:224:7: ( BYTESTRPREFIX ) ( SLBYTESTRING )+
                pass 
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:224:7: ( BYTESTRPREFIX )
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:224:8: BYTESTRPREFIX
                pass 
                self.mBYTESTRPREFIX()





                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:224:23: ( SLBYTESTRING )+
                cnt13 = 0
                while True: #loop13
                    alt13 = 2
                    LA13_0 = self.input.LA(1)

                    if (LA13_0 == 34 or LA13_0 == 39) :
                        alt13 = 1


                    if alt13 == 1:
                        # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:224:24: SLBYTESTRING
                        pass 
                        self.mSLBYTESTRING()



                    else:
                        if cnt13 >= 1:
                            break #loop13

                        eee = EarlyExitException(13, self.input)
                        raise eee

                    cnt13 += 1



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

            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:230:5: ( ( 'a' .. 'z' | 'A' .. 'Z' | '_' | '.' ) ( 'a' .. 'z' | 'A' .. 'Z' | '0' .. '9' | '_' | '.' )* )
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:230:7: ( 'a' .. 'z' | 'A' .. 'Z' | '_' | '.' ) ( 'a' .. 'z' | 'A' .. 'Z' | '0' .. '9' | '_' | '.' )*
            pass 
            if self.input.LA(1) == 46 or (65 <= self.input.LA(1) <= 90) or self.input.LA(1) == 95 or (97 <= self.input.LA(1) <= 122):
                self.input.consume()
            else:
                mse = MismatchedSetException(None, self.input)
                self.recover(mse)
                raise mse



            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:230:35: ( 'a' .. 'z' | 'A' .. 'Z' | '0' .. '9' | '_' | '.' )*
            while True: #loop15
                alt15 = 2
                LA15_0 = self.input.LA(1)

                if (LA15_0 == 46 or (48 <= LA15_0 <= 57) or (65 <= LA15_0 <= 90) or LA15_0 == 95 or (97 <= LA15_0 <= 122)) :
                    alt15 = 1


                if alt15 == 1:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:
                    pass 
                    if self.input.LA(1) == 46 or (48 <= self.input.LA(1) <= 57) or (65 <= self.input.LA(1) <= 90) or self.input.LA(1) == 95 or (97 <= self.input.LA(1) <= 122):
                        self.input.consume()
                    else:
                        mse = MismatchedSetException(None, self.input)
                        self.recover(mse)
                        raise mse




                else:
                    break #loop15




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

            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:235:5: ( '//' (~ ( '\\n' | '\\r' ) )* ( '\\r' )? '\\n' | '/*' ( options {greedy=false; } : . )* '*/' | '#' (~ ( '\\n' | '\\r' ) )* ( '\\r' )? '\\n' )
            alt21 = 3
            LA21_0 = self.input.LA(1)

            if (LA21_0 == 47) :
                LA21_1 = self.input.LA(2)

                if (LA21_1 == 47) :
                    alt21 = 1
                elif (LA21_1 == 42) :
                    alt21 = 2
                else:
                    nvae = NoViableAltException("", 21, 1, self.input)

                    raise nvae


            elif (LA21_0 == 35) :
                alt21 = 3
            else:
                nvae = NoViableAltException("", 21, 0, self.input)

                raise nvae


            if alt21 == 1:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:235:7: '//' (~ ( '\\n' | '\\r' ) )* ( '\\r' )? '\\n'
                pass 
                self.match("//")


                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:235:12: (~ ( '\\n' | '\\r' ) )*
                while True: #loop16
                    alt16 = 2
                    LA16_0 = self.input.LA(1)

                    if ((0 <= LA16_0 <= 9) or (11 <= LA16_0 <= 12) or (14 <= LA16_0 <= 65535)) :
                        alt16 = 1


                    if alt16 == 1:
                        # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:
                        pass 
                        if (0 <= self.input.LA(1) <= 9) or (11 <= self.input.LA(1) <= 12) or (14 <= self.input.LA(1) <= 65535):
                            self.input.consume()
                        else:
                            mse = MismatchedSetException(None, self.input)
                            self.recover(mse)
                            raise mse




                    else:
                        break #loop16


                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:235:26: ( '\\r' )?
                alt17 = 2
                LA17_0 = self.input.LA(1)

                if (LA17_0 == 13) :
                    alt17 = 1
                if alt17 == 1:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:235:26: '\\r'
                    pass 
                    self.match(13)




                self.match(10)

                #action start
                _channel=HIDDEN;
                #action end



            elif alt21 == 2:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:236:7: '/*' ( options {greedy=false; } : . )* '*/'
                pass 
                self.match("/*")


                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:236:12: ( options {greedy=false; } : . )*
                while True: #loop18
                    alt18 = 2
                    LA18_0 = self.input.LA(1)

                    if (LA18_0 == 42) :
                        LA18_1 = self.input.LA(2)

                        if (LA18_1 == 47) :
                            alt18 = 2
                        elif ((0 <= LA18_1 <= 46) or (48 <= LA18_1 <= 65535)) :
                            alt18 = 1


                    elif ((0 <= LA18_0 <= 41) or (43 <= LA18_0 <= 65535)) :
                        alt18 = 1


                    if alt18 == 1:
                        # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:236:40: .
                        pass 
                        self.matchAny()


                    else:
                        break #loop18


                self.match("*/")


                #action start
                _channel=HIDDEN;
                #action end



            elif alt21 == 3:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:237:7: '#' (~ ( '\\n' | '\\r' ) )* ( '\\r' )? '\\n'
                pass 
                self.match(35)

                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:237:11: (~ ( '\\n' | '\\r' ) )*
                while True: #loop19
                    alt19 = 2
                    LA19_0 = self.input.LA(1)

                    if ((0 <= LA19_0 <= 9) or (11 <= LA19_0 <= 12) or (14 <= LA19_0 <= 65535)) :
                        alt19 = 1


                    if alt19 == 1:
                        # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:
                        pass 
                        if (0 <= self.input.LA(1) <= 9) or (11 <= self.input.LA(1) <= 12) or (14 <= self.input.LA(1) <= 65535):
                            self.input.consume()
                        else:
                            mse = MismatchedSetException(None, self.input)
                            self.recover(mse)
                            raise mse




                    else:
                        break #loop19


                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:237:25: ( '\\r' )?
                alt20 = 2
                LA20_0 = self.input.LA(1)

                if (LA20_0 == 13) :
                    alt20 = 1
                if alt20 == 1:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:237:25: '\\r'
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

            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:241:5: ( ( ' ' | '\\t' | '\\r' | '\\n' ) )
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:241:7: ( ' ' | '\\t' | '\\r' | '\\n' )
            pass 
            if (9 <= self.input.LA(1) <= 10) or self.input.LA(1) == 13 or self.input.LA(1) == 32:
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
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:255:5: ( ( 'e' | 'E' ) ( '+' | '-' )? ( '0' .. '9' )+ )
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:255:7: ( 'e' | 'E' ) ( '+' | '-' )? ( '0' .. '9' )+
            pass 
            if self.input.LA(1) == 69 or self.input.LA(1) == 101:
                self.input.consume()
            else:
                mse = MismatchedSetException(None, self.input)
                self.recover(mse)
                raise mse



            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:255:17: ( '+' | '-' )?
            alt22 = 2
            LA22_0 = self.input.LA(1)

            if (LA22_0 == 43 or LA22_0 == 45) :
                alt22 = 1
            if alt22 == 1:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:
                pass 
                if self.input.LA(1) == 43 or self.input.LA(1) == 45:
                    self.input.consume()
                else:
                    mse = MismatchedSetException(None, self.input)
                    self.recover(mse)
                    raise mse






            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:255:28: ( '0' .. '9' )+
            cnt23 = 0
            while True: #loop23
                alt23 = 2
                LA23_0 = self.input.LA(1)

                if ((48 <= LA23_0 <= 57)) :
                    alt23 = 1


                if alt23 == 1:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:
                    pass 
                    if (48 <= self.input.LA(1) <= 57):
                        self.input.consume()
                    else:
                        mse = MismatchedSetException(None, self.input)
                        self.recover(mse)
                        raise mse




                else:
                    if cnt23 >= 1:
                        break #loop23

                    eee = EarlyExitException(23, self.input)
                    raise eee

                cnt23 += 1





        finally:
            pass

    # $ANTLR end "EXPONENT"



    # $ANTLR start "HEX_DIGIT"
    def mHEX_DIGIT(self, ):
        try:
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:260:5: ( ( '0' .. '9' | 'a' .. 'f' | 'A' .. 'F' ) )
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:
            pass 
            if (48 <= self.input.LA(1) <= 57) or (65 <= self.input.LA(1) <= 70) or (97 <= self.input.LA(1) <= 102):
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
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:265:5: ( ( '0' .. '9' ) )
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:
            pass 
            if (48 <= self.input.LA(1) <= 57):
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
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:270:5: ( ( INT_PART )? FRAC_PART | INT_PART '.' )
            alt25 = 2
            alt25 = self.dfa25.predict(self.input)
            if alt25 == 1:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:270:7: ( INT_PART )? FRAC_PART
                pass 
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:270:7: ( INT_PART )?
                alt24 = 2
                LA24_0 = self.input.LA(1)

                if ((48 <= LA24_0 <= 57)) :
                    alt24 = 1
                if alt24 == 1:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:270:7: INT_PART
                    pass 
                    self.mINT_PART()





                self.mFRAC_PART()



            elif alt25 == 2:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:271:7: INT_PART '.'
                pass 
                self.mINT_PART()


                self.match(46)



        finally:
            pass

    # $ANTLR end "FLOAT_NO_EXP"



    # $ANTLR start "FLOAT_EXP"
    def mFLOAT_EXP(self, ):
        try:
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:276:5: ( ( INT_PART | FLOAT_NO_EXP ) EXPONENT )
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:276:7: ( INT_PART | FLOAT_NO_EXP ) EXPONENT
            pass 
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:276:7: ( INT_PART | FLOAT_NO_EXP )
            alt26 = 2
            alt26 = self.dfa26.predict(self.input)
            if alt26 == 1:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:276:9: INT_PART
                pass 
                self.mINT_PART()



            elif alt26 == 2:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:276:20: FLOAT_NO_EXP
                pass 
                self.mFLOAT_NO_EXP()





            self.mEXPONENT()





        finally:
            pass

    # $ANTLR end "FLOAT_EXP"



    # $ANTLR start "INT_PART"
    def mINT_PART(self, ):
        try:
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:281:5: ( ( DIGIT )+ )
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:281:7: ( DIGIT )+
            pass 
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:281:7: ( DIGIT )+
            cnt27 = 0
            while True: #loop27
                alt27 = 2
                LA27_0 = self.input.LA(1)

                if ((48 <= LA27_0 <= 57)) :
                    alt27 = 1


                if alt27 == 1:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:
                    pass 
                    if (48 <= self.input.LA(1) <= 57):
                        self.input.consume()
                    else:
                        mse = MismatchedSetException(None, self.input)
                        self.recover(mse)
                        raise mse




                else:
                    if cnt27 >= 1:
                        break #loop27

                    eee = EarlyExitException(27, self.input)
                    raise eee

                cnt27 += 1





        finally:
            pass

    # $ANTLR end "INT_PART"



    # $ANTLR start "FRAC_PART"
    def mFRAC_PART(self, ):
        try:
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:286:5: ( '.' ( DIGIT )+ )
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:286:7: '.' ( DIGIT )+
            pass 
            self.match(46)

            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:286:11: ( DIGIT )+
            cnt28 = 0
            while True: #loop28
                alt28 = 2
                LA28_0 = self.input.LA(1)

                if ((48 <= LA28_0 <= 57)) :
                    alt28 = 1


                if alt28 == 1:
                    # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:
                    pass 
                    if (48 <= self.input.LA(1) <= 57):
                        self.input.consume()
                    else:
                        mse = MismatchedSetException(None, self.input)
                        self.recover(mse)
                        raise mse




                else:
                    if cnt28 >= 1:
                        break #loop28

                    eee = EarlyExitException(28, self.input)
                    raise eee

                cnt28 += 1





        finally:
            pass

    # $ANTLR end "FRAC_PART"



    # $ANTLR start "STRPREFIX"
    def mSTRPREFIX(self, ):
        try:
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:294:5: ( 'r' | 'R' | 'u' | 'U' )
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:
            pass 
            if self.input.LA(1) == 82 or self.input.LA(1) == 85 or self.input.LA(1) == 114 or self.input.LA(1) == 117:
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
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:299:5: ( '\\\\' . )
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:299:7: '\\\\' .
            pass 
            self.match(92)

            self.matchAny()




        finally:
            pass

    # $ANTLR end "STRING_ESC"



    # $ANTLR start "SLSTRING"
    def mSLSTRING(self, ):
        try:
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:306:5: ( '\\'' ( STRING_ESC |~ ( '\\\\' | '\\r' | '\\n' | '\\'' ) )* '\\'' | '\"' ( STRING_ESC |~ ( '\\\\' | '\\r' | '\\n' | '\"' ) )* '\"' | '\\'\\'\\'' ( STRING_ESC |~ ( '\\\\' ) )* '\\'\\'\\'' | '\"\"\"' ( STRING_ESC |~ ( '\\\\' ) )* '\"\"\"' )
            alt33 = 4
            LA33_0 = self.input.LA(1)

            if (LA33_0 == 39) :
                LA33_1 = self.input.LA(2)

                if (LA33_1 == 39) :
                    LA33_3 = self.input.LA(3)

                    if (LA33_3 == 39) :
                        alt33 = 3
                    else:
                        alt33 = 1

                elif ((0 <= LA33_1 <= 9) or (11 <= LA33_1 <= 12) or (14 <= LA33_1 <= 38) or (40 <= LA33_1 <= 65535)) :
                    alt33 = 1
                else:
                    nvae = NoViableAltException("", 33, 1, self.input)

                    raise nvae


            elif (LA33_0 == 34) :
                LA33_2 = self.input.LA(2)

                if (LA33_2 == 34) :
                    LA33_5 = self.input.LA(3)

                    if (LA33_5 == 34) :
                        alt33 = 4
                    else:
                        alt33 = 2

                elif ((0 <= LA33_2 <= 9) or (11 <= LA33_2 <= 12) or (14 <= LA33_2 <= 33) or (35 <= LA33_2 <= 65535)) :
                    alt33 = 2
                else:
                    nvae = NoViableAltException("", 33, 2, self.input)

                    raise nvae


            else:
                nvae = NoViableAltException("", 33, 0, self.input)

                raise nvae


            if alt33 == 1:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:306:7: '\\'' ( STRING_ESC |~ ( '\\\\' | '\\r' | '\\n' | '\\'' ) )* '\\''
                pass 
                self.match(39)

                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:306:12: ( STRING_ESC |~ ( '\\\\' | '\\r' | '\\n' | '\\'' ) )*
                while True: #loop29
                    alt29 = 3
                    LA29_0 = self.input.LA(1)

                    if (LA29_0 == 92) :
                        alt29 = 1
                    elif ((0 <= LA29_0 <= 9) or (11 <= LA29_0 <= 12) or (14 <= LA29_0 <= 38) or (40 <= LA29_0 <= 91) or (93 <= LA29_0 <= 65535)) :
                        alt29 = 2


                    if alt29 == 1:
                        # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:306:13: STRING_ESC
                        pass 
                        self.mSTRING_ESC()



                    elif alt29 == 2:
                        # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:306:26: ~ ( '\\\\' | '\\r' | '\\n' | '\\'' )
                        pass 
                        if (0 <= self.input.LA(1) <= 9) or (11 <= self.input.LA(1) <= 12) or (14 <= self.input.LA(1) <= 38) or (40 <= self.input.LA(1) <= 91) or (93 <= self.input.LA(1) <= 65535):
                            self.input.consume()
                        else:
                            mse = MismatchedSetException(None, self.input)
                            self.recover(mse)
                            raise mse




                    else:
                        break #loop29


                self.match(39)


            elif alt33 == 2:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:307:7: '\"' ( STRING_ESC |~ ( '\\\\' | '\\r' | '\\n' | '\"' ) )* '\"'
                pass 
                self.match(34)

                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:307:11: ( STRING_ESC |~ ( '\\\\' | '\\r' | '\\n' | '\"' ) )*
                while True: #loop30
                    alt30 = 3
                    LA30_0 = self.input.LA(1)

                    if (LA30_0 == 92) :
                        alt30 = 1
                    elif ((0 <= LA30_0 <= 9) or (11 <= LA30_0 <= 12) or (14 <= LA30_0 <= 33) or (35 <= LA30_0 <= 91) or (93 <= LA30_0 <= 65535)) :
                        alt30 = 2


                    if alt30 == 1:
                        # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:307:12: STRING_ESC
                        pass 
                        self.mSTRING_ESC()



                    elif alt30 == 2:
                        # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:307:25: ~ ( '\\\\' | '\\r' | '\\n' | '\"' )
                        pass 
                        if (0 <= self.input.LA(1) <= 9) or (11 <= self.input.LA(1) <= 12) or (14 <= self.input.LA(1) <= 33) or (35 <= self.input.LA(1) <= 91) or (93 <= self.input.LA(1) <= 65535):
                            self.input.consume()
                        else:
                            mse = MismatchedSetException(None, self.input)
                            self.recover(mse)
                            raise mse




                    else:
                        break #loop30


                self.match(34)


            elif alt33 == 3:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:308:7: '\\'\\'\\'' ( STRING_ESC |~ ( '\\\\' ) )* '\\'\\'\\''
                pass 
                self.match("'''")


                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:308:16: ( STRING_ESC |~ ( '\\\\' ) )*
                while True: #loop31
                    alt31 = 3
                    LA31_0 = self.input.LA(1)

                    if (LA31_0 == 39) :
                        LA31_1 = self.input.LA(2)

                        if (LA31_1 == 39) :
                            LA31_4 = self.input.LA(3)

                            if (LA31_4 == 39) :
                                LA31_5 = self.input.LA(4)

                                if ((0 <= LA31_5 <= 65535)) :
                                    alt31 = 2


                            elif ((0 <= LA31_4 <= 38) or (40 <= LA31_4 <= 65535)) :
                                alt31 = 2


                        elif ((0 <= LA31_1 <= 38) or (40 <= LA31_1 <= 65535)) :
                            alt31 = 2


                    elif (LA31_0 == 92) :
                        alt31 = 1
                    elif ((0 <= LA31_0 <= 38) or (40 <= LA31_0 <= 91) or (93 <= LA31_0 <= 65535)) :
                        alt31 = 2


                    if alt31 == 1:
                        # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:308:17: STRING_ESC
                        pass 
                        self.mSTRING_ESC()



                    elif alt31 == 2:
                        # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:308:30: ~ ( '\\\\' )
                        pass 
                        if (0 <= self.input.LA(1) <= 91) or (93 <= self.input.LA(1) <= 65535):
                            self.input.consume()
                        else:
                            mse = MismatchedSetException(None, self.input)
                            self.recover(mse)
                            raise mse




                    else:
                        break #loop31


                self.match("'''")



            elif alt33 == 4:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:309:7: '\"\"\"' ( STRING_ESC |~ ( '\\\\' ) )* '\"\"\"'
                pass 
                self.match("\"\"\"")


                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:309:13: ( STRING_ESC |~ ( '\\\\' ) )*
                while True: #loop32
                    alt32 = 3
                    LA32_0 = self.input.LA(1)

                    if (LA32_0 == 34) :
                        LA32_1 = self.input.LA(2)

                        if (LA32_1 == 34) :
                            LA32_4 = self.input.LA(3)

                            if (LA32_4 == 34) :
                                LA32_5 = self.input.LA(4)

                                if ((0 <= LA32_5 <= 65535)) :
                                    alt32 = 2


                            elif ((0 <= LA32_4 <= 33) or (35 <= LA32_4 <= 65535)) :
                                alt32 = 2


                        elif ((0 <= LA32_1 <= 33) or (35 <= LA32_1 <= 65535)) :
                            alt32 = 2


                    elif (LA32_0 == 92) :
                        alt32 = 1
                    elif ((0 <= LA32_0 <= 33) or (35 <= LA32_0 <= 91) or (93 <= LA32_0 <= 65535)) :
                        alt32 = 2


                    if alt32 == 1:
                        # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:309:14: STRING_ESC
                        pass 
                        self.mSTRING_ESC()



                    elif alt32 == 2:
                        # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:309:27: ~ ( '\\\\' )
                        pass 
                        if (0 <= self.input.LA(1) <= 91) or (93 <= self.input.LA(1) <= 65535):
                            self.input.consume()
                        else:
                            mse = MismatchedSetException(None, self.input)
                            self.recover(mse)
                            raise mse




                    else:
                        break #loop32


                self.match("\"\"\"")




        finally:
            pass

    # $ANTLR end "SLSTRING"



    # $ANTLR start "BYTESTRPREFIX"
    def mBYTESTRPREFIX(self, ):
        try:
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:320:5: ( 'b' | 'B' | 'br' | 'Br' | 'bR' | 'BR' | 'rb' | 'rB' | 'Rb' | 'RB' )
            alt34 = 10
            LA34 = self.input.LA(1)
            if LA34 == 98:
                LA34 = self.input.LA(2)
                if LA34 == 114:
                    alt34 = 3
                elif LA34 == 82:
                    alt34 = 5
                else:
                    alt34 = 1

            elif LA34 == 66:
                LA34 = self.input.LA(2)
                if LA34 == 114:
                    alt34 = 4
                elif LA34 == 82:
                    alt34 = 6
                else:
                    alt34 = 2

            elif LA34 == 114:
                LA34_3 = self.input.LA(2)

                if (LA34_3 == 98) :
                    alt34 = 7
                elif (LA34_3 == 66) :
                    alt34 = 8
                else:
                    nvae = NoViableAltException("", 34, 3, self.input)

                    raise nvae


            elif LA34 == 82:
                LA34_4 = self.input.LA(2)

                if (LA34_4 == 98) :
                    alt34 = 9
                elif (LA34_4 == 66) :
                    alt34 = 10
                else:
                    nvae = NoViableAltException("", 34, 4, self.input)

                    raise nvae


            else:
                nvae = NoViableAltException("", 34, 0, self.input)

                raise nvae


            if alt34 == 1:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:320:7: 'b'
                pass 
                self.match(98)


            elif alt34 == 2:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:320:13: 'B'
                pass 
                self.match(66)


            elif alt34 == 3:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:320:19: 'br'
                pass 
                self.match("br")



            elif alt34 == 4:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:320:26: 'Br'
                pass 
                self.match("Br")



            elif alt34 == 5:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:320:33: 'bR'
                pass 
                self.match("bR")



            elif alt34 == 6:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:320:40: 'BR'
                pass 
                self.match("BR")



            elif alt34 == 7:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:320:47: 'rb'
                pass 
                self.match("rb")



            elif alt34 == 8:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:320:54: 'rB'
                pass 
                self.match("rB")



            elif alt34 == 9:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:320:61: 'Rb'
                pass 
                self.match("Rb")



            elif alt34 == 10:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:320:68: 'RB'
                pass 
                self.match("RB")




        finally:
            pass

    # $ANTLR end "BYTESTRPREFIX"



    # $ANTLR start "SLBYTESTRING"
    def mSLBYTESTRING(self, ):
        try:
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:325:5: ( '\\'' ( BYTES_CHAR_SQ | BYTES_ESC )* '\\'' | '\"' ( BYTES_CHAR_DQ | BYTES_ESC )* '\"' | '\\'\\'\\'' ( BYTES_CHAR_SQ | BYTES_TESC )* '\\'\\'\\'' | '\"\"\"' ( BYTES_CHAR_DQ | BYTES_TESC )* '\"\"\"' )
            alt39 = 4
            LA39_0 = self.input.LA(1)

            if (LA39_0 == 39) :
                LA39_1 = self.input.LA(2)

                if (LA39_1 == 39) :
                    LA39_3 = self.input.LA(3)

                    if (LA39_3 == 39) :
                        alt39 = 3
                    else:
                        alt39 = 1

                elif ((0 <= LA39_1 <= 9) or (11 <= LA39_1 <= 12) or (14 <= LA39_1 <= 38) or (40 <= LA39_1 <= 127)) :
                    alt39 = 1
                else:
                    nvae = NoViableAltException("", 39, 1, self.input)

                    raise nvae


            elif (LA39_0 == 34) :
                LA39_2 = self.input.LA(2)

                if (LA39_2 == 34) :
                    LA39_5 = self.input.LA(3)

                    if (LA39_5 == 34) :
                        alt39 = 4
                    else:
                        alt39 = 2

                elif ((0 <= LA39_2 <= 9) or (11 <= LA39_2 <= 12) or (14 <= LA39_2 <= 33) or (35 <= LA39_2 <= 127)) :
                    alt39 = 2
                else:
                    nvae = NoViableAltException("", 39, 2, self.input)

                    raise nvae


            else:
                nvae = NoViableAltException("", 39, 0, self.input)

                raise nvae


            if alt39 == 1:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:325:7: '\\'' ( BYTES_CHAR_SQ | BYTES_ESC )* '\\''
                pass 
                self.match(39)

                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:325:12: ( BYTES_CHAR_SQ | BYTES_ESC )*
                while True: #loop35
                    alt35 = 3
                    LA35_0 = self.input.LA(1)

                    if ((0 <= LA35_0 <= 9) or (11 <= LA35_0 <= 12) or (14 <= LA35_0 <= 38) or (40 <= LA35_0 <= 91) or (93 <= LA35_0 <= 127)) :
                        alt35 = 1
                    elif (LA35_0 == 92) :
                        alt35 = 2


                    if alt35 == 1:
                        # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:325:13: BYTES_CHAR_SQ
                        pass 
                        self.mBYTES_CHAR_SQ()



                    elif alt35 == 2:
                        # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:325:29: BYTES_ESC
                        pass 
                        self.mBYTES_ESC()



                    else:
                        break #loop35


                self.match(39)


            elif alt39 == 2:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:326:7: '\"' ( BYTES_CHAR_DQ | BYTES_ESC )* '\"'
                pass 
                self.match(34)

                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:326:11: ( BYTES_CHAR_DQ | BYTES_ESC )*
                while True: #loop36
                    alt36 = 3
                    LA36_0 = self.input.LA(1)

                    if ((0 <= LA36_0 <= 9) or (11 <= LA36_0 <= 12) or (14 <= LA36_0 <= 33) or (35 <= LA36_0 <= 91) or (93 <= LA36_0 <= 127)) :
                        alt36 = 1
                    elif (LA36_0 == 92) :
                        alt36 = 2


                    if alt36 == 1:
                        # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:326:12: BYTES_CHAR_DQ
                        pass 
                        self.mBYTES_CHAR_DQ()



                    elif alt36 == 2:
                        # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:326:28: BYTES_ESC
                        pass 
                        self.mBYTES_ESC()



                    else:
                        break #loop36


                self.match(34)


            elif alt39 == 3:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:327:7: '\\'\\'\\'' ( BYTES_CHAR_SQ | BYTES_TESC )* '\\'\\'\\''
                pass 
                self.match("'''")


                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:327:16: ( BYTES_CHAR_SQ | BYTES_TESC )*
                while True: #loop37
                    alt37 = 2
                    LA37_0 = self.input.LA(1)

                    if (LA37_0 == 39) :
                        LA37_1 = self.input.LA(2)

                        if (LA37_1 == 39) :
                            LA37_3 = self.input.LA(3)

                            if (LA37_3 == 39) :
                                LA37_4 = self.input.LA(4)

                                if ((0 <= LA37_4 <= 91) or (93 <= LA37_4 <= 127)) :
                                    alt37 = 1


                            elif ((0 <= LA37_3 <= 38) or (40 <= LA37_3 <= 91) or (93 <= LA37_3 <= 127)) :
                                alt37 = 1


                        elif ((0 <= LA37_1 <= 38) or (40 <= LA37_1 <= 91) or (93 <= LA37_1 <= 127)) :
                            alt37 = 1


                    elif ((0 <= LA37_0 <= 38) or (40 <= LA37_0 <= 91) or (93 <= LA37_0 <= 127)) :
                        alt37 = 1


                    if alt37 == 1:
                        # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:
                        pass 
                        if (0 <= self.input.LA(1) <= 91) or (14 <= self.input.LA(1) <= 38) or (40 <= self.input.LA(1) <= 91) or (93 <= self.input.LA(1) <= 127):
                            self.input.consume()
                        else:
                            mse = MismatchedSetException(None, self.input)
                            self.recover(mse)
                            raise mse




                    else:
                        break #loop37


                self.match("'''")



            elif alt39 == 4:
                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:328:7: '\"\"\"' ( BYTES_CHAR_DQ | BYTES_TESC )* '\"\"\"'
                pass 
                self.match("\"\"\"")


                # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:328:13: ( BYTES_CHAR_DQ | BYTES_TESC )*
                while True: #loop38
                    alt38 = 2
                    LA38_0 = self.input.LA(1)

                    if (LA38_0 == 34) :
                        LA38_1 = self.input.LA(2)

                        if (LA38_1 == 34) :
                            LA38_3 = self.input.LA(3)

                            if (LA38_3 == 34) :
                                LA38_4 = self.input.LA(4)

                                if ((0 <= LA38_4 <= 91) or (93 <= LA38_4 <= 127)) :
                                    alt38 = 1


                            elif ((0 <= LA38_3 <= 33) or (35 <= LA38_3 <= 91) or (93 <= LA38_3 <= 127)) :
                                alt38 = 1


                        elif ((0 <= LA38_1 <= 33) or (35 <= LA38_1 <= 91) or (93 <= LA38_1 <= 127)) :
                            alt38 = 1


                    elif ((0 <= LA38_0 <= 33) or (35 <= LA38_0 <= 91) or (93 <= LA38_0 <= 127)) :
                        alt38 = 1


                    if alt38 == 1:
                        # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:
                        pass 
                        if (0 <= self.input.LA(1) <= 91) or (14 <= self.input.LA(1) <= 33) or (35 <= self.input.LA(1) <= 91) or (93 <= self.input.LA(1) <= 127):
                            self.input.consume()
                        else:
                            mse = MismatchedSetException(None, self.input)
                            self.recover(mse)
                            raise mse




                    else:
                        break #loop38


                self.match("\"\"\"")




        finally:
            pass

    # $ANTLR end "SLBYTESTRING"



    # $ANTLR start "BYTES_CHAR_SQ"
    def mBYTES_CHAR_SQ(self, ):
        try:
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:333:5: ( '\\u0000' .. '\\u0009' | '\\u000B' .. '\\u000C' | '\\u000E' .. '\\u0026' | '\\u0028' .. '\\u005B' | '\\u005D' .. '\\u007F' )
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:
            pass 
            if (0 <= self.input.LA(1) <= 9) or (11 <= self.input.LA(1) <= 12) or (14 <= self.input.LA(1) <= 38) or (40 <= self.input.LA(1) <= 91) or (93 <= self.input.LA(1) <= 127):
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
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:342:5: ( '\\u0000' .. '\\u0009' | '\\u000B' .. '\\u000C' | '\\u000E' .. '\\u0021' | '\\u0023' .. '\\u005B' | '\\u005D' .. '\\u007F' )
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:
            pass 
            if (0 <= self.input.LA(1) <= 9) or (11 <= self.input.LA(1) <= 12) or (14 <= self.input.LA(1) <= 33) or (35 <= self.input.LA(1) <= 91) or (93 <= self.input.LA(1) <= 127):
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
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:351:5: ( '\\\\' '\\u0000' .. '\\u007F' )
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:351:7: '\\\\' '\\u0000' .. '\\u007F'
            pass 
            self.match(92)

            self.matchRange(0, 127)




        finally:
            pass

    # $ANTLR end "BYTES_ESC"



    # $ANTLR start "BYTES_TESC"
    def mBYTES_TESC(self, ):
        try:
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:357:5: ( '\\u0000' .. '\\u005B' | '\\u005D' .. '\\u007F' )
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:
            pass 
            if (0 <= self.input.LA(1) <= 91) or (93 <= self.input.LA(1) <= 127):
                self.input.consume()
            else:
                mse = MismatchedSetException(None, self.input)
                self.recover(mse)
                raise mse






        finally:
            pass

    # $ANTLR end "BYTES_TESC"



    def mTokens(self):
        # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:1:8: ( COLONMINUS | COMMA | LBRACKET | LPAREN | RBRACKET | RPAREN | T__54 | T__55 | T__56 | NEGATION | INSERT | DELETE | EQUAL | SIGN | INT | FLOAT | STRING | ID | COMMENT | WS )
        alt40 = 20
        alt40 = self.dfa40.predict(self.input)
        if alt40 == 1:
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:1:10: COLONMINUS
            pass 
            self.mCOLONMINUS()



        elif alt40 == 2:
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:1:21: COMMA
            pass 
            self.mCOMMA()



        elif alt40 == 3:
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:1:27: LBRACKET
            pass 
            self.mLBRACKET()



        elif alt40 == 4:
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:1:36: LPAREN
            pass 
            self.mLPAREN()



        elif alt40 == 5:
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:1:43: RBRACKET
            pass 
            self.mRBRACKET()



        elif alt40 == 6:
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:1:52: RPAREN
            pass 
            self.mRPAREN()



        elif alt40 == 7:
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:1:59: T__54
            pass 
            self.mT__54()



        elif alt40 == 8:
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:1:65: T__55
            pass 
            self.mT__55()



        elif alt40 == 9:
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:1:71: T__56
            pass 
            self.mT__56()



        elif alt40 == 10:
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:1:77: NEGATION
            pass 
            self.mNEGATION()



        elif alt40 == 11:
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:1:86: INSERT
            pass 
            self.mINSERT()



        elif alt40 == 12:
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:1:93: DELETE
            pass 
            self.mDELETE()



        elif alt40 == 13:
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:1:100: EQUAL
            pass 
            self.mEQUAL()



        elif alt40 == 14:
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:1:106: SIGN
            pass 
            self.mSIGN()



        elif alt40 == 15:
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:1:111: INT
            pass 
            self.mINT()



        elif alt40 == 16:
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:1:115: FLOAT
            pass 
            self.mFLOAT()



        elif alt40 == 17:
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:1:121: STRING
            pass 
            self.mSTRING()



        elif alt40 == 18:
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:1:128: ID
            pass 
            self.mID()



        elif alt40 == 19:
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:1:131: COMMENT
            pass 
            self.mCOMMENT()



        elif alt40 == 20:
            # C:\\Users\\Strazzie\\Documents\\GitHub\\congress\\congress\\datalog\\Congress.g:1:139: WS
            pass 
            self.mWS()








    # lookup tables for DFA #10

    DFA10_eot = DFA.unpack(
        u"\3\uffff\1\6\1\uffff\1\6\1\uffff"
        )

    DFA10_eof = DFA.unpack(
        u"\7\uffff"
        )

    DFA10_min = DFA.unpack(
        u"\2\56\2\60\1\uffff\1\60\1\uffff"
        )

    DFA10_max = DFA.unpack(
        u"\1\71\1\145\1\71\1\145\1\uffff\1\145\1\uffff"
        )

    DFA10_accept = DFA.unpack(
        u"\4\uffff\1\2\1\uffff\1\1"
        )

    DFA10_special = DFA.unpack(
        u"\7\uffff"
        )


    DFA10_transition = [
        DFA.unpack(u"\1\2\1\uffff\12\1"),
        DFA.unpack(u"\1\3\1\uffff\12\1\13\uffff\1\4\37\uffff\1\4"),
        DFA.unpack(u"\12\5"),
        DFA.unpack(u"\12\5\13\uffff\1\4\37\uffff\1\4"),
        DFA.unpack(u""),
        DFA.unpack(u"\12\5\13\uffff\1\4\37\uffff\1\4"),
        DFA.unpack(u"")
    ]

    # class definition for DFA #10

    class DFA10(DFA):
        pass


    # lookup tables for DFA #25

    DFA25_eot = DFA.unpack(
        u"\3\uffff\1\4\1\uffff"
        )

    DFA25_eof = DFA.unpack(
        u"\5\uffff"
        )

    DFA25_min = DFA.unpack(
        u"\2\56\1\uffff\1\60\1\uffff"
        )

    DFA25_max = DFA.unpack(
        u"\2\71\1\uffff\1\71\1\uffff"
        )

    DFA25_accept = DFA.unpack(
        u"\2\uffff\1\1\1\uffff\1\2"
        )

    DFA25_special = DFA.unpack(
        u"\5\uffff"
        )


    DFA25_transition = [
        DFA.unpack(u"\1\2\1\uffff\12\1"),
        DFA.unpack(u"\1\3\1\uffff\12\1"),
        DFA.unpack(u""),
        DFA.unpack(u"\12\2"),
        DFA.unpack(u"")
    ]

    # class definition for DFA #25

    class DFA25(DFA):
        pass


    # lookup tables for DFA #26

    DFA26_eot = DFA.unpack(
        u"\4\uffff"
        )

    DFA26_eof = DFA.unpack(
        u"\4\uffff"
        )

    DFA26_min = DFA.unpack(
        u"\2\56\2\uffff"
        )

    DFA26_max = DFA.unpack(
        u"\1\71\1\145\2\uffff"
        )

    DFA26_accept = DFA.unpack(
        u"\2\uffff\1\2\1\1"
        )

    DFA26_special = DFA.unpack(
        u"\4\uffff"
        )


    DFA26_transition = [
        DFA.unpack(u"\1\2\1\uffff\12\1"),
        DFA.unpack(u"\1\2\1\uffff\12\1\13\uffff\1\3\37\uffff\1\3"),
        DFA.unpack(u""),
        DFA.unpack(u"")
    ]

    # class definition for DFA #26

    class DFA26(DFA):
        pass


    # lookup tables for DFA #40

    DFA40_eot = DFA.unpack(
        u"\1\uffff\1\36\5\uffff\1\37\1\uffff\2\32\1\uffff\4\32\2\uffff\2"
        u"\50\1\32\1\uffff\4\32\6\uffff\1\51\6\32\1\50\2\uffff\1\50\11\32"
        u"\2\13\4\32\1\51\10\32\2\107\2\110\2\uffff"
        )

    DFA40_eof = DFA.unpack(
        u"\111\uffff"
        )

    DFA40_min = DFA.unpack(
        u"\1\11\1\55\5\uffff\1\56\1\uffff\1\157\1\117\1\uffff\1\116\1\156"
        u"\1\105\1\145\2\uffff\2\56\1\42\1\uffff\4\42\6\uffff\1\56\1\164"
        u"\1\124\1\123\1\163\1\114\1\154\1\56\2\uffff\1\56\10\42\1\53\2\56"
        u"\1\105\1\145\1\105\1\145\1\56\1\122\1\162\1\124\1\164\1\124\1\164"
        u"\1\105\1\145\4\56\2\uffff"
        )

    DFA40_max = DFA.unpack(
        u"\1\172\1\55\5\uffff\1\172\1\uffff\1\157\1\117\1\uffff\1\116\1\156"
        u"\1\105\1\145\2\uffff\2\145\1\142\1\uffff\2\162\1\142\1\47\6\uffff"
        u"\1\172\1\164\1\124\1\123\1\163\1\114\1\154\1\145\2\uffff\1\145"
        u"\10\47\1\71\2\172\1\105\1\145\1\105\1\145\1\172\1\122\1\162\1\124"
        u"\1\164\1\124\1\164\1\105\1\145\4\172\2\uffff"
        )

    DFA40_accept = DFA.unpack(
        u"\2\uffff\1\2\1\3\1\4\1\5\1\6\1\uffff\1\11\2\uffff\1\12\4\uffff"
        u"\1\15\1\16\3\uffff\1\21\4\uffff\1\22\1\23\1\24\1\1\1\10\1\7\10"
        u"\uffff\1\17\1\20\35\uffff\1\13\1\14"
        )

    DFA40_special = DFA.unpack(
        u"\111\uffff"
        )


    DFA40_transition = [
        DFA.unpack(u"\2\34\2\uffff\1\34\22\uffff\1\34\1\13\1\25\1\33\3\uffff"
        u"\1\25\1\4\1\6\1\uffff\1\21\1\2\1\21\1\7\1\33\1\23\11\22\1\1\1\10"
        u"\1\uffff\1\20\3\uffff\1\32\1\27\1\32\1\16\4\32\1\14\4\32\1\12\3"
        u"\32\1\30\2\32\1\31\5\32\1\3\1\uffff\1\5\1\uffff\1\32\1\uffff\1"
        u"\32\1\26\1\32\1\17\4\32\1\15\4\32\1\11\3\32\1\24\2\32\1\31\5\32"),
        DFA.unpack(u"\1\35"),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u"\1\32\1\uffff\12\40\7\uffff\32\32\4\uffff\1\32\1\uffff"
        u"\32\32"),
        DFA.unpack(u""),
        DFA.unpack(u"\1\41"),
        DFA.unpack(u"\1\42"),
        DFA.unpack(u""),
        DFA.unpack(u"\1\43"),
        DFA.unpack(u"\1\44"),
        DFA.unpack(u"\1\45"),
        DFA.unpack(u"\1\46"),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u"\1\51\1\uffff\12\47\13\uffff\1\51\37\uffff\1\51"),
        DFA.unpack(u"\1\51\1\uffff\1\52\11\51\13\uffff\1\51\37\uffff\1\51"),
        DFA.unpack(u"\1\25\4\uffff\1\25\32\uffff\1\54\37\uffff\1\53"),
        DFA.unpack(u""),
        DFA.unpack(u"\1\25\4\uffff\1\25\52\uffff\1\56\37\uffff\1\55"),
        DFA.unpack(u"\1\25\4\uffff\1\25\52\uffff\1\60\37\uffff\1\57"),
        DFA.unpack(u"\1\25\4\uffff\1\25\32\uffff\1\62\37\uffff\1\61"),
        DFA.unpack(u"\1\25\4\uffff\1\25"),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u"\1\32\1\uffff\12\40\7\uffff\4\32\1\63\25\32\4\uffff"
        u"\1\32\1\uffff\4\32\1\63\25\32"),
        DFA.unpack(u"\1\64"),
        DFA.unpack(u"\1\65"),
        DFA.unpack(u"\1\66"),
        DFA.unpack(u"\1\67"),
        DFA.unpack(u"\1\70"),
        DFA.unpack(u"\1\71"),
        DFA.unpack(u"\1\51\1\uffff\12\47\13\uffff\1\51\37\uffff\1\51"),
        DFA.unpack(u""),
        DFA.unpack(u""),
        DFA.unpack(u"\1\51\1\uffff\1\52\11\51\13\uffff\1\51\37\uffff\1\51"),
        DFA.unpack(u"\1\25\4\uffff\1\25"),
        DFA.unpack(u"\1\25\4\uffff\1\25"),
        DFA.unpack(u"\1\25\4\uffff\1\25"),
        DFA.unpack(u"\1\25\4\uffff\1\25"),
        DFA.unpack(u"\1\25\4\uffff\1\25"),
        DFA.unpack(u"\1\25\4\uffff\1\25"),
        DFA.unpack(u"\1\25\4\uffff\1\25"),
        DFA.unpack(u"\1\25\4\uffff\1\25"),
        DFA.unpack(u"\1\51\1\uffff\1\51\2\uffff\12\72"),
        DFA.unpack(u"\1\32\1\uffff\12\32\7\uffff\32\32\4\uffff\1\32\1\uffff"
        u"\32\32"),
        DFA.unpack(u"\1\32\1\uffff\12\32\7\uffff\32\32\4\uffff\1\32\1\uffff"
        u"\32\32"),
        DFA.unpack(u"\1\73"),
        DFA.unpack(u"\1\74"),
        DFA.unpack(u"\1\75"),
        DFA.unpack(u"\1\76"),
        DFA.unpack(u"\1\32\1\uffff\12\72\7\uffff\32\32\4\uffff\1\32\1\uffff"
        u"\32\32"),
        DFA.unpack(u"\1\77"),
        DFA.unpack(u"\1\100"),
        DFA.unpack(u"\1\101"),
        DFA.unpack(u"\1\102"),
        DFA.unpack(u"\1\103"),
        DFA.unpack(u"\1\104"),
        DFA.unpack(u"\1\105"),
        DFA.unpack(u"\1\106"),
        DFA.unpack(u"\1\32\1\uffff\12\32\7\uffff\32\32\4\uffff\1\32\1\uffff"
        u"\32\32"),
        DFA.unpack(u"\1\32\1\uffff\12\32\7\uffff\32\32\4\uffff\1\32\1\uffff"
        u"\32\32"),
        DFA.unpack(u"\1\32\1\uffff\12\32\7\uffff\32\32\4\uffff\1\32\1\uffff"
        u"\32\32"),
        DFA.unpack(u"\1\32\1\uffff\12\32\7\uffff\32\32\4\uffff\1\32\1\uffff"
        u"\32\32"),
        DFA.unpack(u""),
        DFA.unpack(u"")
    ]

    # class definition for DFA #40

    class DFA40(DFA):
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
