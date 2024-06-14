import os
import unittest

branch_coverage = {
    "branch_1": False,
    "branch_2": False,
    "branch_3": False,
    "branch_4": False
}

def log(message):
    print(message)

def get_env_bool(name, default):
    '''
    Returns `True`, `False` or `default` depending on whether $<name> is '1',
    '0' or unset. Otherwise assert-fails.
    '''
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
    if ret != default:
        log(f'Using non-default setting from {name}: {v!r}')
    return ret

def print_coverage():
    for branch, hit in branch_coverage.items():
        print(f"{branch} was {'hit' if hit else 'not hit'}")

os.environ['VAR'] = '1'
result = get_env_bool('VAR', 1)
print_coverage()

os.environ['VAR'] = '0'
result = get_env_bool('VAR', 0)
print_coverage()

del os.environ['VAR']
result = get_env_bool('VAR', 0)
print_coverage()

os.environ['VAR'] = 'unrecognized'
try:
    result = get_env_bool('VAR', 1)
except AssertionError as e:
    print(f"AssertionError: {e}")
print_coverage()