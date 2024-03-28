import os
import csv
import re

# Prompt the user to input the directory path where the CSV files are located
directory_path = input("Enter the directory path: ")

# Define a regular expression pattern to match "f. " followed by anything up to the first number between 1 and 9
fpattern = r"(f\.\s*)([^1-9]*)([1-9])"
flyleafpattern = r"(Flyleaf\s*) ([^1-9]*)([1-9])"

# Loop through all CSV files in the directory
for file_name in os.listdir(directory_path):
    if file_name.endswith(".csv"):
        file_path = os.path.join(directory_path, file_name)
        # Open the CSV file for reading and writing
        with open(file_path, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = []
            for row in reader:
                # Remove anything between "f. " and the first number between 1 and 9 in the 'Title' column
                row['Title'] = re.sub(fpattern, r"\1\3", row['Title'])
                row['Title'] = re.sub(flyleafpattern, r"\1\3", row['Title'])
                rows.append(row)
        # Write the updated rows to the CSV file
        with open(file_path, 'w', newline='') as csvfile:
            fieldnames = reader.fieldnames
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
