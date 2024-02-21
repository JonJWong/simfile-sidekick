from .searchListener import searchListener
from .searchParser import searchParser

class parserListener(searchListener):
    def __init__(self):
        self._queryObject = {
            'title': None,
            'subtitle': None,
            'artist': None,
            'stepartist': None,
            'rating': None,
            'bpm': None
        }

        self._currentQuery = {}
        self._resetCurrentQuery()

    def _resetCurrentQuery(self):
        self._currentQuery = {'tag': None, 'value': None} 

    def getQueryObject(self):
        return self._queryObject

    # Enter a parse tree produced by searchParser#song_title.
    def exitSong_title(self, ctx:searchParser.Song_titleContext):
        self._queryObject['title'] = ctx.getText()

    # Enter a parse tree produced by searchParser#tag_statement.
    def exitTag_statement(self, ctx:searchParser.Tag_statementContext):
        tag = self._currentQuery["tag"]
        value = self._currentQuery["value"]

        self._queryObject[tag]=value
        self._resetCurrentQuery()

    # Enter a parse tree produced by searchParser#tag.
    def enterTag(self, ctx:searchParser.TagContext):
        self._currentQuery['tag'] = ctx.getText()

    # Enter a parse tree produced by searchParser#value.
    def enterValue(self, ctx:searchParser.ValueContext):
        self._currentQuery['value'] = ctx.getText()
