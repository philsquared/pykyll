import calendar
import re
import os
import dateutil.parser
from datetime import datetime
from utils import fatalError
import uuid
import markdown
import codecs
import json


dateParser = re.compile( r'(\d\d\d\d)-(\d\d)-(\d\d)T(\d\d)-(\d\d).md' )
htmlTitleParser = re.compile( r'.*?<h1>(.*?)</h1>(.*)', re.DOTALL )
scriptParser = re.compile( r'.*?<script>(.*?)</script>(.*)', re.DOTALL)

mdTitleParser = re.compile( r'.*?#(.*)', re.DOTALL )

urlReplacements = { 
    "<em>": "",  
    "</em>": "",  
    " ": "-",  
    "/": "-", 
    "\\": "-", 
    "+": "p",
    ";": "-",
    ",": "-",
    "...": "",
    "..": "",
    "'": "",
    '"': "",
    "<": "",
    ">": "",
    "!": "",  
    "*": "",  
    "?": "",  
    "(": "", 
    ")": "",
    "#": "sharp" }

def loadContent( mdFilename ):
    with codecs.open ( mdFilename, "r", "utf-8" ) as contentFile:
        mdText = contentFile.read()
    mdText = mdText.replace("```c++", "```cpp" )
    return markdown.markdown(mdText, extensions=['fenced_code'])

def extractHtmlTitle( name, html ):
    m = htmlTitleParser.match(html)
    if not m:
        fatalError("'{}' does not start with a title (#)".format( name ) )
    title = m.group(1)
    return title, html[len( title )+9:]

def ordinal( n ):
    return "%d%s" % (n,"tsnrhtdd"[(n/10%10!=1)*(n%10<4)*n%10::4])

def replaceAll( str, replacements ):
    keepLooping = True
    while keepLooping:
        keepLooping = False
        for (f, to) in replacements.items():
            newStr = str.replace(f, to)
            if str != newStr:
                str = newStr
                keepLooping = True
    return str

def makeSlug( str ):
    # !TBD: escape more invalid chars
    str = str.lower()
    str = replaceAll( str, urlReplacements )
    str = replaceAll( str, { ".": "-" } )
    str = replaceAll( str, { "--": "-" } )
    return str.strip("-")

def makeTimestampFromFilename( filename ):
    m = dateParser.match( os.path.basename( filename ) )
    if not m:
        fatalError( "Unable to parse filename: '{}' is not a date/time".format( filename ) )
    year = int(m.group(1))
    monthNumber = int(m.group(2))
    day = int(m.group(3))
    hour = int(m.group(4))
    minute = int(m.group(5))
    month = calendar.month_name[monthNumber]

    return "{} {} {} at {}:{}".format( ordinal(day), month, year, str(hour).zfill(2), str(minute).zfill(2) )

class Post:

    # !TBD: refactor so that only <script> header is read in constructor,
    # rest of content is read lazily
    def __init__( self, filename ):
        self.properties = {}
        self.dirty = False

        contentWithMetadata = loadContent( filename )

        m = scriptParser.match( contentWithMetadata )
        if m:
            script = m.group(1)
            try:
                self.properties = json.loads( script )
            except Exception as err:
                print( "Processing " + filename )
                print( script )
                print( "*** " + str(err) )
                raise

            contentWithMetadata = m.group(2)

        if not "version" in self.properties:
            self.properties["version"] = 1
            self.dirty = True
        if not "guid" in self.properties:
            self.properties["guid"] = str(uuid.uuid4())
            self.dirty = True

        m = htmlTitleParser.match(contentWithMetadata)
        if not m:
            print (contentWithMetadata)
            fatalError("'{}' does not start with a title (#)".format( filename ) )
        self.title = m.group(1)
        self.content = m.group(2)

        #self.title, self.content = extractHtmlTitle( filename, contentWithMetadata )

        self.slug = makeSlug( self.title )
        self.filename = filename

    def timestamp(self):        
        return makeTimestampFromFilename( self.filename )

    def datetime(self):        
        basename = os.path.basename( self.filename )
        timestamp = basename[:13] + ":" + basename[14:-3]
        return dateutil.parser.parse( timestamp )

    def updateIfDirty( self ):
        if self.dirty:
            with codecs.open ( self.filename, "r", "utf-8" ) as f:
                allText = f.read()
            m = mdTitleParser.match(allText)
            if not m :
                fatalError("'{}' does not start with a title (#)".format( self.filename ) )
            with codecs.open( self.filename + ".new", "w", "utf-8" ) as outFile:
                outFile.write("<script>\n")
                json.dump(self.properties, outFile, indent=4)
                outFile.write("\n</script>\n\n#")
                outFile.write( m.group(1))
            os.remove(self.filename)
            os.rename(self.filename + ".new", self.filename)

            


