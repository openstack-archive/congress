
TOPDIR=$(CURDIR)
SRCDIR=$(TOPDIR)/congress

all: CongressLexer.py

clean:
	rm -f Congress.tokens congress/policy/CongressLexer.py congress/policy/CongressParser.py
	find . -name '*.pyc' -exec rm -f {} \;

CongressLexer.py CongressParser.py: congress/policy/Congress.g 
	java -jar $(TOPDIR)/thirdparty/antlr-3.5-complete.jar $(SRCDIR)/policy/Congress.g




