"""
Utilities and other helper functions for transforming CSV to JSON
"""
import pandas as pd
import transform.config as config

def setup_main_csv(path_to_csv: str, log: bool):
    csv_file = pd.read_csv(path_to_csv)

    # check if any columns are missing compared with the standard list
    missing_columns = check_csv_columns_against_standard_list(config.field_names[config.record_type], config.RECORD_LABELS[config.record_type], csv_file.columns, log=log)
    
    for col in missing_columns:
        csv_file[col] = pd.Series(dtype='string')

    return csv_file


def check_csv_columns_against_standard_list(columns_list_doc: str, record_type: str, csv_columns: list, log: bool):
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
    if log:
        print(f"The following '{record_type}' CSV columns will be ignored:")
        print(extra_columns)
        print("\n")
        print(f"The following expected columns are missing from the '{record_type}' CSV and will be supplied as null values:")
        print(missing_columns)
        print("\n")
    return missing_columns

def setup_side_csv(path_to_allowed_fields_doc: str, property_key: str, property_label: str):
    path_to_csv = input(f"Please input a path to the CSV containing the rows for creating the {property_key} field (or leave blank if unused):")
    if path_to_csv:
        csv = pd.read_csv(path_to_csv, index_col='ID')
        missing_col = check_csv_columns_against_standard_list(path_to_allowed_fields_doc, property_label, csv.columns, log=True)
        print("Note: 'ID' may be erroneously reported as missing since it is used as the DataFrame index column, if the script did not report a failure, it is okay to ignore this")
        user_response = input("Please press enter to continue with the migration script")
        for col in missing_col:
            csv[col] = pd.Series(dtype='string')
    else:
        csv = None
    return csv

def initialize_side_csv(path_to_csv: str, path_to_allowed_fields_doc: str):
    csv = pd.read_csv(path_to_csv, index_col='ID')
    missing_col = check_csv_columns_against_standard_list(path_to_allowed_fields_doc, '', csv.columns, log=False)
    for col in missing_col:
        csv[col] = pd.Series(dtype='string')
    return csv

# Returns a Data Frame from a CSV file, filtered by a list of IDs, optionally sorted by a "Sequence" field
# Used to pre-process "side" CSVs referenced from the main CSV, e.g. for work witnesses

def get_side_csv_data(ids: list, csv: pd.DataFrame, sort_by_sequence: bool):
    data = csv.loc[list(map(int, ids))]
    if sort_by_sequence:
        return data.sort_values("Sequence")
    return data

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

# Takes an unoredered list and a list of integers representing the correct sequence
# Returns a list that has been reordered according to the sequence
def order_list_by_sequence(unordered: list, seq: list):
    # initialize a list of the same length as the unordered list
    ordered = [None] * len(unordered)
    for i in range(0, len(seq)):
        ordered[seq[i]-1] = unordered[i]
    return ordered

def parse_iso_date(iso: str):
    not_before = str(iso).split("/")[0]
    if len(str(iso).split("/")) > 1:
        not_after = str(iso).split("/")[1]
    else:
        not_after = ""
    date = {}
    date["not_before"] = not_before.zfill(4)
    # only add not_after property if the ISO date is a range
    if not_after != "":
        date["not_after"] = not_after.zfill(4)
    return date