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
    // Structure
    THEORY;
    STRUCTURED_NAME;

    // Kinds of Formulas
    RULE;
    LITERAL;
    ATOM;
    NOT;

    // Terms
    VARIABLE;
    STRING_OBJ;
    INTEGER_OBJ;
    FLOAT_OBJ;
    SYMBOL_OBJ;
}

prog
    : formula formula* EOF -> ^(THEORY formula+)
    | EOF
    ;

formula
    : bare_formula formula_terminator? -> bare_formula
    ;

formula_terminator
    : ';'
    | '.'
    ;

bare_formula
    : rule
    | atom
    ;

rule
    : atom COLONMINUS literal_list -> ^(RULE atom literal_list)
    ;

literal_list
    : literal (COMMA literal)* -> literal+
    ;

literal
    : atom      -> atom
    | NEGATION atom  -> ^(NOT atom)
    ;

NEGATION
    : 'not'
    | 'NOT'
    | '!'
    ;

atom
    : relation_constant (LPAREN term_list? RPAREN)? -> ^(ATOM relation_constant term_list?)
    ;

term_list
    : term (COMMA term)* -> term+
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
    : ID   -> ^(VARIABLE ID)
    ;

relation_constant
    : ID (':' ID)* -> ^(STRUCTURED_NAME ID+)
    ;

ID  :   ('a'..'z'|'A'..'Z'|'_') ('a'..'z'|'A'..'Z'|'0'..'9'|'_')*
    ;

INT :   '0'..'9'+
    ;

FLOAT
    :   ('0'..'9')+ '.' ('0'..'9')* EXPONENT?
    |   '.' ('0'..'9')+ EXPONENT?
    |   ('0'..'9')+ EXPONENT
    ;

COMMENT
    :   '//' ~('\n'|'\r')* '\r'? '\n' {$channel=HIDDEN;}
    |   '/*' ( options {greedy=false;} : . )* '*/' {$channel=HIDDEN;}
    ;

WS  :   ( ' '
        | '\t'
        | '\r'
        | '\n'
        ) {$channel=HIDDEN;}
    ;

// Characters in string are either
//    (i) any character except ", carriage-return, linefeed, backslash
//    (ii) an escape sequence like \t, \n, \r
//    (iii) or a universal character name like \u10af
// Order of the above 3 in the following rule is important.
STRING
    : '"' (~('"' | '\r' | '\n' | '\\')
           | ESC_SEQ )*
      '"'
    ;

// Escape sequences
// Simple escape sequences like \n, \t, \\ are taken from Stroustrup.
// Octal escape sequences are either 1, 2, or 3 octal digits exactly.
// Hexadecimal escape sequences begin with \x and continue until non-hex found.
// No handling of tri-graph sequences.



CHAR:  '\'' ( ESC_SEQ | ~('\''|'\\') ) '\''
    ;

fragment
EXPONENT : ('e'|'E') ('+'|'-')? ('0'..'9')+ ;

fragment
HEX_DIGIT : ('0'..'9'|'a'..'f'|'A'..'F') ;

fragment
ESC_SEQ
    :   '\\' ('b'|'t'|'n'|'f'|'r'|'"'|'\''|'\\')
    |   UNICODE_ESC
    |   OCTAL_ESC
    ;

fragment
OCTAL_ESC
    :   '\\' ('0'..'3') ('0'..'7') ('0'..'7')
    |   '\\' ('0'..'7') ('0'..'7')
    |   '\\' ('0'..'7')
    ;

fragment
UNICODE_ESC
    :   '\\' 'u' HEX_DIGIT HEX_DIGIT HEX_DIGIT HEX_DIGIT
    ;
