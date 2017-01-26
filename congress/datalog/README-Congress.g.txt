If you modify the congress/datalog/Congress.g file, you need to use antlr3
to re-generate the CongressLexer.py and CongressParser.py files with
the following steps:

1. Make sure a recent version of Java is installed. http://java.com/
2. Download ANTLR 3.5.2 or another compatible version from http://www.antlr3.org/download/antlr-3.5.2-complete.jar
3. Execute the following commands in shell

$ cd path/to/congress_repo/congress/datalog
$ java -jar path/to/antlr-3.5.2-complete.jar Congress.g -o Python2 -language Python
$ java -jar path/to/antlr-3.5.2-complete.jar Congress.g -o Python3 -language Python3
