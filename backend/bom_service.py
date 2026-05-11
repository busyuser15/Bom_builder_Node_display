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

    print(f"Found headers: {headers}")
    print(f"Header indices: {indices}")
    
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

    print(f"Total rows parsed: {len(data)}")
    if data:
        print(f"Sample row: {data[0]}")
    
    return data


def build_hierarchy(data):
    print(f"\n=== Starting build_hierarchy with {len(data)} rows ===")
    
    # Build component revisions (simplified)
    comp_rev = {}
    parent_rev = {}
    
    for row in data:
        comp_part = row.get("COMPONENT_PART_NUMBER")
        parent_part = row.get("PARENT_PART_NUMBER")
        
        if comp_part and comp_part not in comp_rev:
            comp_rev[comp_part] = "-00"
        if parent_part and parent_part not in parent_rev:
            parent_rev[parent_part] = "-00"
    
    # Build hierarchical structure similar to tkinter
    levels = set()
    
    for row in data:
        level = row.get("LEVEL")
        if level is not None:
            try:
                level = int(level)
            except (ValueError, TypeError):
                print(f"Warning: Could not convert level {level} to int")
                continue
            levels.add(level)
    
    levels = sorted(levels)
    print(f"Found levels: {levels}")
    
    if not levels:
        print("ERROR: No valid levels found")
        return {"tree_data": [], "comp_values": {}, "comp_status": {}, "levels": []}
    
    component_level_lists = {level: [] for level in levels}
    parent_level_lists = {level: [] for level in levels}
    comp_status = {}
    comp_values = {}
    
    for row in data:
        level = row.get("LEVEL")
        parent_part = row.get("PARENT_PART_NUMBER")
        comp_part = row.get("COMPONENT_PART_NUMBER")
        
        try:
            level = int(level)
        except (ValueError, TypeError):
            continue
        
        if level not in component_level_lists or not comp_part:
            continue
        
        if parent_part:
            parent_part = parent_part + parent_rev.get(parent_part, "-00")
        comp_part = comp_part + comp_rev.get(comp_part, "-00")
        
        parent_level_lists[level].append(parent_part)
        component_level_lists[level].append(comp_part)
        
        # Build comp_status
        comp_status[comp_part] = row.get("STATUS")
        
        # Build comp_values
        type_val = row.get("TYPE", "")
        if isinstance(type_val, str):
            if type_val.endswith("ASM"):
                type_val = "ASSEMBLY"
            elif type_val.endswith("PRT"):
                type_val = "PART"
        
        # Description placeholder
        desc = f"Description for {comp_part}"
        
        values = [
            desc,  # Description
            row.get("STATUS"),  # Status
            type_val,  # Type
            False,  # Phantom Assembly
            False,  # Treat as part
            "",  # Classification
            row.get("Attrib_SPAREPART", ""),  # Attr:SpareParts
            row.get("Attrib_SPAREPART_SEVERITY", ""),  # Attr:SpareParts Severity
            row.get("Attrib_SPARESLISTQTY", "")  # Attr:SpareParts Qty
        ]
        comp_values[comp_part] = values
    
    print(f"Component values count: {len(comp_values)}")
    print(f"Component level lists: {[(k, len(v)) for k, v in component_level_lists.items()]}")
    
    # Build tree structure
    def build_tree_structure():
        tree_data = []
        processed_parts = set()
        max_level = max(levels) if levels else 0
        
        def add_node(part_num, current_level):
            if part_num in processed_parts or not part_num:
                return None
            
            processed_parts.add(part_num)
            node = {
                "id": part_num,
                "text": part_num,
                "values": comp_values.get(part_num, []),
                "children": []
            }
            
            # Find children in subsequent levels
            for next_level in range(current_level + 1, max_level + 1):
                if next_level in component_level_lists:
                    for i, parent in enumerate(parent_level_lists[next_level]):
                        if parent == part_num:
                            child_part = component_level_lists[next_level][i]
                            child_node = add_node(child_part, next_level)
                            if child_node:
                                node["children"].append(child_node)
            
            return node
        
        # Start with level 0 parts (those with no parent)
        level_0_parts = set()
        if 0 in parent_level_lists:
            for i, parent in enumerate(parent_level_lists[0]):
                if not parent:  # No parent means root level
                    part = component_level_lists[0][i]
                    level_0_parts.add(part)
        
        print(f"Level 0 parts found: {len(level_0_parts)}")
        
        # Also check for parts that appear as parents but not as children at lower levels
        all_children = set()
        for level in levels:
            if level > 0:
                all_children.update(component_level_lists[level])
        
        all_parents = set()
        for level in levels:
            for parent in parent_level_lists[level]:
                if parent:
                    all_parents.add(parent)
        
        potential_roots = all_parents - all_children
        print(f"Potential roots found: {len(potential_roots)}")
        level_0_parts.update(potential_roots)
        
        for part in level_0_parts:
            root_node = add_node(part, 0)
            if root_node:
                tree_data.append(root_node)
        
        print(f"Tree nodes created: {len(tree_data)}")
        return tree_data
    
    tree_structure = build_tree_structure()
    
    return {
        "tree_data": tree_structure,
        "comp_values": comp_values,
        "comp_status": comp_status,
        "levels": levels
    }


def parse_bom_excel(file_path):
    workbook = openpyxl.load_workbook(file_path, data_only=True)
    sheet = workbook.active
    rows = parse_excel_rows(sheet)
    print(f"\nParsed {len(rows)} rows from Excel")
    hierarchy = build_hierarchy(rows)
    print(f"Hierarchy result: tree_data has {len(hierarchy['tree_data'])} nodes")
    print(f"Hierarchy result: comp_values has {len(hierarchy['comp_values'])} items")
    print(f"Full hierarchy: {hierarchy}")
    return hierarchy
