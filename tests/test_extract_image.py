"""
Extract images from a PDF file, save them in a newly created folder and delete them after test
"""
import os
import fitz
import shutil

pdf_file_path = 'tests/resources/joined.pdf'


def delete_image_after_extract(pdf_file_path):
    images_directory_path = pdf_file_path[:-pdf_file_path[::-1].find(
        '/')]+'images_from_'+pdf_file_path[-pdf_file_path[::-1].find('/'):].replace('.', '_')
    shutil.rmtree(images_directory_path)


def extract_image(pdf_file_path):
    pdf_file = fitz.open(pdf_file_path)

    images_directory_path = pdf_file_path[:-pdf_file_path[::-1].find(
        '/')]+'images_from_'+pdf_file_path[-pdf_file_path[::-1].find('/'):].replace('.', '_')

    # if the test output folder does not exist yet, create it
    if not os.path.exists(images_directory_path):
        os.mkdir(images_directory_path)
    
    image_count = 1
    for index in range(1, pdf_file.xref_length()-1):
        pix = pdf_file.extract_image(index)
        if isinstance(pix, dict):
            with open(images_directory_path+'/image_'+str(image_count)+'.'+pix['ext'], 'wb') as image_out:
                image_out.write(pix["image"])
            image_count += 1
    
    delete_image_after_extract(pdf_file_path)


if __name__ == '__main__':
    extract_image(pdf_file_path)
