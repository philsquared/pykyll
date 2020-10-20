import codecs
import json
import markdown
import re
import os
import hashlib
import copy

scriptParser = re.compile( r'.*?<script>(.*?)</script>(.*)', re.DOTALL)
htmlTitleParser = re.compile( r'.*?<h1>(.*?)</h1>(.*)', re.DOTALL )


class Page:
    def __init__(self, filename, read_chars = None, needs_title=True ):
        self.filename = filename
        self.properties = {}
        self.title = None
        self.markdown = None
        self.html = None

        with codecs.open ( filename, "r", "utf-8" ) as file:
            if read_chars:
                buffer = file.read( read_chars )
            else:
                buffer = file.read()

        m = scriptParser.match( buffer )
        if m:
            script = m.group(1)
            try:
                self.properties = json.loads( script )
            except Exception as err:
                print( "Processing " + filename )
                print( script )
                print( "*** " + str(err) )
                raise
            self.markdown = m.group(2)
        else:
            self.markdown = buffer

        html_content = markdown.markdown( self.markdown, extensions=['fenced_code'] )
        m = htmlTitleParser.match( html_content )
        if not m:
            if needs_title:
                print( html_content )
                raise Exception("'{}' does not start with a title (#)".format( filename ) )
            else:
                self.html = html_content
        else:
            self.title = m.group(1)
            self.html = m.group(2)

    def hash(self):
        return hashlib.sha256( self.html.encode() ).hexdigest()

    def write(self):
        with codecs.open( self.filename + ".new", "w", "utf-8" ) as outFile:
            outFile.write( "<script>\n" )
            json.dump( self.properties, outFile, sort_keys=True, indent=4 )
            outFile.write( "\n</script>\n\n" )
            outFile.write( self.markdown.strip("\n") )
        os.remove(self.filename)
        os.rename(self.filename + ".new", self.filename)
