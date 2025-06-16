import jschon, json, requests, os, sys

'''
CONSTANTS
'''
OUTPUT_FILE = 'log.json'
# PATH_TO_RECORDS = '/Users/wpotter/Documents/GitHub/sinai_metadata/portal_data/works/'
AGENTS_SCHEMA_URL = 'https://raw.githubusercontent.com/UCLALibrary/sinai_metadata/master/data-model/tnb_docs/agent.schema.json'
WORKS_SCHEMA_URL = 'https://raw.githubusercontent.com/UCLALibrary/sinai_metadata/master/data-model/tnb_docs/work.schema.json'
MSOBJS_SCHEMA_URL = 'https://raw.githubusercontent.com/UCLALibrary/sinai_metadata/master/data-model/tnb_docs/ms-obj.schema.json'
LAYERS_SCHEMA_URL = 'https://raw.githubusercontent.com/UCLALibrary/sinai_metadata/master/data-model/tnb_docs/layer.schema.json'
TXTUNITS_SCHEMA_URL = 'https://raw.githubusercontent.com/UCLALibrary/sinai_metadata/master/data-model/tnb_docs/text_unit.schema.json'
EXPORT_SCHEMA_URL = 'https://raw.githubusercontent.com/UCLALibrary/sinai_metadata/refs/heads/master/data-model/jsonschemas/smdl.json'

# declare a json schema catalog
jschon.create_catalog('2020-12')

# Users supply a command line argument to select
# Valid options are: agents, works, msobjs, layers, or txtunits
schema_option = sys.argv[1]
if schema_option == "agents":
    selected_schema = AGENTS_SCHEMA_URL
elif schema_option == "works":
    selected_schema = WORKS_SCHEMA_URL
elif schema_option == "msobjs":
    selected_schema = MSOBJS_SCHEMA_URL
elif schema_option == "layers":
    selected_schema = LAYERS_SCHEMA_URL
elif schema_option == "txtunits":
    selected_schema = TXTUNITS_SCHEMA_URL
elif schema_option == "export":
    selected_schema = EXPORT_SCHEMA_URL
else:
    selected_schema = "" # this will cause an error

path_to_records = input("Supply the full path to a directory of JSON records you'd like to validate:")

# get the json schema from the URL
schema_json = requests.get(selected_schema).json()

# declare the json as a JSON Schema
schema = jschon.JSONSchema(schema_json)

# read in the json files from the directory
files = os.listdir(path_to_records)
output = []
for file in files:
    with open(path_to_records + "/" + file) as f:
        # ignore non-JSON files (e.g., .DS_Store)
        if file.endswith(".json"):
            # read the contents as JSON
            rec = json.load(f)

            # evaluate against the schema, report by file name only if there are errors
            result = schema.evaluate(jschon.json.JSON(rec))
            if(not(result.output('flag')['valid'])):
                validation_result = result.output('basic')
                validation_result["filename"] = file
                
                output.append(validation_result)

with open('log.json', 'w+') as f:
    json.dump(output, f, indent=2)