'''
This module contains the main functions used for transforming the CSV data to JSON
'''
import pandas as pd
import json, datetime
import transform.config as config
import transform.helpers as helpers
from io import StringIO


"""
Takes a Pandas Data Frame representing a CSV row; and a string representing a data portal record type
Transforms the CSV data into a Python dictionary to be serialized as a JSON record following the Data Portal data model
"""
def transform_row_to_json(row: pd.DataFrame, record_type: str):
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

    # add language for text_units
    if record_type == "text_units":
        lang_ids = helpers.parse_rolled_up_field(str(row["Language ID"]), ",", '"')
        lang_labels = helpers.parse_rolled_up_field(str(row["Language Label"]), ",", '"')
        data["lang"] = []
        for i in range(0, len(lang_ids)):
            data["lang"].append(
                {
                    "id": lang_ids[i],
                    "label": lang_labels[i]
                }
            )

    # add work_wits for text_units
    if record_type == "text_units":
        work_wit_ids = helpers.parse_rolled_up_field(str(row["Work Witnesses"]), ",", '"')
        work_wit_data = helpers.get_side_csv_data(ids=work_wit_ids, csv=config.other_csvs["work_wits"]["data"], sort_by_sequence=True)
        data["work_wit"] = create_work_witnesses_from_row(work_wit_data)

    # add extent
    if record_type != "text_units" and not(pd.isnull(row["Extent"])):
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
        feature_labels = helpers.parse_rolled_up_field(str(row["Feature Labels"]), ",", '"')
        feature_ids = helpers.parse_rolled_up_field(str(row["Feature ID"]), ",", '"')
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
        # if part data referenced in separate parts csv, and that csv exists, use data there
        if (not(pd.isnull(row["Part IDs"]))) and (config.other_csvs["parts"]["data"] is not None):
            data["part"] = []
            part_refs = pd.read_csv(StringIO(str(row["Part IDs"])), header=None).iloc[0]
            part_data = helpers.get_side_csv_data(ids=part_refs, csv=config.other_csvs["parts"]["data"], sort_by_sequence=True)
            for i, part in part_data.iterrows():
                data["part"].append(create_part_from_row(part))
        # otherwise use the data for parts encoded in the ms objs csv
        else:     
            data["part"] = [create_part_from_row(row)]

    # TBD: this may not be used for the ms_objs level
    if record_type == "ms_objs":
        data["layer"] = create_layer_reference_from_row(row, False) # note: this function is for creating the layer sub-object that references layer records
    # remove ms layers if none created
    if "layer" in data and len(data["layer"]) == 0:
        data.pop("layer")
    
    # add paracontent stub, which may be removed later if none are created
    data["para"] = []

    # TBD: paracontent for ms objs and text units, and for layers that aren't colophons

    # add colophons as paracontent objects for layers
    if record_type == "layers" and not(pd.isnull(row["Colophon"])):
        data["para"] += create_paracontent_from_row(row, "Colophon", config.other_csvs["paracontents"]["data"])


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
        notes = helpers.parse_rolled_up_field(str(row["Origin Date Note"]), "|~|", "#")
        if len(notes) <= 1 and (notes[0] == "nan" or notes[0] == "<NA>"):
            notes = []
        data["assoc_date"].append(create_associated_date(
            type= {"id": "origin", "label": "Date of Origin"},
            as_written="",
            value=str(row["Origin Date"]),
            iso=str(row["Origin Date ISO"]),
            note=notes
        ))
    # add assoc_name for scribes
    if record_type == "layers":
        if not(pd.isnull(row["Scribe ID"])):
            scribe_arks = helpers.parse_rolled_up_field(str(row["Scribe ID"]), ",", "#")
            values = helpers.parse_rolled_up_field(str(row["Scribe Value"]), "|~|", "#")
            if len(values) <= 1 and values[0] == "nan":
                values = []
                for i in range(0, len(scribe_arks)):
                    values.append('')
            notes = helpers.parse_rolled_up_field(str(row["Scribe Note"]), "|~|", "#")
            if len(notes) <= 1 and notes[0] == "nan":
                notes = []
                for i in range(0, len(scribe_arks)):
                    notes.append('')
            for i in range(0, len(scribe_arks)):
                n = []
                if notes[i] != "":
                    n.append(notes[i])
                data["assoc_name"].append(create_associated_name(
                    id=scribe_arks[i],
                    value=values[i],
                    as_written="",
                    role={"id": "scribe", "label": "Scribe"},
                    note=n
                ))
        elif not(pd.isnull(row["Scribe Value"])):
            notes = helpers.parse_rolled_up_field(str(row["Scribe Note"]), "|~|", "#")
            if len(notes) <= 1 and (notes[0] == "nan" or notes[0] == "<NA>"):
                notes = []
            data["assoc_name"].append(create_associated_name(
                    id="",
                    value=str(row["Scribe Value"]),
                    as_written="",
                    role={"id": "scribe", "label": "Scribe"},
                    note=notes
                ))
                
    # add assoc_place for origin place
    # TBD: if we have ARKs ever, rewrite this; currently only have a value field
    if record_type == "layers" and not(pd.isnull(row["Origin Place Value"])):
        notes = helpers.parse_rolled_up_field(str(row["Origin Place Note"]), "|~|", "#")
        if len(notes) <= 1 and (notes[0] == "nan" or notes[0] == "<NA>"):
            notes = []
        data["assoc_place"].append(create_associated_place(
            id="",
            value=str(row["Origin Place Value"]),
            as_written="",
            event={"id": "origin", "label": "Place of Origin"},
            note=notes
        ))

    # Add notes field
    data["note"] = create_notes_from_row(row, record_type, 0)
    # remove notes field if none were created
    if len(data["note"]) == 0:
        data.pop("note")

    # Add related_mss field if it is not flagged as being at the part level
    if record_type in ["ms_objs", "layers"] and not(pd.isnull(row["Related MSS"])):
            data["related_mss"] = []
            rel_mss_refs = pd.read_csv(StringIO(str(row["Related MSS"])), header=None).iloc[0]
            rel_mss_data = helpers.get_side_csv_data(ids=rel_mss_refs, csv=config.other_csvs["related_mss"]["data"], sort_by_sequence=False)
            for i, rel_mss in rel_mss_data.iterrows():
                # filter for only the ms obj level related mss
                if str(rel_mss["Related MSS Level"]) == "ms":
                    data["related_mss"].append(create_related_mss_from_row(rel_mss))
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
        data["bib"] = create_bibs_from_row(row, config.other_csvs["bibs"]["data"])
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
        contributors = helpers.parse_rolled_up_field(str(row["Contributor Name"]), ",", "#")
        messages = helpers.parse_rolled_up_field(str(row["Change Log Message"]), "|~|", "#")
        orcids = helpers.parse_rolled_up_field(str(row["Contributor ORCiD"]), ",", "#")

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
        data["reconstructed_from"] = helpers.parse_rolled_up_field(str(row["Reconstructed From"]), ",", "#")


    # Parent, for records that are not ms_objs
    if record_type != "ms_objs":
        data["parent"] = helpers.parse_rolled_up_field(str(row["Parent ARKs"]), ",", "#")
    
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
   
    return data

