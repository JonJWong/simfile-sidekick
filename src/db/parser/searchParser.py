# Generated from search.g4 by ANTLR 4.8
# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO


def serializedATN():
    with StringIO() as buf:
        buf.write("\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\3\f")
        buf.write("=\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6\3\2\3\2\3\2")
        buf.write("\3\2\6\2\21\n\2\r\2\16\2\22\3\2\3\2\3\2\7\2\30\n\2\f\2")
        buf.write("\16\2\33\13\2\5\2\35\n\2\3\3\3\3\3\4\3\4\3\4\3\4\3\4\3")
        buf.write("\5\3\5\3\6\6\6)\n\6\r\6\16\6*\3\6\7\6.\n\6\f\6\16\6\61")
        buf.write("\13\6\3\6\6\6\64\n\6\r\6\16\6\65\7\68\n\6\f\6\16\6;\13")
        buf.write("\6\3\6\2\2\7\2\4\6\b\n\2\3\3\2\6\13\2?\2\34\3\2\2\2\4")
        buf.write("\36\3\2\2\2\6 \3\2\2\2\b%\3\2\2\2\n(\3\2\2\2\f\35\5\4")
        buf.write("\3\2\r\20\5\4\3\2\16\17\7\3\2\2\17\21\5\6\4\2\20\16\3")
        buf.write("\2\2\2\21\22\3\2\2\2\22\20\3\2\2\2\22\23\3\2\2\2\23\35")
        buf.write("\3\2\2\2\24\31\5\6\4\2\25\26\7\3\2\2\26\30\5\6\4\2\27")
        buf.write("\25\3\2\2\2\30\33\3\2\2\2\31\27\3\2\2\2\31\32\3\2\2\2")
        buf.write("\32\35\3\2\2\2\33\31\3\2\2\2\34\f\3\2\2\2\34\r\3\2\2\2")
        buf.write("\34\24\3\2\2\2\35\3\3\2\2\2\36\37\5\n\6\2\37\5\3\2\2\2")
        buf.write(" !\7\4\2\2!\"\5\b\5\2\"#\7\5\2\2#$\5\n\6\2$\7\3\2\2\2")
        buf.write("%&\t\2\2\2&\t\3\2\2\2\')\7\f\2\2(\'\3\2\2\2)*\3\2\2\2")
        buf.write("*(\3\2\2\2*+\3\2\2\2+9\3\2\2\2,.\7\3\2\2-,\3\2\2\2.\61")
        buf.write("\3\2\2\2/-\3\2\2\2/\60\3\2\2\2\60\63\3\2\2\2\61/\3\2\2")
        buf.write("\2\62\64\7\f\2\2\63\62\3\2\2\2\64\65\3\2\2\2\65\63\3\2")
        buf.write("\2\2\65\66\3\2\2\2\668\3\2\2\2\67/\3\2\2\28;\3\2\2\29")
        buf.write("\67\3\2\2\29:\3\2\2\2:\13\3\2\2\2;9\3\2\2\2\t\22\31\34")
        buf.write("*/\659")
        return buf.getvalue()


