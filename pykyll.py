from .templater import Templater

import re
import os
from .post import Post, makeDescription
import codecs
import datetime
from urllib.parse import urlparse
from .utils import ensureDirs

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

def addRedditUrl( templater, post, rootUrl, canonicalUrl ):
    if "reddit_url" in post.properties:
        redditUrl = post.properties["reddit_url"]
    else:
        redditUrl = os.path.join( rootUrl, canonicalUrl )

        templater.vars["reddit_url"] = "reddit_url='{}'".format( redditUrl )


def writePost( rootUrl, postTemplater, post, htmlFile, canonicalUrl, next, prev, nextTitle="next", prevTitle="prev" ):
    postTemplater.vars["title"] = post.title
    postTemplater.vars["timestamp"] = post.timestamp
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

    if next:
        postTemplater.vars["next_post_title"] = nextTitle
        postTemplater.vars["next_post_url"] = next
    if prev:
        postTemplater.vars["prev_post_title"] = prevTitle
        postTemplater.vars["prev_post_url"] = prev


    if "reddit_url" in post.properties:
        redditUrl = post.properties["reddit_url"]
    else:
        redditUrl = os.path.join( rootUrl, canonicalUrl )

    addRedditUrl( postTemplater, post, rootUrl, canonicalUrl )

    postTemplater.writeFile( htmlFile )

def formatDateForRss( date ):
    return date.strftime(format="%a, %d %b %Y %H:%M:%S %z") + "+0000"

def makeSlugPath( outputFolder, slug ):
    htmlFilename = slug + ".html"
    return os.path.join(outputFolder, htmlFilename)


class Posts:
    def __init__( self, rootUrl, postsFolder, outputFolder, contentFolder="", seedVars={} ):
        self.rootUrl = rootUrl
        self.postsFolder = postsFolder
        self.contentFolder = contentFolder
        self.postInfos = []
        self.draftPostInfos = []
        self.redirects = []
        self.seedVars = seedVars

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
                "timestamp": post.timestamp }

            if post.isDraft:
                self.draftPostInfos.append( postInfo )
            else:
                self.postInfos.append( postInfo )

            if "redirect" in post.properties:
                url = urlparse( post.properties["redirect"] )
                print( "Path: " + url.path[1:] )

                redirectInfo = { \
                    "url": relativeUrl, \
                    "redirectPath": url.path[1:] } 
                self.redirects.append( redirectInfo )
            
        print("... read")

    def writePostInternal( self, templater, postInfo, prev = None, next = None, nextTitle=None, prevTitle=None, relativeUrl = None ):
        post = Post( os.path.join( self.postsFolder, postInfo["filename"] ) )
        canonicalUrl = postInfo["url"]
        if not relativeUrl:
            relativeUrl = canonicalUrl


        # !TBD: Only write file if timestamp differs (or flag set)
        writePost( self.rootUrl, templater, post, os.path.join( self.contentFolder, relativeUrl ), canonicalUrl=canonicalUrl, next=next, prev=prev, nextTitle=nextTitle, prevTitle=prevTitle )

        # If page properties were generated, write them back
        post.updateIfDirty()

    def writePost( self, templater, index, relativeUrl = None ):
        postInfo = self.postInfos[index]

        if index < len(self.postInfos)-1:
            prev = self.postInfos[index+1]["htmlFilename"]
            prevTitle = self.postInfos[index+1]["title"]
        else:
            prev = None
            prevTitle=None
        if index > 0:
            next = self.postInfos[index-1]["htmlFilename"]
            nextTitle = self.postInfos[index - 1]["title"]
        else:
            next = None
            nextTitle = None

        self.writePostInternal( templater, postInfo, prev, next, prevTitle=prevTitle, nextTitle=nextTitle, relativeUrl=relativeUrl )

    def writeDraftPost( self, postInfo, templater ):
        self.writePostInternal( templater, postInfo )

    def addSeedVars(self, templater):
        for k, v in self.seedVars.items():
            templater.vars[k] = v

    def writeFirstPost( self ):
        # !TBD: This should go in a template file?
        templater = Templater( "post" )
        self.addSeedVars( templater );
        self.writePost( templater, 0, "index.html" )

    def writeAllPosts( self ):
        templater = Templater( "post" )
        templater.vars["rootdir"] = "../"
        self.addSeedVars( templater );

        print( "Generating posts: >>>" )
        for i, _ in enumerate(self.postInfos):
            self.writePost( templater, i )
        print( "<<< done" )

        if len(self.draftPostInfos) > 0:
            print("Generating drafts: >>>")
            for postInfo in self.draftPostInfos:
                self.writeDraftPost( postInfo, templater )
            print("<<< done")

    def summarise( self, numberOfPosts = 3, titlePrefix = "" ):
        propertyList = []
        olderPropertyList = []
        description = ""

        postInfos = self.postInfos

        for i, postInfo in enumerate(postInfos):
            post = Post( os.path.join( self.postsFolder, postInfo["filename"] ) )
            if description == "":
                description = makeDescription( post.content )

            if len(propertyList) == 0:
                titleClass = ""
            else:
                titleClass = "old-news"

            if len(post.title) > 25:
                titleClass = titleClass + " smallTitle"

            tags = []
            if "tags" in post.properties:
                tags = post.properties["tags"].split(",")
                tags = [tag.strip() for tag in tags]

            url = postInfo["url"]
            rootedUrl = "reddit_url='{}'".format( os.path.join( self.rootUrl, url ) )
            postProperties = (titleClass, titlePrefix + post.title, post.timestamp, tags, post.content, url, rootedUrl)

            if i < numberOfPosts:
                propertyList.append( postProperties )
            else:
                olderPropertyList.append(postProperties)

        return propertyList, olderPropertyList, description, tags


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
                rssItemTemplater.vars["timestamp"] = formatDateForRss( post.datetime )
                rssItemTemplater.vars["guid"] = post.properties["guid"]
                if "tags" in post.properties:
                    tags = post.properties["tags"].split(",")
                    rssItemTemplater.vars["tags"] = [tag.strip() for tag in tags]

                for line in rssItemTemplater.generateContent():
                    outFile.write(line)

            rssEndTemplater = Templater( "rssEnd" )
            for line in rssEndTemplater.generateContent():
                outFile.write(line)



