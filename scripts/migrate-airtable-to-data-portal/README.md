# Instructions for running the script:

## Prequisites

Script requires Pandas module

A CSV file containing the records to be transformed. The required column names are listed in the `*_fields.txt` files, e.g. `ms_obj_fields.txt`

Optionally, CSV files for the reference instances (to create `bib` objects), paracontents (to create `para` objects)

For text units, a CSV file for the work witnesses (to create `work_wit` objects) is required

## Running the Script

run the script from terminal with the following options:

- path to the CSV containing the records (ms obj, layer, text unit)
- one of the following record types: `ms_objs`, `layers`, `text_units`

`$ python migrate-airtable-to-data-portal.py {path-to-csv} {record-type}`

e.g., `$ python migrate-airtable-to-data-portal.py /Users/wpotter/Desktop/SMDP-Migration/csvs/layers.csv layers`

The script will then ask for several additional csvs:
- reference instances (optional, can just press enter to skip if not used)
- paracontents (optional, can just press enter to skip if not used)
- for text units only, it will ask for a work witnesses path, which is required

For each of the csvs that are entered, it will check the column names against those listed in *_fields.txt. It will let you know which columns will be ignored and which it will add as empty. The first lets you know if you spelled a column header wrong; the second is to ensure that Pandas doesn’t cause an error for missing columns.

The script will then check the columns in the main record csv, let you know the variants, and supply empty columns for those that aren’t in the csv. You will have an option to cancel the script at this point if there are column issues to address.

If you want to continue with the transform, the script will prompt for an output directory. The default is to save into an output sub-directory of the script based on the record type: `out/$record-type`

The script will then attempt to create a JSON record for each of the rows based on the selected record type and save it to the output directory, naming the file based on the ARK (e.g. `z11234.json` if ARK is `ark:/21198/z11234`)
