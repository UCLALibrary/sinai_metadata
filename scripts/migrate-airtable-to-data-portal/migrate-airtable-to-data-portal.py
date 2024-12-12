import pandas as pd, json, sys, os, datetime
from io import StringIO

# Function Declarations
"""
Takes a Pandas Data Frame representing a CSV row; and a string representing a data portal record type
Transforms the CSV data into a Python dictionary to be serialized as a JSON record following the Data Portal data model
"""
def transform_row_to_json(row, record_type):
    """
     Based on the mapping of CSV column headers to JSON fields, create a json file from the data row
    """
    # declare an empty dictionary for the resulting JSON
    data = {}
    """
    N.B.: Order of fields should be retained,
    hence the use of if/then for fields only relevant to a subest of record types
    """

    data["ark"] = str(row["Item ARK"])

    # TBD: review field contents to make sure this comparison works correctly
    data["reconstruction"] = str(row["Reconstruction"]) == "true"
    
    # For ms objects only, add the ms_obj type
    if record_type == "ms_objs":
        data["type"] = {
            "id": str(row["Type ID"]),
            "label": str(row["Type Label"])
        }
    
    # Supply the shelf mark for MS Objects
    if record_type == "ms_objs":
        data["shelfmark"] = str(row["Shelfmark"])
    # Otherwise, use the label property
    else:
        data["label"] = str(row["Label"])
    
    # add locus for layers and text_units
    if record_type != "ms_objs" and not(pd.isnull(row["Locus"])):
        data["locus"] = str(row["Locus"])
    
    if not(pd.isnull(row["Summary"])):
        data["summary"] = str(row["Summary"])

    # add extent
    if not(pd.isnull(row["Extent"])):
        data["extent"] = str(row["Extent"])

    if record_type == "ms_objs" and not(pd.isnull(row["Weight"])):
        data["weight"] = str(row["Weight"])
    
    if record_type == "ms_objs" and not(pd.isnull(row["MS Dimensions"])):
        data["dim"] = str(row["MS Dimensions"])
    
    # TBD: reordering of fields in layers schema?
    if record_type == "ms_objs" or record_type == "layers":
        data["state"] = {
            "id": str(row["State ID"]), 
            "label": str(row["State Label"])
        }
    
    # For layers, create writing array of objects
    if record_type == "layers":
        data["writing"] = [create_writing_from_row(row)]
    
    # For layers, create ink object
    # TBD: for boolean, would we have locus or notes if not ink color?
    if record_type == "layers" and not(pd.isnull(row["Ink Color"])):
        data["ink"] = [create_ink_from_row(row)]

    # For layers, create layout objects
    # If any of the fields are non-empty, create the object
    if record_type == "layers" and (not(pd.isnull(row["Layout Columns"])) or not(pd.isnull(row["Layout Lines"])) or not(pd.isnull(row["Layout Note"])) or  not(pd.isnull(row["Layout Locus"])) or not(pd.isnull(row["Layout Dimensions"]))):
        data["layout"] = [create_layout_from_row(row)]

    # Add text_unit object to layers
    if record_type == "layers":
        data["text_unit"] = create_text_unit_reference_from_row(row)
    
    if record_type == "ms_objs" and not(pd.isnull(row["Foliation"])):
        data["fol"] = str(row["Foliation"])

    if record_type == "ms_objs" and not(pd.isnull(row["Collation"])):
        data["coll"] = str(row["Collation"])
    
    # Collate and add features data if any
    if not(pd.isnull(row["Feature Labels"])) and not(pd.isnull(row["Feature ID"])):
        feature_labels = parse_rolled_up_field(str(row["Feature Labels"]), ",", '"')
        feature_ids = parse_rolled_up_field(str(row["Feature ID"]), ",", '"')
        features = []
        for i in range(0, len(feature_ids)):
            feat = {
                "id": feature_ids[i],
                "label": feature_labels[i]
            }
            features.append(feat)
        data["features"] = features
    # remove features property if empty
    if "features" in data and len(data["features"]) == 0:
        data.pop("features")

    if record_type == "ms_objs":
        data["part"] = [create_part_from_row(row)]

    # TBD: this may not be used for the ms_objs level
    if record_type == "ms_objs":
        data["layer"] = create_layer_reference_from_row(row, False) # note: this function is for creating the layer sub-object that references layer records
    # remove ms layers if none created
    if "layer" in data and len(data["layer"]) == 0:
        data.pop("layer")
    
    # add paracontent stub, which may be removed later if none are created
    data["para"] = []

    # add colophons as paracontent objects for layers
    if record_type == "layers" and not(pd.isnull(row["Colophon"])):
        data["para"] += create_paracontent_from_row(row, "Colophon", paracontents_table)

    # TBD: has_bind -- waiting to see how the data will look
    if record_type == "ms_objs" and not(pd.isnull(row["Has Binding"])):
        data["has_bind"] = str(row["Has Binding"]) == "true"
    

    # add location if an ms_obj
    if record_type == "ms_objs":
        location = {}
        location["id"] = str(row["Location ID"])
        # add collection only if it is not empty
        if not(pd.isnull(row["Collection"])):
            location["collection"] = str(row["Collection"])
        location["repository"] = str(row["Repository"])

        data["location"] = [location]
    
    # Add stub assoc_*; these will be added to or deleted if they remain empty
    data["assoc_date"] = []
    data["assoc_name"] = []
    data["assoc_place"] = []

    # add assoc_date for origin date in layers
    if record_type == "layers" and not(pd.isnull(row["Origin Date"])):
        data["assoc_date"].append(create_associated_date(
            type= {"id": "origin", "label": "Date of Origin"},
            as_written="",
            value=str(row["Origin Date"]),
            iso=str(row["Origin Date ISO"]),
            note=[str(row["Origin Date Note"])]
        ))
    # add assoc_name for scribes
    if record_type == "layers":
        if not(pd.isnull(row["Scribe ID"])):
            values = parse_rolled_up_field(str(row["Scribe Value"]), "|~|", "#")
            scribe_arks = parse_rolled_up_field(str(row["Scribe ID"]), ",", "#")
            notes = parse_rolled_up_field(str(row["Scribe Note"]), "|~|", "#")
            for i in range(0, len(scribe_arks)):
                data["assoc_name"].append(create_associated_name(
                    id=scribe_arks[i],
                    value=values[i],
                    as_written="",
                    role={"id": "scribe", "label": "Scribe"},
                    note=[notes[i]]
                ))
        elif not(pd.isnull(row["Scribe Value"])):
            data["assoc_name"].append(create_associated_name(
                    id="",
                    value=str(row["Scribe Value"]),
                    as_written="",
                    role={"id": "scribe", "label": "Scribe"},
                    note=parse_rolled_up_field(str(row["Scribe Note"]), "|~|", "#")
                ))
                
    # add assoc_place for origin place
    # TBD: if we have ARKs ever, rewrite this; currently only have a value field
    if record_type == "layers" and not(pd.isnull(row["Origin Place Value"])):
        data["assoc_place"].append(create_associated_place(
            id="",
            value=str(row["Origin Place Value"]),
            as_written="",
            event={"id": "origin", "label": "Place of Origin"},
            note=parse_rolled_up_field(str(row["Origin Place Note"]), "|~|", "#")
        ))

    # Add notes field
    data["note"] = create_notes_from_row(row, record_type, 0)
    # remove notes field if none were created
    if len(data["note"]) == 0:
        data.pop("note")

    # Add related_mss field if it is not flagged as being at the part level
    if record_type in ["ms_objs", "layers"] and not(pd.isnull(row["Related MSS JSON"])) and str(row["Related MSS Level"]) != "part":
        data["related_mss"] = create_related_mss_from_row(row)
    # remove related_mss field if none were created
    if "related_mss" in data and len(data["related_mss"]) == 0:
        data.pop("related_mss")

    # Viscodex, ms_objs only
    if record_type == "ms_objs" and not(pd.isnull(row["Viscodex URL"])) and not(pd.isnull(row["Viscodex Label"])):
        # hard-coded type
        viscodex_type = {"id": "manuscript", "label": "Manuscript"}
        # create the viscodex object and add to the record
        viscodex = {
            "type": viscodex_type,
            "label": str(row["Viscodex Label"]),
            "url": str(row["Viscodex URL"])
        }
        data["viscodex"] = [viscodex]
    
    if not(pd.isnull(row["Reference Instances"])):
        data["bib"] = create_bibs_from_row(row, ref_instances)
    # remove bib field if none were created
    if "bib" in data and len(data["bib"]) == 0:
        data.pop("bib")

    # IIIF info, ms_objs only
    if record_type == "ms_objs":
        # hard-coded type is 'main'
        iiif = {}
        iiif["type"] = {
                    "id": "main",
                    "label": "Main"
                }
        iiif["manifest"] = str(row["IIIF Manifest URL"])
        if not(pd.isnull(row["IIIF Text Direction"])): 
            iiif["text_direction"] = str(row["IIIF Text Direction"])

        if not(pd.isnull(row["IIIF Behavior"])):
            iiif["behavior"] = str(row["IIIF Behavior"])

        if not(pd.isnull(row["IIIF Thumbnail URL"])):
            iiif["thumbnail"] = str(row["IIIF Thumbnail URL"])
        
        data["iiif"] = [iiif]
    
    #TBD: internal (from admin notes)
    """
    TBD: Cataloguer field not needed at the ms_obj level. TBD for layers
    # TBD cataloguer field for running the script (set in a config for who runs the script?)
    data["cataloguer"] = [] # TBD: this initiates the field for use in the Contributo info; otherwise replace with the contributor data for who runs the script

    # Cataloguer info from Contributor field
    if not(pd.isnull(row["Contributor Name"])):
        timestamp = datetime.datetime.now()
        # parse the rolled up fields containing change log info
        contributors = parse_rolled_up_field(str(row["Contributor Name"]), ",", "#")
        messages = parse_rolled_up_field(str(row["Change Log Message"]), "|~|", "#")
        orcids = parse_rolled_up_field(str(row["Contributor ORCiD"]), ",", "#")

        # for each listed contribution, add the change log info
        change_log = []
        for i in range(0, len(contributors)):
            change = {}
            change["message"] = messages[i]
            change["contributor"] = contributors[i]
            change["added_by"] = orcids[i]
            change["timestamp"] = timestamp
            change_log.append(change)
        
        data["cataloguer"] += change_log
    """

    # reconstructed from, only used for records that are reconstructions
    if data["reconstruction"]:
        data["reconstructed_from"] = parse_rolled_up_field(str(row["Reconstructed From"]), ",", "#")


    # Parent, for records that are not ms_objs
    if record_type != "ms_objs":
        data["parent"] = parse_rolled_up_field(str(row["Parent ARKs"]), ",", "#")
    
    # Remove empty paracontents if no data was added
    if "para" in data and len(data["para"]) == 0:
        data.pop("para")
    # Remove empty assoc_* if no data was added to them
    if "assoc_date" in data and len(data["assoc_date"]) == 0:
        data.pop("assoc_date")
    if "assoc_name" in data and len(data["assoc_name"]) == 0:
        data.pop("assoc_name")
    if "assoc_place" in data and len(data["assoc_place"]) == 0:
        data.pop("assoc_place")
    """

     Left to write for layers:
    - [x] writing (script, script label, locus, notes)
    - [x] ink color and notes, and locus
    - [x] layout (columns, lines, notes)
    - [x] text unit object (reuse algorithm from ms_obj.layers)
    - [x] colophon (make it a generic paracontent function), sub function for all record types?
    - [x] assoc_name for scribe (implied type)
        - make generic, so callable from para function as well, with optional passed type
    - [x] assoc_date for origin (implied type)
            - make generic, so callable from para function as well, with optional passed type
    - [x] assoc_place for place of origin (implied type)
            - make generic, so callable from para function as well, with optional passed type
    - [x] notes for layers
        - [x] ornamentation
        - [x] contents
        - [x] provenance
        - [x] paracontent
        - [x] general
        - [x] origin
    - [ ] Contributor (in progress, check it works)

    UTOs
    - [x] locus
    - [ ] related_mss at layer level?
        - already implemented, just needs to be added to the data
        - and/or related note?
    - [ ] notes in UTOs
        - bib note? (reference notes)
        - [x] foliation note

              """
    return data

