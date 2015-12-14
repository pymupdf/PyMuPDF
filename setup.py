from distutils.core import setup, Extension
import sys

# check the platform
if sys.platform.startswith('linux'):
    module = Extension('fitz._fitz', # name of the module
                       ['fitz/fitz_wrap.c'], # C source file
                       include_dirs=['/usr/include/mupdf',
                                     '/usr/local/include/mupdf'], # we need the path of the MuPDF's headers
                       #library_dirs=['<mupdf_and_3rd_party_libraries_dir>'],
                       libraries=['mupdf', 'mujs', 'crypto',
                                  'jbig2dec', 'openjp2', 'jpeg',
                                  'freetype'],                   # the libraries to link with
                      )
else:
#===============================================================================
# This will build / setup python-fitz under Windows
# There is a wiki page with detailed instructions on how to set up
# python-fitz in Windows 7.
#===============================================================================
    module = Extension('fitz._fitz',
                       include_dirs=['./fitz',
                                     './mupdf18/include/',
                                     './mupdf18/include/mupdf'],  # "./mupdf18" = top level mupdf source dir
                       libraries=[                                # only these 2 are needed in Windows
                                  'libmupdf',                        
                                  'libthirdparty',                    
                                 ],
                       extra_link_args=['/NODEFAULTLIB:MSVCRT'],
                       library_dirs=['./PyMuPDF-optional-material/LibWin32'],               # dir of libmupdf.lib / libthirdparty.lib
                       sources=['./fitz/fitz_wrap.c'])

setup(name = 'fitz',
      version = '1.8.0',
      description = 'Python bindings for the PDF rendering library MuPDF',
      classifiers = ['Development Status :: 4 - Beta',
                     'Environment :: Console',
                     'Intended Audience :: Developers',
                     'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
                     'Operating System :: WINDOWS',
                     'Programming Language :: C',
                     'Topic :: Utilities'],
      url = 'https://github.com/rk700/PyMuPDF',
      author = 'Ruikai Liu',
      author_email = 'lrk700@gmail.com',
      license = 'GPLv3+',
      ext_modules = [module],
      py_modules = ['fitz.fitz'])
