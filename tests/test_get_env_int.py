import os
import unittest

branch_coverage = {
    "branch_1": False, 
    "branch_2": False
}

def log(message):
    print(message)

def get_env_int( name, default):
    v = os.environ.get( name)
    if v is None:
        branch_coverage["branch_1"] = True
        ret = default
    else:
        branch_coverage["branch_2"] = True
        ret = int(v)
    if ret != default:
        log(f'Using non-default setting from {name}: {v}')
    return ret

def print_coverage():
    for branch, hit in branch_coverage.items():
        print(f"{branch} was {'hit' if hit else 'not hit'}")

os.environ['VAR'] = '1'
result = get_env_int('VAR', 1)
print_coverage()

del os.environ['VAR']
result = get_env_int('VAR', 0)
print_coverage()