def create_part_from_row(row: pd.Series):
    part_data = {}

    if not(pd.isnull(row["Part Label"])):
        part_data["label"] = str(row["Part Label"])

    # Collate and add support data
    support_labels = parse_rolled_up_field(str(row["Support Label"]), ",", '"')
    support_ids = parse_rolled_up_field(str(row["Support ID"]), ",", '"')
    supports = []
    for i in range(0, len(support_ids)):
        sup = {
            "id": support_ids[i],
            "label": support_labels[i]
        }
        supports.append(sup)
    part_data["support"] = supports

    if not(pd.isnull(row["Part Dimensions"])):
        part_data["dim"] = str(row["Part Dimensions"])

    part_data["layer"] = create_layer_reference_from_row(row, True)
    
    part_data["note"] = create_notes_from_row(row, "ms_objs", 1)
    # remove notes field if none were created
    if len(part_data["note"]) == 0:
        part_data.pop("note")
    
    # Add related_mss field if non-empty and flagged as being at the part level
    if not(pd.isnull(row["Related MSS JSON"])) and str(row["Related MSS Level"]) == "part":
        part_data["related_mss"] = create_related_mss_from_row(row)
    
    return part_data


# Takes a row from a CSV and a boolean indicating if is called by a part or not
# Creates the overtext, undertext, and guest content layers
def create_layer_reference_from_row(row: pd.Series, is_part: bool):
    layers = []
    column_prefix = "MS "
    # include overtexts and use part columns if called by a part; overtext is required if part
    if is_part:
       overtext_data = get_layer_data(arks=str(row["Overtext ARKs"]), 
                                      labels=str(row["Overtext Labels"]), 
                                      locus=str(row["Overtext Locus"]), 
                                      sep="\|~\|", quotechar="#")
       layers += create_layer_object(overtext_data,
                                        type={"id": "overtext", "label": "Overtext"})
       column_prefix = "Part " # prefix will be 'Part ' otherwise stays "MS "
    
    # UTOs, optional
    if not(pd.isnull(row[column_prefix + "UTO ARKs"])):
        undertext_data = get_layer_data(arks=str(row[column_prefix + "UTO ARKs"]), 
                                      labels=str(row[column_prefix + "UTO Labels"]), 
                                      locus=str(row[column_prefix + "UTO Locus"]), 
                                      sep="\|~\|", quotechar="#")
        layers += create_layer_object(undertext_data,
                                type={"id": "undertext", "label": "Undertext"})

    # Guest Content, optional
    if not(pd.isnull(row[column_prefix + "Guest ARKs"])):
        guest_data = get_layer_data(arks=str(row[column_prefix + "Guest ARKs"]), 
                                      labels=str(row[column_prefix + "Guest Labels"]), 
                                      locus=str(row[column_prefix + "Guest Locus"]), 
                                      sep="\|~\|", quotechar="#")
        layers += create_layer_object(guest_data,
                                    type={"id": "guest", "label": "Guest Content"})

    return layers

