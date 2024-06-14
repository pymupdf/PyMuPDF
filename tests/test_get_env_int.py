import os
import unittest

branch_coverage = {
    "branch_1": False, 
    "branch_2": False
}

def get_env_int( name, default):
    v = os.environ.get( name)
    if v is None:
        branch_coverage["branch_1"] = True
        ret = default
    else:
        branch_coverage["branch_2"] = True
        ret = int(v)
    return ret

def print_coverage():
    for branch, hit in branch_coverage.items():
        print(f"{branch} was {'hit' if hit else 'not hit'}")


def test_get_env_int_default_is_not_None_returns_1():
    os.environ['VAR'] = '1'
    result = get_env_int('VAR', 1)
    print_coverage()

def test_get_env_int_default_is_not_None_returns_0():
    os.environ['VAR'] = '0'
    result = get_env_int('VAR', 1)
    print_coverage()

def test_get_env_int_default_isNone_returns_default():
    del os.environ['VAR']
    result = get_env_int('VAR', 0)
    print_coverage()

test_get_env_int_default_is_not_None_returns_1()
test_get_env_int_default_is_not_None_returns_0()
test_get_env_int_default_isNone_returns_default()