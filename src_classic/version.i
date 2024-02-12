%pythoncode %{
VersionFitz = "1.23.10" # MuPDF version.
VersionBind = "1.23.22" # PyMuPDF version.
VersionDate = "2024-02-12 00:00:01"
version = (VersionBind, VersionFitz, "20240212000001")
pymupdf_version_tuple = tuple( [int(i) for i in VersionFitz.split('.')])
%}
