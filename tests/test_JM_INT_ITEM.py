import os
import unittest

branch_coverage = {
    "branch_1": False,
    "branch_2": False,
}

def JM_INT_ITEM(obj, idx):
    if idx < len(obj):
        branch_coverage["branch_1"] = True
        temp = obj[idx]
        if isinstance(temp, (int, float)):
            return 0, temp
    else:
        branch_coverage["branch_2"] = True
    return 1, None

def print_coverage():
    for branch, hit in branch_coverage.items():
        print(f"{branch} was {'hit' if hit else 'not hit'}")

result = JM_INT_ITEM("test", 1)
print_coverage()

result = JM_INT_ITEM("test", 213)
print_coverage()
