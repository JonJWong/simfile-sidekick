# Generated from search.g4 by ANTLR 4.8
from antlr4 import *
from io import StringIO
from typing.io import TextIO
import sys



def serializedATN():
    with StringIO() as buf:
        buf.write("\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\2\f")
        buf.write("K\b\1\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6\4\7\t\7")
        buf.write("\4\b\t\b\4\t\t\t\4\n\t\n\4\13\t\13\3\2\3\2\3\3\3\3\3\4")
        buf.write("\3\4\3\5\3\5\3\5\3\5\3\5\3\5\3\6\3\6\3\6\3\6\3\6\3\6\3")
        buf.write("\6\3\6\3\6\3\7\3\7\3\7\3\7\3\7\3\7\3\7\3\b\3\b\3\b\3\b")
        buf.write("\3\b\3\b\3\b\3\b\3\b\3\b\3\b\3\t\3\t\3\t\3\t\3\t\3\t\3")
        buf.write("\t\3\n\3\n\3\n\3\n\3\13\3\13\2\2\f\3\3\5\4\7\5\t\6\13")
        buf.write("\7\r\b\17\t\21\n\23\13\25\f\3\2\3\4\2\n\f\16\17\2J\2\3")
        buf.write("\3\2\2\2\2\5\3\2\2\2\2\7\3\2\2\2\2\t\3\2\2\2\2\13\3\2")
        buf.write("\2\2\2\r\3\2\2\2\2\17\3\2\2\2\2\21\3\2\2\2\2\23\3\2\2")
        buf.write("\2\2\25\3\2\2\2\3\27\3\2\2\2\5\31\3\2\2\2\7\33\3\2\2\2")
        buf.write("\t\35\3\2\2\2\13#\3\2\2\2\r,\3\2\2\2\17\63\3\2\2\2\21")
        buf.write(">\3\2\2\2\23E\3\2\2\2\25I\3\2\2\2\27\30\7\"\2\2\30\4\3")
        buf.write("\2\2\2\31\32\7/\2\2\32\6\3\2\2\2\33\34\7<\2\2\34\b\3\2")
        buf.write("\2\2\35\36\7v\2\2\36\37\7k\2\2\37 \7v\2\2 !\7n\2\2!\"")
        buf.write("\7g\2\2\"\n\3\2\2\2#$\7u\2\2$%\7w\2\2%&\7d\2\2&\'\7v\2")
        buf.write("\2\'(\7k\2\2()\7v\2\2)*\7n\2\2*+\7g\2\2+\f\3\2\2\2,-\7")
        buf.write("c\2\2-.\7t\2\2./\7v\2\2/\60\7k\2\2\60\61\7u\2\2\61\62")
        buf.write("\7v\2\2\62\16\3\2\2\2\63\64\7u\2\2\64\65\7v\2\2\65\66")
        buf.write("\7g\2\2\66\67\7r\2\2\678\7c\2\289\7t\2\29:\7v\2\2:;\7")
        buf.write("k\2\2;<\7u\2\2<=\7v\2\2=\20\3\2\2\2>?\7t\2\2?@\7c\2\2")
        buf.write("@A\7v\2\2AB\7k\2\2BC\7p\2\2CD\7i\2\2D\22\3\2\2\2EF\7d")
        buf.write("\2\2FG\7r\2\2GH\7o\2\2H\24\3\2\2\2IJ\n\2\2\2J\26\3\2\2")
        buf.write("\2\3\2\2")
        return buf.getvalue()


class searchLexer(Lexer):

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    T__0 = 1
    T__1 = 2
    T__2 = 3
    T__3 = 4
    T__4 = 5
    T__5 = 6
    T__6 = 7
    T__7 = 8
    T__8 = 9
    CHAR = 10

    channelNames = [ u"DEFAULT_TOKEN_CHANNEL", u"HIDDEN" ]

    modeNames = [ "DEFAULT_MODE" ]

    literalNames = [ "<INVALID>",
            "' '", "'-'", "':'", "'title'", "'subtitle'", "'artist'", "'stepartist'", 
            "'rating'", "'bpm'" ]

    symbolicNames = [ "<INVALID>",
            "CHAR" ]

    ruleNames = [ "T__0", "T__1", "T__2", "T__3", "T__4", "T__5", "T__6", 
                  "T__7", "T__8", "CHAR" ]

    grammarFileName = "search.g4"

    def __init__(self, input=None, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.8")
        self._interp = LexerATNSimulator(self, self.atn, self.decisionsToDFA, PredictionContextCache())
        self._actions = None
        self._predicates = None