def create_work_witnesses_from_row(work_wits_data: pd.DataFrame):
    work_wits = []
    for work_wit_row in work_wits_data:
        # paracontent_table.loc[int(id), "Type ID"]
        wit = {}
        wit["work"] = {}
        # work field should just have the work's ARK if available, otherwise it needs a desc_title and optional creators and genre array
        if not(pd.isnull(work_wit_row["Work ID"])):
            wit["work"]["id"] = str(work_wit_row["Work ID"])
        else:
            wit["work"]["desc_title"] = str(work_wit_row["Work Descriptive Title"])
            if not(pd.isnull(work_wit_row["Work Creator"])):
                wit["work"]["creator"] = helpers.parse_rolled_up_field(str(work_wit_row["Work Creator"]), ",", '"')
            if not(pd.isnull(work_wit_row["Work Genre ID"])):
                genre_ids = helpers.parse_rolled_up_field(str(work_wit_row["Work Genre ID"]), ",", '"')
                genre_labels = helpers.parse_rolled_up_field(str(work_wit_row["Work Genre Label"]), ",", '"')
                wit["work"]["genre"] = []
                for i in range(0, len(genre_ids)):
                    wit["work"]["genre"].append(
                        {
                            "id": genre_ids[i],
                            "label": genre_labels[i]
                        }
                    )
            
        if not(pd.isnull(work_wit_row["Alternative Title"])):
            wit["alt_title"] = str(work_wit_row["Alternative Title"])
        if not(pd.isnull(work_wit_row["As Written"])):
            wit["as_written"] = str(work_wit_row["As Written"])
        if not(pd.isnull(work_wit_row["Locus"])):
            wit["locus"] = str(work_wit_row["Locus"])

        # Create excerpts for incipit and explicit
        wit["excerpt"] = []
        if not(pd.isnull(work_wit_row["Incipit As Written"])):
            inc_type = {"id": "incipit", "label": "Incipit"}
            wit["excerpt"].append(create_excerpt(work_wit_row, inc_type, "Incipit "))
        if not(pd.isnull(work_wit_row["Explicit As Written"])):
            expl_type = {"id": "explicit", "label": "Explicit"}
            wit["excerpt"].append(create_excerpt(work_wit_row, expl_type, "Explicit "))

        # If no excerpts created, remove the field
        if "excerpt" in wit and len(wit["excerpt"]) == 0:
            wit.pop("excerpt")

        
        # TBD: contents, partially implemented, sufficient for first migration pass
        # hacked together to create the contents label, but should also support other fields in contents...
        if not(pd.isnull(work_wit_row["Contents Label"])):
            contents = []
            labels = helpers.parse_rolled_up_field(str(work_wit_row["Contents Label"]), "|~|", "#")
            for i in range(0, len(labels)):
                contents.append(
                    {
                        "label": labels[i]
                    }
                )
            wit["contents"] = contents
        
        # Add notes, if any
        if not(pd.isnull(work_wit_row["Note"])):
            wit["note"] = helpers.parse_rolled_up_field(str(work_wit_row["Note"]), "|~|", "#")

        # Add bib, if any, using reference instances table
        if not(pd.isnull(work_wit_row["Reference Instances"])):
            wit["bib"] = create_bibs_from_row(work_wit_row, config.other_csvs["bibs"]["data"])
        # remove bib field if none were created
        if "bib" in wit and len(wit["bib"]) == 0:
            wit.pop("bib")

        work_wits.append(wit)

    return work_wits

