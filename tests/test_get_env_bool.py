import os
import unittest

branch_coverage = {
    "branch_1": False,
    "branch_2": False,
    "branch_3": False,
    "branch_4": False
}

def get_env_bool(name, default):
    v = os.environ.get(name)
    if v is None:
        branch_coverage["branch_1"] = True
        ret = default
    elif v == '1':
        branch_coverage["branch_2"] = True
        ret = True
    elif v == '0':
        branch_coverage["branch_3"] = True
        ret = False
    else:
        branch_coverage["branch_4"] = True
        assert 0, f'There is an unrecognised value existing {name}: {v!r}'
    return ret

def print_coverage():
    for branch, hit in branch_coverage.items():
        print(f"{branch} was {'hit' if hit else 'not hit'}")

def  test_get_env_bool_default_isOne_returns_true():
    os.environ['VAR'] = '1'
    result = get_env_bool('VAR', 1)
    print_coverage()

def  test_get_env_bool_default_isZero_returns_false():
    os.environ['VAR'] = '0'
    result = get_env_bool('VAR', 0)
    print_coverage()

def  test_get_env_bool_default_isNone_returns_default():
    del os.environ['VAR']
    result = get_env_bool('VAR', 0)
    print_coverage()

def  test_get_env_bool_default_unrecognized_returns_assertion():
    os.environ['VAR'] = 'unrecognized'
    try:
        result = get_env_bool('VAR', 1)
    except AssertionError as e:
        print(f"AssertionError: {e}")
    print_coverage()

test_get_env_bool_default_isOne_returns_true()
test_get_env_bool_default_isZero_returns_false()
test_get_env_bool_default_isNone_returns_default()
test_get_env_bool_default_unrecognized_returns_assertion()
