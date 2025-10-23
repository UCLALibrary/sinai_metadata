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


def set_configs(args):
    # set the global MODE config variable based on the arguments
    global MODE
    MODE = args.mode
    # set the Airtable User key from user input based on 
    if args.mode == "airtable":
        global AIRTABLE_USER_KEY
        AIRTABLE_USER_KEY = user.get_airtable_user_key()
    
    # Open the file passed by the args.config value
    # TODO: try/catch i/o issues

    with open(args.config + "/table_configs.yml") as fh:
        data = yaml.safe_load(fh)
        global AIRTABLE_BASE
        AIRTABLE_BASE = data["airtable_base"]
        global TABLES
        TABLES = data["tables"]

    # add the configuration data for each table's fields to its object
    for table_name in TABLES:
        with open(args.config + "/" + TABLES[table_name]["fields"]) as fh:
            field_data = yaml.safe_load(fh)
            TABLES[table_name]["fields"] = field_data
    """
    TODO:
    - hold this space as a place to add more configurations should they prove necessary
    """