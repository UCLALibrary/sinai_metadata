"""
This module contains configurations, constant variables, etc. used for the CSV to JSON transformations
"""
import json, yaml
from migrate import user

# CONSTANTS

VALID_MODES = ["airtable", "csv"]

TABLES = {}

MODE = ""

AIRTABLE_BASE = ""
AIRTABLE_USER_KEY = ""

# Default metadata and image rights statements
# TODO: does this need to be set in the config file?
METADATA_RIGHTS = ""
IMAGE_RIGHTS = ""

# Default key ordering for top-level objects
# Note: lower-level objects' key ordering are set by the functions which create them (see transform.py if needing to edit)
MS_OBJ_FIELD_ORDER = ["ark", "reconstruction", "type", "shelfmark", "summary", "extent", "weight", "dim", "state", "fol", "coll", "features", "part", "layer", "para", "location", "assoc_date", "assoc_name", "assoc_place", "note", "related_mss", "viscodex", "bib", "iiif", "internal", "desc_provenance", "image_provenance", "cataloguer", "reconstructed_from"]

LAYER_FIELD_ORDER = ["ark", "reconstruction", "state", "label", "locus", "summary", "extent", "writing", "ink", "layout", "text_unit", "para", "assoc_date", "assoc_name", "assoc_place", "features", "related_mss", "note", "bib", "desc_provenance", "cataloguer", "reconstructed_from", "parent", "internal"]

TEXT_UNIT_FIELD_ORDER = ["ark", "reconstruction", "label", "summary", "locus", "lang", "work_wit", "para", "features", "note", "bib", "desc_provenance", "cataloguer", "reconstructed_from", "parent", "internal"]


def set_configs(args):
    # set the global MODE config variable based on the arguments
    set_mode(args.mode)

    # set the Airtable User key from user input based on 
    if args.mode == "airtable":
        global AIRTABLE_USER_KEY
        AIRTABLE_USER_KEY = user.get_airtable_user_key()
    
    # Open the file passed by the args.config value
    # TODO: try/catch i/o issues
    set_table_configs(dir=args.config, file="table_configs.yml")

    # add the configuration data for each table's fields to its object
    set_field_configs(dir=args.config)
    """
    TODO:
    - hold this space as a place to add more configurations should they prove necessary
    """

def set_mode(mode):
    global MODE
    MODE = mode

def set_table_configs(dir, file="table_configs.yml"):
    file_path = dir + "/" + file
    with open(file_path) as fh:
        data = yaml.safe_load(fh)
        global AIRTABLE_BASE
        AIRTABLE_BASE = data["airtable_base"]
        global TABLES
        TABLES = data["tables"]

def set_field_configs(dir):
    for table_name in TABLES:
        with open(dir + "/" + TABLES[table_name]["fields"]) as fh:
            field_data = yaml.safe_load(fh)
            TABLES[table_name]["fields"] = field_data