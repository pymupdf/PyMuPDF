import os
import unittest

branch_coverage = {
    "branch_1": False,
    "branch_2": False
}

def JM_UnicodeFromStr(s):
    if s is None:
        branch_coverage["branch_1"] = True
        return ''
    if isinstance(s, bytes):
        branch_coverage["branch_2"] = True
        s = s.decode('utf8')
    assert isinstance(s, str), f'{type(s)=} {s=}'
    return s

def print_coverage():
    for branch, hit in branch_coverage.items():
        print(f"{branch} was {'hit' if hit else 'not hit'}")

result = JM_UnicodeFromStr(None)
print_coverage()

result = JM_UnicodeFromStr(b"xxx")
print_coverage()
