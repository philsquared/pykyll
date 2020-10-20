import re

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
    str = str.lower()
    str = replace_all( str, urlReplacements )
    str = replace_all( str, { ".": "-" } )
    str = replace_all( str, { "--": "-" } )
    return str.strip("-")


def remove_tags(text):
    tagParser = re.compile(r'(.*?)<(.*?)>(.*)', re.DOTALL)
    keepLooping = True
    while keepLooping:
        m = tagParser.match( text )
        if m:
            text = m.group(1) + m.group(3)
        else:
            keepLooping = False
    return text


def split_into_sentences( str ):
    # !TBD: make this more sophisticated - e.g. don't split on . used for abbreviations, split on : ond other chars
    sentences = [sentence.strip() for sentence in re.split( "\.[ \n\t]", str )]
    # sentences = [sentence.strip() for sentence in re.split( "\.", str )]
    return sentences


def make_description( content, maxDescriptionLength = 300, attributeSafe = True ):
    content = remove_tags(content)

    # remove anything that shouldn't be in an attribiute
    if attributeSafe:
        content = replace_all(content, {
            '"': "'",
            "\n": " ",
            "\t": " ",
            "  ": " ",
            "!": ".",
            "?": "." })

    # !TBD: more substitutions?

    sentences = split_into_sentences( content )

    description = ""
    for sentence in sentences:
        biggerDescription = description + sentence + ". "
        if len( biggerDescription ) < maxDescriptionLength:
            description = biggerDescription
        else:
            if len( description ) == 0:
                description = biggerDescription[:maxDescriptionLength]
            break
    return description.strip().strip(".").strip()
