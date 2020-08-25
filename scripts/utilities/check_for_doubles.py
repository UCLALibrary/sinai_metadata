#!/usr/bin/env python
# -*- coding: utf-8 -*-
import csv
import os
from pathlib import Path
from operator import itemgetter
from collections import Counter

csvDirectory = input('CSV Directory: ')
#strip starting and trailing spaces so we can simply drag and drop
csvDirectory = csvDirectory.strip()

columnNum = input('Column Number to check for duplicates (7 for SLDP): ')
#strip starting and trailing spaces so we can simply drag and drop
columnNum = columnNum.strip()
columnInt = int(columnNum)
key = itemgetter(columnInt)

for csvFile in os.listdir(csvDirectory):
    finalList = []
    newName = os.path.join(csvDirectory,csvFile)
    if not csvFile.startswith('.'):
        with open(newName) as f:
            c = Counter(key(row) for row in csv.reader(f))
            dups = [t for t in c.most_common() if t[1] > 1]
            if len(dups) > 0:
                textout = '{csvFile}: {dups}'.format(csvFile = csvFile, dups = dups)
                print(textout)
                finalList.append(textout)
    if len(finalList) > 0:
        with open('{csvFile}_dupes.txt'.format(csvFile = csvFile), 'w') as filehandle:
            for listitem in finalList:
                filehandle.write('{listitem}\n'.format(listitem = listitem))
