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
    field_info["data"] = source[field_config["name"]]
    return get_data(**field_info)

def preprocess(func):
    def wrapper(*args, **kwargs):
        if(kwargs["mode"] in ["text+", "record+"]): # TODO: change to first check if it's text+; elif record+ and data is a string rather than an array
            kwargs["data"] = split_by_delim(kwargs["data"], kwargs["delim"])
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