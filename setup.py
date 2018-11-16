from distutils.core import setup, Extension
import sys, os

# check the platform
if sys.platform.startswith('linux'):
    module = Extension('fitz._fitz', # name of the module
                       ['fitz/fitz_wrap.c'], # C source file
                       include_dirs=[  # we need the path of the MuPDF and zlib headers
                                     '/usr/include/mupdf',
                                     '/usr/local/include/mupdf',
                                     '/usr/local/thirdparty/zlib',
                                    ],
                       #library_dirs=['/usr/local/lib'],
                       libraries=[
                           'mupdf',
                           'mupdf-third',
                           # 'jbig2dec', 'openjp2', 'jpeg', 'freetype',
                           # 'crypto', #openssl is required by mupdf on archlinux
                           ], # the libraries to link with
                      )
elif sys.platform.startswith(('darwin', 'freebsd')):
    module = Extension('fitz._fitz', # name of the module
                       ['fitz/fitz_wrap.c'], # C source file
                       # this are directories containing mupdf's and zlib's header files
                       include_dirs=['/usr/local/include/mupdf',
                                     '/usr/local/include',
                                     '/usr/local/thirdparty/zlib'],
                       library_dirs=['/usr/local/lib'],
                       libraries=['mupdf', 'mupdf-third']
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
                                     './mupdf/thirdparty/zlib', 
                                    ],
                       libraries=[ # these are needed in Windows
                                  'libmupdf', 'libresources',
                                  'libthirdparty',
                                 ],
                       extra_link_args=['/NODEFAULTLIB:MSVCRT'],
                                     # x86 dir of libmupdf.lib etc.
                       library_dirs=['./mupdf/platform/win32/Release'],
                                     # x64 dir of libmupdf.lib etc.
                       #library_dirs=['./mupdf/platform/win32/x64/Release'],
                       sources=['./fitz/fitz_wrap.c',])

setup(name = 'PyMuPDF',
      version = "1.14.0",
      description = 'Python bindings for the PDF rendering library MuPDF',
      classifiers = ['Development Status :: 5 - Production/Stable',
                     'Environment :: Console',
                     'Intended Audience :: Developers',
                     'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
                     'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
                     'Operating System :: Microsoft :: Windows',
                     'Operating System :: POSIX :: Linux',
                     'Operating System :: MacOS',
                     'Programming Language :: C',
                     'Programming Language :: Python :: 2.7',
                     'Programming Language :: Python :: 3',
                     'Topic :: Utilities'],
      url = 'https://github.com/rk700/PyMuPDF',
      author = 'Ruikai Liu, Jorj McKie',
      author_email = 'lrk700@gmail.com',
      license = 'GPLv3+',
      ext_modules = [module],
      py_modules = ['fitz.fitz', 'fitz.utils'])
