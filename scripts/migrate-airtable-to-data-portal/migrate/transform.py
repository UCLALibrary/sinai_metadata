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
        file_path = f"/Users/wpotter/Desktop/SMDP-Script-Tests/{table_name}/" + transformed_record["ark"][10:]+".json" 
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

    result["summary"] = parse.get_data_from_field(source=record, field_config=fields['summary'])
    
    notes_data = parse.get_typed_notes_data(source=record, note_fields=fields['typed_notes'])
    result["notes"] = transform_notes_data(notes_data)

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

    # Paracontents
    paracontents_data = parse.get_data_from_field(source=record, field_config=fields["paracontent"])
    result["para"] = transform_paracontents_data(paracontents_data)

    bibs = parse.get_data_from_field(source=record, field_config=fields['bibs'])
    
    if bibs and len(bibs) > 0:
        result["bib"] = [transform_bib_data(bibs)]

    # Add description program and provenance
    metadata_rights = parse.get_data_from_field(source=record, field_config=fields['metadata_rights'])
    metadata_rights = metadata_rights if metadata_rights else config.METADATA_RIGHTS
    desc_programs =  parse.get_data_from_multiple_fields(source=record,fields=fields, field_list=["desc_program_labels", "desc_program_descs"])
    result["desc_provenance"] = {
        "program": transform_program_data(desc_programs, "desc") if desc_programs["desc_program_labels"] else None, # process program info only if there is at least one label | TODO: technically not a schema requirement, so other way around?
        "rights": metadata_rights
    } # TODO: hard-code or add a config variable for the image rights statement? Or should it be a part of the spreadsheets?

    # Add reconstructed_from
    result["reconstructed_from"] = parse.get_data_from_field(source=record, field_config=fields['reconstructed_from'])

    # change log
    change_log = parse.get_data_from_multiple_fields(source=record,fields=fields, field_list=["change_log_message", "change_log_contributor", "change_log_added_by", "change_log_timestamp"])
    result["cataloguer"] = transform_change_log_data(change_log)

    if(record_type == "manuscript_objects"):
        transform_manuscript_object_fields(record, result, fields)
        # TODO: reorder keys based on ms obj preferred order (a config?)
    if(record_type == "layers"):
        transform_layer_fields(record, result, fields)
        # TODO: reorder keys based on layer preferred order (a config?)
    if(record_type == "text_units"):
        transform_text_unit_fields(record, result, fields)
        # TODO: reorder keys based on layer preferred order (a config?)

    return del_none(result) # TODO: reorder based on an established order?

# This function handles the ms-obj-specific transforms
# A result object should be passed in, which is the current record being transformed
def transform_manuscript_object_fields(record, result, fields):

    result['type'] = {
        "id": parse.get_data_from_field(source=record, field_config=fields['type_id']),
        "label": parse.get_data_from_field(source=record, field_config=fields['type_label'])
    }

    result["shelfmark"] = parse.get_data_from_field(source=record, field_config=fields['shelfmark'])

    result["extent"] = parse.get_data_from_field(source=record, field_config=fields['extent'])
    
    result["weight"] = parse.get_data_from_field(source=record, field_config=fields['weight'])

    result["dim"] = parse.get_data_from_field(source=record, field_config=fields['ms_dim'])

    state = {}
    state["id"] = parse.get_data_from_field(source=record, field_config=fields['state_id'])
    state["label"] = parse.get_data_from_field(source=record,field_config=fields['state_label'])
    result["state"] = state

    result["fol"] = parse.get_data_from_field(source=record, field_config=fields['fol'])

    result["coll"] = parse.get_data_from_field(source=record, field_config=fields['coll'])


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
    # If there are any referenced parts, use that data table; otherwise use the part fields in the ms obj record
    parts = parse.get_data_from_field(source=record,field_config=fields['part_id'])
    if parts and len(parts) > 0:
        result["part"] = []
        for part in parts:
            result["part"].append(transform_part_data(part_data=part))
    else:
        result["part"] = get_part_data_from_ms_table(record=record, fields=fields, other_layer_data=other_layers, related_mss_data=related_mss)

    # add location info
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

    # Add the associated entities (ms and layers only)
    create_associated_entities(result, record, fields)
    # Add viscodex
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

    # TODO: hard-code type or get from data? Multiples!
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

    # Image rights and programs
    image_rights = parse.get_data_from_field(source=record, field_config=fields['image_rights'])
    image_rights = image_rights if image_rights else config.IMAGE_RIGHTS

    image_programs =  parse.get_data_from_multiple_fields(source=record,fields=fields, field_list=["image_program_labels", "image_program_descs", "image_program_camera_operators", "image_program_imaging_date", "image_program_delivery", "image_program_msi_processing", "image_program_condition_category", "image_program_imaging_system", "image_program_note"])
    result["image_provenance"] = {
        "program": transform_program_data(image_programs, "image") if image_programs["image_program_labels"] else None, # process program info only if there is at least one label | TODO: technically not a schema requirement, so other way around?
        "rights": image_rights
    } # TODO: hard-code or add a config variable for the image rights statement? Or should it be a part of the spreadsheets?

