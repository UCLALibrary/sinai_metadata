import pandas as pd

# Load the CSV files into dataframes
df1 = pd.read_csv("file1.csv")
df2 = pd.read_csv("file2.csv")

# Merge the dataframes using the "filename" column as a key
merged_df = pd.merge(df1, df2, on="key", how="outer")

# Write the merged dataframe to a new CSV file
merged_df.to_csv("merged.csv", index=False)
