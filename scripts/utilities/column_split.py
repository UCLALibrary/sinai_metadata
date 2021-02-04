#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import re
import csv
import os
from pathlib import Path

csvFileRead = input('File: ')
#strip starting and trailing spaces so we can simply drag and drop
csvFileRead = csvFileRead.strip()

csvSplitCat = input('Column to split: ')
#strip starting and trailing spaces so we can simply drag and drop
csvSplitCat = csvSplitCat.strip()

data = pd.read_csv(csvFileRead, na_filter=False)

for i, x in data.groupby(csvSplitCat):
    p = os.path.join(os.getcwd(), "{}.csv".format(i.rsplit('/', 1)[-1]))
    x.to_csv(p, index=False)
