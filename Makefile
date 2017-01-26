
TOPDIR=$(CURDIR)
SRCDIR=$(TOPDIR)/congress

all: docs

clean:
	find . -name '*.pyc' -exec rm -f {} \;
	rm -Rf $(TOPDIR)/doc/html/*

docs: $(TOPDIR)/doc/source/*.rst
	sphinx-build -b html $(TOPDIR)/doc/source $(TOPDIR)/doc/html
