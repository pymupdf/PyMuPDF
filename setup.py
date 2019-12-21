from distutils.core import setup, Extension
from distutils.command.build_py import build_py as build_py_orig
import sys, os

# custom build_py command which runs build_ext first
# this is necessary because build_py needs the fitz.py which is only generated
# by SWIG in the build_ext step
class build_ext_first(build_py_orig):
    def run(self):
        self.run_command("build_ext")
        return super().run()


# check the platform
if sys.platform.startswith("linux"):
    module = Extension(
        "fitz._fitz",  # name of the module
        ["fitz/fitz.i"],
        include_dirs=[  # we need the path of the MuPDF headers
            "/usr/include/mupdf",
            "/usr/local/include/mupdf",
        ],
        # library_dirs=['<mupdf_and_3rd_party_libraries_dir>'],
        libraries=[
            "mupdf",
            #'crypto', #openssl is required by mupdf on archlinux
            #'jbig2dec', 'openjp2', 'jpeg', 'freetype',
            "mupdf-third",
        ],  # the libraries to link with
    )
elif sys.platform.startswith(("darwin", "freebsd")):
    module = Extension(
        "fitz._fitz",  # name of the module
        ["fitz/fitz.i"],
        # directories containing mupdf's header files
        include_dirs=["/usr/local/include/mupdf", "/usr/local/include"],
        # libraries should already be linked here by brew
        library_dirs=["/usr/local/lib"],
        # library_dirs=['/usr/local/Cellar/mupdf-tools/1.8/lib/',
        #'/usr/local/Cellar/openssl/1.0.2g/lib/',
        #'/usr/local/Cellar/jpeg/8d/lib/',
        #'/usr/local/Cellar/freetype/2.6.3/lib/',
        #'/usr/local/Cellar/jbig2dec/0.12/lib/'
        # ],
        libraries=["mupdf", "mupdf-third"],
    )

else:
    # ===============================================================================
    # Build / set up PyMuPDF under Windows
    # ===============================================================================
    module = Extension(
        "fitz._fitz",
        ["fitz/fitz.i"],
        include_dirs=[  # we need the path of the MuPDF's headers
            "./mupdf/include",
            "./mupdf/include/mupdf",
        ],
        libraries=[  # these are needed in Windows
            "libmupdf",
            "libresources",
            "libthirdparty",
        ],
        extra_link_args=["/NODEFAULTLIB:MSVCRT"],
        # x86 dir of libmupdf.lib etc.
        library_dirs=["./mupdf/platform/win32/Release"],
        # x64 dir of libmupdf.lib etc.
        # library_dirs=['./mupdf/platform/win32/x64/Release'],
    )

pkg_tab = open("PKG-INFO").read().split("\n")
long_dtab = []
classifier = []
for l in pkg_tab:
    if l.startswith("Classifier: "):
        classifier.append(l[12:])
        continue
    if l.startswith(" "):
        long_dtab.append(l.strip())
long_desc = "\n".join(long_dtab)

setup(
    name="PyMuPDF",
    version="1.16.10",
    description="Python bindings for the PDF rendering library MuPDF",
    long_description=long_desc,
    classifiers=classifier,
    url="https://github.com/pymupdf/PyMuPDF",
    author="Jorj McKie, Ruikai Liu",
    author_email="jorj.x.mckie@outlook.de",
    cmdclass={"build_py": build_ext_first},
    ext_modules=[module],
    py_modules=["fitz.fitz", "fitz.utils", "fitz.__main__"],
)