def get_layer_data(arks, labels, locus, sep, quotechar):
    layer_data = {}
    layer_data["arks"] = pd.read_csv(StringIO(arks), sep=sep, quotechar=quotechar, skipinitialspace=True, engine='python', header=None).iloc[0]
    layer_data["labels"] = pd.read_csv(StringIO(labels), sep=sep, quotechar=quotechar, skipinitialspace=True, engine='python', header=None).iloc[0]
    # only parse locus if not empty
    if len(locus) > 0 and locus != "nan":
        layer_data["locus"] = pd.read_csv(StringIO(locus), sep=sep, quotechar=quotechar, skipinitialspace=True, engine='python', header=None, keep_default_na=False).iloc[0]
    # supply values that will be ignored for empty locus fields
    else:
        layer_data["locus"] = []
        for i in range(0, len(layer_data["arks"])):
            layer_data["locus"].append("nan")
    return layer_data

# restriction: relies on exact match of arks and labels
# TBD: throw exception if lengths of ark and label arrays don't match?
# Given a dictionary of lists of arks, labels, locus; and a type object return a list of layer objects
def create_layer_object(layer_data, type):
    layers = []
    for i in range(0, len(layer_data["arks"])):
        if layer_data["arks"][i] == "" or layer_data["arks"][i] == "nan":
            continue
        layer = {}
        layer["id"] = layer_data["arks"][i]
        layer["label"] = layer_data["labels"][i]
        layer["type"] = type

        # add locus only if it exists for this pairing
        if "locus" in layer_data and layer_data["locus"][i] != "<NA>" and layer_data["locus"][i] != "nan" and layer_data["locus"][i] != "":
            layer["locus"] = layer_data["locus"][i]
        
        layers.append(layer)
    return layers

