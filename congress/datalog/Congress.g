// Copyright (c) 2013 VMware, Inc. All rights reserved.
//
//    Licensed under the Apache License, Version 2.0 (the "License"); you may
//    not use this file except in compliance with the License. You may obtain
//    a copy of the License at
//
//         http://www.apache.org/licenses/LICENSE-2.0
//
//    Unless required by applicable law or agreed to in writing, software
//    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
//    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
//    License for the specific language governing permissions and limitations
//    under the License.
//

grammar Congress;

options {
    language=Python;
    output=AST;
    ASTLabelType=CommonTree;
}

tokens {
    PROG;
    COMMA=',';
    COLONMINUS=':-';
    LPAREN='(';
    RPAREN=')';
    RBRACKET=']';
    LBRACKET='[';

    // Structure
    THEORY;
    STRUCTURED_NAME;

    // Kinds of Formulas
    EVENT;
    RULE;
    LITERAL;
    MODAL;
    ATOM;
    NOT;
    AND;

    // Terms
    NAMED_PARAM;
    COLUMN_NAME;
    COLUMN_NUMBER;
    VARIABLE;
    STRING_OBJ;
    INTEGER_OBJ;
    FLOAT_OBJ;
    SYMBOL_OBJ;
}

// a program can be one or more statements or empty
prog
    : statement+ EOF -> ^(THEORY statement+)
    | EOF
    ;

// a statement is either a formula or a comment
// let the lexer handle comments directly for efficiency
statement
    : formula formula_terminator? -> formula
    | COMMENT
    ;

formula
    : rule
    | fact
    | event
    ;

// An Event represents the insertion/deletion of policy statements.
// Events always include :-.  This is to avoid ambiguity in the grammar
//   for the case of insert[p(1)].  Without the requirement that an event
//   includes a :-, insert[p(1)] could either represent the event where p(1)
//   is inserted or simply a policy statement with an empty body and the modal
//   'insert' in the head.
//   This means that to represent the event where p(1) is inserted, you must write
//   insert[p(1) :- true].  To represent the query that asks if insert[p(1)] is true
//   you write insert[p(1)].

event
    : event_op LBRACKET rule (formula_terminator STRING)? RBRACKET -> ^(EVENT event_op rule STRING?)
    ;

event_op
    : 'insert'
    | 'delete'
    ;

formula_terminator
    : ';'
    | '.'
    ;

rule
    : literal_list COLONMINUS literal_list -> ^(RULE literal_list literal_list)
    ;

literal_list
    : literal (COMMA literal)* -> ^(AND literal+)
    ;

literal
    : fact            -> fact
    | NEGATION fact   -> ^(NOT fact)
    ;

// Note: if we replace modal_op with ID, it tries to force statements
//  like insert[p(x)] :- q(x) to be events instead of rules.  Bug?
fact
    : atom
    | modal_op LBRACKET atom RBRACKET -> ^(MODAL modal_op atom)
    ;

modal_op
    : 'execute'
    | 'insert'
    | 'delete'
    ;

atom
    : relation_constant (LPAREN parameter_list? RPAREN)? -> ^(ATOM relation_constant parameter_list?)
    ;

parameter_list
    : parameter (COMMA parameter)* -> parameter+
    ;

parameter
    : term -> term
    | column_ref EQUAL term -> ^(NAMED_PARAM column_ref term)
    ;

column_ref
    : ID   ->  ^(COLUMN_NAME ID)
    | INT  ->  ^(COLUMN_NUMBER INT)
    ;

term
    : object_constant
    | variable
    ;

object_constant
    : INT      -> ^(INTEGER_OBJ INT)
    | FLOAT    -> ^(FLOAT_OBJ FLOAT)
    | STRING   -> ^(STRING_OBJ STRING)
    ;

variable
    : ID -> ^(VARIABLE ID)
    ;

relation_constant
    : ID (':' ID)* SIGN? -> ^(STRUCTURED_NAME ID+ SIGN?)
    ;

// start of the lexer
// first, define keywords to ensure they have lexical priority

NEGATION
    : 'not'
    | 'NOT'
    | '!'
    ;

EQUAL
    :  '='
    ;

SIGN
    :  '+' | '-'
    ;

// Python integers, conformant to 3.4.2 spec
// Note that leading zeros in a non-zero decimal number are not allowed
// This is taken care of by the first and second alternatives
INT
    : '1'..'9' ('0'..'9')*
    | '0'+
    | '0' ('o' | 'O') ('0'..'7')+
    | '0' ('x' | 'X') (HEX_DIGIT)+
    | '0' ('b' | 'B') ('0' | '1')+
    ;

// Python floating point literals, conformant to 3.4.2 spec
// The integer and exponent parts are always interpreted using radix 10
FLOAT
    : FLOAT_NO_EXP
    | FLOAT_EXP
    ;

