import os
import unittest

branch_coverage = {
    "branch_1": False,
    "branch_2": False, 
}

def _int_rc(text):
    rc = text.find('rc')
    if rc >= 0:
        branch_coverage["branch_1"] = True
        text = text[:rc]
    else:
        branch_coverage["branch_2"] = True
    return int(text)

def print_coverage():
    for branch, hit in branch_coverage.items():
        print(f"{branch} was {'hit' if hit else 'not hit'}")

result = _int_rc("9876")
print_coverage()

result = _int_rc("-333")
print_coverage()

result = _int_rc("333rc")
print_coverage()