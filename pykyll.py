from templater import Templater

import re
import os
from post import Post, makeDescription
import codecs
import datetime
from urlparse import urlparse
from utils import ensureDirs

timeStripperParser = re.compile( r'(.*?) at .*' )

def stripTime( timestamp ):
    m = timeStripperParser.match( timestamp )
    if m:
        return m.group(1)
    else:
        return timestamp

def formatIf( formatStr, sub ):
    if sub:
        return formatStr.format(sub)
    else:
        return ""

def writePost( rootUrl, postTemplater, post, htmlFile, canonicalUrl, next, prev ):
    postTemplater.vars["title"] = post.title
    postTemplater.vars["timestamp"] = post.timestamp()
    postTemplater.vars["content"] = post.content
    postTemplater.vars["description"] = makeDescription( post.content )
    postTemplater.vars["url"] = canonicalUrl

    if len(post.title) > 25:
        postTemplater.vars["title-class"] = "smallTitle"
    else:
        postTemplater.vars["title-class"] = ""
    
    postTemplater.vars["tags"] = ""
    if "tags" in post.properties:
        tags = post.properties["tags"].split(",")
        postTemplater.vars["tags"] = [tag.strip() for tag in tags]

    postTemplater.vars["next_post"] = formatIf( "<a id='next' href='{}'>Next</a>", next )
    postTemplater.vars["prev_post"] = formatIf( "<a id='prev' href='{}'>Prev</a>", prev )


    if "reddit_url" in post.properties:
        redditUrl = post.properties["reddit_url"]
    else:
        redditUrl = os.path.join( rootUrl, canonicalUrl )

    postTemplater.vars["reddit_url"] = "reddit_url='{}'".format( redditUrl )


    postTemplater.writeFile( htmlFile )

def formatDateForRss( date ):
    return date.strftime(format="%a, %d %b %Y %H:%M:%S %z") + "+0000"

def makeSlugPath( outputFolder, slug ):
    htmlFilename = slug + ".html"
    return os.path.join(outputFolder, htmlFilename)


class Posts:
    def __init__( self, rootUrl, postsFolder, outputFolder, contentFolder="" ):
        self.rootUrl = rootUrl
        self.postsFolder = postsFolder
        self.contentFolder = contentFolder
        self.postInfos = []
        self.redirects = []

        posts = [f for f in os.listdir( postsFolder ) if os.path.isfile(os.path.join( postsFolder, f)) and f.endswith(".md")]
        posts.sort(reverse=True)

        print("Reading posts...")
        for filename in posts:
            post = Post( os.path.join( self.postsFolder, filename ) )
            relativeUrl = makeSlugPath( outputFolder, post.slug )
            postInfo = { \
                "filename": filename, \
                "url": relativeUrl, \
                "htmlFilename": os.path.basename( relativeUrl ), \
                "title": post.title, \
                "timestamp": post.timestamp() }

            self.postInfos.append( postInfo )

            if "redirect" in post.properties:
                url = urlparse( post.properties["redirect"] )
                print( "Path: " + url.path[1:] )

                redirectInfo = { \
                    "url": relativeUrl, \
                    "redirectPath": url.path[1:] } 
                self.redirects.append( redirectInfo )
            
        print("... read")

    def writePost( self, templater, index, relativeUrl = None ):
        postInfo = self.postInfos[index]
        post = Post( os.path.join( self.postsFolder, postInfo["filename"] ) )
        canonicalUrl = postInfo["url"]
        if not relativeUrl:
            relativeUrl = canonicalUrl

        if index < len(self.postInfos)-1:
            prev = self.postInfos[index+1]["htmlFilename"]
        else:
            prev = None
        if index > 0:
            next = self.postInfos[index-1]["htmlFilename"]
        else:
            next = None

        # !TBD: Only write file if timestamp differs (or flag set)
        writePost( self.rootUrl, templater, post, os.path.join( self.contentFolder, relativeUrl ), canonicalUrl=canonicalUrl, next=next, prev=prev )

        # If page properties were generated, write them back
        post.updateIfDirty()

    def writeFirstPost( self ):
        # !TBD: This should go in a template file?
        templater = Templater( "post" )
        self.writePost( templater, 0, "index.html" )

    def writeAllPosts( self ):
        templater = Templater( "post" )
        templater.vars["rootdir"] = "../"

        for i, _ in enumerate(self.postInfos):
            self.writePost( templater, i )

    def writeSummaryPage( self, filename, numberOfPosts = 3 ):
        templater = Templater( "post-summary" )
        templater.vars["rootdir"] = "../"
        templater.vars["title"] = "News"

        propertyList = []
        description = ""

        postInfos = self.postInfos[:numberOfPosts]

        for postInfo in postInfos:
            post = Post( os.path.join( self.postsFolder, postInfo["filename"] ) )
            if description == "":
                description = makeDescription( post.content )

            if len(propertyList) == 0:
                titleClass = ""
            else:
                titleClass = "old-news"

            if len(post.title) > 25:
                titleClass = titleClass + " smallTitle"

            templater.vars["tags"] = ""
            tags = []
            if "tags" in post.properties:
                tags = post.properties["tags"].split(",")
                tags = [tag.strip() for tag in tags]

            postProperties = ( titleClass, post.title, post.timestamp(), tags, post.content, postInfo["url"] )
            propertyList.append( postProperties )

        templater.vars["post-properties"] = propertyList
        templater.vars["description"] = description
        templater.writeFile(filename)


    def writeRedirects( self ):
        redirectTemplater = Templater( "redirect" )
        for redirect in self.redirects:
            redirectPath = os.path.join( self.contentFolder, redirect["redirectPath"] )
            redirectDir = os.path.dirname( redirectPath )
            ensureDirs(redirectDir)
            redirectTemplater.vars["url"] = self.rootUrl + "/" + redirect["url"]
            redirectTemplater.writeFile( redirectPath )


    def writeIndex( self ):
        entries = [(stripTime( entry["timestamp"] ), entry["url"], entry["title"]) for entry in self.postInfos]
        indexTemplater = Templater( "index" )
        indexTemplater.vars["title"] = "Index"
        indexTemplater.vars["entries"] = entries
        indexTemplater.writeFile( os.path.join( self.contentFolder, "post_index.html" ) )

    def writeRss( self, numberOfPosts, name="main.rss" ):
        with codecs.open( os.path.join( self.contentFolder, name ), "w", "utf-8" ) as outFile:
            rssItemTemplater = Templater( "rssItem" )
            rssStartTemplater = Templater( "rssStart" )
            rssStartTemplater.vars["lastBuildDate"] = formatDateForRss( datetime.datetime.now() )

            for line in rssStartTemplater.generateContent():
                outFile.write(line)
            
            postInfos = self.postInfos[0:numberOfPosts]
            for postInfo in postInfos:
                post = Post( os.path.join( self.postsFolder, postInfo["filename"] ) )
                link = os.path.join( self.rootUrl, postInfo["url"] )
                rssItemTemplater.vars["content"] = post.content
                rssItemTemplater.vars["title"] = post.title
                rssItemTemplater.vars["link"] = link
                rssItemTemplater.vars["timestamp"] = formatDateForRss( post.datetime() )
                rssItemTemplater.vars["guid"] = post.properties["guid"]
                if "tags" in post.properties:
                    tags = post.properties["tags"].split(",")
                    rssItemTemplater.vars["tags"] = [tag.strip() for tag in tags]

                for line in rssItemTemplater.generateContent():
                    outFile.write(line)

            rssEndTemplater = Templater( "rssEnd" )
            for line in rssEndTemplater.generateContent():
                outFile.write(line)



