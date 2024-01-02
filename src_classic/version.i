%pythoncode %{
VersionFitz = "1.23.7" # MuPDF version.
VersionBind = "1.23.9rc1" # PyMuPDF version.
VersionDate = "2024-01-02 00:00:01"
version = (VersionBind, VersionFitz, "20240102000001")
pymupdf_version_tuple = tuple( [int(i) for i in VersionFitz.split('.')])
%}
