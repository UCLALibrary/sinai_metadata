import pandas as pd
import os
import exifread
from pathlib import Path
from pathlib import PureWindowsPath, PurePosixPath

def find_full_path(filename, file_location):
    for root, dirs, files in os.walk(file_location):
        for file in files:
            if filename in file:
                return (os.path.join(root, file)), True
    return ('No match found for ' + str(filename)), False

def make_output_df():
    destination_cols=['File Path','Title', 'Object Type',
                      'Source','Parent ARK', 'Item ARK']
    output_df = pd.DataFrame(columns=destination_cols)
    return output_df

def main():
    #get .csv with filenames to look for
    filename_csv_path = input('Enter the path to the .csv containing file names: ')
    filename_csv = pd.read_csv(filename_csv_path)
    
    #where should we look for files?
    file_location = input('Enter the top-level directory to look for files in: ')

    #create dataframe to use for final .csv output
    output_df = make_output_df()

    #get full list of files in directory, then loop through for the ones we want
    full_filenames = []
    sources = []
    titles = []
    print('Looking for files')
    #keep track of how far we've gotten
    done_counter = 0
    total_files = len(filename_csv['files'])
    old_pct = 0
    for filename in filename_csv['files']:
        full_name, found = find_full_path(filename, file_location)
        full_filenames.append(full_name)
        sources.append(os.path.split(full_name)[0])
        if found:
            img = open(full_name, 'rb')
            tags = exifread.process_file(img)
            title = tags['Image ImageDescription']
            titles.append(title)
        done_counter += 1
        pct_done = done_counter/total_files
        if pct_done > old_pct + .05:
            print(str(round(pct_done *100)) + ' percent done')
        old_pct = pct_done
        


    #add new column values to output dataframe
    output_df['File Path'] = full_filenames
    output_df['Object Type'] = 'page'
    output_df['Source'] = sources
    output_df['Title'] = titles

    print('Outputting results to output_paths.csv')
    output_df.to_csv('output_paths.csv', index=False, na_rep='')

if __name__ == '__main__':
    main()