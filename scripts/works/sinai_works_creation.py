#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import re
import csv
import os
from pathlib import Path

#This is necessary to pull in long values from Pandas tables
pd.options.display.max_colwidth = 100000

def make_ordinal(n):
    n = int(n)
    suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    return str(n) + suffix

def centuryFromYear(year):
    return (year) // 100 + 1    # 1 because 2017 is 21st century, and 1989 = 20th century

#replaces text markup that we do not need
def sinaiWorkbookTextReplace (text):
    text = text.replace('[', '')
    text = text.replace(']', '')
    text = text.replace("('", '')
    text = text.replace("',)", '')
    text = text.replace(', ', ';')
    finalText = text
    return finalText

def sinaiDelimReplace (text):
    text = text.replace(', ', ';')
    finalText = text
    return finalText


imgDirectory = input('Directory that contains the delivery images: ')
#strip starting and trailing spaces so we can simply drag and drop
imgDirectory = imgDirectory.strip()

pwork = False
progressWorkbook = input('Progress Workbook: ')
#strip starting and trailing spaces so we can simply drag and drop
progressWorkbook = progressWorkbook.strip()
if progressWorkbook:
    pwork = True

batchNum = input('Batch Number: ')
batchNum = batchNum.strip()

if progressWorkbook:
    workbookdf = pd.read_csv(progressWorkbook, na_filter=False)
    #strip out whitespace in column names so we can call columns
    workbookdf = workbookdf.rename(columns=lambda x: x.strip())

    #strip out whitespace in column names so we can call columns
    workbookdf = workbookdf.rename(columns=lambda x: x.strip())
    #remove blank rows and fix NaN issues. Should not be a problem with the old workbook
    workbookdf['Shelfmark'].replace('', np.nan, inplace=True)
    workbookdf.dropna(subset=['Shelfmark'], inplace=True)
    workbookdf = workbookdf.fillna('')

    # Fill in values that would otherwise stop the merging
    workbookdf["Height"] = workbookdf["Height"].fillna(0)
    workbookdf["Width"] = workbookdf["Width"].fillna(0)
    workbookdf["Thickness"] = workbookdf["Thickness"].fillna(0)

    #clean up comma separated cells to have the |~| convention
    workbookdf["Language"] = workbookdf["Language"].str.strip()
    #there may be some spaces inbeteween the different languages, yet still spaces in each entry....
    workbookdf["Language"] = workbookdf["Language"].str.replace(' / ',';')

    #Putting together the values that are displayed in the website. These almost certainly should be their own columns in the future
    workbookdf['Format.dimensions'] = workbookdf["Height"].astype(int).astype(str) +' x '+ workbookdf["Width"].astype(int).astype(str) +' x '+ workbookdf["Thickness"].astype(float).astype(str) +' mm'
    workbookdf["Folia"] = workbookdf["Folia"].str.strip()
    workbookdf['Support'] = workbookdf["Material"]
    workbookdf['Format'] = workbookdf["Form"]

#create the main dataframe
dfWorkbook = pd.DataFrame(columns=['Title',
'Item ARK',
'Object Type',
'Date.normalized',
'Date.creation',
'Format.extent',
'Format.weight',
'Format',
'Format.dimensions',
'Support',
'Language',
'AltIdentifier.local',
'delivery',
'Comments',
'User Comments'])


#strip out whitespace in column names so we can call columns
dfWorkbook = dfWorkbook.rename(columns=lambda x: x.strip())

#set the dataframe constants; this can be modified for a different project (or even better made a config)
parentArk = 'ark:/21198/z1bk2gmg'
viewingHint = 'paged'
Visibility = 'sinai'
typeOfResource = 'text'
Rights_statementLocal = "Images: Contact the Monastery of St. Catherine's of the Sinai. Metadata: Unless otherwise indicated all metadata associated with this manuscript is copyright the authors and released under Creative Commons Attribution 4.0 International License."
Rights_contact = "To inquire about image rights, contact St. Catherine's Monastery, https://www.sinaimonastery.com, sinaimonastery@gmail.com."
Name_repository = "Saint Catherine (Monastery : Mount Sinai)"
Collection_physical = "Sinai. Old Collection"
originator = "Statement of responsibility: Imaging performed under the auspices of His Eminence Archbishop Damianos and The Holy Council, Father Justin Sinaites Librarian, Early Manuscripts Electronic Library. Phelps Michael B. Project Director; Kasotakis Damianos. Imaging Director"
objectType = 'Work'

