#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pandas as pd
import csv
import os

#This is necessary to pull in long values from Pandas tables
pd.options.display.max_colwidth = 100000

#outputdirectory
newCsvFile = input('csv File Directory: ')
#strip starting and trailing spaces so we can simply drag and drop
newCsvFile = newCsvFile.strip()

topcolumns = ['File Name','Item Sequence','Visibility','Title','IIIF Range','viewingHint','Parent ARK','Item ARK','Object Type','Rights.statementLocal','Source', 'Bucketeer State', 'IIIF Access URL']

for csvFile in os.listdir(newCsvFile):
    if not csvFile.startswith('.'):
        dfWorkbook = []
        newName = os.path.join(newCsvFile,csvFile)
        print(newName)

        dfnew = pd.read_csv(newName)

        for i, row in dfnew.iterrows():
            if 'lcc' not in row[0]:
                dfWorkbook.append(row)
        df = pd.DataFrame(dfWorkbook, columns = topcolumns)
        df.to_csv("{csvFile}".format(csvFile = csvFile),index=False)
