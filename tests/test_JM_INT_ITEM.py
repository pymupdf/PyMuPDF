import os
import unittest

branch_coverage = {
    "branch_1": False,
    "branch_2": False,
    "branch_3": False,
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
    return 1, None

def print_coverage():
    for branch, hit in branch_coverage.items():
        print(f"{branch} was {'hit' if hit else 'not hit'}")

def test_JM_INT_ITEM_within_bounds_returns_0():
    result = JM_INT_ITEM("test", 1)
    print_coverage()

def test_JM_INT_ITEM_out_of_bounds_returns_1():
    result = JM_INT_ITEM("test", 213)
    print_coverage()

def test_JM_INT_ITEM_list_within_bounds_returns_0():
    result = JM_INT_ITEM([2, 4, 6, 8], 2)
    print_coverage()

def test_JM_INT_ITEM_list_out_of_bounds_returns_1():
    result = JM_INT_ITEM([3, 6, 9, 12], 10)
    print_coverage()

def test_JM_INT_ITEM_empty_returns_1():
    result = JM_INT_ITEM([], 0)
    print_coverage()

test_JM_INT_ITEM_within_bounds_returns_0()
test_JM_INT_ITEM_out_of_bounds_returns_1()
test_JM_INT_ITEM_list_within_bounds_returns_0()
test_JM_INT_ITEM_list_out_of_bounds_returns_1()
test_JM_INT_ITEM_empty_returns_1()
