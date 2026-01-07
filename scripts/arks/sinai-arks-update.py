import csv
import os
import requests
import argparse
from getpass import getpass

ERC_WHO = "Sinai Manuscripts Data Portal"

def update_ark_metadata(auth, ark, what, when, dry_run=False):
    data = {
        "_profile": "erc",
        "erc.who": ERC_WHO,
    }

    if what:
        data["erc.what"] = what
    if when:
        data["erc.when"] = when

    if dry_run:
        print(f"[DRY RUN] Would update {ark} with:")
        for k, v in data.items():
            print(f"  {k}: {v}")
        return

    url = f"https://ezid.cdlib.org/id/{ark}"
    headers = {
        "Content-Type": "text/plain; charset=UTF-8",
    }

    data_encoded = "\n".join(f"{k}: {v}" for k, v in data.items()).encode("utf-8")

    response = requests.post(
        url,
        headers=headers,
        data=data_encoded,
        auth=auth,
    )

    if response.status_code not in (200, 201):
        print(f"ERROR updating {ark}: {response.status_code}")
        print(response.text)
    else:
        print(f"Updated {ark}")

def main():
    parser = argparse.ArgumentParser(
        description="Update ERC metadata for existing ARKs in a CSV"
    )
    parser.add_argument("csv", help="Input CSV file")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print updates without sending them to EZID",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.csv):
        print(f"Error: The file '{args.csv}' does not exist.")
        return

    auth_input = getpass("Enter EZID credentials (username:password): ").strip()

    if ":" not in auth_input:
        print("Error: credentials must be in the form username:password")
        return

    username, password = auth_input.split(":", 1)
    auth = (username, password)

    with open(args.csv, mode="r", newline="", encoding="utf-8-sig") as infile:
        reader = csv.DictReader(infile)

        required_fields = {"ARK", "Name", "Dates"}
        missing = required_fields - set(reader.fieldnames or [])
        if missing:
            print(f"Missing required columns: {', '.join(missing)}")
            return

        for row in reader:
            ark = row.get("ARK")
            what = row.get("Name")
            when = row.get("Dates")

            if not ark:
                continue

            update_ark_metadata(auth, ark, what, when, dry_run=args.dry_run)

    print("Completed ERC metadata updates.")

if __name__ == "__main__":
    main()