def create_text_unit_reference_from_row(row):
    # reusing the get_layer_data function since the same info is required
    text_unit_data = get_layer_data(arks=str(row["Text Unit ARKs"]),
                                    labels=str(row["Text Unit Labels"]),
                                    locus=str(row["Text Unit Locus"]),
                                    sep="\|~\|",
                                    quotechar="#")
    # TBD: could make the create_*_object function more generic by giving 'type' as optional param
    return create_text_unit_object(text_unit_data)
    

def create_text_unit_object(text_unit_data):
    text_units = []
    for i in range(0, len(text_unit_data["arks"])):
        if text_unit_data["arks"][i] == "" or text_unit_data["arks"][i] == "nan":
            continue
        text_unit = {}
        text_unit["id"] = text_unit_data["arks"][i]
        text_unit["label"] = text_unit_data["labels"][i]

        # add locus only if it exists for this pairing
        if "locus" in text_unit_data and text_unit_data["locus"][i] != "<NA>" and text_unit_data["locus"][i] != "nan" and text_unit_data["locus"][i] != "":
            text_unit["locus"] = text_unit_data["locus"][i]
        
        text_units.append(text_unit)
    return text_units

def create_paracontent_from_row(row: pd.Series, column_name: str, paracontent_table: pd.DataFrame):
    paracontents = []
    para_refs = pd.read_csv(StringIO(str(row[column_name])), header=None).iloc[0]
    for id in para_refs:
        para_data = {}
        para_data["type"] = {
            "id": str(paracontent_table.loc[int(id), "Type ID"]),
            "label": str(paracontent_table.loc[int(id), "Type Label"])
        }
        if not(pd.isnull(paracontent_table.loc[int(id), "Locus"])):
            para_data["locus"] = str(paracontent_table.loc[int(id), "Locus"])
        
        lang_ids = parse_rolled_up_field(str(paracontent_table.loc[int(id), "Language ID"]), ",", '#')
        lang_labels = parse_rolled_up_field(str(paracontent_table.loc[int(id), "Language Label"]), ",", '#')
        para_data["lang"] = []
        for i in range(0, len(lang_ids)):
            para_data["lang"].append(
                {
                    "id": lang_ids[i],
                    "label": lang_labels[i]
                }
            )
        
        # script, optional. Array of objects
        if not(pd.isnull(paracontent_table.loc[int(id), "Script ID"])):
            script_ids = parse_rolled_up_field(str(paracontent_table.loc[int(id), "Script ID"]), ",", '#')
            script_labels = parse_rolled_up_field(str(paracontent_table.loc[int(id), "Script Label"]), ",", '#')
            writing_systems = parse_rolled_up_field(str(paracontent_table.loc[int(id), "Writing System"]), ",", '#')
            para_data["script"] = []
            for i in range(0, len(script_ids)):
                para_data["script"].append(
                    {
                        "id": script_ids[i],
                        "label": script_labels[i],
                        "writing_system": writing_systems[i]
                    }
                )

        if not(pd.isnull(paracontent_table.loc[int(id), "Label"])):
            para_data["label"] = str(paracontent_table.loc[int(id), "Label"])
        
        if not(pd.isnull(paracontent_table.loc[int(id), "As Written"])):
            para_data["as_written"] = str(paracontent_table.loc[int(id), "As Written"])

        # translation: optional, array of strings
        if not(pd.isnull(paracontent_table.loc[int(id), "Translation"])):
            para_data["translation"] = parse_rolled_up_field(paracontent_table.loc[int(id), "Translation"], "|~|", "#")
        
        # assoc_*: optional, array of objects, need to be created via other function
        if not(pd.isnull(paracontent_table.loc[int(id), "Associated Name Role ID"])):
            para_data["assoc_name"] = create_list_of_para_associated(paracontent_table.loc[int(id)], "assoc_name")
        
        if not(pd.isnull(paracontent_table.loc[int(id), "Associated Place Event ID"])):
            para_data["assoc_place"] = create_list_of_para_associated(paracontent_table.loc[int(id)], "assoc_place")

        if not(pd.isnull(paracontent_table.loc[int(id), "Associated Date Type ID"])):
            para_data["assoc_date"] = create_list_of_para_associated(paracontent_table.loc[int(id)], "assoc_date")


        # note: optional, array of strings
        if not(pd.isnull(paracontent_table.loc[int(id), "Notes"])):
            para_data["note"] = parse_rolled_up_field(paracontent_table.loc[int(id), "Notes"], "|~|", "#")
        
        paracontents.append(para_data)

    return paracontents

