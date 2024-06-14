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

result = JM_norm_rotation(-50)
print_coverage()

result = JM_norm_rotation(360)
print_coverage()

result = JM_norm_rotation(170)
print_coverage()

result = JM_norm_rotation(180)
print_coverage()

result = JM_norm_rotation(450)
print_coverage()