import pymupdf
import pathlib
import json
import tempfile


def _get_test_file():
    """Helper to get the test PDF path."""
    return (
        pathlib.Path(__file__).resolve().parent.parent
        / "tests"
        / "resources"
        / "test_personinfo.pdf"
    )


def test_set_value():
    """Test set_value method."""
    filename = _get_test_file()
    doc = pymupdf.open(filename)
    ff = doc.get_form_fields()
    field_info = ff.field_info("Person.MaritalStatus")
    assert field_info["value"] == "married", f'{field_info["value"]=}'
    ff.set_value("Person.MaritalStatus", "single")
    data = doc.tobytes()
    doc.close()
    doc = pymupdf.open(stream=data)
    ff = doc.get_form_fields()
    field_info = ff.field_info("Person.MaritalStatus")
    assert field_info["value"] == "single"


def test_csv_roundtrip():
    """Roundtrip through CSV export, update, import."""
    filename = _get_test_file()
    doc = pymupdf.open(filename)
    ff = doc.get_form_fields()
    value = {}  # terminal fields with values
    for name, item in ff.fields.items():
        if not item["terminal"]:
            continue
        value[name] = item["value"]

    csv_data = ff.to_csv().splitlines()
    last_line = csv_data[-1]

    # confirm last line is the right field
    assert last_line.endswith("married,")
    assert last_line.startswith("Person.MaritalStatus")
    last_line += "single"  # provide a new value for the field

    # rebuild the csv string
    csv_data[-1] = last_line
    csv_data = "\n".join(csv_data)
    # apply any updates
    ff._apply_csv_updates(csv_data)

    # prepare original value dict for comparison
    value["Person.MaritalStatus"] = "single"
    value2 = {}  # terminal fields with values after CSV update
    for name, item in ff.fields.items():
        if not item["terminal"]:
            continue
        value2[name] = item["value"]

    assert value == value2


def test_field_names():
    """Test that field_names returns sorted list of all field names."""
    filename = _get_test_file()
    doc = pymupdf.open(filename)
    ff = doc.get_form_fields()

    field_names = ff.field_names()
    assert isinstance(field_names, list)
    assert len(field_names) > 0
    assert field_names == sorted(field_names)  # verify it's sorted

    # Verify all field names are strings and in the fields dict
    for name in field_names:
        assert isinstance(name, str)
        assert name in ff.fields


def test_field_info():
    """Test that field_info retrieves correct field metadata."""
    filename = _get_test_file()
    doc = pymupdf.open(filename)
    ff = doc.get_form_fields()

    field_info = ff.field_info("Person.MaritalStatus")
    assert field_info is not None
    assert "type" in field_info
    assert "value" in field_info
    assert "terminal" in field_info
    assert "widgets" in field_info

    # Test nonexistent field
    nonexistent = ff.field_info("NonExistent.Field")
    assert nonexistent is None


def test_list_valid_terminal_fields():
    """Test that only valid terminal fields are returned."""
    filename = _get_test_file()
    doc = pymupdf.open(filename)
    ff = doc.get_form_fields()

    valid_fields = ff.list_valid_terminal_fields()
    assert isinstance(valid_fields, list)
    assert len(valid_fields) > 0

    for field in valid_fields:
        assert "name" in field
        assert "type" in field
        assert "format" in field
        assert "value" in field
        assert "editable" in field
        assert field["type"] not in ("signature", "button")

        # Verify the field info is marked as terminal and valid
        info = ff.field_info(field["name"])
        assert info["terminal"]
        assert info["diagnosis"]["ok"]


def test_to_csv():
    """Test CSV export functionality."""
    filename = _get_test_file()
    doc = pymupdf.open(filename)
    ff = doc.get_form_fields()

    csv_content = ff.to_csv()
    assert isinstance(csv_content, str)

    # Verify CSV structure
    lines = csv_content.strip().split("\n")
    assert len(lines) > 1  # At least header + one field

    # Check header (strip \r from Windows line endings)
    header = lines[0].rstrip('\r')
    expected_headers = ["field", "type", "format", "editable", "choices", "current_value", "new_value"]
    assert header == ",".join(expected_headers)

    # Verify at least one data row
    assert len(lines) > 1


def test_to_csv_file_export():
    """Test CSV export to file."""
    filename = _get_test_file()
    doc = pymupdf.open(filename)
    ff = doc.get_form_fields()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
        tmp_path = tmp.name

    try:
        result = ff.to_csv(file=tmp_path)
        assert result is None  # Should not return when writing to file

        # Verify file was created and contains data
        with open(tmp_path, 'r') as f:
            content = f.read()
        assert len(content) > 0
        assert "field" in content
        assert "type" in content
    finally:
        pathlib.Path(tmp_path).unlink(missing_ok=True)


def test_to_json():
    """Test JSON export functionality."""
    filename = _get_test_file()
    doc = pymupdf.open(filename)
    ff = doc.get_form_fields()

    json_content = ff.to_json()
    assert isinstance(json_content, str)

    # Verify it's valid JSON
    data = json.loads(json_content)
    assert isinstance(data, list)
    assert len(data) > 0

    # Verify structure of first item
    item = data[0]
    assert "field" in item
    assert "type" in item
    assert "current_value" in item
    assert "new_value" in item