def create_list_of_para_associated(para_row: pd.Series, assoc_type: str):
    data = []
    sep = "\|~\|"
    quotechar = "#"
    # assoc_name and assoc_place share most similarities
    if assoc_type == "assoc_name" or assoc_type == "assoc_place":
        # set the column prefix
        if assoc_type == "assoc_name":
            col_prefix = "Associated Name "
            # parse role id and labels (as 'type')
            type_ids = pd.read_csv(StringIO(str(para_row[col_prefix + "Role ID"])), sep=sep, quotechar=quotechar, skipinitialspace=True, engine='python', header=None).iloc[0]
            type_labels = pd.read_csv(StringIO(str(para_row[col_prefix + "Role Label"])), sep=sep, quotechar=quotechar, skipinitialspace=True, engine='python', header=None).iloc[0]
            
        elif assoc_type == "assoc_place":
            col_prefix = "Associated Place "
            # parse event id and labels (as 'type')
            type_ids = pd.read_csv(StringIO(str(para_row[col_prefix + "Event ID"])), sep=sep, quotechar=quotechar, skipinitialspace=True, engine='python', header=None).iloc[0]
            type_labels = pd.read_csv(StringIO(str(para_row[col_prefix + "Event Label"])), sep=sep, quotechar=quotechar, skipinitialspace=True, engine='python', header=None).iloc[0]
        
        # parse arks, supply empty strings if the cell is blank
        arks = pd.read_csv(StringIO(str(para_row[col_prefix + "ARKs"])), sep=sep, quotechar=quotechar, skipinitialspace=True, engine='python', keep_default_na=False, header=None).iloc[0].values.flatten().tolist()
        # if cell was blank, add empty strings up to the length of types
        if len(arks) <= 1 and arks[0] == "nan": # 'nan' would be returned as the only value if cell is empty
            arks = []
            for i in range(0, len(type_ids)):
                arks.append("")

         # parse values, supply empty strings if the cell is blank
        values = pd.read_csv(StringIO(str(para_row[col_prefix + "Value"])), sep=sep, quotechar=quotechar, skipinitialspace=True, engine='python', keep_default_na=False, header=None).iloc[0].values.flatten().tolist()
        # if cell was blank, add empty strings up to the length of types
        if len(values) <= 1 and values[0] == "nan": # 'nan' would be returned as the only value if cell is empty
            values = []
            for i in range(0, len(type_ids)):
                values.append("")

        as_written = pd.read_csv(StringIO(str(para_row[col_prefix + "As Written"])), sep=sep, quotechar=quotechar, skipinitialspace=True, engine='python', keep_default_na=False, header=None).iloc[0].values.flatten().tolist()
        # if cell was blank, add empty strings up to the length of types
        if len(as_written) <= 1 and as_written[0] == "nan": # 'nan' would be returned as the only value if cell is empty
            as_written = []
            for i in range(0, len(type_ids)):
                as_written.append("")

        # TBD: treating notes as a one-to-one with assoc_* object, update to allow multiple delimiter types if needing more than one note per object
        notes = pd.read_csv(StringIO(str(para_row[col_prefix + "Note"])), sep=sep, quotechar=quotechar, skipinitialspace=True, engine='python', keep_default_na=False, header=None).iloc[0].values.flatten().tolist()
        # if cell was blank, add empty strings up to the length of types
        if len(notes) <= 1 and notes[0] == "nan": # 'nan' would be returned as the only value if cell is empty
            notes = []
            for i in range(0, len(type_ids)):
                notes.append("")


        for i in range(0, len(type_ids)):
            if assoc_type == "assoc_name":
                data.append(create_associated_name(
                    id=arks[i],
                    value=values[i],
                    as_written=as_written[i],
                    role={"id": type_ids[i], "label": type_labels[i]},
                    note=notes[i]
                ))
            elif assoc_type == "assoc_place":
                data.append(create_associated_place(
                    id=arks[i],
                    value=values[i],
                    as_written=as_written[i],
                    event={"id": type_ids[i], "label": type_labels[i]},
                    note=notes[i]
                ))
    elif assoc_type == "assoc_date":
        col_prefix = "Associated Date "
        type_ids = pd.read_csv(StringIO(str(para_row[col_prefix + "Type ID"])), sep=sep, quotechar=quotechar, skipinitialspace=True, engine='python', header=None).iloc[0]
        type_labels = pd.read_csv(StringIO(str(para_row[col_prefix + "Type Label"])), sep=sep, quotechar=quotechar, skipinitialspace=True, engine='python', header=None).iloc[0]
        as_written = pd.read_csv(StringIO(str(para_row[col_prefix + "As Written"])), sep=sep, quotechar=quotechar, skipinitialspace=True, engine='python', keep_default_na=False, header=None).iloc[0].values.flatten().tolist()
        # if cell was blank, add empty strings up to the length of types
        if len(as_written) <= 1 and as_written[0] == "nan": # 'nan' would be returned as the only value if cell is empty
            as_written = []
            for i in range(0, len(type_ids)):
                as_written.append("")
        values = pd.read_csv(StringIO(str(para_row[col_prefix + "Value"])), sep=sep, quotechar=quotechar, skipinitialspace=True, engine='python', keep_default_na=False, header=None).iloc[0].values.flatten().tolist()
        # if cell was blank, add empty strings up to the length of types
        if len(values) <= 1 and values[0] == "nan": # 'nan' would be returned as the only value if cell is empty
            values = []
            for i in range(0, len(type_ids)):
                values.append("")
        
        iso = pd.read_csv(StringIO(str(para_row[col_prefix + "ISO"])), sep=sep, quotechar=quotechar, skipinitialspace=True, engine='python', keep_default_na=False, header=None).iloc[0].values.flatten().tolist()
        if len(iso) <= 1 and iso[0] == 'nan':
            iso = []
            for i in range(0, len(type_ids)):
                iso.append("")

        as_written = pd.read_csv(StringIO(str(para_row[col_prefix + "As Written"])), sep=sep, quotechar=quotechar, skipinitialspace=True, engine='python', keep_default_na=False, header=None).iloc[0].values.flatten().tolist()
        if len(as_written) <= 1 and as_written[0] == 'nan':
            as_written = []
            for i in range(0, len(type_ids)):
                as_written.append("")
        
        # TBD: treating notes as a one-to-one with assoc_* object, update to allow multiple delimiter types if needing more than one note per object
        notes = pd.read_csv(StringIO(str(para_row[col_prefix + "Note"])), sep=sep, quotechar=quotechar, skipinitialspace=True, engine='python', keep_default_na=False, header=None).iloc[0].values.flatten().tolist()
        # if cell was blank, add empty strings up to the length of types
        if len(notes) <= 1 and notes[0] == "nan": # 'nan' would be returned as the only value if cell is empty
            notes = []
            for i in range(0, len(type_ids)):
                notes.append("")

        for i in range(0, len(type_ids)):
            data.append(create_associated_date(
                type={"id": type_ids[i], "label": type_labels[i]},
                as_written=str(as_written[i]),
                value=str(values[i]),
                iso=str(iso[i]),
                note=notes[i]
                )
            )
            
    return data
    
