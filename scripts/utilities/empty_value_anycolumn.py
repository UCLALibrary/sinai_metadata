import os
import pandas as pd

# Take the folder path and column to search for as inputs
folder_path = input("Enter the folder path: ")
column_name = input("Enter the column name to search for: ")

# Create an empty dataframe to store the filtered rows
filtered_df = pd.DataFrame()

# Recursively loop through the folder and subfolders
for root, dirs, files in os.walk(folder_path):
    for filename in files:
        if filename.endswith(".csv"):
            # Load the CSV file into a dataframe
            df = pd.read_csv(os.path.join(root, filename))

            # Filter out rows with no value in the specified column
            no_value_df = df[df[column_name].isna()]

            # Append the filtered rows to the overall filtered dataframe
            filtered_df = filtered_df.append(no_value_df, ignore_index=True)

# Write the filtered dataframe to a new CSV file
filtered_df.to_csv("no_value_rows.csv", index=False)