def test_to_json_file_export():
    """Test JSON export to file."""
    filename = _get_test_file()
    doc = pymupdf.open(filename)
    ff = doc.get_form_fields()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        tmp_path = tmp.name

    try:
        result = ff.to_json(file=tmp_path)
        assert result is None  # Should not return when writing to file

        # Verify file was created and contains valid JSON
        with open(tmp_path, 'r') as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) > 0
    finally:
        pathlib.Path(tmp_path).unlink(missing_ok=True)


def test_to_dicts():
    """Test dictionary list export."""
    filename = _get_test_file()
    doc = pymupdf.open(filename)
    ff = doc.get_form_fields()

    dicts = ff.to_dicts()
    assert isinstance(dicts, list)
    assert len(dicts) > 0

    for item in dicts:
        assert "field" in item
        assert "type" in item
        assert "format" in item
        assert "editable" in item
        assert "choices" in item
        assert "current_value" in item
        assert "new_value" in item


def test_from_dicts():
    """Test importing field values from dictionary list."""
    filename = _get_test_file()
    doc = pymupdf.open(filename)
    ff = doc.get_form_fields()

    # Get current state and valid choices for MaritalStatus field
    original_value = ff.field_info("Person.MaritalStatus")["value"]
    valid_choices = ff.field_info("Person.MaritalStatus")["choices"]

    # Use a valid choice (if original is "married", use "single", else use "married")
    new_value = "single" if original_value == "married" else "married"

    # Create update dict
    updates = [
        {
            "field": "Person.MaritalStatus",
            "new_value": new_value
        }
    ]

    ff.from_dicts(updates)

    # Verify update applied
    updated_value = ff.field_info("Person.MaritalStatus")["value"]
    assert updated_value == new_value
    assert updated_value != original_value


def test_from_json():
    """Test importing field values from JSON."""
    filename = _get_test_file()
    doc = pymupdf.open(filename)
    ff = doc.get_form_fields()

    # Get current state and valid choices
    original_value = ff.field_info("Person.MaritalStatus")["value"]
    new_value = "single" if original_value == "married" else "married"

    # Create JSON with updates using a valid choice
    updates = [
        {
            "field": "Person.MaritalStatus",
            "new_value": new_value
        }
    ]
    json_str = json.dumps(updates)

    ff.from_json(json_str)

    # Verify update applied
    updated_value = ff.field_info("Person.MaritalStatus")["value"]
    assert updated_value == new_value


def test_json_roundtrip():
    """Test full JSON export and import roundtrip."""
    filename = _get_test_file()
    doc = pymupdf.open(filename)
    ff = doc.get_form_fields()

    # Capture initial state
    initial_values = {}
    for name, item in ff.fields.items():
        if item["terminal"]:
            initial_values[name] = item["value"]

    # Export to JSON
    json_content = ff.to_json()
    dicts = json.loads(json_content)

    # Modify some values in the JSON
    for item in dicts:
        if item["field"] == "Person.MaritalStatus":
            item["new_value"] = "single"

    # Reimport
    ff.from_json(json.dumps(dicts))

    # Verify changes
    assert ff.field_info("Person.MaritalStatus")["value"] == "single"


def test_multiple_field_updates():
    """Test updating multiple fields at once."""
    filename = _get_test_file()
    doc = pymupdf.open(filename)
    ff = doc.get_form_fields()

    # Update multiple fields
    updates = [
        {"field": "Person.MaritalStatus", "new_value": "single"},
    ]

    # Get additional field names to update if available
    for name, info in ff.fields.items():
        if info["terminal"] and info["type"] == "text" and name != "Person.MaritalStatus":
            updates.append({"field": name, "new_value": "TestValue"})
            break

    ff.from_dicts(updates)

    # Verify all updates were applied
    for update in updates:
        field_name = update["field"]
        expected_value = update["new_value"]
        actual_value = ff.field_info(field_name)["value"]
        assert actual_value == expected_value


def test_field_type_detection():
    """Test that various field types are correctly identified."""
    filename = _get_test_file()
    doc = pymupdf.open(filename)
    ff = doc.get_form_fields()

    # Collect field types found
    field_types = set()
    for name, info in ff.fields.items():
        if info["terminal"]:
            field_types.add(info["type"])

    # Should have at least one type
    assert len(field_types) > 0

    # Each type should have valid format
    valid_types = {"text", "radio", "checkbox", "choice", "button", "signature", "unknown"}
    for field_type in field_types:
        assert field_type in valid_types


def test_field_diagnosis():
    """Test field diagnosis information."""
    filename = _get_test_file()
    doc = pymupdf.open(filename)
    ff = doc.get_form_fields()

    for name, info in ff.fields.items():
        assert "diagnosis" in info
        diagnosis = info["diagnosis"]
        assert "ok" in diagnosis
        assert isinstance(diagnosis["ok"], bool)