def transform_layer_fields(record, result, fields):
    # TODO: ? add related mss??
    state = {}
    state["id"] = parse.get_data_from_field(source=record, field_config=fields['state_id'])
    state["label"] = parse.get_data_from_field(source=record,field_config=fields['state_label'])
    result["state"] = state

    result["label"] = parse.get_data_from_field(source=record, field_config=fields['label'])

    result["extent"] = parse.get_data_from_field(source=record, field_config=fields['extent'])
    
    result["locus"] = parse.get_data_from_field(source=record, field_config=fields['locus'])

    # writing; TODO: only handles creating a single writing object...update config for locus and note to be text+, and multi-level, if needed; same with scripts...
    # other option is to let this just be a limitation of the script that is documented, since a rare case
    writing_data = parse.get_data_from_multiple_fields(source=record, fields=fields, field_list=["script_id", "script_label", "script_system", "writing_locus", "writing_note"])
    result["writing"] = [transform_writing_data(writing_data)]

    # ink
    ink_data = parse.get_data_from_multiple_fields(source=record, fields=fields, field_list=["ink_locus", "ink_color", "ink_note"])
    result["ink"] = transform_ink_data(ink_data)

    # layout
    layout_data = parse.get_data_from_multiple_fields(source=record, fields=fields, field_list=["layout_locus", "layout_columns", "layout_lines", "layout_dim", "layout_note"])
    result["layout"] = transform_layout_data(layout_data)

    # text unit reference: id, label, locus (id and label required)
    text_unit_reference_data = parse.get_data_from_multiple_fields(source=record, fields=fields, field_list=["text_unit_ark", "text_unit_label", "text_unit_locus"])
    result["text_unit"] = transform_text_unit_reference_data(text_unit_reference_data)

    # Add the associated entities (ms and layers only)
    create_associated_entities(result, record, fields)

    result["parent"] = parse.get_data_from_field(source=record, field_config=fields['parent_arks'])

def transform_text_unit_fields(record, result, fields):
    result["label"] = parse.get_data_from_field(source=record, field_config=fields['label'])

    result["locus"] = parse.get_data_from_field(source=record, field_config=fields['locus'])

    # lang
    lang_ids = parse.get_data_from_field(source=record, field_config=fields['language_id'])
    lang_labels = parse.get_data_from_field(source=record, field_config=fields['language_label'])
    result["lang"] = []
    for i in range(0, len(lang_ids)):
        result["lang"].append({
            "id": lang_ids[i],
            "label": lang_labels[i]
        })

    # work wit
    work_wit_data = parse.get_data_from_field(source=record, field_config=fields["work_wit_id"])
    result["work_wit"] = transform_work_wit_data(work_wit_data)

    result["parent"] = parse.get_data_from_field(source=record, field_config=fields['parent_arks'])