def create_excerpt(data_row: pd.Series, type: object, column_prefix: str):
    excerpt = {}
    excerpt["type"] = type # TBD: make generic, so can supply type or look for it from the row columns

    if not(pd.isnull(data_row[column_prefix + "Locus"])):
            excerpt["locus"] = str(data_row[column_prefix + "Locus"])
    if not(pd.isnull(data_row[column_prefix + "As Written"])):
            excerpt["as_written"] = str(data_row[column_prefix + "As Written"])
    if not(pd.isnull(data_row[column_prefix + "Translation"])):
            excerpt["translation"] = helpers.parse_rolled_up_field(str(data_row[column_prefix + "Translation"]), "|~|", "#")
    if not(pd.isnull(data_row[column_prefix + "Note"])):
            excerpt["note"] = helpers.parse_rolled_up_field(str(data_row[column_prefix + "Note"]), "|~|", "#")
    
    return excerpt

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
            bib_data["note"] = helpers.parse_rolled_up_field(str(ref_instances.loc[int(id), "Notes"]), "|~|", "#")

        bibs.append(bib_data)
    return bibs

def create_writing_from_row(row: pd.Series):
    writing = {}
    scripts = []
    script_ids = helpers.parse_rolled_up_field(str(row["Script ID"]), ',', "#")
    script_labels = helpers.parse_rolled_up_field(str(row["Script Label"]), ',', "#")
    writing_systems = helpers.parse_rolled_up_field(str(row["Writing System"]), ',', "#")
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
        writing["note"] = helpers.parse_rolled_up_field(str(row["Writing Note"]), '|~|', "#")
    return writing

def create_ink_from_row(row: pd.Series):
    ink = {}
    if not(pd.isnull(row["Ink Locus"])):
        ink["locus"] = str(row["Ink Locus"])
    if not(pd.isnull(row["Ink Color"])):
        ink["color"] = helpers.parse_rolled_up_field(str(row["Ink Color"]), "|~|", "#")
    if not(pd.isnull(row["Ink Note"])):
        ink["note"] = helpers.parse_rolled_up_field(str(row["Ink Note"]), "|~|", "#")
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
        layout["note"] = helpers.parse_rolled_up_field(str(row["Layout Note"]), "|~|", "#")
    return layout

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

