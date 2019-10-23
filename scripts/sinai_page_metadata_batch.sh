#!/usr/local/bin/bash

# Prompt for input, and enter target directory to generate CSVs into and .txt that lists selected MSS to run the script on
echo Path to download directory:
read targetDIR
echo Path to MSS list:
read whichMSS

# read-while loop to enter each subdirectory and iterate over multiple files listed in .txt
while read MS; do
    cd "$MS"
    # Extract image file paths as well as Title and Source info from TIFF header to temporary CSV
    exiftool -csv -Title -Source $PWD > /$targetDIR/${PWD##*/}"_temp1.csv"

    # Sort rows
    sort -k1 -n -t, /$targetDIR/${PWD##*/}"_temp1.csv" > /$targetDIR/${PWD##*/}"_temp2.csv"

    # Remove first 4 rows (sample shots)
    sed -i '' 1,4d /$targetDIR/${PWD##*/}"_temp2.csv"

    # Remove last row (original header, now last after sort)
    sed -i '' '$d' /$targetDIR/${PWD##*/}"_temp2.csv"

    # Remove MS name from Title info and prepend titles of folio images (i.e. _f_) with "f."
    awk 'BEGIN{FS=OFS=","} NF>2 && NR==1{s=$3} {sub("^" s "[[:blank:]]+", "", $2)} $1 ~ /_f_/{$2 = "f. " $2} 1' /$targetDIR/${PWD##*/}"_temp2.csv" >> /$targetDIR/${PWD##*/}"_temp3.csv"

    # Add a sequence column to all rows; add 8 new columns with specified values (and/or none); rearrange column order; add a header with specified values
    awk -F, -v OFS=, '{$4=NR}1' /$targetDIR/${PWD##*/}"_temp3.csv" > /$targetDIR/${PWD##*/}"_temp4.csv" && awk -F"," 'BEGIN { OFS = "," } {$5=""; $6=""; $7=""; $8=""; $9="ChildWork"; $10="copyrighted"; $11="Contact the Monastery of St. Catherine’s of the Sinai. Metadata: Unless otherwise indicated all metadata associated with this manuscript is copyright the authors and released under Creative Commons Attribution 4.0 International License."; $12="discovery"; print}' /$targetDIR/${PWD##*/}"_temp4.csv" > /$targetDIR/${PWD##*/}"_temp5.csv" && awk -F, '{print $1,$4,$12,$2,$5,$6,$7,$8,$9,$10,$11,$3}' OFS=, /$targetDIR/${PWD##*/}"_temp5.csv" > /$targetDIR/${PWD##*/}"_temp6.csv" && { echo 'File Name,Item Sequence,Visibility,Title,IIIF Range,viewingHint,Parent ARK,Item ARK,Object Type,Rights.copyrightStatus,Rights.statementLocal,Source'; cat /$targetDIR/${PWD##*/}"_temp6.csv"; } > /$targetDIR/${PWD##*/}"_temp7.csv"

    # Populate column 5 with specified values according to column 1 and save to output CSV
    awk -F, 'BEGIN{OFS=","}
    $1~/sld_[a-z]{3}[0-9]{4}_[0-9]{4}_f_[0-9]{3}[a-z]*\.tif$/{$5="Text"}
    $1~/sld_[a-z]{3}[0-9]{4}_[0-9]{4}_[a-b]_[0-9]{1,3}[a-z]*\.tif$/{$5="Front matter"}
    $1~/sld_[a-z]{3}[0-9]{4}_[0-9]{4}_y_[0-9]{1,3}[a-z]*\.tif$/{$5="Back matter"}
    $1~/sld_[a-z]{3}[0-9]{4}_[0-9]{4}_z_1[a-z]*\.tif$/{$5="Back matter"}
    1' /$targetDIR/${PWD##*/}"_temp7.csv" > /$targetDIR/${PWD##*/}".csv"

    # Delete all temporary CSVs
    rm /$targetDIR/${PWD##*/}"_temp1.csv" /$targetDIR/${PWD##*/}"_temp2.csv" /$targetDIR/${PWD##*/}"_temp3.csv" /$targetDIR/${PWD##*/}"_temp4.csv" /$targetDIR/${PWD##*/}"_temp5.csv" /$targetDIR/${PWD##*/}"_temp6.csv" /$targetDIR/${PWD##*/}"_temp7.csv"

    # Come back out of current subdirectory to restart loop
    cd ..
done <$whichMSS
