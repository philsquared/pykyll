from pykyll.fileutils import path_diff
from pykyll.utils import ordinal, exhaustive_replace, truncate_text_by_sentence, common_prefix, dict_merge


def test_ordinals():
    ordinals = ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th", "10th",
                "11th", "12th", "13th", "14th", "15th", "16th", "17th", "18th", "19th", "20th",
                "21st", "22nd", "23rd", "24th", "25th", "26th", "27th", "28th", "29th", "30th",
                "31st", "32nd", "33rd"]
    for i, o in enumerate(ordinals):
        assert ordinal(i+1) == o

    assert ordinal(100) == "100th"
    assert ordinal(101) == "101st"

    assert ordinal(1000) == "1000th"
    assert ordinal(1001) == "1001st"


def test_exhaustive_replace():
    assert exhaustive_replace("abcd", {"b": "a", "d": "c", "c": "b"}) == "aaaa"


def test_truncate_text_by_sentence():
    sentences = ["This is a really long sentence", "This is an even longer sentence"]
    text = ". ".join(sentences)
    assert truncate_text_by_sentence(text, 200) == text
    assert truncate_text_by_sentence(text, 63) == text
    assert truncate_text_by_sentence(text, 62) == sentences[0]
    assert truncate_text_by_sentence(text, 40) == sentences[0]
    assert truncate_text_by_sentence(text, 10) == sentences[0]
    assert truncate_text_by_sentence(text, 10, allow_sentence_to_be_cut=True) == "This is a"


def test_common_prefix():
    assert common_prefix("abcdef", "abcxyz") == "abc"
    assert common_prefix("abc", "abc") == "abc"
    assert common_prefix("", "") == ""
    assert common_prefix("abc", "") == ""
    assert common_prefix("", "abc") == ""
    assert common_prefix("abcd", "abc") == "abc"
    assert common_prefix("abc", "abcd") == "abc"


def test_path_diff():
    assert path_diff("web/static/css", "web/static/fonts") == "../fonts"
    assert path_diff("web/static/css/", "web/static/fonts") == "../fonts"
    assert path_diff("web/static/css/sub", "web/static/fonts") == "../../fonts"
    assert path_diff("web/static/samedir", "web/static/samedir") == ""
    assert path_diff("web/static", "web/static/fonts") == "fonts"
    assert path_diff("web/static/css", "web/static") == "../"


def test_dict_merge():
    d1 = {
        "one": 42,
        "two": 7,
        "three": {
            "inner1": "hello",
            "array": [1, 2, 3, 4]
        }
    }
    d2 = {
        "two": 100,
        "three": {
            "array": [1, 1, 2, 3, 5],
            "new_key": 99
        },
        "other": "value"
    }

    d1_2 = {
        "one": 42,
        "two": 100,
        "three": {
            "inner1": "hello",
            "array": [1, 1, 2, 3, 5],
            "new_key": 99
        },
        "other": "value"
    }
    d3 = {
        "three": {
            "four": {
                "key": "value"
            }
        }
    }
    d1_3 = {
        "one": 42,
        "two": 7,
        "three": {
            "inner1": "hello",
            "array": [1, 2, 3, 4],
            "four": {
                "key": "value"
            }
        }
    }
    d2_3 = {
        "two": 100,
        "three": {
            "array": [1, 1, 2, 3, 5],
            "new_key": 99,
            "four": {
                "key": "value"
            }
        },
        "other": "value"
    }

    assert dict_merge(d1, {}) == d1
    assert dict_merge({}, d2) == d2
    assert dict_merge(d1, d2) == d1_2
    assert dict_merge(d1, d3) == d1_3
    assert dict_merge(d2, d3) == d2_3
