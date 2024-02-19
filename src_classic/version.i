%pythoncode %{
VersionFitz = "1.23.10" # MuPDF version.
VersionBind = "1.23.24" # PyMuPDF version.
VersionDate = "2024-02-19 00:00:01"
version = (VersionBind, VersionFitz, "20240219000001")
pymupdf_version_tuple = tuple( [int(i) for i in VersionFitz.split('.')])
%}
