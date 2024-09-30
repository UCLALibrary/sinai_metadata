import json, csv, sys

# I/O and CSV Parameters
path_to_csv = sys.argv[1] # specify CSV file to use as terminal parameter
csv_has_header = True
# optionally set the ordered field names of the CSV -- N.B. overriden by has_header being true
headers = []
if (csv_has_header):
    headers=None
separator = ","

# this is the base JSON snippet into which the list of controlled term objects will be placed
json_base = {
    "$ref": "https://raw.githubusercontent.com/UCLALibrary/sinai_metadata/master/data-model/jsonschemas/utils.json#/$defs/controlled_term",
    "oneOf": []
}

#########
# Main Script #
#########
with open(path_to_csv) as csvfile:
    reader = csv.DictReader(csvfile, delimiter=separator, fieldnames=headers, restkey="misc", restval="")
    for row in reader:
        # skip empty ID rows
        if(row["id"] == ""):
            continue

        enum_term = {
        "const": {
            "id": row["id"],
            "label": row["label"]
            }
        }
        json_base["oneOf"].append(enum_term)

# prints updated JSON snippet to console; copy and paste this into the enums.json schema where needed
print(json.dumps(json_base, indent=4))


"""
Example output:
{
    "$ref": "https://raw.githubusercontent.com/UCLALibrary/sinai_metadata/master/data-model/jsonschemas/utils.json#/$defs/controlled_term"
    "oneOf": [
        {
            "const": {
                "id": "person",
                "label": "Person"
            }
        },
        {
            "const": {
                "id": "organization",
                "label": "Organization"
            }
        }
    ]
}
Note that the reference to the controlled_term subschema provides the following base parameters:
"type": "object",
"unevaluatedProperties": false,
"properties": {
    "id": {
        "type": "string"
    },
    "label": {
        "type": "string"
    }
},
"required": [
    "id",
    "label"
    ]
"""