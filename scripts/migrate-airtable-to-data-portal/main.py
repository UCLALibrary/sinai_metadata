import transform
import argparse
import json

parser = argparse.ArgumentParser()

#TBD: make these arguments mutually exclusive
parser.add_argument("-i", "--interactive", help="run the script in interactive mode, allowing it to prompt you for configurations", action="store_true")
parser.add_argument("-c", "--config", help="Specify a path to a config JSON file")

args = parser.parse_args()


if args.interactive:
    transform.user.set_config_interactive()
else:
    transform.user.set_config_from_file(args.config)
    print("Initializing configuration variables")

for i, row in transform.config.main_csv["data"].iterrows():
    record = transform.transform_row_to_json(row, transform.config.record_type)
    ark = str(row["Item ARK"])
    filename = ark.split("/")[2]
    filepath = f'{transform.config.output_directory}/{filename}.json'
    with open(filepath, 'w+') as f:
        json.dump(record, f, ensure_ascii=False, indent=4)
        print("File saved to " + filepath)
