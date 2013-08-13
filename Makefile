
TOPDIR=$(CURDIR)
SRCDIR=$(TOPDIR)/src

all: CongressLexer.py

clean:
	rm -f Congress.tokens src/policy/CongressLexer.py src/policy/CongressParser.py
	find . -name '*.pyc' -exec rm -f {} \;

CongressLexer.py CongressParser.py: src/policy/Congress.g 
	java -jar $(TOPDIR)/thirdparty/antlr-3.5-complete.jar $(SRCDIR)/policy/Congress.g