class searchParser ( Parser ):

    grammarFileName = "search.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "' '", "'-'", "':'", "'title'", "'subtitle'", 
                     "'artist'", "'stepartist'", "'rating'", "'bpm'" ]

    symbolicNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "CHAR" ]

    RULE_search_statement = 0
    RULE_song_title = 1
    RULE_tag_statement = 2
    RULE_tag = 3
    RULE_value = 4

    ruleNames =  [ "search_statement", "song_title", "tag_statement", "tag", 
                   "value" ]

    EOF = Token.EOF
    T__0=1
    T__1=2
    T__2=3
    T__3=4
    T__4=5
    T__5=6
    T__6=7
    T__7=8
    T__8=9
    CHAR=10

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.8")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class Search_statementContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def song_title(self):
            return self.getTypedRuleContext(searchParser.Song_titleContext,0)


        def tag_statement(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(searchParser.Tag_statementContext)
            else:
                return self.getTypedRuleContext(searchParser.Tag_statementContext,i)


        def getRuleIndex(self):
            return searchParser.RULE_search_statement

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterSearch_statement" ):
                listener.enterSearch_statement(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitSearch_statement" ):
                listener.exitSearch_statement(self)




    def search_statement(self):

        localctx = searchParser.Search_statementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_search_statement)
        self._la = 0 # Token type
        try:
            self.state = 26
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,2,self._ctx)
            if la_ == 1:
                self.enterOuterAlt(localctx, 1)
                self.state = 10
                self.song_title()
                pass

            elif la_ == 2:
                self.enterOuterAlt(localctx, 2)
                self.state = 11
                self.song_title()
                self.state = 14 
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                while True:
                    self.state = 12
                    self.match(searchParser.T__0)
                    self.state = 13
                    self.tag_statement()
                    self.state = 16 
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)
                    if not (_la==searchParser.T__0):
                        break

                pass

            elif la_ == 3:
                self.enterOuterAlt(localctx, 3)
                self.state = 18
                self.tag_statement()
                self.state = 23
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                while _la==searchParser.T__0:
                    self.state = 19
                    self.match(searchParser.T__0)
                    self.state = 20
                    self.tag_statement()
                    self.state = 25
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)

                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Song_titleContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def value(self):
            return self.getTypedRuleContext(searchParser.ValueContext,0)


        def getRuleIndex(self):
            return searchParser.RULE_song_title

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterSong_title" ):
                listener.enterSong_title(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitSong_title" ):
                listener.exitSong_title(self)




    def song_title(self):

        localctx = searchParser.Song_titleContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_song_title)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 28
            self.value()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class Tag_statementContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def tag(self):
            return self.getTypedRuleContext(searchParser.TagContext,0)


        def value(self):
            return self.getTypedRuleContext(searchParser.ValueContext,0)


        def getRuleIndex(self):
            return searchParser.RULE_tag_statement

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterTag_statement" ):
                listener.enterTag_statement(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitTag_statement" ):
                listener.exitTag_statement(self)




    def tag_statement(self):

        localctx = searchParser.Tag_statementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_tag_statement)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 30
            self.match(searchParser.T__1)
            self.state = 31
            self.tag()
            self.state = 32
            self.match(searchParser.T__2)
            self.state = 33
            self.value()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class TagContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return searchParser.RULE_tag

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterTag" ):
                listener.enterTag(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitTag" ):
                listener.exitTag(self)




    def tag(self):

        localctx = searchParser.TagContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_tag)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 35
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << searchParser.T__3) | (1 << searchParser.T__4) | (1 << searchParser.T__5) | (1 << searchParser.T__6) | (1 << searchParser.T__7) | (1 << searchParser.T__8))) != 0)):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ValueContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def CHAR(self, i:int=None):
            if i is None:
                return self.getTokens(searchParser.CHAR)
            else:
                return self.getToken(searchParser.CHAR, i)

        def getRuleIndex(self):
            return searchParser.RULE_value

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterValue" ):
                listener.enterValue(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitValue" ):
                listener.exitValue(self)




    def value(self):

        localctx = searchParser.ValueContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_value)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 38 
            self._errHandler.sync(self)
            _alt = 1
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt == 1:
                    self.state = 37
                    self.match(searchParser.CHAR)

                else:
                    raise NoViableAltException(self)
                self.state = 40 
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,3,self._ctx)

            self.state = 55
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,6,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 45
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)
                    while _la==searchParser.T__0:
                        self.state = 42
                        self.match(searchParser.T__0)
                        self.state = 47
                        self._errHandler.sync(self)
                        _la = self._input.LA(1)

                    self.state = 49 
                    self._errHandler.sync(self)
                    _alt = 1
                    while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                        if _alt == 1:
                            self.state = 48
                            self.match(searchParser.CHAR)

                        else:
                            raise NoViableAltException(self)
                        self.state = 51 
                        self._errHandler.sync(self)
                        _alt = self._interp.adaptivePredict(self._input,5,self._ctx)
             
                self.state = 57
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,6,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx





