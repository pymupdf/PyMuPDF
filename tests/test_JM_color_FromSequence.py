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

def test_JM_color_FromSequence_is_float_returns_1_and_ret():
    result = JM_color_FromSequence([0.5])
    print_coverage()

def test_JM_color_FromSequence_is_negFloat_returns_1_and_ret():
    result = JM_color_FromSequence([-0.5])
    print_coverage()

def test_JM_color_FromSequence_is_int_returns_1_and_0():
    result = JM_color_FromSequence([4])
    print_coverage()

def test_JM_color_FromSequence_is_negInt_returns_1_and_0():
    result = JM_color_FromSequence([-4])
    print_coverage()

def test_JM_color_FromSequence_invalid_length_returns_neg1_and_empty():
    result = JM_color_FromSequence([4, 0])
    print_coverage()

def test_JM_color_FromSequence_valid_length_returns_corrected_list_1():
    result = JM_color_FromSequence([0, 1, 3, 4])
    print_coverage()

def test_JM_color_FromSequence_valid_length_returns_corrected_list_2():
    result = JM_color_FromSequence([0, -1, -6, 4])
    print_coverage()

def test_JM_color_FromSequence_valid_length_returns_corrected_list_3():
    result = JM_color_FromSequence([-4, 1, 6, -4])
    print_coverage()

def test_JM_color_FromSequence_valid_length_returns_corrected_list_4():
    result = JM_color_FromSequence([0, 1, 7, 4])
    print_coverage()

def test_JM_color_FromSequence_valid_length_returns_all_0_list():
    result = JM_color_FromSequence([0, 0, 0, 0])
    print_coverage()

def test_JM_color_FromSequence_not_list_tuple_returns_neg1_and_empty():
    result = JM_color_FromSequence("testtest")
    print_coverage()

def test_JM_color_FromSequence_empty_list_returns_0_and_empty():
    result = JM_color_FromSequence([])
    print_coverage()

def test_JM_color_FromSequence_is_negNo_returns_1_and_0():
    result = JM_color_FromSequence([-4])
    print_coverage()

def test_JM_color_FromSequence_mix_list_returns_corrected_list():
    result = JM_color_FromSequence([-4 ,0 ,1.0 , 3.4])
    print_coverage()

def test_JM_color_FromSequence_invalid_len_returns_neg1_and_empty():
    result = JM_color_FromSequence([1, 2, 3, 4, 5, -6.8])
    print_coverage()

def test_JM_color_FromSequence_invalid_len_float_negInt_returns_neg1_and_empty():
    result = JM_color_FromSequence([1.5, -2, 300000])
    print_coverage()

def test_JM_color_FromSequence_all_neg_returns_corrected_list():
    result = JM_color_FromSequence([-2, -3, -3, -2])
    print_coverage()

def test_JM_color_FromSequence_none_returns_neg1_and_empty():
    result = JM_color_FromSequence(None)
    print_coverage()

test_JM_color_FromSequence_is_float_returns_1_and_ret()
test_JM_color_FromSequence_is_negFloat_returns_1_and_ret()
test_JM_color_FromSequence_is_int_returns_1_and_0()
test_JM_color_FromSequence_is_negInt_returns_1_and_0()
test_JM_color_FromSequence_invalid_length_returns_neg1_and_empty()
test_JM_color_FromSequence_valid_length_returns_corrected_list_1()
test_JM_color_FromSequence_valid_length_returns_corrected_list_2()
test_JM_color_FromSequence_valid_length_returns_corrected_list_3()
test_JM_color_FromSequence_valid_length_returns_corrected_list_4()
test_JM_color_FromSequence_valid_length_returns_all_0_list()
test_JM_color_FromSequence_not_list_tuple_returns_neg1_and_empty()
test_JM_color_FromSequence_empty_list_returns_0_and_empty()
test_JM_color_FromSequence_is_negNo_returns_1_and_0()
test_JM_color_FromSequence_mix_list_returns_corrected_list()
test_JM_color_FromSequence_invalid_len_returns_neg1_and_empty()
test_JM_color_FromSequence_invalid_len_float_negInt_returns_neg1_and_empty()
test_JM_color_FromSequence_all_neg_returns_corrected_list()
test_JM_color_FromSequence_none_returns_neg1_and_empty()

"""
Since I was not able to add the result lists to the name of the function, function names are a bit longer.
"""
