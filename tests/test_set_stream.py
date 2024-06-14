import os
import unittest

branch_coverage = {
    "branch_1": False,
    "branch_2": False,
    "branch_3": False,
    "branch_4": False, 
    "branch_5": False
}

def _set_stream(name, default):
    t = os.environ.get(name)
    if t is None:
        branch_coverage["branch_1"] = True
        return default
    elif t.startswith('fd:'):
        branch_coverage["branch_2"] = True
        return open(int(t[3:]), mode='w', closefd=False)
    elif t.startswith('path:'):
        branch_coverage["branch_3"] = True
        return open(t[5:], 'w')
    elif t.startswith('path+:'):
        branch_coverage["branch_4"] = True
        return open(t[6:], 'a')
    else:
        branch_coverage["branch_5"] = True
        raise Exception(f'Unrecognised stream specification for {name!r} should match `fd:<int>`, `path:<string>` or `path+:<string>`: {t!r}')
    
def print_coverage():
    for branch, hit in branch_coverage.items():
        print(f"{branch} was {'hit' if hit else 'not hit'}")

def test_set_stream_name_startsWithFd_opensFile():
    os.environ['VAR'] = 'fd:1'
    result = _set_stream('VAR', "")
    print_coverage()

def test_set_stream_name_startsWithPath_opensFile():
    os.environ['VAR'] = 'path:example.txt'
    result = _set_stream('VAR', "")
    print_coverage()

def test_set_stream_name_startsWithPathPlus_opensFile():
    os.environ['VAR'] = 'path+:example.txt'
    result = _set_stream('VAR', "")
    print_coverage()

def test_set_stream_name_unrecognized_raisesException():
    os.environ['VAR'] = 'unrecognized'
    try:
        result = _set_stream('VAR', "")
    except Exception as e:
        print(e)
    print_coverage()

def test_set_stream_name_isNone_returns_default():
    del os.environ['VAR']
    result = _set_stream('VAR', 0)
    print_coverage()

test_set_stream_name_startsWithFd_opensFile()
test_set_stream_name_startsWithPath_opensFile()
test_set_stream_name_startsWithPathPlus_opensFile()
test_set_stream_name_unrecognized_raisesException()
test_set_stream_name_isNone_returns_default()
