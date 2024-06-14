import os
import unittest

branch_coverage = {
    "branch_1": False,
    "branch_2": False,
    "branch_3": False,
    "branch_4": False
}

def JM_color_FromSequence(color):

    if isinstance(color, (int, float)):
        branch_coverage["branch_1"] = True
        color = [color]

    if not isinstance( color, (list, tuple)):
        branch_coverage["branch_2"] = True
        return -1, []

    if len(color) not in (0, 1, 3, 4):
        branch_coverage["branch_3"] = True
        return -1, []

    ret = color[:]
    for i in range(len(ret)):
        if ret[i] < 0 or ret[i] > 1:
            branch_coverage["branch_4"] = True
            ret[i] = 1
    return len(ret), ret

def print_coverage():
    for branch, hit in branch_coverage.items():
        print(f"{branch} was {'hit' if hit else 'not hit'}")

result = JM_color_FromSequence([0.5])
print_coverage()

result = JM_color_FromSequence([4])
print_coverage()

result = JM_color_FromSequence([4, 0])
print_coverage()

result = JM_color_FromSequence([0, 1, 3, 4])
print_coverage()

result = JM_color_FromSequence([0, -1, -6, 4])
print_coverage()

result = JM_color_FromSequence([0, 1, 7, 4])
print_coverage()

result = JM_color_FromSequence([0, 0, 0, 0])
print_coverage()