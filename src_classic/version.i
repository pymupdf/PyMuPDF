%pythoncode %{
VersionFitz = "1.24.1" # MuPDF version.
VersionBind = "1.24.1" # PyMuPDF version.
VersionDate = "2024-04-02 00:00:01"
version = (VersionBind, VersionFitz, "20240402000001")
pymupdf_version_tuple = tuple( [int(i) for i in VersionFitz.split('.')])
%}
