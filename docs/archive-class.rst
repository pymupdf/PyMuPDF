.. include:: header.rst

.. _Archive:

================
Archive
================

* New in v1.21.0

This class represents a generalization of file folders and container files like ZIP and TAR archives. Archives allow accessing arbitrary collections of file folders, ZIP / TAR files and single binary data elements as if they all were part of one hierarchical tree of folders.

In PyMuPDF, archives are currently only used by :ref:`Story` objects to specify where to look for fonts, images and other resources.

================================ ===================================================
**Method / Attribute**           **Short Description**
================================ ===================================================
:meth:`Archive.add`              add new data to the archive
:meth:`Archive.has_entry`        check if given name is a member
:meth:`Archive.read_entry`       read the data given by the name
:attr:`Archive.entry_list`       list[dict] of archive items
================================ ===================================================

**Class API**

.. class:: Archive

   .. method:: __init__(self [, content [, path]])

      Creates a new archive. Without parameters, an empty archive is created.

      If provided, `content` may be one of the following:

      * another Archive: the archive is being made a sub-archive of the new one.

      * a string: this must be the name of a local folder or file. `pathlib.Path` objects are also supported.

         - A **folder** will be converted to a sub-archive, so its files (and any sub-folders) can be accessed by their names.
         - A **file** will be read with mode `"rb"` and these binary data (a `bytes` object) be treated as a single-member sub-archive. In this case, the `path` parameter is **mandatory** and should be the member name under which this item can be found / retrieved.

      * a `zipfile.ZipFile` or `tarfile.TarFile` object: Will be added as a sub-archive.

      * a Python binary object (`bytes`, `bytearray`, `io.BytesIO`): this will add a single-member sub-archive. In this case, the `path` parameter is **mandatory** and should be the member name under which this item can be found / retrieved.

      * a tuple `(data, name)`: This will add a single-member sub-archive with the member name ``name``. ``data`` may be a Python binary object or a local file name (in which case its binary file content is used). Use this format if you need to specify `path`.

      * a Python sequence: This is a convenience format to specify any combination of the above.

      If provided, `path` must be a string.
      
      * If `content` is either binary data or a file name, this parameter is mandatory and must be the name under which the data can be found.

      * Otherwise this parameter is optional. It can be used to simulate a folder name or a mount point, under which this sub-archive's elements can be found. For example this specification `Archive((data, "name"), "path")` means that `data` will be found using the element name `"path/name"`. Similar is true for other sub-archives: to retrieve members of a ZIP sub-archive, their names must be prefixed with `"path/"`. The main purpose of this parameter probably is to differentiate between duplicate names.

      .. note:: If duplicate entry names exist in the archive, always the last entry with that name will be found / retrieved. During archive creation, or appending more data to an archive (see :meth:`Archive.add`) no check for duplicates will be made. Use the `path` parameter to prevent this from happening.

   .. method:: add(content [,path])

      Append a sub-archive. The meaning of the parameters are exactly the same as explained above. Of course, parameter `content` is not optional here.

   .. method:: has_entry(name)

      Checks whether an entry exists in any of the sub-archives.

      :arg str name: The fully qualified name of the entry. So must include any `path` prefix under which the entry's sub-archive has been added.

      :returns: `True` or `False`.

   .. method:: read_entry(name)

      Retrieve the data of an entry.

      :arg str name: The fully qualified name of the entry. So must include any `path` prefix under which the entry's sub-archive has been added.

      :returns: The binary data (`bytes`) of the entry. If not found, an exception is raised.

   .. attribute:: entry_list

      A list of the archive's sub-archives. Each list item is a dictionary with the following keys:

      * `entries` -- a list of (top-level) entry names in this sub-archive.
      * `fmt` -- the format of the sub-archive. This is one of the strings "dir" (file folder), "zip" (ZIP archive), "tar" (TAR archive), or "tree" for single binary entries or file content.
      * `path` -- the value of the `path` parameter under which this sub-archive was added.

      **Example:**

      >>> from pprint import pprint
      >>> import pymupdf
      >>> dir1 = "fitz-32"  # a folder name
      >>> dir2 = "fitz-64"  # a folder name
      >>> img = ("nur-ruhig.jpg", "img")  # an image file
      >>> members = (dir1, img, dir2)  # we want to append these in one go
      >>> arch = pymupdf.Archive()
      >>> arch.add(members, path="mypath")
      >>> pprint(arch.entry_list)
      [{'entries': ['310', '37', '38', '39'], 'fmt': 'dir', 'path': 'mypath'},
      {'entries': ['img'], 'fmt': 'tree', 'path': 'mypath'},
      {'entries': ['310', '311', '37', '38', '39', 'pypy'],
      'fmt': 'dir',
      'path': 'mypath'}]
      >>> 

.. include:: footer.rst
