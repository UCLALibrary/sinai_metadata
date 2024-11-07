//const Ajv = require("ajv").default
const Ajv = require("ajv/dist/2020.js").default
const fs=require("fs")
const path = require('path')
const ajv = new Ajv({strict: "log", allErrors: true})
const addFormats = require("ajv-formats")
addFormats(ajv)

schemaFilesDirectory = "/Users/wpotter/Documents/GitHub/sinai_metadata/data-model/jsonschemas/"
schemaFileNames = new Array

fs.readdirSync(schemaFilesDirectory).forEach(file => {
  if(path.extname(file) == ".json") {
    schemaFileNames.push(file)
    json = JSON.parse(fs.readFileSync(schemaFilesDirectory+file))
    ajv.addSchema(json, file)
  }
});

data = {
  "ark": "ark:/21198/z1fere",
  "label": "Sinai Test",
  "reconstruction": false,
  "state": {
    "id": "overtext",
    "label": "Overtext"
  },
  "writing": [
    {
      "script": [
        {"id": "syriac", "label": "Syriac", "writing_system": "not a true one"}]
    }
  ],
  "text_unit": [
    {
      "id": "ark:/21198/z1fer",
      "label": "A text"
    }
  ],
  "parent": ["ark:/21198/z1fer"]
}


console.log(ajv.validate("text_unit.json", data))

console.log(JSON.stringify(ajv.errors, null, 2))