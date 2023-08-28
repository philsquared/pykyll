from datetime import datetime
import calendar


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


def ordinal(n: int) -> str:
    """formats a number a 1st, 2nd, 3rd etc"""
    if n in range(11, 19):
        return "%dth" % n
    else:
        return "%d%s" % (n, "tsnrhtdd"[(n / 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])


def format_longdate(dt: datetime) -> str:
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