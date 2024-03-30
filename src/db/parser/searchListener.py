# Generated from search.g4 by ANTLR 4.8
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .searchParser import searchParser
else:
    from searchParser import searchParser

# This class defines a complete listener for a parse tree produced by searchParser.


class searchListener(ParseTreeListener):

    # Enter a parse tree produced by searchParser#search_statement.
    def enterSearch_statement(self, ctx: searchParser.Search_statementContext):
        pass

    # Exit a parse tree produced by searchParser#search_statement.
    def exitSearch_statement(self, ctx: searchParser.Search_statementContext):
        pass

    # Enter a parse tree produced by searchParser#song_title.
    def enterSong_title(self, ctx: searchParser.Song_titleContext):
        pass

    # Exit a parse tree produced by searchParser#song_title.
    def exitSong_title(self, ctx: searchParser.Song_titleContext):
        pass

    # Enter a parse tree produced by searchParser#tag_statement.
    def enterTag_statement(self, ctx: searchParser.Tag_statementContext):
        pass

    # Exit a parse tree produced by searchParser#tag_statement.
    def exitTag_statement(self, ctx: searchParser.Tag_statementContext):
        pass

    # Enter a parse tree produced by searchParser#tag.
    def enterTag(self, ctx: searchParser.TagContext):
        pass

    # Exit a parse tree produced by searchParser#tag.
    def exitTag(self, ctx: searchParser.TagContext):
        pass

    # Enter a parse tree produced by searchParser#value.
    def enterValue(self, ctx: searchParser.ValueContext):
        pass

    # Exit a parse tree produced by searchParser#value.
    def exitValue(self, ctx: searchParser.ValueContext):
        pass


del searchParser
