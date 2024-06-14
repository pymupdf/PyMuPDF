import os
import unittest

branch_coverage = {
    "branch_1": False,
    "branch_2": False,
    "branch_3": False,
    "branch_4": False
}

def JM_norm_rotation(rotate):
    while rotate < 0:
        branch_coverage["branch_1"] = True
        rotate += 360
    while rotate >= 360:
        branch_coverage["branch_2"] = True
        rotate -= 360
    if rotate % 90 != 0:
        branch_coverage["branch_3"] = True
        return 0

    branch_coverage["branch_4"] = True
    return rotate

def print_coverage():
    for branch, hit in branch_coverage.items():
        print(f"{branch} was {'hit' if hit else 'not hit'}")

def test_JM_norm_rotation_below_0_returns_310():
    result = JM_norm_rotation(-50)
    print_coverage()
    
def test_JM_norm_rotation_is_360_returns_0():
    result = JM_norm_rotation(360)
    print_coverage()

def test_JM_norm_rotation_is_not_multipleOf_90_returns_0():
    result = JM_norm_rotation(170)
    print_coverage()

def test_JM_norm_rotation_is_multipleOf_90_returns_180():
    result = JM_norm_rotation(180)
    print_coverage()

def test_JM_norm_rotation_is_multipleOf_90_and_above_360_returns_90():
    result = JM_norm_rotation(450)
    print_coverage()

def test_JM_norm_rotation_is_not_multipleOf_90_and_above_360_returns_10():
    result = JM_norm_rotation(370)
    print_coverage()

def test_JM_norm_rotation_below_0_returns_270():
    result = JM_norm_rotation(-90)
    print_coverage()

def test_JM_norm_rotation_below_0_returns_180():
    result = JM_norm_rotation(-900)
    print_coverage()

test_JM_norm_rotation_below_0_returns_310()
test_JM_norm_rotation_is_360_returns_0()
test_JM_norm_rotation_is_not_multipleOf_90_returns_0()
test_JM_norm_rotation_is_multipleOf_90_returns_180()
test_JM_norm_rotation_is_multipleOf_90_and_above_360_returns_90()
test_JM_norm_rotation_below_0_returns_270()
test_JM_norm_rotation_below_0_returns_180()
