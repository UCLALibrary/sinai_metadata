import os
import csv

def find_csv_with_empty_title(dir_path):
    with open('no-titles.csv', 'w', newline='') as no_titles_file:
        writer = csv.writer(no_titles_file)
        writer.writerow(['File Name'])

        empty_title_files = set()
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                if file.endswith('.csv'):
                    csv_path = os.path.join(root, file)
                    if csv_path in empty_title_files:
                        continue
                    with open(csv_path, 'r') as csv_file:
                        reader = csv.reader(csv_file)
                        header = next(reader, None)
                        if header is None or 'Title' not in header:
                            continue
                        title_col_index = header.index('Title')
                        empty_title_found = False
                        for row in reader:
                            if len(row) > title_col_index and not row[title_col_index].strip():
                                empty_title_found = True
                                break
                        if empty_title_found:
                            writer.writerow([csv_path])
                            empty_title_files.add(csv_path)

if __name__ == '__main__':
    dir_path = input('Enter directory path: ')
    find_csv_with_empty_title(dir_path)
