"""
This module holds the main logic for converting records into Portal JSON files
"""
import migrate.config as config
import migrate.parse as parse

# the main transformation function
def transform_records(table_name: str):
    main_table = config.TABLES[table_name] # TODO: raise exception if not in main table types?
    for record in main_table["data"]:
        transformed_record = transform_single_record(record=main_table["data"].get(record), 
                                                     record_type=table_name,
                                                     fields=config.TABLES[table_name]["fields"])
        print(transformed_record) #TODO: save this to a file instead

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

    # TODO: features (record+ for airtable)

    # TODO: parts...
    """
    - if part_ids, use that
    - else this involves: part_label, part_summary, part_locus, part_extent, support(id and labe), notes (support, ), part_dim, overtext parsing (and other layers parsing), maybe related mss, maybe paracontent
    """

    # TODO: location (id, repository, collection) (record+ for airtable)]

    # TODO: assoc_* (needs a sub-function)
    
    # TODO: related mss (and for parts...)

    # TODO: viscodex (label and url) - easy, but need to get both, then for each

    bibs = parse.get_data_from_field(source=record, field_config=fields['bibs'])
    
    if bibs and len(bibs) > 0:
        result["bib"] = [transform_bib_data(bibs)]

    iiif = {}
    iiif["manifest"] = parse.get_data_from_field(source=record, field_config=fields['iiif_manifest_url'])
    iiif["text_direction"] = parse.get_data_from_field(source=record, field_config=fields['iiif_text_direction'])
    iiif["behavior"] = parse.get_data_from_field(source=record, field_config=fields['iiif_behavior'])
    iiif["thumbnail"] = parse.get_data_from_field(source=record, field_config=fields['iiif_thumbnail_url'])

    result["iiif"] = iiif

    # TODO: description and image program (waiting on config)

    # TODO: reconstructed from (waiting on config)

    return del_none(result) # TODO: reorder based on an established order?

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
