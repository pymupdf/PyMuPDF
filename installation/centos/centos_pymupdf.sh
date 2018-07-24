wget https://mupdf.com/downloads/mupdf-1.13.0-source.tar.gz
tar -zxvf mupdf-1.13.0-source.tar.gz

cd mupdf-1.13.0-source
export CFLAGS="-fPIC -std=gnu99"

make HAVE_X11=no HAVE_GLFW=no HAVE_GLUT=no prefix=/usr/local
sudo make HAVE_X11=no HAVE_GLFW=no HAVE_GLUT=no prefix=/usr/local install

cd ..

rm -rf PyMuPDF
git clone https://github.com/rk700/PyMuPDF.git
cd PyMuPDF

sudo python setup.py build
sudo python setup.py install