"""A handle function for abstracting the associate_* creation """
def create_associated_entities(result, record, fields):
    # Associated things
    result["assoc_name"] = transform_associated_entity_data(
        arks=parse.get_data_from_field(source=record, field_config=fields["assoc_name_ark"]),
        values=parse.get_data_from_field(source=record, field_config=fields["assoc_name_value"]),
        as_written=parse.get_data_from_field(source=record, field_config=fields["assoc_name_as_written"]),
        type_id=parse.get_data_from_field(source=record, field_config=fields["assoc_name_role_id"]),
        type_label=parse.get_data_from_field(source=record, field_config=fields["assoc_name_role_label"]),
        notes=parse.get_data_from_field(source=record, field_config=fields["assoc_name_note"]),
        iso=None,
        entity_type="name"
    )

    result["assoc_place"] = transform_associated_entity_data(
        arks=parse.get_data_from_field(source=record, field_config=fields["assoc_place_ark"]),
        values=parse.get_data_from_field(source=record, field_config=fields["assoc_place_value"]),
        as_written=parse.get_data_from_field(source=record, field_config=fields["assoc_place_as_written"]),
        type_id=parse.get_data_from_field(source=record, field_config=fields["assoc_place_event_id"]),
        type_label=parse.get_data_from_field(source=record, field_config=fields["assoc_place_event_label"]),
        notes=parse.get_data_from_field(source=record, field_config=fields["assoc_place_note"]),
        iso=None,
        entity_type="place"
    )

    result["assoc_date"] = transform_associated_entity_data(
        arks=None,
        values=parse.get_data_from_field(source=record, field_config=fields["assoc_date_value"]),
        as_written=parse.get_data_from_field(source=record, field_config=fields["assoc_date_as_written"]),
        type_id=parse.get_data_from_field(source=record, field_config=fields["assoc_date_type_id"]),
        type_label=parse.get_data_from_field(source=record, field_config=fields["assoc_date_type_label"]),
        notes=parse.get_data_from_field(source=record, field_config=fields["assoc_date_note"]),
        iso=parse.get_data_from_field(source=record, field_config=fields["assoc_date_iso"]),
        entity_type="date"
    )

def get_part_data_from_ms_table(record, fields, other_layer_data=None, related_mss_data=None):
    # TODO: should this be in a config somewhere???
    part_fields = ["part_label", "part_summary", "part_locus", "part_extent", "support_id", "support_label", "part_dim", "overtext_ark", "overtext_label", "overtext_locus", "part_paracontent"]

    part_notes_data = parse.get_typed_notes_data(source=record, note_fields=fields["part_typed_notes"])

    part_data = parse.get_data_from_multiple_fields(source=record, fields=fields, field_list=part_fields)
    return transform_part_data(part_data, other_layer_data=other_layer_data, related_mss_data=related_mss_data, notes_data=part_notes_data)

"""
Transform part data into the part object needed for output
"""
# TODO: refactor to split out some of the mess, e.g. for layers and such
def transform_part_data(part_data, other_layer_data=None, related_mss_data=None, notes_data=None):
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
    part["para"] = transform_paracontents_data(part_data["part_paracontent"])

    if(notes_data):
        part["note"] = transform_notes_data(notes_data)
    else:
        part["note"] = transform_notes_data(part_data["part_typed_notes"])

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