def create_part_from_row(row: pd.Series):
    part_data = {}

    if not(pd.isnull(row["Part Label"])):
        part_data["label"] = str(row["Part Label"])

    if not(pd.isnull(row["Part Summary"])):
        part_data["summary"] = str(row["Part Summary"])

    if not(pd.isnull(row["Part Locus"])):
        part_data["locus"] = str(row["Part Locus"])

    # Collate and add support data
    support_labels = helpers.parse_rolled_up_field(str(row["Support Label"]), ",", '"')
    support_ids = helpers.parse_rolled_up_field(str(row["Support ID"]), ",", '"')
    supports = []
    for i in range(0, len(support_ids)):
        sup = {
            "id": support_ids[i],
            "label": support_labels[i]
        }
        supports.append(sup)
    part_data["support"] = supports

    if not(pd.isnull(row["Part Extent"])):
        part_data["extent"] = str(row["Part Extent"])
    
    if not(pd.isnull(row["Part Dimensions"])):
        part_data["dim"] = str(row["Part Dimensions"])

    if not(pd.isnull(row["Part Paracontents"])):
        part_data["para"] = create_paracontent_from_row(row, "Part Paracontents", config.other_csvs["paracontents"]["data"])

    part_data["layer"] = create_layer_reference_from_row(row, True)
    
    part_data["note"] = create_notes_from_row(row, "ms_objs", 1)
    # remove notes field if none were created
    if len(part_data["note"]) == 0:
        part_data.pop("note")
    
    # Add related_mss data if non-empty and flagged as being at the part level
    if not(pd.isnull(row["Related MSS"])):
        part_data["related_mss"] = []
        rel_mss_refs = pd.read_csv(StringIO(str(row["Related MSS"])), header=None).iloc[0]
        rel_mss_data = helpers.get_side_csv_data(ids=rel_mss_refs, csv=config.other_csvs["related_mss"]["data"], sort_by_sequence=False)
        for i, rel_mss in rel_mss_data.iterrows():
            # filter for only the ms obj level related mss
            if str(rel_mss["Related MSS Level"]) == "part":
                part_data["related_mss"].append(create_related_mss_from_row(rel_mss))

    return part_data


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
        
        lang_ids = helpers.parse_rolled_up_field(str(paracontent_table.loc[int(id), "Language ID"]), ",", '#')
        lang_labels = helpers.parse_rolled_up_field(str(paracontent_table.loc[int(id), "Language Label"]), ",", '#')
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
            script_ids = helpers.parse_rolled_up_field(str(paracontent_table.loc[int(id), "Script ID"]), ",", '#')
            script_labels = helpers.parse_rolled_up_field(str(paracontent_table.loc[int(id), "Script Label"]), ",", '#')
            writing_systems = helpers.parse_rolled_up_field(str(paracontent_table.loc[int(id), "Writing System"]), ",", '#')
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
            para_data["translation"] = helpers.parse_rolled_up_field(paracontent_table.loc[int(id), "Translation"], "|~|", "#")
        
        # assoc_*: optional, array of objects, need to be created via other function
        if not(pd.isnull(paracontent_table.loc[int(id), "Associated Name Role ID"])):
            para_data["assoc_name"] = create_list_of_para_associated(paracontent_table.loc[int(id)], "assoc_name")
        
        if not(pd.isnull(paracontent_table.loc[int(id), "Associated Place Event ID"])):
            para_data["assoc_place"] = create_list_of_para_associated(paracontent_table.loc[int(id)], "assoc_place")

        if not(pd.isnull(paracontent_table.loc[int(id), "Associated Date Type ID"])):
            para_data["assoc_date"] = create_list_of_para_associated(paracontent_table.loc[int(id)], "assoc_date")


        # note: optional, array of strings
        if not(pd.isnull(paracontent_table.loc[int(id), "Notes"])):
            para_data["note"] = helpers.parse_rolled_up_field(paracontent_table.loc[int(id), "Notes"], "|~|", "#")
        
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


# take a row and parse the fields to create a related_mss object
def create_related_mss_from_row(related_data: pd.Series):
    related_mss = {}
    related_mss["type"] = {
        "id": str(related_data["Related MSS Type"]),
        "label": str(related_data["Related MSS Type Label"])
    }
    related_mss["label"] = str(related_data["Related MSS Label"])

    if not(pd.isnull(related_data["Related MSS Note"])):
        related_mss["note"] = helpers.parse_rolled_up_field(str(related_data["Related MSS Note"]), "|~|", "#")
    if not(pd.isnull(related_data["Related MSS JSON"])):
        mss = json.loads(str(related_data["Related MSS JSON"]))
        related_mss["mss"] = mss["mss"]
    return related_mss


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

    if record_type == "text_units":
        cols += [
                {
                    "data": str(row["Contents note"]),
                    "type": {
                        "id": "contents",
                        "label": "Contents Note"
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
        for note in helpers.parse_rolled_up_field(note_type["data"], "|~|", "#"):
            # skip empty, but create note objects for each delimited note field
            if note != "<NA>" and note != "" and note != "nan":
                all_notes.append(
                    {
                        "type": note_type["type"],
                        "value": note
                    }
                )
    return all_notes
