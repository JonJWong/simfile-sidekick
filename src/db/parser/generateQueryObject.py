from antlr4 import InputStream, CommonTokenStream, ParseTreeWalker
from .searchLexer import searchLexer
from .searchParser import searchParser
from .parserListener import parserListener
from .parserErrorListener import ParserErrorListener


def generateQueryObject(input: str):
    lexer = searchLexer(InputStream(input))
    stream = CommonTokenStream(lexer)
    try:
        parser = searchParser(None)
        parser.addErrorListener(ParserErrorListener())
        parser.setInputStream(stream)

        tree = parser.search_statement()

        listener = parserListener()
        walker = ParseTreeWalker()
        walker.walk(listener, tree)
        return {'queryObject': listener.getQueryObject(), 'error': None}
    except Exception as re:
        return {'queryObject': None, 'error': re.args[0]}
