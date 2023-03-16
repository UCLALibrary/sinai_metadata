import os
import pandas as pd

# Set the folder path where the CSVs are located
folder_path = "/Users/kirschbombe/Sites/sinai_metadata/metadata_csvs"

# Create an empty dataframe to store the filtered rows
filtered_df = pd.DataFrame()

# Recursively loop through the folder and subfolders
for root, dirs, files in os.walk(folder_path):
    for filename in files:
        if filename.endswith(".csv"):
            # Load the CSV file into a dataframe
            df = pd.read_csv(os.path.join(root, filename))

            # Filter out rows with no value in the "Title" column
            no_title_df = df[df["Title"].isna()]

            # Append the filtered rows to the overall filtered dataframe
            filtered_df = filtered_df.append(no_title_df, ignore_index=True)

# Write the filtered dataframe to a new CSV file
filtered_df.to_csv("no_title_rows.csv", index=False)

