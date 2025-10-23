""""
This module deals with wrangling data inputs from airtable or csv files.
These data will be parsed and processed by other modules
"""
import migrate.config as config
import pyairtable
import pandas as pd

"""
generic get data from config document that calls the airtable or pandas ones
based on the config setting of 'mode', which is from user
maybe here is the for each part?
it should set or add to a variable from config with the data itself?
"""
"""
TODO: consider if should return and set rather than return null and set as side effect?
"""
def get_data():
    print("Getting data")
    if config.MODE == "airtable":
        print("Retrieving data from Airtable")
        airtable_client = pyairtable.Api(config.AIRTABLE_USER_KEY)
    for table in config.TABLES:
        if(config.MODE == "csv"):
            get_table_data_from_csv(config.TABLES[table])
        elif(config.MODE == "airtable"):
            get_table_data_from_airtable(config.TABLES[table], airtable_client)

def get_table_data_from_csv(table_info):
    with open(table_info["csv"]) as fh:
        table_data = pd.read_csv(fh, index_col=table_info.get("index_col"))
        data = {}
        # Parse the DataFrame into a 2-dim dictionary to match how Airtable will be parsed
        for row_index, row in table_data.iterrows():
            row_data = {}
            for column_index, column in row.items():
                # Replace nan with None
                if(pd.isna(column)):
                   row_data[column_index] = None
                # Otherwise, add the field as a key/value pair
                else:
                   row_data[column_index] = column
            data[row_index] = row_data
        table_info["data"] = data

def get_table_data_from_airtable(table_info, airtable_client):
    # get and parse the URL into the base, table, and view keys
    url = table_info["airtable"]
    print(f"getting Airtable data for {url}")
    base_key, table_key, view_key = parse_airtable_url(url)
    # TODO: Check base_key against config.AIRTABLE_BASE
    
    # use the API parameters to get all records from the table (and view, if not None)
    table_data = airtable_client.table(base_key, table_key).all(view=view_key)

    # Parse this data into a dictionary where the keys represent the Airtable record ID
    table_info["data"] = {record["id"]:record["fields"] for record in table_data}

"""
Assumes that URL looks like https://airtable.com/appiXmKhPFEVmVQrD/tblKIvl8xqSkze5jF/viwn0c2SSDH6oXvyq
"""
def parse_airtable_url(url):
    # get the list of keys from the URL path portion
    keys_string = url.split("airtable.com/")[1]
    keys = keys_string.split("/")

    # make sure the last one doesn't have trailing whitespace or search parameters
    keys[-1] = keys[-1].rstrip().split("?")[0]

    # add None for the view key if not included
    if len(keys) < 3:
        keys.append(None)

    return keys
"""
- for each in config of tables, get the airtable records
- calls a get single table
- passes to a processor that takes them and makes a dict with keys as record IDs
- returns to the for each function
"""