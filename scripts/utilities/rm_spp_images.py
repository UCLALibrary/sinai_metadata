import json
import csv

def load_csv(csv_file):
    labels = []
    try:
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                label = row.get('File name cleanup', '').strip()
                if label:
                    labels.append(label)
    except FileNotFoundError:
        print(f"Error: CSV file '{csv_file}' not found.")
    except Exception as e:
        print(f"Error loading CSV file '{csv_file}': {e}")
    
    return labels

def load_json(json_file):
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        return manifest
    except FileNotFoundError:
        print(f"Error: JSON file '{json_file}' not found.")
    except Exception as e:
        print(f"Error loading JSON file '{json_file}': {e}")
    return None

def write_json(json_file, data):
    try:
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"Updated manifest: {json_file}")
    except Exception as e:
        print(f"Error writing JSON file '{json_file}': {e}")

def process_manifest(csv_labels, manifest):
    try:
        items = manifest.get('item', [])
        filtered_items = [item for item in items if item.get('label') not in csv_labels]
        manifest['item'] = filtered_items
        return manifest
    except Exception as e:
        print(f"Error processing manifest: {e}")
    return None

def main():
    csv_file = input("Enter path to CSV file: ").strip()
    json_file = input("Enter path to JSON manifest file: ").strip()

    csv_labels = load_csv(csv_file)
    if not csv_labels:
        return

    manifest = load_json(json_file)
    if not manifest:
        return

    modified_manifest = process_manifest(csv_labels, manifest)
    if modified_manifest:
        write_json(json_file, modified_manifest)

    print("Manifest processing complete.")

if __name__ == "__main__":
    main()
