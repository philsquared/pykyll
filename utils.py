import calendar
import copy
from datetime import datetime
from collections.abc import Mapping


def empty_or_null(string: str):
    return string is None or string == ""


def map_element(data: dict, element_name: str, fun):
    value = data.get(element_name)
    if value:
        data[element_name] = fun(value)
        return True
    else:
        return False


def join(items: list, seperator: str, last_seperator: str):
    return last_seperator.join(filter(None, [seperator.join(items[:-1])] + items[-1:]))


def dict_merge(d1: Mapping, d2: Mapping) -> dict:
    """
    Performs a "deep merge" of two dictionaries.
    Any values in the 2nd dict overwrite values for the same key in the 1st
    - unless they are both dictionaries, in which case the process recurses into them
    """
    if not d1:
        return d2
    if not d2:
        return d1
    merged = dict(copy.deepcopy(d1))
    for k, v in d2.items():
        if k in d1 and isinstance(v, Mapping):
            v1 = d1[k]
            if isinstance(v1, Mapping):
                v = dict_merge(v1, v)
        merged[k] = v
    return merged


def ordinal(n: int) -> str:
    """formats a number a 1st, 2nd, 3rd etc"""
    if n in range(11, 19):
        return "%dth" % n
    else:
        return "%d%s" % (n, "tsnrhtdd"[(n / 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])


def format_longdate(dt: datetime) -> str:
    """
    formats a date as, e.g. 1st May 2022
    """
    month_name = calendar.month_name[dt.month]
    return f"{ordinal(dt.day)} {month_name} {dt.year}"


def format_time(dt: datetime) -> str:
    return f"{dt.hour:02d}:{dt.minute:02d}"


def format_datetime_for_blog(dt: datetime) -> str:
    return f"{format_longdate(dt)} at {format_time(dt)}"


def format_datetime_for_rss(date):
    return date.strftime(format="%a, %d %b %Y %H:%M:%S %z") + "+0000"


def exhaustive_replace(text: str, replacements: {str, str}) -> str:
    """
    Keeps replacing strings until no replacements are made
    """
    keep_looping = True
    while keep_looping:
        keep_looping = False
        for (f, to) in replacements.items():
            replaced = text.replace(f, to)
            if text != replaced:
                text = replaced
                keep_looping = True
    return text


def truncate_text_by_sentence(text: str, max_length: int, allow_sentence_to_be_cut=False) -> str:
    paragraphs = [paragraph.strip() for paragraph in text.split("\n")]
    truncated = ""

    for p in [p for p in paragraphs if p != ""]:
        sentences = [sentence.strip() for sentence in p.split(".")]

        for i, sentence in enumerate(sentences):
            if i == 0:
                longer_text = truncated + sentence
            elif sentence == "":
                longer_text = truncated + "."
            else:
                longer_text = truncated + ". " + sentence
            if len(longer_text) <= max_length:
                truncated = longer_text
            else:
                if len(truncated) == 0:
                    if allow_sentence_to_be_cut:
                        truncated = longer_text[:max_length].strip()
                    else:
                        truncated = longer_text
                return truncated.strip()
        truncated = truncated.strip() + "\n"
    return truncated.strip()


def reduce_text_to(text: str, max_len: int) -> str:
    """
    First reduces by sentence, then by comma.
    Throws if it can't reduce enough
    """
    original_text = text
    text = truncate_text_by_sentence(text, max_len)
    while len(text) > max_len:
        comma = text.find(",")
        if comma != -1:
            text = text[:comma]
        else:
            bracket = text.find("(")
            if bracket != -1:
                text = text[:bracket]
            else:
                raise Exception("Could not condense summary text: " + original_text)
    return text


def common_prefix(str1: str, str2: str) -> str:
    """
    Finds the longest matching substring at the start of the two supplied strings
    """
    common_len = min(len(str1), len(str2))
    for c in range(0, common_len):
        if str1[c] != str2[c]:
            return str1[0:c]
    return str1[0:common_len]


def common_suffix(range1: str | list, range2: str | list) -> str:
    """
    Finds the longest matching sub-range at the end of the two supplied strings or lists
    """
    if type(range1) is str:
        default_value = ""
    else:
        default_value = []

    common_len = min(len(range1), len(range2))
    if common_len == 0:
        return default_value
    for c in range(1, common_len+1):
        if range1[-c] != range2[-c]:
            if c == 1:
                return default_value
            else:
                return range1[-(c - 1):]
    return range1[-common_len:]

