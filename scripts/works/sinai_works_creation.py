#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import re
import csv
import os
from pathlib import Path
from airtable import Airtable

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
    text = text.replace(', ', '|~|')
    finalText = text
    return finalText

def sinaiDelimReplace (text):
    text = text.replace(', ', '|~|')
    finalText = text
    return finalText

base_key = 'appBjMUh5e1Dgqj6p'

allAirTableName = 'Old Collection mss'
genresTableName = 'Genres'
referencesTableName = 'References'
featuresTableName = 'Features'
languagesTableName = 'Languages'
writingsysTableName = 'Writing systems'
scriptsTableName = 'Scripts'
formTableName = 'Form'
supportTableName = 'Support'
namesTableName = 'Names'
uniformtitlesTableName = 'Uniform titles'

personal_key = 'keyaMF47wU6DgwfO8'

print('Building from Airtables...')
allAirTable = Airtable(base_key, allAirTableName, personal_key)
NamesAirTable = Airtable(base_key, namesTableName, personal_key)
UniformTitlesAirTable = Airtable(base_key, uniformtitlesTableName, personal_key)


allAirRecords = allAirTable.get_all()
allAirdf = pd.DataFrame.from_records((r['fields'] for r in allAirRecords))

imgDirectory = input('Image Directory (blank if you are updating): ')
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

#clean up the airtable incase there are strange errors in the data, extra spaces, etc
allAirdf['Shelfmark'].replace('', np.nan, inplace=True)
allAirdf.dropna(subset=['Shelfmark'], inplace=True)
allAirdf = allAirdf.fillna('')
allAirdf['Author'] = allAirdf['Author'].astype(str)
allAirdf['Author'] = allAirdf['Author'].fillna('')
allAirdf['Uniform title'] = allAirdf['Uniform title'].astype(str)
allAirdf['Uniform title'] = allAirdf['Uniform title'].fillna('')
allAirdf['Scribe'] = allAirdf['Scribe'].astype(str)
allAirdf['Scribe'] = allAirdf['Scribe'].fillna('')



if progressWorkbook:
    # Fill in values that would otherwise stop the merging
    workbookdf["Height"] = workbookdf["Height"].fillna(0)
    workbookdf["Width"] = workbookdf["Width"].fillna(0)
    workbookdf["Thickness"] = workbookdf["Thickness"].fillna(0)

    #clean up comma separated cells to have the |~| convention
    workbookdf["Language"] = workbookdf["Language"].str.strip()
    #there may be some spaces inbeteween the different languages, yet still spaces in each entry....
    workbookdf["Language"] = workbookdf["Language"].str.replace(' / ','|~|')

    #Putting together the values that are displayed in the website. These almost certainly should be their own columns in the future
    workbookdf['Format.dimensions'] = workbookdf["Height"].astype(int).astype(str) +' x '+ workbookdf["Width"].astype(int).astype(str) +' x '+ workbookdf["Thickness"].astype(int).astype(str) +' mm'
    workbookdf["Folia"] = workbookdf["Folia"].str.strip()
    workbookdf['Format.extent'] = workbookdf["Folia"].astype(str) +' ff. ; '+ workbookdf["Weight (g)"].astype(str) +' g'
    workbookdf['Support'] = workbookdf["Material"]
    workbookdf['Format'] = workbookdf["Form"]

