import sys

import pipcl


def build():
    return list()

def sdist():
    return pipcl.git_items('.')

version = '2.0'

p = pipcl.Package(
        'pymupdf',
        '2.0',
        pure=1,
        requires_dist = [
                f'pymupdf4llm=={version}',
                f'pymupdf_core=={version}',
                f'pymupdf_layout=={version}',
                ],
        fn_build=build,
        fn_sdist=sdist,
        )

build_wheel = p.build_wheel
build_sdist = p.build_sdist

if __name__ == '__main__':
    p.handle_argv(sys.argv)
