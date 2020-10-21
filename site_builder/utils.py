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
            if m.group(2) == "/p":
                text = m.group(1) + "\n" + m.group(3)
            else:
                text = m.group(1) + m.group(3)
        else:
            keepLooping = False
    return text


def find_last_of( str, tokens ):
    lastPositions = list(filter(lambda pos : pos > -1, [str.rfind(token) for token in tokens]))
    if len(lastPositions) > 0:
        return min( lastPositions )
    else:
        return -1


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

    content = content.strip()

    if len(content) <= maxDescriptionLength:
        return content

    truncatedContent = content[:maxDescriptionLength]
    lastSplitPoint = find_last_of( truncatedContent, [". ", ".\n", ".\t"] )
    if lastSplitPoint == -1:
        lastSplitPoint = find_last_of( truncatedContent, [" ", "\t", "\n"] )

    if lastSplitPoint != -1:
        truncatedContent = truncatedContent[:lastSplitPoint]

    return truncatedContent.strip().strip(".").strip()
