import csv
import os
import requests
import argparse
from getpass import getpass

# Function to mint an ARK using the ERC profile
def mint_ark(auth, shoulder, what, when, dry_run=False):
    url = f"https://ezid.cdlib.org/shoulder/{shoulder}"
    headers = {
        "Content-Type": "text/plain; charset=UTF-8",
    }
    data = {
        "_profile": "erc",
        "erc.who": "Sinai Manuscripts Data Portal",
        "erc.what": what,
        "erc.when": when,
    }

    if dry_run:
        print(f"[DRY RUN] Would mint ARK on shoulder {shoulder} with:")
        for k, v in data.items():
            print(f"  {k}: {v}")
        return None

    data_encoded = "\n".join(f"{k}: {v}" for k, v in data.items()).encode("utf-8")

    response = requests.post(
        url,
        headers=headers,
        data=data_encoded,
        auth=auth,
    )

    if response.status_code == 201:
        ark = response.text.strip()
        if ark.startswith("success: "):
            return ark[len("success: "):].strip()
        return ark
    else:
        print(f"Error minting ARK: {response.status_code} - {response.text}")
        print(f"Data sent: {data}")
        return None

def main():
    parser = argparse.ArgumentParser(
        description="Mint ARKs for rows missing ARKs and write them to a new CSV"
    )
    parser.add_argument("csv", help="Input CSV file")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be minted without calling EZID",
    )
    args = parser.parse_args()

    input_csv = args.csv

    if not os.path.isfile(input_csv):
        print(f"Error: The file '{input_csv}' does not exist.")
        return

    base_name, ext = os.path.splitext(input_csv)
    output_csv = f"{base_name}-arks{ext}"

    shoulder = input("Enter ARK shoulder (e.g., ark:/21198/s1): ").strip()

    auth_input = getpass("Enter EZID credentials (username:password): ").strip()
    if ":" not in auth_input:
        print("Error: credentials must be in the form username:password")
        return

    username, password = auth_input.split(":", 1)
    auth = (username, password)

    with open(input_csv, mode="r", newline="", encoding="utf-8-sig") as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames or []

        if "ARK" not in fieldnames:
            fieldnames.append("ARK")

        rows = list(reader)

    with open(output_csv, mode="w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            existing_ark = row.get("ARK")
            what = row.get("Name")
            when = row.get("Dates")

            if not existing_ark:
                full_ark = mint_ark(
                    auth,
                    shoulder,
                    what,
                    when,
                    dry_run=args.dry_run,
                )
                if full_ark:
                    row["ARK"] = full_ark
            else:
                row["ARK"] = existing_ark

            writer.writerow(row)

    print(f"Completed. Output saved to {output_csv}")

if __name__ == "__main__":
    main()
