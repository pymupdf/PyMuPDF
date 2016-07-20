from distutils.core import setup, Extension
import sys, os

# check the platform
if sys.platform.startswith('linux'):
    module = Extension('fitz._fitz', # name of the module
                       ['fitz/fitz_wrap.c'], # C source file
                       include_dirs=[  # we need the path of the MuPDF's headers
                                     '/usr/include/mupdf',
                                     '/usr/local/include/mupdf'
                                    ],
                       #library_dirs=['<mupdf_and_3rd_party_libraries_dir>'],
                       libraries=[
                           'mupdf',
                           'crypto', #openssl is required by mupdf on archlinux
                           'jbig2dec', 'openjp2', 'jpeg', 'freetype',
                           'mupdfthird',
                           ], # the libraries to link with
                      )
elif sys.platform.startswith('darwin'):
    module = Extension('fitz._fitz', # name of the module
                       ['fitz/fitz_wrap.c'], # C source file
                       # this is directory containing mupdf's header files
                       include_dirs=['/usr/local/include/mupdf'],
                       # libraries should already be linked here by brew
                       library_dirs=['/usr/local/lib'],
                       #library_dirs=['/usr/local/Cellar/mupdf-tools/1.8/lib/',
                                    #'/usr/local/Cellar/openssl/1.0.2g/lib/',
                                    #'/usr/local/Cellar/jpeg/8d/lib/',
                                    #'/usr/local/Cellar/freetype/2.6.3/lib/',
                                    #'/usr/local/Cellar/jbig2dec/0.12/lib/'
                           #],
                       libraries=['mupdf', 'crypto', 'jpeg', 'freetype', 'jbig2dec', 'mupdfthird']
                      )

else:
#===============================================================================
# This will build / set up PyMuPDF under Windows.
# For details consult the documentation.
#===============================================================================
    module = Extension('fitz._fitz',
                       include_dirs=[ # we need the path of the MuPDF's headers
                                     './mupdf/include',
                                     './mupdf/include/mupdf',
                                    ],
                       libraries=[ # these are needed in Windows
                                  'libmupdf', 'libfonts',
                                  'libthirdparty',
                                 ],
                       extra_link_args=['/NODEFAULTLIB:MSVCRT'],
                                     # dir of libmupdf.lib etc.
                       library_dirs=['./PyMuPDF-optional-material/LibWin32'],
                       sources=['./fitz/fitz_wrap.c',])

setup(name = 'fitz',
      version = "1.9.1",
      description = 'Python bindings for the PDF rendering library MuPDF',
      classifiers = ['Development Status :: 4 - Beta',
                     'Environment :: Console',
                     'Intended Audience :: Developers',
                     'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
                     'Operating System :: WINDOWS',
                     'Programming Language :: Python',
                     'Topic :: Utilities'],
      url = 'https://github.com/rk700/PyMuPDF',
      author = 'Ruikai Liu',
      author_email = 'lrk700@gmail.com',
      license = 'GPLv3+',
      ext_modules = [module],
      py_modules = ['fitz.fitz', 'fitz.utils'])
