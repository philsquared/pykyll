import os
import re
import uuid
from datetime import datetime
import dateutil.parser
from .page import Page

scriptParser = re.compile( r'.*?<script>(.*?)</script>(.*)', re.DOTALL)
htmlTitleParser = re.compile( r'.*?<h1>(.*?)</h1>(.*)', re.DOTALL )

urlReplacements = {
    "<em>": "",
    "</em>": "",
    " ": "-",
    "/": "-",
    "\\": "-",
    "+": "p",
    ";": "-",
    ":": "",
    ",": "-",
    "...": "",
    "..": "",
    "'": "",
    '"': "",
    "`": "",
    "<": "",
    ">": "",
    "!": "",
    "*": "",
    "?": "",
    "(": "",
    ")": "",
    "#": "sharp" }


def replace_all(str, replacements):
    keepLooping = True
    while keepLooping:
        keepLooping = False
        for (f, to) in replacements.items():
            newStr = str.replace(f, to)
            if str != newStr:
                str = newStr
                keepLooping = True
    return str


def make_slug( str ):
    # !TBD: escape more invalid chars?
    str = str.encode('ascii', 'ignore').decode("utf-8")
    str = str.lower()
    str = replace_all( str, urlReplacements )
    str = replace_all( str, { ".": "-" } )
    str = replace_all( str, { "--": "-" } )
    return str.strip("-")

def make_user_slug( name ):
    return replace_all( make_slug( replace_all( name, { " ": "_", ".": "_" } ) ), { "__": "_" } )


def ordinal( n ):
    if n in range(11, 19):
        return "%dth" % (n)
    else:
        return "%d%s" % (n,"tsnrhtdd"[(n/10%10!=1)*(n%10<4)*n%10::4])

def format_date(dt):
    import calendar
    monthName = calendar.month_name[dt.month]
    return "{} {} {}".format( ordinal(dt.day), monthName, dt.year )

def format_datetime(dt):
    import calendar
    monthName = calendar.month_name[dt.month]
    return "{} {} {} at {}:{}".format( ordinal(dt.day), monthName, dt.year, str(dt.hour).zfill(2), str(dt.minute).zfill(2) )

def format_date_for_rss(date):
    return date.strftime(format="%a, %d %b %Y %H:%M:%S %z") + "+0000"


class PostMetadata:
    def __init__( self ):
        self.filename = None
        self.title = None
        self.slug = None
        self.timestamp = None
        self.guid = None
        self.version = None
        self.file_timestamp = None

        # computed
        self.page = None # local page name
        self.url = None
        self.formatted_timestamp = None
        self.rss_formatted_timestamp = None


class Post:
    def __init__(self, filename, base_url ):
        self.metadata = PostMetadata()
        self.properties = {}
        self.html = None
        self.page = None

        self.metadata.filename = filename
        self.metadata.title = None
        self.isDraft = "draft" in filename

        if self.isDraft:
            self.metadata.timestamp = datetime.now()

        else:
            basename = os.path.basename(filename)
            timestamp = basename[:13] + ":" + basename[14:-3]
            self.metadata.timestamp =  dateutil.parser.parse( timestamp )

        self.metadata.formatted_timestamp = format_datetime( self.metadata.timestamp )
        self.metadata.rss_formatted_timestamp = format_date_for_rss(self.metadata.timestamp)


        page = Page( filename )
        self.metadata.title = page.title
        self.properties = page.properties

        self.metadata.slug = self.properties.get("slug")
        self.metadata.guid = self.properties.get("guid")
        self.metadata.version = self.properties.get("version")
        self.metadata.page_image = self.properties.get("page-image")

        if not self.metadata.slug:
            self.metadata.slug = make_slug( self.metadata.title )
        if not self.metadata.guid:
            self.metadata.guid = str(uuid.uuid4())
        if not self.metadata.version:
            self.metadata.version = 0

        self.metadata.page = "{}.html".format( self.metadata.slug )
        self.metadata.url = "{}/{}".format( base_url, self.metadata.page )


    def property_changed_or_missing(self, name, value, optional=False):
        prop = self.properties.get(name)
        if not prop:
            if optional:
                print("  '{}' missing".format(name))
            elif value:
                self.properties[name] = value
                return True
        elif prop != value:
            print("  '{}' changed".format(name))
            self.properties[name] = value
            return True

        return False


    def has_changed(self):
        changed = False
        if self.properties == {}:
            print( "  No properties" )
            changed = True

        changed = self.property_changed_or_missing( "slug", self.metadata.slug ) or changed
        changed = self.property_changed_or_missing( "guid", self.metadata.guid ) or changed
        hash_changed = self.property_changed_or_missing( "hash", self.page.hash() )
        changed = changed or hash_changed
        if changed:
            # If anything changed, bump the version # and recompute the hash
            self.metadata.version = self.metadata.version+1
            self.properties["version"] = self.metadata.version
            self.property_changed_or_missing( "hash", self.page.hash() )
        return changed

    def read_content(self):
        if not self.html:
            self.page = Page(self.metadata.filename)
            self.html = self.page.html

    def get_html(self):
        self.read_content()
        return self.html

    def save_if_updated(self):
        if self.has_changed():
            print("'{}' has changed - saving".format(self.metadata.title))
            self.page.properties = self.properties
            self.page.write()
            return True
        else:
            return False

    def save(self):
        self.has_changed()
        self.page.properties = self.properties
        self.page.write()


def load_posts( dir, base_url ):
    post_filenames = [f for f in os.listdir(dir) if os.path.isfile(os.path.join(dir, f)) and f.endswith(".md")]
    post_filenames.sort(reverse=True)

    posts = [Post(os.path.join(dir, filename), base_url) for filename in post_filenames]
    return posts

def update_posts( dir, posts, forceRebuild ):
    if forceRebuild:
        for post in posts:
            post.save()
        return True
    else:
        changed = False
        for post in posts:
            changed = post.save_if_updated() or changed
        return changed
