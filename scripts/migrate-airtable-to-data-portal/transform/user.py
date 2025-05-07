"""
A module controlling how a user interacts with the script
"""
import transform.config as config
import transform.helpers as helpers
import json

def set_config_interactive():
    # Sets the record type
    config.record_type = input(f"Enter the record type, must be one of {config.RECORD_TYPES}: ")
    while not(config.record_type in config.RECORD_TYPES):
        config.record_type = input(f"'{config.record_type}' is not a valid type, must be one of {config.RECORD_TYPES}: ")
    
    # Set the Main CSV path and data
    # TBD: re-write into a do/while loop?
    config.main_csv["file_path"] = input("Enter a path to the CSV file for the main record type: ")

    try:
        config.main_csv["data"] = helpers.setup_main_csv(config.main_csv["file_path"], log=True)
    except OSError:
        print("ERROR: Incorrect path to csv, the file may not exist in the provided directory")

    # Set the other CSV paths and create their DataFrames

    for csv in config.other_csvs:
        # only include those in scope (e.g., ignore work wit unless recor type is 'text unit')
        if config.record_type in config.other_csvs[csv]["scope"]:
            config.other_csvs[csv]["data"] = helpers.setup_side_csv(config.field_names[csv], config.other_csvs[csv]["key"], config.other_csvs[csv]["label"])

    # Set the output directory
    config.output_directory = input(f"Enter an ouptut directory (defaults to out/{config.record_type}/): ")
    if config.output_directory == "":
        config.output_directory = f"out/{config.record_type}/"


# Input a path to a configuration file. Currently requires a JSON file
# TBD: add a parameter to give it a type, either JSON, XML, or YAML, to handle multiple options
def set_config_from_file(path_to_file: str):
    with open(path_to_file, 'r') as f:
        data = json.load(f)
        config.record_type = data["record_type"]
        config.main_csv["file_path"] = data["main_csv"]
        config.output_directory = data["output_directory"]

        # set other csvs
        for csv in config.other_csvs:
            # only set if in-scope for this rec type and included in the config file
            if config.record_type in config.other_csvs[csv]["scope"] and csv in data["other_csvs"]:
                config.other_csvs[csv]["file_path"] = data["other_csvs"][csv]
        
        # set the field names path variable, only if set in the file
        if "field_names" in data:
            for rec in config.field_names:
                if rec in data["field_names"]:
                    config.field_names[rec] = data["field_names"][rec]
    # initialize the config variables that need to be DataFrames based on the supplied paths
    config.initialize_csv_data_from_paths()
