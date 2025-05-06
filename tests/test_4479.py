import pymupdf


def test_4479():
    if pymupdf.mupdf_version_tuple < (1, 26, 0):
        print("Skipping test_4479: requires MuPDF 1.26.0 or later")
        return
    path = os.path.abspath(f"{__file__}/../../tests/resources/test-4479.pdf")
    doc = pymupdf.open(path)

    for layer in doc.layer_ui_configs():
        if layer["text"] == "layer_2":
            assert not layer["on"]
        else:
            assert layer["on"]
    doc.set_layer_ui_config("layer_7", action=pymupdf.PDF_OC_TOGGLE)
    for layer in doc.layer_ui_configs():
        if layer["text"] in ("layer_2", "layer_7"):
            assert not layer["on"]
        else:
            assert layer["on"]
