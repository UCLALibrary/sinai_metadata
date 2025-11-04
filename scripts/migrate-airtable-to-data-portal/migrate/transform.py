"""
This module holds the main logic for converting records into Portal JSON files
"""
import migrate.config as config
import migrate.parse as parse
import json

# the main transformation function
def transform_records(table_name: str):
    main_table = config.TABLES[table_name] # TODO: raise exception if not in main table types?
    for record in main_table["data"]:
        transformed_record = transform_single_record(record=main_table["data"].get(record), 
                                                     record_type=table_name,
                                                     fields=config.TABLES[table_name]["fields"])
        file_path = "/Users/wpotter/Desktop/SMDP-Script-Tests/ms_objs/" + transformed_record["ark"][10:]+".json" 
        with open(file_path, mode="w") as fh:
            json.dump(transformed_record, fh, indent=2, ensure_ascii=False)
        # print(json.dumps(transformed_record, indent=2))

def transform_single_record(record, record_type, fields):

    # TODO: raise exception if not in main table types?
    result = {}

    # Add the ARK
    result['ark'] = parse.get_data_from_field(source=record, field_config=fields['ark'])

    # Add the reconstruction bool
    reconstruction = parse.get_data_from_field(source=record, field_config=fields['reconstruction'])
    result['reconstruction'] = reconstruction == 'true'

    # TODO: ms obj and layer only? or maybe just ms obj?
    result['type'] = {
        "id": parse.get_data_from_field(source=record, field_config=fields['type_id']),
        "label": parse.get_data_from_field(source=record, field_config=fields['type_label'])
    }

    # TODO: ms obj specific
    result["shelfmark"] = parse.get_data_from_field(source=record, field_config=fields['shelfmark'])

    result["summary"] = parse.get_data_from_field(source=record, field_config=fields['summary'])

    result["extent"] = parse.get_data_from_field(source=record, field_config=fields['extent'])

    result["weight"] = parse.get_data_from_field(source=record, field_config=fields['weight'])

    result["dim"] = parse.get_data_from_field(source=record, field_config=fields['ms_dim'])

    state = {}
    state["id"] = parse.get_data_from_field(source=record, field_config=fields['state_id'])
    state["label"] = parse.get_data_from_field(source=record,field_config=fields['state_label'])
    result["state"] = state

    result["fol"] = parse.get_data_from_field(source=record, field_config=fields['fol'])

    result["coll"] = parse.get_data_from_field(source=record, field_config=fields['coll'])
    
    # TODO: notes
    """
    - fol_note
    - coll_note
    - para_note
    - binding_note
    - provenance_note
    - condition_note
    - contents_note
    - general_note
    - ornamentation_note
    """

    # Add features; will throw an error if for some reason the id/label lengths are mismatched
    features = []
    feature_ids = parse.get_data_from_field(source=record, field_config=fields['feature_id'])
    feature_labels = parse.get_data_from_field(source=record,field_config=fields['feature_label'])
    if feature_ids and len(feature_ids) > 0:
        for i in range(0, len(feature_ids)):
            features.append(
                {
                    "id": feature_ids[i],
                    "label": feature_labels[i]
                }
            )
    result["feature"] = features

    other_layers = parse.get_data_from_multiple_fields(source=record, fields=fields, field_list=["other_layer_ark", "other_layer_label", "other_layer_type_id", "other_layer_type_label", "other_layer_locus", "other_layer_level"])
    
    # add ms-obj level layer info
    other_layer_field_map = {
        "id": "other_layer_ark",
        "label": "other_layer_label",
        "type_id": "other_layer_type_id",
        "type_label": "other_layer_type_label",
        "locus": "other_layer_locus",
        "level": "other_layer_level"
    }
    result["layer"] = transform_layer_reference_data(record=other_layers, field_map=other_layer_field_map, has_multiple_layers=isinstance(other_layers["other_layer_ark"], list), level_filter="ms")
    

    related_mss = parse.get_data_from_field(source=record, field_config=fields['related_mss'])

    result["related_mss"] = transform_related_mss_data(related_mss_data=related_mss, level_filter="ms")
    # Process part data
    # TODO: ms obj only
    # If there are any referenced parts, use that data table; otherwise use the part fields in the ms obj record
    parts = parse.get_data_from_field(source=record,field_config=fields['part_id'])
    if parts and len(parts) > 0:
        result["part"] = []
        for part in parts:
            result["part"].append(transform_part_data(part_data=part))
    else:
        result["part"] = get_part_data_from_ms_table(record=record, fields=fields, other_layer_data=other_layers, related_mss_data=related_mss)

    # add location info
    # TODO: MS obj only
    location_ids =  parse.get_data_from_field(source=record,field_config=fields['location_id'])
    repositories =  parse.get_data_from_field(source=record,field_config=fields['repository'])
    collections =  parse.get_data_from_field(source=record,field_config=fields['collection'])
    result["location"] = []
    for i in range(0, len(location_ids)):
        result["location"].append(
            {
                "id": location_ids[i],
                "repository": repositories[i],
                "collection": collections[i]
            }
        )

    # TODO: assoc_* (needs a sub-function)
    

    # Add viscodex
    # TODO: ms obj only
    # TODO: move to its own function
    # TODO: type is hard-coded
    viscodex_label = parse.get_data_from_field(source=record, field_config=fields['viscodex_label'])
    viscodex_url = parse.get_data_from_field(source=record, field_config=fields['viscodex_url'])
    result["viscodex"] = []
    if viscodex_url and len(viscodex_url) > 0:
        for i in range(0, len(viscodex_label)):
            result["viscodex"].append(
                {
                    "type": {
                        "id": "manuscript",
                        "label": "Manuscript"
                    },
                    "label": viscodex_label[i],
                    "url": viscodex_url[i]
                }
            )

    bibs = parse.get_data_from_field(source=record, field_config=fields['bibs'])
    
    if bibs and len(bibs) > 0:
        result["bib"] = [transform_bib_data(bibs)]

    # TODO: ms obj
    # TODO: hard-code type or get from data?
    iiif = {
        "type": {
            "id": "main",
            "label": "Main"
        }
    }
    iiif["manifest"] = parse.get_data_from_field(source=record, field_config=fields['iiif_manifest_url'])
    iiif["text_direction"] = parse.get_data_from_field(source=record, field_config=fields['iiif_text_direction'])
    iiif["behavior"] = parse.get_data_from_field(source=record, field_config=fields['iiif_behavior'])
    iiif["thumbnail"] = parse.get_data_from_field(source=record, field_config=fields['iiif_thumbnail_url'])

    result["iiif"] = iiif

    # TODO: description and image program (waiting on config)

    # TODO: reconstructed from (waiting on config)

    return del_none(result) # TODO: reorder based on an established order?

