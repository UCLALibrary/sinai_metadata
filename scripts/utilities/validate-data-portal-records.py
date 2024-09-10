import jschon, json, requests, os

'''
CONSTANTS
'''
PATH_TO_RECORDS = '/Users/wpotter/Desktop/SMDP-Migration/works/'
AGENTS_SCHEMA_URL = 'https://raw.githubusercontent.com/UCLALibrary/sinai_metadata/master/data-model/tnb_docs/agent.schema.json'
WORKS_SCHEMA_URL = 'https://raw.githubusercontent.com/UCLALibrary/sinai_metadata/master/data-model/tnb_docs/work.schema.json'

# select a JSON schema to use
selected_schema = WORKS_SCHEMA_URL # change to AGENTS_SCHEMA_URL; to do: rewrite to use user input prompting

# declare a json schema catalog
jschon.create_catalog('2020-12')

# get the json schema from the URL
schema_json = requests.get(selected_schema).json()

# declare the json as a JSON Schema
schema = jschon.JSONSchema(schema_json)

# read in the json files from the directory
files = os.listdir(PATH_TO_RECORDS)
for file in files:
    with open(PATH_TO_RECORDS + file) as f:
        # read the contents as JSON
        rec = json.load(f)

        # evaluate against the schema, report by file name only if there are errors
        result = schema.evaluate(jschon.json.JSON(rec))
        if(not(result.output('flag')['valid'])):
            print(file)
            print(result.output('detailed'))