"""
This module contains functions related to parsing the input data fields into
forms usable by the main transform module
"""
import pandas as pd
import migrate.config as config
from io import StringIO

def get_data_from_field(source, field_config):
    field_info = field_config
    field_info["mode"] = field_config[config.MODE]
    field_info["data"] = source.get(field_config["name"])
    return get_data(**field_info)

def preprocess(func):
    def wrapper(*args, **kwargs):
        # if data is empty, return an empty bit of data
        if(not(kwargs["data"]) or len(kwargs["data"]) == 0):
            return None
        # pre-process delmited strings into arrays
        if(kwargs["mode"] in ["text+", "record+"] and isinstance(kwargs["data"], str)):
            kwargs["data"] = split_by_delim(kwargs["data"], kwargs["delimiter"])
        
        # pre-process record lookups into dictionaries containing those records' data for each record
        if(kwargs["mode"] in ["record", "record+"]):
            if(isinstance(kwargs["data"], str)):
                kwargs["data"] = get_data_from_lookup(kwargs["data"], kwargs["lookup"])
            else:
                kwargs["data"] = [get_data_from_lookup(rec_id, kwargs["lookup"]) for rec_id in kwargs["data"]]
        return func(*args, **kwargs)
    return wrapper

def split_by_delim(data, delim, quotechar=None):
    depth = len(delim)
    if(depth == 0):
        return data
    agg_data = []
    if(isinstance(data, str)):
        for frag in string_split_with_escape(to_split=data, delim=delim[0], quotechar=quotechar):
            agg_data.append(split_by_delim(frag, delim[1:], quotechar))
    else:
        for frag in data:
            agg_data.append(split_by_delim(frag, delim[0], quotechar))
    return agg_data


# This function simplifies the parsing of delimited strings that also contain quote characters for escaping the delimiter, just in case
# Returns a list of the strings, divided at the delimiter
# current implementation uses StringIO and reads it with pands.read_csv, as this has proven most reliable with escape characters, 
def string_split_with_escape(to_split: str, delim, quotechar=None):
    split_data = []
    # if the split string is empty, return an empty array
    if len(to_split) == 0:
        return split_data
    if quotechar:
        split_data = pd.read_csv(StringIO(to_split), sep=delim, quotechar=quotechar, skipinitialspace=True, engine='python', header=None).astype(str).iloc[0].values.flatten().tolist()
    # if no quotechar, then assume quoting is off, which is set by quoting=3 per Pandas spec
    else:
        split_data = pd.read_csv(StringIO(to_split), sep=delim, quoting=3, skipinitialspace=True, engine='python', header=None).astype(str).iloc[0].values.flatten().tolist()

    # return the resulting list, replacing 'nan' with an empty string
    return list(map(lambda x: '' if x == 'nan' else x, split_data))


@preprocess
def get_data(*args, **kwargs):
    return kwargs["data"]

def get_data_from_lookup(rec_id, lookup_info):
    table_name = lookup_info.split(".")[0]
    field_names = lookup_info.split(".")[1]
    
    table = config.TABLES[table_name]
    record = table["data"][rec_id]

    # Use this as "all fields", TODO: maybe default as well to 'None', so if we just give a lookup table name it defaults to pulling in all of the fields?
    if field_names == "*":
        field_data = {}
        for field in table["fields"]:
            field_data[field] = get_data_from_field(source=record, field_config=table["fields"][field])
        return field_data

    if isinstance(field_names, str):
        return get_data_from_field(source=record, field_config=table["fields"][field_names])
    """
    - if field_names is '*', get all of the fields from the lookup table
    - if it's an array, get all of those fields from the lookup table
        - recursively...
    - if it's just a string
    """