def get_part_data_from_ms_table(record, fields, other_layer_data=None, related_mss_data=None):
    # TODO: should this be in a config somewhere???
    part_fields = ["part_label", "part_summary", "part_locus", "part_extent", "support_id", "support_label", "support_note", "part_dim", "overtext_ark", "overtext_label", "overtext_locus"]
    # TODO: figure out how best to include other layers, related mss, paracontent if at the part level

    part_data = parse.get_data_from_multiple_fields(source=record, fields=fields, field_list=part_fields)
    return transform_part_data(part_data, other_layer_data=other_layer_data, related_mss_data=related_mss_data)

"""
Transform part data into the part object needed for output
"""
# TODO: refactor to split out some of the mess, e.g. for layers and such
def transform_part_data(part_data, other_layer_data=None, related_mss_data=None):
    part = {}
    part["label"] = part_data["part_label"]
    part["summary"] = part_data["part_summary"]
    part["locus"] = part_data["part_locus"]
    part["extent"] = part_data["part_extent"]

    part["support"] = []
    for i in range(0, len(part_data["support_id"])):
        part["support"].append(
            {
                "id": part_data["support_id"][i],
                "label": part_data["support_label"][i]
            }
        )

    part["dim"] = part_data["part_dim"]

    # TODO: refactor to make this a reusable pattern, esp. the None filling
    # TODO: also need to have a helper function for dealing with when a string should be treated as an array of 1 item but also a string sometimes...or some other way of doing this...jesus christ.
    overtext_layer_field_map = {
        "id": "overtext_ark",
        "label": "overtext_label",
        "type_id": None,
        "type_label": None,
        "locus": "overtext_locus"
    }
    part["layer"] = transform_layer_reference_data(record=part_data,
                                                   field_map=overtext_layer_field_map,
                                                   has_multiple_layers=isinstance(part_data["overtext_ark"], list),
                                                   type_override={"id": "overtext", "label": "Overtext"})

    other_layer_field_map = {
        "id": "other_layer_ark",
        "label": "other_layer_label",
        "type_id": "other_layer_type_id",
        "type_label": "other_layer_type_label",
        "locus": "other_layer_locus",
        "level": "other_layer_level"
    }
    # Add other layer info if it exists
    if(other_layer_data):
        part["layer"] += transform_layer_reference_data(record=other_layer_data,
                                                    field_map=other_layer_field_map,
                                                    has_multiple_layers=isinstance(other_layer_data["other_layer_ark"], list),
                                                    level_filter="part")
    # If there is no other layer data, then see if it's in the part info already
    else:
        part["layer"] += transform_layer_reference_data(record=part_data,
                                                    field_map=other_layer_field_map,
                                                    has_multiple_layers=isinstance(part_data["other_layer_ark"], list))

    # para??
    # note = support note; part collation note?

    if related_mss_data:
        part["related_mss"] = transform_related_mss_data(related_mss_data=related_mss_data, level_filter="part")
    else:
        part["related_mss"] = transform_related_mss_data(related_mss_data=part_data["related_mss"], level_filter=None)

    return part

