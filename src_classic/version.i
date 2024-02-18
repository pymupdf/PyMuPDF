%pythoncode %{
VersionFitz = "1.23.10" # MuPDF version.
VersionBind = "1.23.23" # PyMuPDF version.
VersionDate = "2024-02-18 00:00:01"
version = (VersionBind, VersionFitz, "20240218000001")
pymupdf_version_tuple = tuple( [int(i) for i in VersionFitz.split('.')])
%}
