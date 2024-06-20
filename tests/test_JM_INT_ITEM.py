import os
import unittest

branch_coverage = {
    "branch_1": False,
    "branch_2": False,
    "branch_3": False,
    "branch_4": False
}

def JM_INT_ITEM(obj, idx):
    if idx < len(obj):
        branch_coverage["branch_1"] = True
        temp = obj[idx]
        if isinstance(temp, (int, float)):
            branch_coverage["branch_2"] = True
            return 0, temp
        else:
            branch_coverage["branch_3"] = True
    else:
        branch_coverage["branch_4"] = True
    return 1, None

def print_coverage():
    for branch, hit in branch_coverage.items():
        print(f"{branch} was {'hit' if hit else 'not hit'}")

def test_JM_INT_ITEM_within_bounds_returns_0():
    result = JM_INT_ITEM("test", 1)

def test_JM_INT_ITEM_out_of_bounds_returns_1():
    result = JM_INT_ITEM("test", 213)

def test_JM_INT_ITEM_list_within_bounds_returns_0():
    result = JM_INT_ITEM([2, 4, 6, 8], 2)

def test_JM_INT_ITEM_list_out_of_bounds_returns_1():
    result = JM_INT_ITEM([3, 6, 9, 12], 10)

def test_JM_INT_ITEM_empty_returns_1():
    result = JM_INT_ITEM([], 0)

def calculate_coverage():
    hit_branches = 0
    for branch, hit in branch_coverage.items():
        if hit:
          hit_branches = hit_branches + 1
    total_branches = len(branch_coverage)
    coverage = (hit_branches / total_branches) * 100
    print("Coverage is", coverage, "%")

test_JM_INT_ITEM_within_bounds_returns_0()
test_JM_INT_ITEM_out_of_bounds_returns_1()
test_JM_INT_ITEM_list_within_bounds_returns_0()
test_JM_INT_ITEM_list_out_of_bounds_returns_1()
test_JM_INT_ITEM_empty_returns_1()
print_coverage()
calculate_coverage()
