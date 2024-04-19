import os
import csv
import re

# Prompt the user to input the directory path where the CSV files are located
directory_path = input("Enter the directory path: ")

# Define regular expression patterns to match "f. " and "Flyleaves "
patterns = [
    (r"(f\.\s*)([^1-9]*)([1-9])", r"\1\3"),  # Pattern for "f. "
    (r"(Flyleaves\s*)([^1-9]*)([1-9])", r"\1\3")  # Pattern for "Flyleaves "
]

# Loop through all CSV files in the directory
for file_name in os.listdir(directory_path):
    if file_name.endswith(".csv"):
        file_path = os.path.join(directory_path, file_name)
        # Open the CSV file for reading and writing
        with open(file_path, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = []
            for row in reader:
                # Apply each pattern to the 'Title' column
                for pattern, replacement in patterns:
                    row['Title'] = re.sub(pattern, replacement, row['Title'])
                rows.append(row)
        # Write the updated rows to the CSV file
        with open(file_path, 'w', newline='') as csvfile:
            fieldnames = reader.fieldnames
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