# takes a row (pandas Series); record_type string; and a boolean indicating whether the context is ms_obj.part or not
# uses the record type and is_part to determine which columns to pass to the function that creates the typed note fields
def create_notes_from_row(row: pd.Series, record_type: str, is_part: bool):
    cols = []
    # pass columns to note based on record type
    if record_type == "ms_objs":
        # column configurations for ms-level notes
        if not(is_part):
            cols += [
                {
                    "data": str(row["Support note"]),
                    "type": {
                        "id": "support",
                        "label": "Support Note"
                    }
                },
                {
                    "data": str(row["Provenance note"]),
                    "type": {
                        "id": "provenance",
                        "label": "Provenance Note"
                    }
                },
                {
                    "data": str(row["Paracontent note"]),
                    "type": {
                        "id": "para",
                        "label": "Paracontent Note"
                    }
                },
                {
                    "data": str(row["Foliation note"]),
                    "type": {
                        "id": "foliation",
                        "label": "Foliation Note"
                    }
                },
                {
                    "data": str(row["Binding note"]),
                    "type": {
                        "id": "binding",
                        "label": "Binding Note"
                    }
                },
                {
                    "data": str(row["Condition note"]),
                    "type": {
                        "id": "condition",
                        "label": "Condition Note"
                    }
                },
                {
                    "data": str(row["Collation note"]),
                    "type": {
                        "id": "collation",
                        "label": "Collation Note"
                    }
                },
                {
                    "data": str(row["Contents note"]),
                    "type": {
                        "id": "contents",
                        "label": "Contents Note"
                    }
                },
                {
                    "data": str(row["Ornamentation note"]),
                    "type": {
                        "id": "ornamentation",
                        "label": "Ornamentation Note"
                    }
                },
                {
                    "data": str(row["General note"]),
                    "type": {
                        "id": "general",
                        "label": "Other Notes"
                    }
                }
            ]
        # Column configurations for part notes
        else:
            cols += [
                {
                    "data": str(row["Part Collation note"]),
                    "type": {
                        "id": "collation",
                        "label": "Collation Note"
                    }
                }
            ]
    # Column configurations for layer notes
    # TBD: could make some 'generic' to reduce duplication here
    if record_type == "layers":
        cols += [
                {
                    "data": str(row["Provenance note"]),
                    "type": {
                        "id": "provenance",
                        "label": "Provenance Note"
                    }
                },
                {
                    "data": str(row["Paracontent note"]),
                    "type": {
                        "id": "para",
                        "label": "Paracontent Note"
                    }
                },
                {
                    "data": str(row["Foliation note"]),
                    "type": {
                        "id": "foliation",
                        "label": "Foliation Note"
                    }
                },
                {
                    "data": str(row["Contents note"]),
                    "type": {
                        "id": "contents",
                        "label": "Contents Note"
                    }
                },
                {
                    "data": str(row["Ornamentation note"]),
                    "type": {
                        "id": "ornamentation",
                        "label": "Ornamentation Note"
                    }
                },
                {
                    "data": str(row["General note"]),
                    "type": {
                        "id": "general",
                        "label": "Other Notes"
                    }
                }
        ]

    return create_notes_from_specific_columns(cols)

