wget https://mupdf.com/downloads/archive/mupdf-1.18.0-source.tar.gz
tar -zxvf mupdf-1.18.0-source.tar.gz

cd mupdf-1.18.0-source
# replace files in mupdf source
cp ../PyMuPDF/fitz/_config.h include/mupdf/fitz/config.h

export CFLAGS="-fPIC"
# install some prerequirement
sudo apt install pkg-config python-dev

make HAVE_X11=no HAVE_GLFW=no HAVE_GLUT=no prefix=/usr/local
sudo make HAVE_X11=no HAVE_GLFW=no HAVE_GLUT=no prefix=/usr/local install

cd ..

rm -rf PyMuPDF
git clone https://github.com/pymupdf/PyMuPDF.git
cd PyMuPDF

sudo python setup.py build
sudo python setup.py install
