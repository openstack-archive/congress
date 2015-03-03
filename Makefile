
TOPDIR=$(CURDIR)
SRCDIR=$(TOPDIR)/congress

all: code docs

code: CongressLexer.py

clean:
	rm -f Congress.tokens $(SRCDIR)/datalog/CongressLexer.py $(SRCDIR)/datalog/CongressParser.py
	find . -name '*.pyc' -exec rm -f {} \;
	rm -Rf $(TOPDIR)/doc/html/*

CongressLexer.py CongressParser.py: $(SRCDIR)/datalog/Congress.g
	java -jar $(TOPDIR)/thirdparty/antlr-3.5-complete.jar $(SRCDIR)/datalog/Congress.g

docs: $(TOPDIR)/doc/source/*.rst
	sphinx-build -b html $(TOPDIR)/doc/source $(TOPDIR)/doc/html


