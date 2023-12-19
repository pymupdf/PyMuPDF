%pythoncode %{
VersionFitz = "1.23.7" # MuPDF version.
VersionBind = "1.23.8" # PyMuPDF version.
VersionDate = "2023-12-19 00:00:01"
version = (VersionBind, VersionFitz, "20231219000001")
pymupdf_version_tuple = tuple( [int(i) for i in VersionFitz.split('.')])
%}
