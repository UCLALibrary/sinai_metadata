import pandas as pd
import os
import exifread
from pathlib import Path

def get_candidate_files(file_location):
    '''Starting at file_location, return list of all files in subdirectories.'''
    file_list = []
    for root, dirs, files in os.walk(file_location):
        for file in files:
            file_list.append(os.path.join(root, file))
    return file_list

def find_full_path(filename, file_list):
    '''Given file name and full file list, find matches'''
    for file in file_list:
        if filename in file:
            return (file), True
    return ('No match found for ' + str(filename)), False

def make_output_df():
    '''Create empty pandas DF to put metadata in'''
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

    #get full list of files in directory ahead of time
    full_filenames = []
    sources = []
    titles = []
    print('Getting directory files')
    candidate_files = get_candidate_files(file_location)
    print('Found ' + str(len(candidate_files)) + ' candidate files')

    #get file names from csv
    files_to_find = filename_csv['files']
    print('Finding matches for ' + str(len(files_to_find)) + ' desired files')
    #variables for tracking % completion
    done_counter = 0
    old_pct = 0
    #main loop: iterate through desired filenames to find paths
    for filename in files_to_find:
        #find paths using helper function, add to list
        full_name, found = find_full_path(filename, candidate_files)
        full_filenames.append(full_name)
        #for found items, add TIFF metadata and source column (folder path)      
        if found:
            img = open(full_name, 'rb')
            tags = exifread.process_file(img)
            title = tags['Image ImageDescription']
            titles.append(title)
            sources.append(os.path.split(full_name)[0])
        #for non-found items, add dummy metadata to keep rows aligned
        else:
            titles.append("File not found")
            sources.append()
        #counter logic: calculate new % done, print if we've reached a new 5%
        done_counter += 1
        pct_done = done_counter/len(files_to_find)
        if pct_done > old_pct + .05:
            print(str(round(pct_done *100)) + ' percent done')
            old_pct = pct_done
        
    #add new column values to output dataframe
    output_df['File Path'] = full_filenames
    output_df['Object Type'] = 'page' #constant for now
    output_df['Source'] = sources
    output_df['Title'] = titles

    print('Outputting results to output_paths.csv')
    output_df.to_csv('output_paths.csv', index=False, na_rep='')

if __name__ == '__main__':
    main()