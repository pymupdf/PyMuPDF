from distutils.core import setup, Extension
#===============================================================================
# This will build / setup python-fitz under Windows
# There is a wiki page with detailed instructions on how to set up
# python-fitz in Windows 7.
#===============================================================================
module = Extension('fitz._fitz',
                   include_dirs=['./fitz',
                                 './mupdf17/include/mupdf'       # mupdf source directory is also needed
                                ],
                   libraries=['libmupdf',                        # only these are needed in Windows
                              'libthirdparty'                    # put them in the dir of setupwin.py or
                             ],                                  # specify a lib directory here
                   sources=['./fitz/fitz_wrap.c'])

setup(name = 'fitz',
      version = '0.0.9',
      description = 'Python bindings for the MuPDF 1.7a rendering library',
      classifiers = ['Development Status :: 4 - Beta',
                     'Environment :: Console',
                     'Intended Audience :: Developers',
                     'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
                     'Operating System :: WINDOWS',
                     'Programming Language :: C',
                     'Topic :: Utilities'],
      url = 'https://github.com/rk700/python-fitz',
      author = 'Ruikai Liu',
      author_email = 'lrk700@gmail.com',
      license = 'GPLv3+',
      packages = ['fitz'],
      ext_modules = [module])
