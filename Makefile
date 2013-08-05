
all: CongressLexer.py

CongressLexer.py CongressParser.py: policy/Congress.g 
	java -jar outside/antlr-3.5-complete.jar policy/Congress.g




