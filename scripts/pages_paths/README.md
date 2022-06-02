This script takes as input a .csv file containing file names to look for and a top-level directory name. 
The top-level directory will be searched recursively to locate all files named in the .csv.
Results will be output to a new file, output_paths.csv, located in the directory where the script was initiated.

Instructions to run the script:
1. Install dependencies (first-time setup only)
    ```
    pip install pandas
    pip install exifread
    ```
2. Initiate script:
    ```
    python3 pages_paths.py
    ```

3. When prompted, provide the full path to the input .csv file:
    ```
    Enter the path to the .csv containing file names: C:\file\path\to\my.csv
    ```

    NOTE: do not include quotation marks around file path.

4. When prompted, provide the full path to the top-level directory you wish to search:
    ```
    Enter the top-level directory to look for files in: \\example\path
    ```

5. Wait for script to run - this may take a while. You will see a new line printed to terminal for every 5% completion.

6. Review the script output in ```output_paths.csv```.