#create the main dataframe
dfWorkbook = pd.DataFrame(columns=['Title',
'Item ARK',
'Object Type',
'Date.normalized',
'Date.creation',
'Format.extent',
'Format',
'Format.dimensions',
'Support',
'Language',
'AltIdentifier.local',
'delivery'])


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
        entryname = splitlist[0].strip().capitalize()
        entrynum = splitlist[1].strip().lstrip("0")
        workentryfinal = "{entryname} {entrynum}".format(entryname = entryname, entrynum = entrynum)

        result = allAirdf.loc[allAirdf['Shelfmark'].str.lower().isin([workentryfinal.lower()])]
        print(result)
        if progressWorkbook:
            workbookRow = workbookdf.loc[workbookdf['Shelfmark'].str.lower().isin([workentryfinal.lower()])]


        shelfmark = result['Shelfmark'].to_string(index=False).strip()

        if progressWorkbook:
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

        uniformTitle = ''
        uniformHolder = []

        if result['Uniform title'].any():
             textEntry = result['Uniform title'].item()
             textEntry = textEntry.replace(', ', ',')
             textEntry = textEntry.replace('[', '')
             textEntry = textEntry.replace(']', '')
             textEntry = textEntry.replace("'", '')
             textLst = textEntry.split(',')
             for entry in textLst:
                 if entry != 'nan':
                     titleinfo = UniformTitlesAirTable.get(entry)
                     uniformHolder.append(titleinfo['fields']['Uniform title'])
        uniformTitle = '|~|'.join(uniformHolder)


        AuthorText =  ''
        authorHolder = []

        if result['Author'].any():
             textEntry = result['Author'].item()
             textEntry = textEntry.replace(', ', ',')
             textEntry = textEntry.replace('[', '')
             textEntry = textEntry.replace(']', '')
             textEntry = textEntry.replace("'", '')
             textLst = textEntry.split(',')
             for entry in textLst:
                 if entry != 'nan':
                     authorinfo = NamesAirTable.get(entry)
                     authorHolder.append(authorinfo['fields']['Name'])
        AuthorText = '|~|'.join(authorHolder)


        scribeText =  ''
        scribeHolder = []

        if result['Scribe'].any():
             textEntry = result['Scribe'].item()
             textEntry = textEntry.replace(', ', ',')
             textEntry = textEntry.replace('[', '')
             textEntry = textEntry.replace(']', '')
             textEntry = textEntry.replace("'", '')
             textLst = textEntry.split(',')
             for entry in textLst:
                 if entry != 'nan':
                     scribeinfo = NamesAirTable.get(entry)
                     scribeHolder.append(scribeinfo['fields']['Name'])
        scribeText = '|~|'.join(scribeHolder)


        altTitleOther = ''
        placeOfO = ''
        IlluminatorText = ''
        RubricatorText =  ''
        CommentatorText =  ''
        CompilerText =  ''
        TranslatorText =  ''
        IncipitText =  ''
        ExplicitText =  ''
        BibliographyText =  ''


        title  = result['Title'].to_string(index=False).strip()
        title = title.replace('[', '')
        title = title.replace(']', '')

        localTitle = 'Sinai ' + workentryfinal
        titlefin = localTitle + '. ' + title +' : manuscript, '


        if humandate.isnumeric() == True:
            titlefin = titlefin + humandate + '.'
        else:
            titlefin = titlefin + '[' + humandate + '].'
        titlefin = titlefin +" St. Catherine's Monastery, Sinai, Egypt"


        genreText = result['Genre (from Genres)'].to_string(index=False).strip()
        genreText = genreText.replace('[', '')
        genreText = genreText.replace(']', '')
        genreText = genreText.replace(', ', '|~|')

        referenceText = result['Reference (from References)'].to_string(index=False).strip()
        referenceText = referenceText.replace('[', '')
        referenceText = referenceText.replace(']', '')
        referenceText = referenceText.replace(', ','|~|')

        contentsText = ''

        if result['Contents note'].any():
            contentsText = result['Contents note'].to_string(index=False).strip()

        if progressWorkbook:
            print('Updating with Airtable and Progress Notebook')

            formatExtentValue = workbookRow['Format.extent'].to_string(index=False).strip()
            formatExtentValue = sinaiWorkbookTextReplace(formatExtentValue)
            formatValue =  workbookRow['Format'].to_string(index=False).strip()
            formatValue = sinaiWorkbookTextReplace(formatValue)
            formatDimensionsValue =  workbookRow['Format.dimensions'].to_string(index=False).strip()
            formatDimensionsValue = sinaiWorkbookTextReplace(formatDimensionsValue)
            supportValue = workbookRow['Support'].to_string(index=False).strip()
            supportValue = sinaiWorkbookTextReplace(supportValue)
            languageValue = workbookRow['Language'].to_string(index=False).strip()
            languageValue = sinaiWorkbookTextReplace(languageValue)
            cameraOperatorValue = workbookRow["Camera Operator"].to_string(index=False).strip()
            cameraOperatorValue = sinaiWorkbookTextReplace(cameraOperatorValue)

        else:
            print("error with workbook")

        #populate the workbook
        new_row = {
               'Title': localTitle,
               'Item ARK':'',
               'Object Type':objectType,
               'Date.normalized': Date_normalized,
               'Date.creation':humandate,
               'Format.extent': formatExtentValue,
               'Format': formatValue,
               'Format.dimensions': formatDimensionsValue,
               'Support': supportValue,
               'Language': languageValue,
               'AltIdentifier.local':localTitle,
               'delivery': batchNum
              }

        dfWorkbook = dfWorkbook.append(new_row, ignore_index=True)

dfWorkbook.to_csv("works{batchNum}.csv".format(batchNum = batchNum), quoting=csv.QUOTE_ALL, index=False)