// String literals according to Python 3.4.2 grammar
// THIS VERSION IMPLEMENTS STRING AND BYTE LITERALS
// AS WELL AS TRIPLE QUOTED STRINGS
// Python strings:
// - can be enclosed in matching single quotes (') or double quotes (")
// - can be enclosed in matching groups of three single or double quotes
// - a backslash (\) character is used to escape characters that otherwise
//   have a special meaning (e.g., newline, backslash, or a quote)
// - can be prefixed with a u to simplify maintenance of 2.x and 3.x code
// - 'ur' is NOT allowed
// - unescpaed newlines and quotes are allowed in triple-quoted literal
//   EXCEPT that three unescaped contiguous quotes terminate the literal
//
// Byte String Literals according to Python 3.4.2 grammar
// Bytes are always prefixed with 'b' or 'B', and can only contain ASCII
// Any byte with a numeric value of >= 128 must be escaped
//
// Also implemented code refactoring to reduce runtime size of parser

STRING
    : (STRPREFIX)? (SLSTRING)+
    | (BYTESTRPREFIX) (SLBYTESTRING)+
    ;

// moved this rule so we could differentiate between .123 and .1aa
// (i.e., relying on lexical priority)
ID
    : ('a'..'z'|'A'..'Z'|'_'|'.') ('a'..'z'|'A'..'Z'|'0'..'9'|'_'|'.')*
    ;

// added Pythonesque comments
COMMENT
    : '//' ~('\n'|'\r')* '\r'? '\n' {$channel=HIDDEN;}
    | '/*' ( options {greedy=false;} : . )* '*/' {$channel=HIDDEN;}
    | '#' ~('\n'|'\r')* '\r'? '\n' {$channel=HIDDEN;}
    ;

WS
    : ( ' '
      | '\t'
      | '\r'
      | '\n'
      ) {$channel=HIDDEN;}
    ;


// fragment rules
// these are helper rules that are used by other lexical rules
// they do NOT generate tokens
fragment
EXPONENT
    : ('e'|'E') ('+'|'-')? ('0'..'9')+
    ;

fragment
HEX_DIGIT
    : ('0'..'9'|'a'..'f'|'A'..'F')
    ;

fragment
DIGIT
    : ('0'..'9')
    ;

fragment
FLOAT_NO_EXP
    : INT_PART? FRAC_PART
    | INT_PART '.'
    ;

fragment
FLOAT_EXP
    : ( INT_PART | FLOAT_NO_EXP ) EXPONENT
    ;

fragment
INT_PART
    : DIGIT+
    ;

fragment
FRAC_PART
    : '.' DIGIT+
    ;

// The following fragments are for string handling

// any form of 'ur' is illegal
fragment
STRPREFIX
    : 'r' | 'R' | 'u' | 'U'
    ;

fragment
STRING_ESC
    : '\\' .
    ;

// The first two are single-line string with single- and double-quotes
// The second two are multi-line strings with single- and double quotes
fragment
SLSTRING
    : '\'' (STRING_ESC | ~('\\' | '\r' | '\n' | '\'') )* '\''
    | '"' (STRING_ESC | ~('\\' | '\r' | '\n' | '"') )* '"'
    | '\'\'\'' (STRING_ESC | ~('\\') )* '\'\'\''
    | '"""' (STRING_ESC | ~('\\') )* '"""'
    ;


// Python Byte Literals
// Each byte within a byte literal can be an ASCII character or an
// encoded hex number from \x00 to \xff (i.e., 0-255)
// EXCEPT the backslash, newline, or quote

fragment
BYTESTRPREFIX
    : 'b' | 'B' | 'br' | 'Br' | 'bR' | 'BR' | 'rb' | 'rB' | 'Rb' | 'RB'
    ;

fragment
SLBYTESTRING
    : '\'' (BYTES_CHAR_SQ | BYTES_ESC)* '\''
    | '"' (BYTES_CHAR_DQ | BYTES_ESC)* '"'
    | '\'\'\'' (BYTES_CHAR_SQ | BYTES_TESC)* '\'\'\''
    | '"""' (BYTES_CHAR_DQ | BYTES_TESC)* '"""'
    ;

fragment
BYTES_CHAR_SQ
    : '\u0000'..'\u0009'
    | '\u000B'..'\u000C'
    | '\u000E'..'\u0026'
    | '\u0028'..'\u005B'
    | '\u005D'..'\u007F'
    ;

fragment
BYTES_CHAR_DQ
    : '\u0000'..'\u0009'
    | '\u000B'..'\u000C'
    | '\u000E'..'\u0021'
    | '\u0023'..'\u005B'
    | '\u005D'..'\u007F'
    ;

fragment
BYTES_ESC
    : '\\' '\u0000'..'\u007F'
    ;


fragment
BYTES_TESC
    : '\u0000'..'\u005B'
    | '\u005D'..'\u007F'
    ;
