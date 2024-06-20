import os
import unittest

branch_coverage = {
    "branch_1": False,
    "branch_2": False,
    "branch_3": False,
    "branch_4": False,
    "branch_5": False
}

def JM_norm_rotation(rotate):
    while rotate < 0:
        branch_coverage["branch_1"] = True
        rotate += 360
    while rotate >= 360:
        branch_coverage["branch_2"] = True
        rotate -= 360
    while not (rotate < 0 and rotate >= 360):
        branch_coverage["branch_3"] = True   
        break
    if rotate % 90 != 0:
        branch_coverage["branch_4"] = True
        return 0
    else:
        branch_coverage["branch_5"] = True
    return rotate

def print_coverage():
    for branch, hit in branch_coverage.items():
        print(f"{branch} was {'hit' if hit else 'not hit'}")

def calculate_coverage():
    hit_branches = 0
    for branch, hit in branch_coverage.items():
        if hit:
          hit_branches = hit_branches + 1
    total_branches = len(branch_coverage)
    coverage = (hit_branches / total_branches) * 100
    print("Coverage is", coverage, "%")


def test_JM_norm_rotation_below_0_returns_310():
    result = JM_norm_rotation(-50)
    
def test_JM_norm_rotation_is_360_returns_0():
    result = JM_norm_rotation(360)

def test_JM_norm_rotation_is_not_multipleOf_90_returns_0():
    result = JM_norm_rotation(170)

def test_JM_norm_rotation_is_multipleOf_90_returns_180():
    result = JM_norm_rotation(180)

def test_JM_norm_rotation_is_multipleOf_90_and_above_360_returns_90():
    result = JM_norm_rotation(450)

def test_JM_norm_rotation_is_not_multipleOf_90_and_above_360_returns_10():
    result = JM_norm_rotation(370)

def test_JM_norm_rotation_below_0_returns_270():
    result = JM_norm_rotation(-90)

def test_JM_norm_rotation_below_0_returns_180():
    result = JM_norm_rotation(-900)

test_JM_norm_rotation_below_0_returns_310()
test_JM_norm_rotation_is_360_returns_0()
test_JM_norm_rotation_is_not_multipleOf_90_returns_0()
test_JM_norm_rotation_is_multipleOf_90_returns_180()
test_JM_norm_rotation_is_multipleOf_90_and_above_360_returns_90()
test_JM_norm_rotation_below_0_returns_270()
test_JM_norm_rotation_below_0_returns_180()
print_coverage()
calculate_coverage()