# Take a list of dictionaries representing notes data organized by types, return a series of data portal note
def create_notes_from_specific_columns(notes_by_type: list):
    all_notes = []
    for note_type in notes_by_type:
        for note in parse_rolled_up_field(note_type["data"], "|~|", "#"):
            # skip empty, but create note objects for each delimited note field
            if note != "<NA>" and note != "" and note != "nan":
                all_notes.append(
                    {
                        "type": note_type["type"],
                        "value": note
                    }
                )
    return all_notes

# TBD: finalize field names here
# take a row and parse the fields related to the related_mss object
def create_related_mss_from_row(row: pd.Series):
    related = {}
    related["type"] = {
        "id": str(row["Related MSS Type"]),
        "label": str(row["Related MSS Type Label"])
    }
    related["label"] = str(row["Related MSS Label"])

    if not(pd.isnull(row["Related MSS Note"])):
        related["note"] = parse_rolled_up_field(str(row["Related MSS Note"]), "|~|", "#")
    
    mss = json.loads(str(row["Related MSS JSON"]))
    related["mss"] = mss["mss"]
    return [related]


def create_bibs_from_row(row: pd.Series, ref_instances: pd.DataFrame):
    bibs = []
    ref_instance_ids = pd.read_csv(StringIO(str(row["Reference Instances"])), header=None).iloc[0]
    for id in ref_instance_ids:
        # ref_info = ref_instances.loc[ref_instances["ID"] == id]
        bib_data = {}
        bib_data["id"] = str(ref_instances.loc[int(id), "UUID"])
        bib_data["type"] = {
            "id": str(ref_instances.loc[int(id), "Type ID"]),
            "label": str(ref_instances.loc[int(id), "Type Label"])
        }
        if not(pd.isnull(ref_instances.loc[int(id), "Range"])):
            bib_data["range"] = str(ref_instances.loc[int(id), "Range"])
        
        if not(pd.isnull(ref_instances.loc[int(id), "Alt shelfmark"])):
            bib_data["alt_shelf"] = str(ref_instances.loc[int(id), "Alt shelfmark"])

        # url is required for otherdigversion, otherwise only use if not blank
        if str(ref_instances.loc[int(id), "Type ID"]) == "otherdigversion" or not(pd.isnull(ref_instances.loc[int(id), "URL"])):
            bib_data["url"] = str(ref_instances.loc[int(id), "URL"])
        
        if not(pd.isnull(ref_instances.loc[int(id), "Notes"])):
            bib_data["note"] = parse_rolled_up_field(str(ref_instances.loc[int(id), "Notes"]), "|~|", "#")

        bibs.append(bib_data)
    return bibs

def create_writing_from_row(row: pd.Series):
    writing = {}
    scripts = []
    script_ids = parse_rolled_up_field(str(row["Script ID"]), ',', "#")
    script_labels = parse_rolled_up_field(str(row["Script Label"]), ',', "#")
    writing_systems = parse_rolled_up_field(str(row["Writing System"]), ',', "#")
    for i in range(0, len(script_ids)):
        obj = {}
        obj["id"] = script_ids[i]
        obj["label"] = script_labels[i]
        obj["writing_system"] = writing_systems[i]
        scripts.append(obj)
    writing["script"] = scripts

    if not(pd.isnull(row["Writing Locus"])):
        writing["locus"] = str(row["Writing Locus"])
    if not(pd.isnull(row["Writing Note"])):
        writing["note"] = parse_rolled_up_field(str(row["Writing Note"]), '|~|', "#")
    return writing

def create_ink_from_row(row: pd.Series):
    ink = {}
    if not(pd.isnull(row["Ink Locus"])):
        ink["locus"] = str(row["Ink Locus"])
    if not(pd.isnull(row["Ink Color"])):
        ink["color"] = parse_rolled_up_field(str(row["Ink Color"]), "|~|", "#")
    if not(pd.isnull(row["Ink Note"])):
        ink["note"] = parse_rolled_up_field(str(row["Ink Note"]), "|~|", "#")
    return ink

def create_layout_from_row(row: pd.Series):
    layout = {}
    if not(pd.isnull(row["Layout Locus"])):
        layout["locus"] = str(row["Layout Locus"])
    if not(pd.isnull(row["Layout Columns"])):
        layout["columns"] = str(row["Layout Columns"])
    if not(pd.isnull(row["Layout Lines"])):
        layout["lines"] = str(row["Layout Lines"])
    if not(pd.isnull(row["Layout Dimensions"])):
        layout["dim"] = str(row["Layout Dimensions"])
    if not(pd.isnull(row["Layout Note"])):
        layout["note"] = parse_rolled_up_field(str(row["Layout Note"]), "|~|", "#")
    return layout
