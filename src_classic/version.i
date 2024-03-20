%pythoncode %{
VersionFitz = "1.24.0" # MuPDF version.
VersionBind = "1.24.0" # PyMuPDF version.
VersionDate = "2024-03-21 00:00:01"
version = (VersionBind, VersionFitz, "20240321000001")
pymupdf_version_tuple = tuple( [int(i) for i in VersionFitz.split('.')])
%}
