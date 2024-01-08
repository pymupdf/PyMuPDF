%pythoncode %{
VersionFitz = "1.23.8" # MuPDF version.
VersionBind = "1.23.9rc2" # PyMuPDF version.
VersionDate = "2024-01-08 00:00:01"
version = (VersionBind, VersionFitz, "20240108000001")
pymupdf_version_tuple = tuple( [int(i) for i in VersionFitz.split('.')])
%}
