import pandas as pd, json, sys, os

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
    # TBD: finalize csv headers
    if record_type == "ms_objs":
        data["type"] = {
            "id": str(row["Type"]),
            "label": str(row["Type label"])
        }
    
    # Supply the shelf mark for MS Objects
    if record_type == "ms_objs":
        data["shelfmark"] = str(row["Shelfmark"])
    # Otherwise, use the label property
    else:
        data["label"] = str(row["Label"])
    
    if not(pd.isnull(row["Summary"])):
        data["summary"] = str(row["Summary"])

    if not(pd.isnull(row["Summary"])) or record_type == "ms_objs":
        data["extent"] = str(row["Extent"])

    if record_type == "ms_objs" and not(pd.isnull(row["Weight"])):
        data["weight"] = str(row["Weight"])
    
    if record_type == "ms_objs" and not(pd.isnull(row["MS Dimensions"])):
        data["dim"] = str(row["MS Dimensions"])
    
    if record_type == "ms_objs":
        data["state"] = {
            "id": str(row["Form ID"]), 
            "label": str(row["Form Label"])
        }
    elif record_type == "layer":
        data["state"] = {} # TBD for layer states
    
    # TBD: check if this will be used
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
    if len(data["features"]) == 0:
        data.pop("features")

    if record_type == "ms_objs":
        data["part"] = [create_part_from_row(row)]

    # TBD: this may not be used for the ms_objs level
    if record_type == "ms_objs":
        data["layer"] = create_layer_reference_from_row(row, False) # note: this function is for creating the layer sub-object that references layer records
    
    # TBD: a lot more to think about with this one...
    # TBD: write the function...
    data["para"] = create_paracontent_from_row(row)

    # TBD: has_bind -- waiting to see how the data will look

    # add location if an ms_obj
    if record_type == "ms_objs":
        location = {}
        location["id"] = str(row["Location ID"])
        # add collection only if it is not empty
        if not(pd.isnull(row["Collection"])):
            location["collection"] = str(row["Collection"])
        location["repository"] = str(row["Repository"])

        data["location"] = [location]
    
    # TBD: assoc_* -- are these even necessary?

    # Add notes field
    data["note"] = create_notes_from_row(row, record_type, 0)
    # remove notes field if none were created
    if len(data["note"]) == 0:
        data.pop("note")

    # Add related_mss field
    # TBD: this should only be ms_obj and possibly layer
    data["related_mss"] = create_related_mss_from_row(row)
    # remove related_mss field if none were created
    if len(data["related_mss"]) == 0:
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

    data["bib"] = create_bibs_from_row(row, ref_instances)
    # remove bib field if none were created
    if len(data["bib"]) == 0:
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

    # TBD cataloguer field (set in a config for who runs the script?)
    # TBD: additional cataloguer info from Contributor field, esp. for texts

    # TBD: reconstructed_from -- needed for UTOs

    # Parent, for records that are not ms_objs
    if record_type != "ms_objs":
        # TBD: possibly multiple; for-each after split by delimiter
        data["parent"] = []
    """
     Sections needed for ms_obj:
     - [x] ARK (string) + layers, text
     - [/] reconstruction (bool) + layers, text
     - [/] type (id, label)
     - [x] shelfmark (string) + layers, text (as label)
     - [/] summary (string) + layers, text
     - [x] extent (string) + layers, text
     - [x] weight (string)
     - [x] dim (string)
     - [x] state (id, label) + layers
     - [/] fol (string)
     - [x] coll (string)
     - [x] features (array: id, label) + layers, text
     - [x] part (array: complex, sub-function)
     - [x] layer (array: complex, sub-function)
     - [ ] para (array: complex, sub-function) + layers, text
     - [ ] has_bind (bool)
     - [x] location (array: id, collection, repo)
     ? assoc_date (array, complex sub-function) + layers, text
     ? assoc_name (array, complex sub-function) + layers, text
     ? assoc_place (array, complex sub-function) + layers, text
     - [x] note (array, complex mappings) + layers, text
     - [x] related_mss (array, complex sub-function) + layers?
     - [ ] viscodex (array, sub-function)
     - [/] bib (array: complex sub-function) + layers, text
     - [/] iiif (array)
     - [ ] internal (array: string)
     - [ ] cataloguer (array?: config file?)
     - [ ] reconstructed_from (array: string)
     - [/] parent for ms_objs?
     """
    return data

def create_part_from_row(row: pd.Series):
    part_data = {}

    # TBD: check field names
    part_data["label"] = str(row["Part Label"])

    # TBD: need summary field?

    # TBD: column name; will we have this?
    if not(pd.isnull(row["Part Locus"])):
        part_data["locus"] = str(row["Part Locus"])

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

    # TBD: need extent field?

    if not(pd.isnull(row["Part Dimensions"])):
        part_data["dim"] = str(row["Part Dimensions"])

    part_data["layer"] = create_layer_reference_from_row(row, True)
    """
    - [/] label
    ?summary
    - [/] locus
    - [/] support
    ?extent
    - [/] dim
    - [/] layer
    ? para
    ? note (typed)
    ? related_mss
    """
    return part_data