def create_associated_date(type: object, as_written: str, value: str, iso: str, note: list):
    date = {}
    date["type"] = type
    date["value"] = value
    
    if iso != "":
        not_before = iso.split("/")[0]
        if len(iso.split("/")) > 1:
            not_after = iso.split("/")[1]
        else:
            not_after = ""
        date["iso"] = {}
        date["iso"]["not_before"] = not_before.zfill(4)
        # only add not_after property if the ISO date is a range
        if not_after != "":
            date["iso"]["not_after"] = not_after.zfill(4)

    if as_written != "":
        date["as_written"] = as_written
    if len(note) > 0:
        date["note"] = note
    
    return date

def create_associated_name(id: str, value: str, as_written: str, role: object, note: list):
    name = {}
    if id != "":
        name["id"] = id
    if value != "":
        name["value"] = value
    if as_written != "":
        name["as_written"] = as_written
    name["role"] = role
    if len(note) > 0:
        name["note"] = note
    return name

def create_associated_place(id: str, value: str, as_written: str, event: object, note: list):
    place = {}
    if id != "":
        place["id"] = id
    if value != "":
        place["value"] = value
    if as_written != "":
        place["as_written"] = as_written
    place["event"] = event
    if len(note) > 0:
        place["note"] = note
    return place

# UTILITY FUNCTIONS

# Returns a list of values parsed out of a rolled-up field, such as the Features field
# Restriction: fails if a quoted field has the quotechar within it, but should not occur in SMDL data
# TBD: check that notes don't fail this restriction
def parse_rolled_up_field(data: str, delimiter: str, quotechar: str):
    vals = []
    # chunk data string first by the quote character
    temp = data.split(quotechar)
    # parse the chunks
    for i in range(0, len(temp)):
        # treat odd indices as 
        if i % 2 != 0:
            vals.append(temp[i])
        # treat even indices as needing additional splitting by the delimiter
        else:
            for x in temp[i].split(delimiter):
                # this allows skipping of the empty trailing whitespaces
                if(x.strip() == ""):
                    continue
                vals.append(x.strip())
    return vals

# CONSTANTS
RECORD_TYPES = ["ms_objs", "layers", "text_units"]

# Check to see if user entered path to csv file and valid command line argument
# Read in the input CSV file as a data frame
try:
    csv_file = pd.read_csv(sys.argv[1])
    record_type = sys.argv[2]
    if record_type not in RECORD_TYPES:
            raise ValueError
except OSError:
    print("ERROR: Incorrect path to csv, the file may not exist in the provided directory")
except IndexError:
     print("Please be sure to enter both command arguments the path to the CSV you would like to transform and the type (agents or works)")
except ValueError:
     print(f"'{record_type}' is not a valid type, must be one of {RECORD_TYPES}")

# Get the path to a CSV of reference instances for creating bibliography records; set the index of the DataFrame as the ID column, useful for accessing by ID
path_to_ref_instances_csv = input("Please input a path to the CSV containing the reference instances for creating the bibliography field (or leave blank if unused):")
# path_to_ref_instances_csv = "/Users/wpotter/Desktop/SMDP-Migration/csvs/reference_instances.csv" # testing remove this line
if path_to_ref_instances_csv:
    ref_instances = pd.read_csv(path_to_ref_instances_csv, index_col='ID')
else:
    ref_instances = None

path_to_paracontents_csv = input("Please input a path to the CSV containing the paracontents info for creating the paracontents field (or leave blank if unused):")
# path_to_paracontents_csv = "/Users/wpotter/Desktop/SMDP-Migration/csvs/colophons_TEST.csv" # testing remove this line
if path_to_paracontents_csv:
    paracontents_table = pd.read_csv(path_to_paracontents_csv, index_col='ID')
else:
    paracontents_table = None

# TBD: check that all of the columns are present, or added, for a given record type
# Report the mismatched fields and prompt user to continue
csv_columns = csv_file.columns

if record_type == "ms_objs":
    columns_list_doc = 'ms_obj_fields.txt'
elif record_type == "layers":
    columns_list_doc = 'layer_fields.txt'
elif record_type == "text_units":
    columns_list_doc = 'text_units_fields.txt'


with open(columns_list_doc) as f:
    expected_cols = f.read().splitlines()

missing_columns = []
extra_columns = []
for c in csv_columns:
    if c not in expected_cols:
        extra_columns.append(c)

for c in expected_cols:
    if c not in csv_columns:
        missing_columns.append(c)

print("The following CSV columns will be ignored:")
print(extra_columns)
print("\n")
print("The following expected columns are missing from the CSV and will be supplied as null values:")
print(missing_columns)
print("\n")
user_response = input("Continue with the migration script? (y/n)")
accept_input = user_response == "y"

# for each row, create a JSON file of the corresponding record type
out_dir = "/Users/wpotter/Desktop/SMDP-Migration/layers/migration_tests"
if not os.path.exists(out_dir):
    os.makedirs(out_dir)
if accept_input:
    for col in missing_columns:
        csv_file[col] = pd.Series(dtype='string')
    for i, row in csv_file.iterrows():
        record = transform_row_to_json(row, record_type)
        # print(type(row))
        ark = str(row["Item ARK"])
        filename = ark.split("/")[2]
        filepath = f'{out_dir}/{filename}.json'
        with open(filepath, 'w+') as f:
            json.dump(record, f, ensure_ascii=False, indent=4)
            print("File saved to " + filepath)
else:
    print("Transform cancelled")