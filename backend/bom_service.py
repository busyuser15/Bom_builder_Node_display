import openpyxl

DESIRED_HEADERS = [
    "LEVEL",
    "PARENT PART NUMBER",
    "COMPONENT PART NUMBER",
    "STATUS",
    "FILE TYPE",
    "QTY",
    "Attrib:SPAREPART",
    "Attrib:SPAREPART SEVERITY",
    "Attrib:SPARESLISTQTY",
]


def normalize_header(title):
    if title == "FILE TYPE":
        return "TYPE"
    return title


def parse_excel_rows(sheet):
    headers_full = [cell.value for cell in sheet[1]]
    headers = []
    indices = []
    for i, title in enumerate(headers_full):
        if title in DESIRED_HEADERS:
            headers.append(normalize_header(title))
            indices.append(i)

    data = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        row_dict = {}
        for j, title in enumerate(headers):
            value = row[indices[j]]
            if value is not None and title in {"PARENT PART NUMBER", "COMPONENT PART NUMBER"}:
                value = str(value).strip()
            if title == "TYPE" and isinstance(value, str):
                if value[3:] == "ASM":
                    value = "ASSEMBLY"
                elif value[3:] == "PRT":
                    value = "PART"
            row_dict[title] = value

        row_dict["PARENT_PART_NUMBER"] = row_dict.pop("PARENT PART NUMBER", None)
        row_dict["COMPONENT_PART_NUMBER"] = row_dict.pop("COMPONENT PART NUMBER", None)
        row_dict["Attrib_SPAREPART"] = row_dict.pop("Attrib:SPAREPART", None)
        row_dict["Attrib_SPAREPART_SEVERITY"] = row_dict.pop("Attrib:SPAREPART SEVERITY", None)
        row_dict["Attrib_SPARESLISTQTY"] = row_dict.pop("Attrib:SPARESLISTQTY", None)
        data.append(row_dict)

    return data


def parse_bom_excel(file_path):
    workbook = openpyxl.load_workbook(file_path, data_only=True)
    sheet = workbook.active
    return parse_excel_rows(sheet)