if imgDirectory:
    imglister = os.listdir(imgDirectory)
    for workentryName in imglister:
        splitlist = workentryName.split('_')
        splitlistresult = [ele.lstrip('0') for ele in splitlist]
        splitlistresultCaps = [ele.upper() for ele in splitlistresult]
        shelftitle = str(splitlistresultCaps[0].title())
        shelfend = splitlistresultCaps[1:]
        shelfend = ' '.join(shelfend)
        shelfmark = shelftitle + ' ' + shelfend
        print(shelfmark)
        if progressWorkbook:
            workbookRow = workbookdf.loc[workbookdf['Shelfmark'].str.lower().isin([shelfmark.lower()])]

            if workbookRow["Date In"].to_string(index=False).strip() == workbookRow["Date Out"].to_string(index=False).strip():
                Date_normalized = workbookRow["Date In"].to_string(index=False).strip()
                humandate = Date_normalized
            else:
                Date_normalized = workbookRow["Date In"].to_string(index=False).strip()
                Date_normalized = Date_normalized + '/'
                Date_normalized = Date_normalized + workbookRow["Date Out"].to_string(index=False).strip()
                humandatestart = int(workbookRow["Date In"].to_string(index=False).strip())
                humandatestart = centuryFromYear(humandatestart)
                humandatestart = make_ordinal(humandatestart)
                humandate = humandatestart + ' c.'
        else:
            Date_normalized = ''
            humandate = ''
            if row:
                Date_normalized = row['Date.normalized']
                humandatestart = row['Date.normalized'].split('/')
                if len(humandatestart) > 1:
                    humandatestart = centuryFromYear(int(humandatestart[0]))
                    humandatestart = make_ordinal(humandatestart)
                    humandate = humandatestart + ' c.'
                else:
                    humandate = humandatestart[0]



        localTitle = 'Sinai ' + shelfmark
        if progressWorkbook:
            print('Updating with Progress Notebook')

            formatExtentValue = workbookRow['Folia'].to_string(index=False).strip()
            formatExtentValue = formatExtentValue +' ff.'
            formatExtentValue = sinaiWorkbookTextReplace(formatExtentValue)
            formatWeightValue = workbookRow['Weight (g)'].to_string(index=False).strip()
            formatWeightValue = formatWeightValue +' g'
            formatValue =  workbookRow['Format'].to_string(index=False).strip()
            formatValue = sinaiWorkbookTextReplace(formatValue)
            formatDimensionsValue =  workbookRow['Format.dimensions'].to_string(index=False).strip()
            formatDimensionsValue = sinaiWorkbookTextReplace(formatDimensionsValue)
            supportValue = workbookRow['Support'].to_string(index=False).strip()
            supportValue = sinaiWorkbookTextReplace(supportValue)
            languageValue = workbookRow['Language'].to_string(index=False).strip()
            languageValue = sinaiDelimReplace(languageValue)
            commentsValue = workbookRow['Comments'].to_string(index=False).strip()
            userCommentsValue = workbookRow['User Comments'].to_string(index=False).strip()

        else:
            print("error with workbook")

        #populate the workbook
        new_row = {
               'Title': localTitle.rstrip('\r\n'),
               'Item ARK':'',
               'Object Type':objectType.rstrip('\r\n'),
               'Date.normalized': Date_normalized.rstrip('\r\n'),
               'Date.creation':humandate.rstrip('\r\n'),
               'Format.extent': formatExtentValue.rstrip('\r\n'),
               'Format.weight': formatWeightValue.rstrip('\r\n'),
               'Format': formatValue.lower().rstrip('\r\n'),
               'Format.dimensions': formatDimensionsValue.rstrip('\r\n'),
               'Support': supportValue.rstrip('\r\n'),
               'Language': languageValue.rstrip('\r\n'),
               'AltIdentifier.local':localTitle.rstrip('\r\n'),
               'delivery': batchNum.rstrip('\r\n'),
               'Comments': commentsValue.rstrip('\r\n'),
               'User Comments': userCommentsValue.rstrip('\r\n')
              }

        dfWorkbook = dfWorkbook.append(new_row, ignore_index=True)

dfWorkbook.to_csv("works{batchNum}.csv".format(batchNum = batchNum), quoting=csv.QUOTE_ALL, index=False, line_terminator='\n', encoding='utf-8')
