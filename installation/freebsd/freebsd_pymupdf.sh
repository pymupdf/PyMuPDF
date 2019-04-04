setenv CFLAGS -fPIC

# also FreeBSD has a mupdf port, we should build it manually
wget https://mupdf.com/downloads/archive/mupdf-1.14.0-source.tar.gz
tar -zxvf mupdf-1.14.0-source.tar.gz

rm -rf PyMuPDF
git clone https://github.com/pymupdf/PyMuPDF.git

cd mupdf-1.14.0-source
# replace 3 files in mupdf-1.14.0
cp ../PyMuPDF/fitz/_mupdf_config.h include/mupdf/fitz/config.hfig.h
cp ../PyMuPDF/fitz/_error.c source/fitz/error.c
cp ../PyMuPDF/fitz/_pdf-device.c source/pdf/pdf-device.c

gmake HAVE_X11=no HAVE_GLFW=no HAVE_GLUT=no prefix=/usr/local
gmake HAVE_X11=no HAVE_GLFW=no HAVE_GLUT=no prefix=/usr/local install

cd ../PyMuPDF
python setup.py build
python setup.py install
