from distutils.core import setup, Extension

module = Extension('fitz._fitz',
				   include_dirs = ['./fitz'],
				   libraries = ['fitz', 'jpeg', 'jbig2dec', 
					   			'openjpeg', 'freetype', 'z', 'm'],
				   sources = ['./fitz/fitz_wrap.c'])
					

setup(name = 'fitz',
      version = '0.0.9',
      description = 'Python bindings for MuPDF rendering library',
      classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: POSIX',
        'Programming Language :: C',
        'Topic :: Utilities',
      ],
      url = 'https://github.com/rk700/python-fitz',
      author = 'Ruikai Liu',
      author_email = 'lrk700@gmail.com',
      license = 'GPLv3+',
      packages = ['fitz'],
	  ext_modules = [module],
     )
