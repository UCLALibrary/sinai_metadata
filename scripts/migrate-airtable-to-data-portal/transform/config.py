"""
This module contains configurations, constant variables, etc. used for the CSV to JSON transformations
"""
import json
import transform.helpers as helpers

# CONSTANTS

RECORD_TYPES = ["ms_objs", "layers", "text_units"]

RECORD_LABELS = {
    "ms_objs": "Manuscript Objects",
    "layers": "Layers",
    "text_units": "Text Units"
}

# The record type for a given pass
record_type = ""

# ~~~~~
# I/O
# ~~~~~

# add for main CSV input path
main_csv = {
    "file_path": "",
    "data": None
}

# Directory where the data should be saved
output_directory = "" # set to a default


# ~~~~~
# Side CSVs
# ~~~~~

other_csvs = {
    "parts": {
        "file_path": "",
        "data": None,
        "key": "part",
        "label": "Parts",
        "scope": ["ms_objs"]
    },
    "related_mss": {
        "file_path": "",
        "data": None,
        "key": "related_mss",
        "label": "Related Manuscripts",
        "scope": ["ms_objs", "layers"]
    },
    "bibs": {
        "file_path": "",
        "data": None,
        "key": "bib",
        "label": "Bibliography",
        "scope": ["ms_objs", "layers", "text_units"]
    },
    "paracontents": {
        "file_path": "",
        "data": None,
        "key": "para",
        "label": "Paracontents",
        "scope": ["ms_objs", "layers", "text_units"]
    },
    "work_wits": {
        "file_path": "",
        "data": None,
        "key": "work_wit",
        "label": "Work Witnesses",
        "scope": ["text_units"]
    },
    "excerpts": {
        "file_path": "",
        "data": None,
        "key": "excerpt",
        "label": "Excerpts",
        "scope": ["text_units"]
    }
}


# ~~~~~
# Paths to Field Name Declaration Docs
# ~~~~~
field_names = {
    "ms_objs": "ms_obj_fields.txt",
    "layers": "layer_fields.txt",
    "text_units": "text_unit_fields.txt",
    "parts": "part_fields.txt",
    "work_wits": "work_wit_fields.txt",
    "bibs": "bib_fields.txt",
    "paracontents": "para_fields.txt",
    "related_mss": "related_mss_fields.txt",
    "excerpts": "excerpt_fields.txt"
}


# ~~~~~
# Config functions
# ~~~~~

def initialize_csv_data_from_paths():
    # initialize main CSV
    main_csv["data"] = helpers.setup_main_csv(main_csv["file_path"], log=False)

    # initialize other CSVs
    for csv in other_csvs:
        if other_csvs[csv]["file_path"] != "":
            other_csvs[csv]["data"] = helpers.initialize_side_csv(other_csvs[csv]["file_path"], field_names[csv])