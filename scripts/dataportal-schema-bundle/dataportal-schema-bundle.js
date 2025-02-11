import $RefParser from "@apidevtools/json-schema-ref-parser";
import * as fs from 'fs';
import * as path from 'path';

/* Schema Base file path */
const schemaLocationsLocal = 'data-model/jsonschemas/';

const schemaOutputDirectory = 'scripts/dataportal-schema-bundle/out/';

/* CHANGE FILE NAMES AS NEEDED */
const schemaFileNames = 
{
  "msObj": "ms_obj.json",
  "layer": "layer.json",
  "textUnit": "text_unit.json",
  "agent": "agent.json",
  "place": "place.json",
  "work": "work.json"
};

//helper function to recursively make missing directories in writing files
function writeFile(filePath, contents, cb) {
  fs.mkdir(path.dirname(filePath), { recursive: true}, function (err) {
    if (err) return cb(err);

    fs.writeFile(filePath, contents, cb);
  });
}

try {
  for (let schema in schemaFileNames) {
    //dereference each schema specified in the schemaFileNames dictionary
    let schemaPath = schemaLocationsLocal + schemaFileNames[schema];
    let bundled_schema = await $RefParser.dereference(schemaPath);

    //put the bundled schema in an output directory named '$SCHEMA-NAME.schema.json'
    let outputPath = schemaOutputDirectory + schemaFileNames[schema].substring(0, schemaFileNames[schema].length-4) + 'schema.json'
    writeFile(outputPath, JSON.stringify(bundled_schema, null, 2), (error) => {
      if (error) {
        console.log('An error has occurred ', error);
        return;
      }
      console.log('Data written successfully to disk: ' + outputPath);
    })
  }
} catch (err) {
  console.error(err);
}