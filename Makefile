
TOPDIR=$(CURDIR)
SRCDIR=$(TOPDIR)/congress

all: code docs

code: CongressLexer.py

clean:
	rm -f Congress.tokens $(SRCDIR)/policy/CongressLexer.py $(SRCDIR)/policy/CongressParser.py
	find . -name '*.pyc' -exec rm -f {} \;
	rm -Rf $(TOPDIR)/doc/html/*

CongressLexer.py CongressParser.py: $(SRCDIR)/policy/Congress.g
	java -jar $(TOPDIR)/thirdparty/antlr-3.5-complete.jar $(SRCDIR)/policy/Congress.g

docs: $(TOPDIR)/doc/source/*.rst
	sphinx-build -b html $(TOPDIR)/doc/source $(TOPDIR)/doc/html


