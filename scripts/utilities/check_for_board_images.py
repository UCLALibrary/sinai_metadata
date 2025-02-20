import glob, csv, os

"""
- parse recursively metadata csvs
- get the source
- if any of the rows contain "Board" in Title, mark as true; maybe mark front and back sep?
- return shelfmark, parent ark = ms ark, t/f for the boards
- 
"""

DIRECTORY_PATH = "/Users/wpotter/Documents/GitHub/sinai_metadata/metadata_csvs/"
OUTPUT_DIR =  "/Users/wpotter/Documents/GitHub/sinai_metadata/scripts/utilities/out/"

filenames = glob.glob(DIRECTORY_PATH+"sinai_*/*")

manuscripts = []

for name in filenames:
    if name.endswith(".csv"):
        with open(name) as f:
            reader = csv.DictReader(f)
            shelfmark = ""
            ark = ""
            has_front_board_images = False
            has_back_board_images = False
            for row in reader:
                shelfmark = row["Source"]
                ark = row["Parent ARK"]
                # if board images not yet found, check if in this row
                if not(has_front_board_images):
                    has_front_board_images = "Front Board" in row["Title"]
                if not(has_back_board_images):
                        has_back_board_images = "Front Board" in row["Title"]
            manuscripts.append(
                {
                    "shelfmark": shelfmark,
                    "ark": ark,
                    "front_board": has_front_board_images,
                    "back_board": has_back_board_images
                }
            )

if not(os.path.exists(OUTPUT_DIR)):
     os.makedirs(OUTPUT_DIR)

with open(OUTPUT_DIR + "board_image_status.csv", "w+", newline='') as csvout:
     fieldnames = list(manuscripts[0].keys())
     writer = csv.DictWriter(csvout, fieldnames=fieldnames)
     writer.writeheader()
     for ms in manuscripts:
          writer.writerow(ms)