import subprocess
import sys
import importlib.metadata
import pymupdf

try:
    importlib.metadata.version("pymupdf")
    pyfull = True
except importlib.metadata.PackageNotFoundError:
    pyfull = False

try:
    importlib.metadata.version("pymupdf_lite")
    plite = True
except importlib.metadata.PackageNotFoundError:
    plite = False

def get_tesseract_version():
    try:
        out = subprocess.check_output(
            ["tesseract", "--version"], stderr=subprocess.STDOUT
        )
        line = out.decode().splitlines()[0]
        return line.split()[-1]
    except Exception:
        return None


def get_pkg_version(name: str):
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


_pymupdf_feature_list = [
    (
        "pymupdf_fonts",
        "1.0.4",
        "Additional Fonts",
        "An optional package that makes more fonts available to PyMuPDF programmers.",
    ),
    (
        "pymupdf_office",
        pymupdf.__version__,
        "Extended Support for Office Documents",
        "A commercial extension that handles Office files like native documents.\n    Install via 'pip install pymupdf-office', and obtain a license key from this\n    website: https://pymupdf.io/office",
    ),
]

_other_feature_list = [
    (
        "tesseract",
        "4.0.0",
        "Tesseract OCR Engine",
        "A popular OCR engine that PyMuPDF can use during document extraction.",
    ),
    (
        "rapidocr",
        "3.9.2",
        "Rapid OCR Engine",
        "An OCR engine that PyMuPDF can use during document extraction.\n    Its installation is strongly recommended for much better OCR results\n    than with Tesseract OCR alone.",
    ),
    (
        "Pillow",
        "0",
        "Python Imaging Library",
        "A popular image library that PyMuPDF can use to deal with images having exotic formats.",
    ),
    (
        "pandas",
        "0",
        "Data Analysis Library",
        "A popular data analysis library that PyMuPDF can use for storing tables as DataFrames.",
    ),
]


def _check_installed_package_version(pack, vsn):
    if pack == "tesseract":  # this is  not a Python package!
        version = get_tesseract_version()
    else:
        version = get_pkg_version(pack)
    if version is None:
        return 2, None

    version = "".join([c for c in version if c in "0123456789."])
    version_tuple = tuple(map(int, version.split(".")))
    vsn_tuple = tuple(map(int, vsn.split(".")))
    if vsn_tuple <= version_tuple:
        return 0, version
    else:
        return 1, version


def _build_feature_dict(feature_list):
    """
    Builds a dict {package_name: info_dict} for the given list of
    (pack, required_version, short, desc) tuples.
    """
    _STATE_LABELS = {
        0: "installed",
        1: "outdated",
        2: "missing",
    }

    result = {}
    for pack, vsn, short, desc in feature_list:
        state, installed_version = _check_installed_package_version(pack, vsn)
        result[pack] = {
            "required_version": vsn,
            "installed_version": installed_version,
            "status": _STATE_LABELS[state],
            "short": short,
            "desc": desc,
        }
    return result


def print_feature_dict(title, feature_dict):
    print(f"\n{title}")
    print("=" * len(title))
    max_pack_len = max(len(pack) for pack in feature_dict.keys()) + 2
    pack_fmt = f"  {{:<{max_pack_len}}}"
    max_version_len = (
        max(len(info["required_version"]) for info in feature_dict.values()) + 2
    )
    max_version_len = max(max_version_len, len("min required") + 2)
    version_fmt = f"{{:<{max_version_len}}}"
    header = f"{'Package':<{max_pack_len+2}}{'Min Required':<{max_version_len}}Status"
    print(header)
    print("-" * (len(header) + 15))
    for pack, info in feature_dict.items():
        status = info["status"]
        vsn = info["required_version"]
        if vsn == "0":
            vsn = "any"
        this_version = info["installed_version"]
        if status == "missing":
            print(pack_fmt.format(pack) + version_fmt.format(vsn) + "not installed")
            print(f"    {info['desc']}")
        elif status == "outdated":
            print(
                pack_fmt.format(pack)
                + version_fmt.format(vsn)
                + f"installed: {this_version} (out of date)"
            )
            print(f"    {info['short']}")
        elif status == "installed":
            if vsn == "any" or vsn != this_version:
                print(
                    pack_fmt.format(pack)
                    + version_fmt.format(vsn)
                    + f"installed: {this_version}"
                )
            else:
                print(pack_fmt.format(pack) + version_fmt.format(vsn) + "installed")

            print(f"    {info['short']}")
        print()


def collect_features():
    """
    Determines the install status of all the different packages that
    contribute to PyMuPDF features (both default and optional ones) and
    stores the results in two dictionaries:

    - pymupdf_components: the PyMuPDF packages themselves
    - other_packages: useful third-party packages PyMuPDF can use

    Returns:
        tuple[dict, dict]: (pymupdf_components, other_packages)
    """
    pymupdf_components = _build_feature_dict(_pymupdf_feature_list)
    other_packages = _build_feature_dict(_other_feature_list)
    return pymupdf_components, other_packages


def config():
    print("Python Version")
    print("==============")
    print(f"{sys.version}")
    print()
    if pyfull:
        print(f"PyMuPDF version {pymupdf.__version__} installed.")
    elif plite:
        print(f"PyMuPDF lite version {pymupdf.__version__} installed. Consider upgrading for advanced features like layout and more.")
    print()
    pymupdf_components, other_packages = collect_features()
    print_feature_dict("PyMuPDF Configuration", pymupdf_components)
    print_feature_dict("Useful Third-party Packages for PyMuPDF", other_packages)