def transform_paracontents_data(paracontents_data):
    paracontents = []

    # dump out if empty
    if not(paracontents_data):
        return paracontents
    
    for record in paracontents_data:
        para = {}
        para_type = {
            "id": record["type_id"],
            "label": record["type_label"]
        }
        para["type"] = para_type

        para["subtype"] = []
        if record["subtype_id"]:
            for i in range(0, len(record["subtype_id"])):
                para["subtype"].append({
                    "id": record["subtype_id"][i],
                    "label": record["subtype_label"][i]
                })

        para["locus"] = record["locus"]

        # lang is required
        para["lang"] = []
        for i in range(0, len(record["lang_id"])):
            para["lang"].append({
                "id": record["lang_id"][i],
                "label": record["lang_label"][i]
            })
        
        # script is optional
        para["script"] = []
        if record["script_id"]:
            for i in range(0, len(record["script_id"])):
                para["script"].append({
                    "id": record["script_id"][i],
                    "label": record["script_label"][i],
                    "writing_system": record["script_system"][i]
                })

        para["label"] = record["label"]

        para["as_written"] = record["as_written"]

        para["translation"] = record["translation"]

        para["assoc_name"] = transform_associated_entity_data(
            arks=record["assoc_name_ark"],
            iso=None,
            values=record["assoc_name_value"],
            as_written=record["assoc_name_as_written"],
            type_id=record["assoc_name_role_id"],
            type_label = record["assoc_name_role_label"],
            notes=record["assoc_name_note"],
            entity_type="name"
        )

        para["assoc_place"] = transform_associated_entity_data(
            arks=record["assoc_place_ark"],
            iso=None,
            values=record["assoc_place_value"],
            as_written=record["assoc_place_as_written"],
            type_id=record["assoc_place_event_id"],
            type_label = record["assoc_place_event_label"],
            notes=record["assoc_place_note"],
            entity_type="place"
        )

        para["assoc_date"] = transform_associated_entity_data(
            arks=None,
            iso=record["assoc_date_iso"],
            values=record["assoc_date_value"],
            as_written=record["assoc_date_as_written"],
            type_id=record["assoc_date_type_id"],
            type_label = record["assoc_date_type_label"],
            notes=record["assoc_date_note"],
            entity_type="date"
        )

        para["note"] = record["note"]

        paracontents.append(para)
    
    return paracontents

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
Transforms the notes information.
Takes a dictionary of note types with merged in data and creates the array of typed notes
"""
def transform_notes_data(notes_data):
    notes = []
    for type in notes_data:
        if not(notes_data[type]["data"]) or len(notes_data[type]["data"]) == 0:
            continue
        for value in notes_data[type]["data"]:
            notes.append(
                {
                    "type": {
                        "id": type,
                        "label": notes_data[type]["label"]
                    },
                    "value": value
                }
            )
    return notes

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

"""
Takes returned data about associated entities from the parser and converts to the associated entity object
"""
def transform_associated_entity_data(arks, iso, values, as_written, type_id, type_label, notes, entity_type: str):
    entities = []

    # dump out if no entities to parse
    if not(type_id):
        return entities

    num_entities = len(type_id)

    # fill the optional fields (all but the type)
    if not(arks) and entity_type in ["name", "place"]:
        arks = [None] * num_entities
    if not(iso) and entity_type == "date":
        iso = [None] * num_entities
    if not(values):
        values = [None] * num_entities
    if not(as_written):
        as_written = [None] * num_entities
    if not(notes):
        notes = [None] * num_entities

    # process each entity into its object
    for i in range(0, len(type_id)):
        e = {}
        if entity_type in ["name", "place"]:
            e["ark"] = arks[i]
        e["value"] = values[i]
        if entity_type == "date":
            e["iso"] = process_iso_string(iso[i])
        e["as_written"] = as_written[i]
        type_obj = {
            "id": type_id[i],
            "label": type_label[i]
        }
        if entity_type == "name":
            e["role"] = type_obj
        elif entity_type == "place":
            e["event"] = type_obj
        elif entity_type == "date":
            e["type"] = type_obj
        
        e["note"] = notes[i]

        entities.append(e)
        
    return entities
    
def process_iso_string(iso):
    date = iso.split("/")
    not_before = date[0].zfill(4)
    not_after = None
    if(len(date) > 1):
        not_after = date[1].zfill(4)
    return {
        "not_before": not_before,
        "not_after": not_after
    }

def transform_program_data(programs, type: str):
    data = []

    count_programs = len(programs[f"{type}_program_labels"])
    for i in range(0, count_programs):
        d = {}
        d["label"] = get_element(programs[f"{type}_program_labels"], i)
        d["description"] = get_element(programs[f"{type}_program_descs"], i)
        # the following are only for image type programs
        if type == "image":
            d["camera_operator"] = get_element(programs[f"{type}_program_camera_operators"], i)
            d["imaging_date"] = get_element(programs[f"{type}_program_imaging_date"], i)
            d["delivery"] = get_element(programs[f"{type}_program_delivery"], i)
            d["msi_processing"] = get_element(programs[f"{type}_program_msi_processing"], i)
            d["condition_category"] = get_element(programs[f"{type}_program_condition_category"], i)
            d["imaging_system"] = get_element(programs[f"{type}_program_imaging_system"], i)
            d["note"] = get_element(programs[f"{type}_program_note"], i)
        data.append(d)
    return data

def transform_writing_data(writing_data):
    writing = {}
    writing["script"] = []
    for i in range(0, len(writing_data["script_id"])):
        script = {
            "id": get_element(writing_data["script_id"], i),
            "label": get_element(writing_data["script_label"], i),
            "writing_system": get_element(writing_data["script_system"], i),
        }
        writing["script"].append(script)
    
    writing["locus"] = writing_data["writing_locus"]

    writing["note"] = writing_data["writing_note"]
    return writing

def transform_ink_data(ink_data):
    inks = []
    ink_count = get_length_from_optional_fields(ink_data)
    for i in range(0, ink_count):
        ink = {
            "locus": get_element(ink_data["ink_locus"], i),
            "color": get_element(ink_data["ink_color"], i),
            "note": get_element(ink_data["ink_note"], i),
        }
        inks.append(ink)
    return inks

def transform_layout_data(layout_data):
    layouts = []
    layout_count = get_length_from_optional_fields(layout_data)
    for i in range(0, layout_count):
        layout = {
            "locus": get_element(layout_data["layout_locus"], i),
            "columns": get_element(layout_data["layout_columns"], i),
            "lines": get_element(layout_data["layout_lines"], i),
            "dim": get_element(layout_data["layout_dim"], i),
            "note": get_element(layout_data["layout_note"], i),
        }
        layouts.append(layout)
    return layouts

def transform_text_unit_reference_data(text_unit_reference_data):
    tu_refs = []
    tu_count = len(text_unit_reference_data["text_unit_ark"])

    for i in range(0, tu_count):
        tu = {
            "id": get_element(text_unit_reference_data["text_unit_ark"], i),
            "label": get_element(text_unit_reference_data["text_unit_label"], i),
            "locus": get_element(text_unit_reference_data["text_unit_locus"], i)
        }
        tu_refs.append(tu)
    return tu_refs

def transform_work_wit_data(work_wit_data):
    # return work_wit_data
    wits = []
    wits_sequence = [int(w["sequence"]) for w in work_wit_data]
    for w in work_wit_data:
        wit = {}

        # get genre info, if it exists
        genres = [] 
        genre_count = get_length_from_optional_fields({k: w[k] for k in ("work_genre_id", "work_genre_label")})
        for i in range(0, genre_count):
            genres.append ({
                "id": get_element(w["work_genre_id"], i),
                "label": get_element(w["work_genre_label"], i)
            })
        # create the work_wit.work property
        wit["work"] = {
            "id": w["work_id"],
            "desc_title": w["work_desc_title"],
            "creator": w["work_creator"],
            "genre": genres
        }


        wit["alt_title"] = w["alt_title"]
        wit["as_written"] = w["as_written"]
        wit["locus"] = w["locus"]

        # excerpts
        if(w["excerpt_id"]):
            excerpts_sequence = [int(e["sequence"]) for e in w["excerpt_id"]]
            # transform excerpts
            excerpts =  transform_excerpts(w["excerpt_id"])
            # order by sequence and add to to wit obj
            wit["excerpt"] = order_list_by_sequence(excerpts, excerpts_sequence)

        # contents
        if(w["content_id"]):
            tocs_sequence = [int(c["sequence"]) for c in w["content_id"]]
            tocs = transform_tocs_from_table(w["content_id"])

            wit["contents"] = order_list_by_sequence(tocs, tocs_sequence)
        # otherwise use contents label and notes fields for inline data
        elif(w["content_label"]):
            wit["contents"] = []
            for i in range(0, len(w["content_label"])):
                wit["contents"].append(
                    {
                        "label": get_element(w["content_label"], i),
                        "note": get_element(w["content_note"], i)
                    }
                )


        wit["note"] = w["note"]

        # bibs
        bibs = w["bibs"]
        if bibs and len(bibs) > 0:
            wit["bib"] = [transform_bib_data(bibs)]

        wits.append(wit)

    # return the list of wits, ordering by sequence
    return order_list_by_sequence(wits, wits_sequence)
    # return work_wit_data # use this for testing purposes

def transform_excerpts(excerpts):
    data = []
    for exc in excerpts:
        data.append({
            "type": {
                "id": exc["type_id"],
                "label": exc["type_label"]
            },
            "locus": exc["locus"],
            "as_written": exc["as_written"],
            "translation": exc["translation"],
            "note": exc["note"]
        })
    return data

def transform_tocs_from_table(contents):
    toc = []
    for c in contents:
        toc.append(
            {
                "label": c["label"],
                "work_id": c["work_id"],
                "locus": c["locus"],
                "note": c["note"]
            }
        )
    return toc

def transform_change_log_data(change_log_data):
    logs = []
    for i in range(0, len(change_log_data["change_log_message"])):
        logs.append({
            "message": get_element(change_log_data["change_log_message"], i),
            "contributor": get_element(change_log_data["change_log_contributor"], i),
            "added_by": get_element(change_log_data["change_log_added_by"], i),
            "timestamp": get_element(change_log_data["change_log_timestamp"], i)
        })
    return logs

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

"""
This function is a helper to handle the many cases where a multi-column field may have empty fields. It handles the TypeError that results from using bracket notation on a None value
TODO: could add a wrapper or alternative or flag that handles when it's required or not, i.e. if it's a required field missing any data it should raise an error?
"""
def get_element(iterable, index, fallback=None):
    try:
        return iterable[index]
    except TypeError:
        return fallback

"""
This helper function gets the length from a set of iterable fields when all are optional
Returns 0 if all are None, but if any have data, returns the max length
Assumes the field is either None or an array
TODO: check that this works if there's a string in there...or confirm it's always arrays or None
"""
def get_length_from_optional_fields(fields):
    length = 0
    for name in fields:
        # if the field exists and its length is 
        length = len(fields[name]) if fields[name] and len(fields[name]) > length else length
    return length

"""
Assumptions:
1. The length of unordered and seq are equal (i.e., every item in unordered has a corresponding sequence)
2. The values of seq are unique (i.e., no sequence number repeats)