# TBD: add locus?
# Takes a row from a CSV and a boolean indicating if is called by a part or not
# Creates the overtext, undertext, and guest content layers
def create_layer_reference_from_row(row: pd.Series, is_part: bool):
    layers = []
    column_prefix = "MS "
    # include overtexts and use part columns if called by a part
    if is_part:
       overtext_arks = parse_rolled_up_field(str(row["Overtext ARKs"]), ",", '"')
       overtext_labels = parse_rolled_up_field(str(row["Overtext Labels"]), ",", '"')
       overtext = create_layer_object(arks=overtext_arks,
                                        labels=overtext_labels,
                                        type={"id": "overtext", "label": "Overtext"})
       layers += overtext
       column_prefix = "Part " # prefix will be 'Part ' otherwise stays "MS "
    
    # UTOs
    undertext_arks = parse_rolled_up_field(str(row[column_prefix + "UTO ARKs"]), ",", '"')
    undertext_labels = parse_rolled_up_field(str(row[column_prefix + "UTO Labels"]), ",", '"')
    undertext = create_layer_object(arks=undertext_arks,
                                labels=undertext_labels,
                                type={"id": "undertext", "label": "Undertext"})
    layers += undertext

    # Guest Content
    guest_arks = parse_rolled_up_field(str(row[column_prefix + "Guest ARKs"]), ",", '"')
    guest_labels = parse_rolled_up_field(str(row[column_prefix + "Guest Labels"]), ",", '"')
    guest_content = create_layer_object(arks=guest_arks,
                                    labels=guest_labels,
                                    type={"id": "guest", "label": "Guest Content"})
    layers += guest_content

    return layers

# TBD: add locus?
# restriction: relies on exact match of arks and labels
# TBD: throw exception if lengths of ark and label arrays don't match?
# Given a list of arks, labels, and a type object return a list of layer objects
def create_layer_object(arks, labels, type):
    layers = []
    for i in range(0, len(arks)):
        if arks[i] == "" or arks[i] == "nan":
            continue
        layers.append({
            "id": arks[i],
            "label": labels[i],
            # TBD: add locus?
            "type": type
        })
    return layers

# TBD: actually write this function...
def create_paracontent_from_row(row):
    layer = []
    return layer

# takes a row (pandas Series); record_type string; and a boolean indicating whether the context is ms_obj.part or not
# uses the record type and is_part to determine which columns to pass to the function that creates the typed note fields
def create_notes_from_row(row: pd.Series, record_type: str, is_part: bool):
    cols = []
    # pass columns to note based on record type
    if record_type == "ms_objs":
        if not(is_part):
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
        # TBD: add column configurations for part notes
        else:
            cols += []
    # TBD: add cols configurations for layers and text_units

    return create_notes_from_specific_columns(cols)

# Take a list of dictionaries representing notes data organized by types, return a series of data portal note
def create_notes_from_specific_columns(notes_by_type: list):
    all_notes = []
    for note_type in notes_by_type:
        for note in parse_rolled_up_field(note_type["data"], "|~|", "#"):
            # skip empty, but create note objects for each delimited note field
            if note != "" and note != "nan":
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
        "label": str(row["Related MSS Type label"])
    }
    related["label"] = str(row["Related MSS Label"])

    if not(pd.isnull(str(row["Related MSS Note"]))):
        related["note"] = parse_rolled_up_field(str(row["Related MSS Note"]), "|~|", "#")
    
    mss = json.loads(str(row["Related MSS JSON"]))
    related["mss"] = mss["mss"]
    return [related]


def create_bibs_from_row(row: pd.Series, ref_instances: pd.DataFrame):
    bibs = []
    ref_instance_ids = parse_rolled_up_field(str(row["Reference instances"]), ",", '"')
    for id in ref_instance_ids:
        # ref_info = ref_instances.loc[ref_instances["ID"] == id]
        bib_data = {}
        bib_data["id"] = str(ref_instances.loc[int(id), "UUID"])
        bib_data["type"] = {
            "id": str(ref_instances.loc[int(id), "Type"]),
            "label": str(ref_instances.loc[int(id), "Type label"])
        }
        if not(pd.isnull(ref_instances.loc[int(id), "Range"])):
            bib_data["range"] = str(ref_instances.loc[int(id), "Range"])
        
        if not(pd.isnull(ref_instances.loc[int(id), "Alt shelfmark"])):
            bib_data["alt_shelf"] = str(ref_instances.loc[int(id), "Alt shelfmark"])

        # url is required for otherdigversion, otherwise only use if not blank
        if str(ref_instances.loc[int(id), "Type"]) == "otherdigversion" or not(pd.isnull(ref_instances.loc[int(id), "URL"])):
            bib_data["url"] = str(ref_instances.loc[int(id), "URL"])
        
        # notes on bibs?

        bibs.append(bib_data)
    return bibs


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

#TBD: could check for each record type that the CSV at least as all required fields using the x in df.columns check

# Get the path to a CSV of reference instances for creating bibliography records; set the index of the DataFrame as the ID column, useful for accessing by ID
path_to_ref_instances_csv = input("Please input a path to the CSV containing the reference instances for creating the bibliography field:")
ref_instances = pd.read_csv(path_to_ref_instances_csv, index_col='ID')

# for each row, create a JSON file of the corresponding record type
for i, row in csv_file.iterrows():
     record = transform_row_to_json(row, record_type)
     # print(type(row))
     print(json.dumps(record, ensure_ascii=False, indent=4))