"""
Takes a record and a mapping of fields, along with an optional type override, to create an array of layer reference object
"""
def transform_layer_reference_data(record, field_map: dict, has_multiple_layers: bool, level_filter=None, type_override=None):   
    layers = []
    # return if empty of layer data
    if(not(record[field_map["id"]]) or len(record[field_map["id"]]) == 0 ):
        return layers
    if has_multiple_layers:
        number_of_layers = len(record[field_map["id"]])
        # None-fill the optional fields if length is 0
        if(len(record[field_map["locus"]]) == 0):
            record[field_map["locus"]] = [None] * len(number_of_layers)

        for i in range(0, number_of_layers):
            # if filtering by level, skip any that are not for part of that level
            if level_filter and record[field_map["level"]][i] != level_filter:
                continue
            else:
                if type_override:
                    layer_type = type_override
                else:
                    layer_type = {
                        "id": record[field_map["type_id"]][i],
                        "label": record[field_map["type_label"]][i]
                    }
                layers.append(
                    {
                        "id": record[field_map["id"]][i],
                        "label": record[field_map["label"]][i],
                        "type": layer_type,
                        "locus": record[field_map["locus"]][i],
                    }
                )
    else:
        if level_filter and record[field_map["level"]] != level_filter:
            return layers
        else:
            if type_override:
                layer_type = type_override
            else:
                layer_type = {
                    "id": record[field_map["type_id"]],
                    "label": record[field_map["type_label"]]
                }
            layers.append(
                    {
                        "id": record[field_map["id"]],
                        "label": record[field_map["label"]],
                        "type": {
                            "id": "overtext",
                            "label": "Overtext"
                        },
                        "locus": record[field_map["locus"]],
                    }
                )
    return layers

def transform_related_mss_data(related_mss_data, level_filter: None):

    if related_mss_data:
        related_mss = []
        for related in related_mss_data:
            # If filtering by level, filter out the ones not at that level
            if level_filter and related["level"] != level_filter:
                continue
            else:
                mss = {}
                if related["mss"]:
                    mss = json.loads(related["mss"])
                related_mss.append(
                    {
                        "type": {
                            "id": related["type_id"],
                            "label": related["type_label"]
                        },
                        "label": related["label"],
                        "note": related["note"],
                        **mss
                    }
                )
        return related_mss

"""
Takes the returned bib data from the parser and reorganizes it into the correct output fields
"""
def transform_bib_data(bibs):
    for bib in bibs:
        return {
            "id": bib["uuid"],
            "shortcode": bib["shortcode"],
            "citation": bib["citation"],
            "type": {
                "id": bib["type_id"],
                "label": bib["type_label"]
            },
            "range": bib["range"],
            "alt_shelf": bib["alt_shelf"],
            "note": bib["note"]
        }

def del_none(d):
    """
    Delete keys with the value ``None`` in a mixed list and/or dictionary, recursively.
    """
    if(isinstance(d, list)):
        for item in d:
            item = del_none(item)
            if item is None or len(item) == 0:
                d.remove(item)
    elif(isinstance(d, dict)):
        for key, value in list(d.items()):
            if value is None:
                del d[key]
            elif isinstance(value, dict) or isinstance(value, list):
                del_none(value)
                if len(d[key]) == 0:
                    del d[key]
    return d