Orders the unordered list based on the associated sequence, ascending
Reduces the sequence, first, to handle gaps in the sequence or cases where the sequence does not start at a 0-index
"""
def order_list_by_sequence(unordered: list, seq: list):
    # initialize a list of the same length as the unordered list
    ordered = [None] * len(unordered)
    # reduce the sequence to a contiguous set from 0 -> len(unordered)
    reduced_seq = reduce_sequence(seq)
    for i in range(0, len(reduced_seq)):
        ordered[reduced_seq[i]] = unordered[i]
    return ordered

# Takes a sequence and reduces it to a contiguous set of values from 0 -> len(seq)
"""
Example:
[8, 4, 6]

should become
[2, 0, 1]
"""
def reduce_sequence(seq):
    seq_copy = seq.copy()
    # creates a map of the existing values in the sequence and their reduced versions
    seq_map = map_sequence_order(seq_copy, 0, {})
    return [seq_map[v] for v in seq]

# Recursive function for mapping a sequence of integers to its ascending
# value order
"""
For the sequence, [8, 4, 6] it will return a dictionary:
{
  8: 2,
  4: 0,
  6: 1
}
"""
def map_sequence_order(seq, i, seq_map):
    # if there is a non-empty sequence, get its minimum value and add to the map
    if(len(seq) > 0):
        min_val = min(seq)
        ind = seq.index(min_val)
        seq_map[min_val] = i
        del(seq[ind])
        return map_sequence_order(seq, i+1, seq_map)
    # if no further seq items to process, return the map
    else:
        return seq_map