#! /usr/bin/python

import sys
sys.path.insert(0, '/home/thinrichs/congress/outside')
import optparse
import CongressLexer
import CongressParser
import antlr3

class CongressException (Exception):
	pass

class Compiler (object):

	def __init__(self):
		self.antlr3_tree = None

	def read_source(self, file):
		# parse with antlr3
		char_stream = antlr3.ANTLRFileStream(file)
		lexer = CongressLexer.CongressLexer(char_stream)
		self.tokens = antlr3.CommonTokenStream(lexer)
		parser = CongressParser.CongressParser(self.tokens)
		self.antlr3_tree = parser.prog().tree

		# convert to internal representation
		self.print_parse_result()


	def print_parse_result(self):
		print_tree(
			self.antlr3_tree,
			lambda x: x.getText(),
			lambda x: x.children,
			ind=1)

def print_tree(tree, text, kids, ind=0):
	""" Print out TREE using function TEXT to extract node description and
	    function KIDS to compute the children of a given node.
	    IND is a number representing the indentation level. """
	print "|" * ind,
	print "{}".format(str(text(tree)))
	children = kids(tree)
	if children:
		for child in children:
			print_tree(child, text, kids, ind + 1)

def main():
	parser = optparse.OptionParser()
	(options, inputs) = parser.parse_args(sys.argv[1:])
	if len(inputs) != 1:
		parser.error("Usage: %prog [options] policy-file")
	compiler = Compiler()
	compiler.read_source(inputs[0])

if __name__ == '__main__':
	sys.exit(main())


