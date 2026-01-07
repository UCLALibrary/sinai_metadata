//const Ajv = require("ajv").default
const Ajv = require("ajv/dist/2020.js").default
const fs=require("fs")
const path = require('path')
const ajv = new Ajv({strict: "log", allErrors: true})
const addFormats = require("ajv-formats")
addFormats(ajv)

schemaFilesDirectory = "/Users/wpotter/Documents/GitHub/sinai_metadata/scripts/dataportal-schema-bundle/schemas/"
schemaFileNames = new Array

fs.readdirSync(schemaFilesDirectory).forEach(file => {
  if(path.extname(file) == ".json") {
    schemaFileNames.push(file)
    json = JSON.parse(fs.readFileSync(schemaFilesDirectory+file))
    console.log("Adding schema to Ajv")
    console.log(file)
    ajv.addSchema(json, file)
  }
});

data = {
  "ark": "ark:/21198/te5f0f9b",
  "type": {
    "id": "building",
    "label": "Building"
  },
  "pref_name": "Library of St. Catherine's Monastery",
  "geojson": [{
    "type": "Feature",
    "geometry": {
      "type": "Point",
      "coordinates": [125.6, 10.1]
    },
    "properties": {
      "name": "Dinagat Islands"
    }
  }]
}


console.log(ajv.validate("place.json", data))

console.log(JSON.stringify(ajv.errors, null, 2))