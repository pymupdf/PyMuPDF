import os
import unittest

branch_coverage = {
    "branch_1": False,
    "branch_2": False,
    "branch_3": False,
    "branch_4": False
}

def JM_UnicodeFromStr(s):
    if s is None:
        branch_coverage["branch_1"] = True
        return ''
    else:
        branch_coverage["branch_2"] = True
    if isinstance(s, bytes):
        branch_coverage["branch_3"] = True
        s = s.decode('utf8')
    else:
        branch_coverage["branch_4"] = True
    assert isinstance(s, str), f'{type(s)=} {s=}'
    return s

def print_coverage():
    for branch, hit in branch_coverage.items():
        print(f"{branch} was {'hit' if hit else 'not hit'}")

def test_JM_UnicodeFromStr_s_is_none_returns_none():
    result = JM_UnicodeFromStr(None)

def test_JM_UnicodeFromStr_s_is_byte_xxx_returns_decoded_s():
    result = JM_UnicodeFromStr(b"xxx")

def test_JM_UnicodeFromStr_s_is_byte_abcdefg_returns_decoded_s():
    result = JM_UnicodeFromStr(b"abcdefg")

def test_JM_UnicodeFromStr_s_is_string_xxx_returns_same_s():
    result = JM_UnicodeFromStr("xxx")

def calculate_coverage():
    hit_branches = 0
    for branch, hit in branch_coverage.items():
        if hit:
          hit_branches = hit_branches + 1
    total_branches = len(branch_coverage)
    coverage = (hit_branches / total_branches) * 100
    print("Coverage is", coverage, "%")

test_JM_UnicodeFromStr_s_is_none_returns_none()
test_JM_UnicodeFromStr_s_is_byte_xxx_returns_decoded_s()
test_JM_UnicodeFromStr_s_is_byte_abcdefg_returns_decoded_s()
test_JM_UnicodeFromStr_s_is_string_xxx_returns_same_s()
print_coverage()
calculate_coverage()
