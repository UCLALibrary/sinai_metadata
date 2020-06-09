#!/usr/bin/env python
# -*- coding: utf-8 -*-
#REMEMBER to install pandas on your ptyon; pip3 install pandas
import pandas as pd
import re
import csv

#the workbook file
workbookfileInput = input('Workbook File (from EMEL):')
#strip starting and trailing spaces so we can simply drag and drop
workbookfileInput = workbookfileInput.strip()
worksfileInput = input('Works File (template to update):')
#strip starting and trailing spaces so we can simply drag and drop
worksfileInput = worksfileInput.strip()
genresfileInput = input('Genres File (from airtables export):')
#strip starting and trailing spaces so we can simply drag and drop
genresfileInput = genresfileInput.strip()
outputfileName = input('Final Works Table File Name:')
#strip starting and trailing spaces so we can simply drag and drop
outputfileName = outputfileName.strip()

#laod the workbooks into dataframes for manipulation
workbookdf = pd.read_csv(workbookfileInput)
worksdf = pd.read_csv(worksfileInput)
genresdf = pd.read_csv(genresfileInput)

#strip out whitespace in column names so we can call columns
workbookdf = workbookdf.rename(columns=lambda x: x.strip())
worksdf = worksdf.rename(columns=lambda x: x.strip())
genresdf = genresdf.rename(columns=lambda x: x.strip())

#setup some helper columns so we can update the works csv.
#Also changing types, filling in blanks with nulls, and otherwise making thing work.

#We need to match on something, so we need to create a Shelfmark column to match on unique values
worksdf["Shelfmark"]= worksdf["Title"].str.split(".", n = 0, expand = True)[0]

#remove the word Sinai so we can match on shelf marks
p = re.compile(r'Sinai')
worksdf["Shelfmark"]  = [p.sub('', x) for x in worksdf['Shelfmark']]

#just to make error checking and all of that easier, we are going to move the column to the front. We will drop this later
#a little overkill to be sure, but it does make things eaiser to read
Shelfmark = worksdf['Shelfmark']
worksdf.drop(labels=['Shelfmark'], axis=1,inplace = True)
worksdf.insert(0, 'Shelfmark', Shelfmark)

# Fill in values that would otherwise stop the merging
workbookdf["Height"] = workbookdf["Height"].fillna(0)
workbookdf["Width"] = workbookdf["Width"].fillna(0)
workbookdf["Thickness"] = workbookdf["Thickness"].fillna(0)

#clean up comma separated cells to have the |~| convention
workbookdf["Language"] = workbookdf["Language"].str.replace('/','|~|')


#Putting together the values that are displayed in the website. These almost certainly should be their own columns in the future
workbookdf['Format.dimensions'] = workbookdf["Height"].astype(int).astype(str) +' x '+ workbookdf["Width"].astype(int).astype(str) +' x '+ workbookdf["Thickness"].astype(int).astype(str) +' mm'
workbookdf["Folia"] = workbookdf["Folia"].astype(pd.Int32Dtype())
workbookdf['Format.extent'] = workbookdf["Folia"].astype(str) +' ff. ; '+ workbookdf["Weight (g)"].astype(str) +' g'
workbookdf['Support'] = workbookdf["Material"]
workbookdf['Format'] = workbookdf["Form"]
workbookdf['General note'] = workbookdf["Comments"]

#populate the genres table with the correctly formatted text and remove any trailing commas
genresdf["Genres (Kamil)"] = genresdf["Genres (Kamil)"].str.replace(',','|~|')

genresdf["Genres (Kamil)"] = genresdf["Genres (Kamil)"].fillna('')

#genresdf["Add. Genres (Kamil)"] = genresdf["Add. Genres (Kamil)"].fillna('')
genresdf['Type.genre'] = genresdf["Genres (Kamil)"].astype(str) #+','+ genresdf["Add. Genres (Kamil)"].astype(str)
genresdf['Type.genre'] = genresdf['Type.genre'].str.replace(r'.$', '')

# a new datatable to store only the columns we want
workbookdfMerge = pd.DataFrame()

#now to grab the columns we want from the workbook dataframe
workbookdfMerge = workbookdf[['Shelfmark', 'Format.dimensions','Format.extent','Format', 'Support','Language', 'Camera Operator', 'General note']].copy()

#update our old table
worksdf.update(workbookdfMerge)
worksdf.update(genresdf)

#drop the added table
worksdf.drop(labels=['Shelfmark'], axis=1,inplace = True)

worksdf["References"] = worksdf["References"].str.replace(',','|~|')


#export the result
worksdf.to_csv('{outputfileName}'.format(outputfileName =outputfileName), quoting=csv.QUOTE_ALL, index=False)
