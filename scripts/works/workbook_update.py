#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import re
import csv
import os
from pathlib import Path
from airtable import Airtable
import pandas as pd

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

arabicTableName = 'Arabic mss'
syriacTableName = 'Syriac mss'
greekTableName = 'Greek mss'
genresTableName = 'Genres'
referencesTableName = 'References'
namesTableName = 'Names'
uniformtitlesTableName = 'Uniform titles'

personal_key = 'keyca2cbv9U4V5uLD'

ArabicAirTable = Airtable(base_key, arabicTableName, personal_key)
SyriacAirTable = Airtable(base_key, syriacTableName, personal_key)
GreekAirTable = Airtable(base_key, greekTableName, personal_key)

base_key = 'appBjMUh5e1Dgqj6p'

arabicTableName = 'Arabic mss'
syriacTableName = 'Syriac mss'
greekTableName = 'Greek mss'
genresTableName = 'Genres'
referencesTableName = 'References'
namesTableName = 'Names'
uniformtitlesTableName = 'Uniform titles'

personal_key = 'keyca2cbv9U4V5uLD'

ArabicAirTable = Airtable(base_key, arabicTableName, personal_key)
SyriacAirTable = Airtable(base_key, syriacTableName, personal_key)
GreekAirTable = Airtable(base_key, greekTableName, personal_key)

ArabicRecords = ArabicAirTable.get_all()
ArabicAirTabledf = pd.DataFrame.from_records((r['fields'] for r in ArabicRecords))

SyriacRecords = SyriacAirTable.get_all()
SyriacAirTabledf = pd.DataFrame.from_records((r['fields'] for r in SyriacRecords))

GreekRecords = GreekAirTable.get_all()
GreekAirTabledf = pd.DataFrame.from_records((r['fields'] for r in GreekRecords))

oldWorkBook = input('Old Workbook: ')
#strip starting and trailing spaces so we can simply drag and drop
oldWorkBook = oldWorkBook.strip()

pwork = False
progressWorkbook = input('Progress Workbook: ')
#strip starting and trailing spaces so we can simply drag and drop
progressWorkbook = progressWorkbook.strip()
if progressWorkbook:
    pwork = True

batchNum = input('Batch Number: ')
batchNum = batchNum.strip()

#load the workbooks into dataframes for manipulation
oldworkbookdf = pd.read_csv(oldWorkBook, na_filter=False)
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


ArabicAirTabledf['Shelfmark'].replace('', np.nan, inplace=True)
ArabicAirTabledf.dropna(subset=['Shelfmark'], inplace=True)
ArabicAirTabledf = ArabicAirTabledf.fillna('')

SyriacAirTabledf['Shelfmark'].replace('', np.nan, inplace=True)
SyriacAirTabledf.dropna(subset=['Shelfmark'], inplace=True)
SyriacAirTabledf = SyriacAirTabledf.fillna('')

GreekAirTabledf['Shelfmark'].replace('', np.nan, inplace=True)
GreekAirTabledf.dropna(subset=['Shelfmark'], inplace=True)
GreekAirTabledf = GreekAirTabledf.fillna('')
if 'Contents note' not in GreekAirTabledf:
    GreekAirTabledf['Contents note'] = ''

#normalize the shelfmarks. Should not be a problem with the old workbook

for index,row in ArabicAirTabledf.iterrows():
  Shelfmark = row['Shelfmark']
  Shelfmark = Shelfmark.split()[0] + ' ' + Shelfmark.split()[1].lstrip("0")
  row['Shelfmark'] = Shelfmark

for index,row in SyriacAirTabledf.iterrows():
  Shelfmark = row['Shelfmark']
  Shelfmark = Shelfmark.split()[0] + ' ' + Shelfmark.split()[1].lstrip("0")
  row['Shelfmark'] = Shelfmark

for index,row in GreekAirTabledf.iterrows():
  Shelfmark = row['Shelfmark']
  Shelfmark = Shelfmark.split()[0] + ' ' + Shelfmark.split()[1].lstrip("0")
  row['Shelfmark'] = Shelfmark

#merge the tables and make the shelfmark consistant with our local id
allAirdf = pd.concat([ArabicAirTabledf, SyriacAirTabledf, GreekAirTabledf], ignore_index=True)
allAirdf['Shelfmark'] = 'Sinai ' + allAirdf['Shelfmark']

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
dfWorkbook = pd.DataFrame(columns=['File Name','Item Sequence','Visibility','Title','Thumbnail URL','IIIF Range','viewingHint',
                          'Parent ARK', 'Item ARK', 'Object Type', 'AltTitle.other', 'AltTitle.uniform', 'Place of origin',
                          'Date.normalized', 'Date binding', 'Date.creation', 'Scribe', 'Illuminator', 'Rubricator', 'Author',
                          'Commentator', 'Compiler', 'Translator','Summary', 'Contents note', 'Colophon', 'Incipit', 'Explicit',
                          'Motif', 'Bibliography', 'References', 'Provenance', 'Signature', 'General note', 'Physical Description',
                          'Format.extent', 'Format', 'Format.dimensions', 'Support', 'Foliation', 'Collation', 'Page layout',
                          'Writing and hands', 'Illustrations note', 'Inscription', 'Additions', 'Binding note', 'Ink color',
                          'Features', 'Condition note', 'Type.typeOfResource', 'Type.genre', 'Language', 'Text direction',
                          'Writing system', 'Script', 'Script note', 'Rights.statementLocal', 'Rights contact',
                          'Name.repository', 'AltIdentifier.local', 'Series', 'Collection (physical)', 'Undertext object(s)',
                          'Overtext mss', 'Other version', 'Ms cataloger/scholar', '(originator of the digitized object)',
                          'Lens make | Lens model', 'Aperature', 'Camera Operator', 'IIIF Manifest URL'])


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

#find the row and get information from airtables and the progress workbook
for index, row in oldworkbookdf.iterrows():
    workentry = row['AltIdentifier.local']
    workentryShort = workentry.replace("Sinai ", "")

    result = allAirdf.loc[allAirdf['Shelfmark'].isin([workentry])]

    if progressWorkbook:
        workbookRow = workbookdf.loc[workbookdf['Shelfmark'].isin([workentryShort])]


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
        Date_normalized = row['Date.normalized']
        humandatestart = row['Date.normalized'].split('/')
        if len(humandatestart) > 1:
            humandatestart = centuryFromYear(int(humandatestart[0]))
            humandatestart = make_ordinal(humandatestart)
            humandate = humandatestart + ' c.'
        else:
            humandate = humandatestart[0]

    uniformTitle = result['Uniform title (from Uniform titles)'].to_string(index=False).strip()
    uniformTitle = uniformTitle.replace('[', '')
    uniformTitle = uniformTitle.replace(']', '')
    #need to add the seperator here
    uniformTitle = sinaiDelimReplace(uniformTitle)

    altTitleOther = row['AltTitle.other']
    #need to add the seperator here
    altTitleOther = sinaiDelimReplace(altTitleOther)

    placeOfO = row['Place of origin']
    #need to add the seperator here
    placeOfO = sinaiDelimReplace(placeOfO)

    scribeText =  row['Scribe']
    #need to add the seperator here
    scribeText = sinaiDelimReplace(scribeText)

    IlluminatorText =  row['Illuminator']
    #need to add the seperator here
    IlluminatorText = sinaiDelimReplace(IlluminatorText)

    RubricatorText =  row['Rubricator']
    #need to add the seperator here
    RubricatorText = sinaiDelimReplace(RubricatorText)

    AuthorText =  row['Author']
    #need to add the seperator here
    #AuthorText = sinaiDelimReplace(AuthorText)

    CommentatorText =  row['Commentator']
    #need to add the seperator here
    CommentatorText = sinaiDelimReplace(CommentatorText)

    CompilerText =  row['Compiler']
    #need to add the seperator here
    CompilerText = sinaiDelimReplace(CompilerText)

    TranslatorText =  row['Translator']
    #need to add the seperator here
    TranslatorText = sinaiDelimReplace(TranslatorText)

    IncipitText =  row['Incipit']
    #need to add the seperator here
    IncipitText = sinaiDelimReplace(IncipitText)

    ExplicitText =  row['Explicit']
    #need to add the seperator here
    ExplicitText = sinaiDelimReplace(ExplicitText)

    BibliographyText =  row['Bibliography']
    #need to add the seperator here
    BibliographyText = sinaiDelimReplace(BibliographyText)

    title  = result['Title'].to_string(index=False).strip()
    title = title.replace('[', '')
    title = title.replace(']', '')

    if progressWorkbook:
        titlefin = 'Sinai ' + workbookRow["Shelfmark"].to_string(index=False).strip() + '. ' + title +': manuscript, '

    else:
        titlefin = 'Sinai ' + workentryShort + '. ' + title +': manuscript, '


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

    #contentsText = ''

    #if result['Contents note'].any():
    #    contentsText = result['Contents note'].to_string(index=False).strip()

    if progressWorkbook:
        print('Updating with Airtable and Progress Notebook')

        if row['Format.extent']:
            formatExtentValue = row['Format.extent']
        else:
            formatExtentValue = workbookRow['Format.extent'].to_string(index=False).strip()
            formatExtentValue = sinaiWorkbookTextReplace(formatExtentValue)

        if row['Format']:
            formatValue = row['Format']
        else:
            formatValue =  workbookRow['Format'].to_string(index=False).strip()
            formatValue = sinaiWorkbookTextReplace(formatValue)

        if row['Format.dimensions']:
            formatDimensionsValue = row['Format.dimensions']
        else:
            formatDimensionsValue =  workbookRow['Format.dimensions'].to_string(index=False).strip()
            formatDimensionsValue = sinaiWorkbookTextReplace(formatDimensionsValue)

        if row['Support']:
            supportValue = row['Support']
            supportValue = sinaiDelimReplace(supportValue)

        else:
            supportValue = workbookRow['Support'].to_string(index=False).strip()
            supportValue = sinaiWorkbookTextReplace(supportValue)

        if row['Language']:
            languageValue = row['Language']
        else:
            languageValue = workbookRow['Language'].to_string(index=False).strip()
            languageValue = sinaiWorkbookTextReplace(languageValue)

        if row['Camera Operator']:
            cameraOperatorValue = row['Camera Operator']
        else:
            cameraOperatorValue = workbookRow["Camera Operator"].to_string(index=False).strip()
            cameraOperatorValue = sinaiWorkbookTextReplace(cameraOperatorValue)

    else:
        print('Updating with Airtable')
        formatExtentValue = row['Format.extent']
        formatValue = row['Format']
        formatDimensionsValue = row['Format.dimensions']
        supportValue = row['Support']
        languageValue = row['Language']
        cameraOperatorValue = row['Camera Operator']

    #populate the workbook
    new_row = {'File Name':row['File Name'],
           'Item Sequence':row['Item Sequence'],
           'Visibility':Visibility,
           'Title': titlefin,
           'Thumbnail URL':row['Thumbnail URL'],
           'IIIF Range':row['IIIF Range'],
           'viewingHint':row['viewingHint'],
           'Parent ARK':row['Parent ARK'],
           'Item ARK':row['Item ARK'],
           'Object Type':row['Object Type'],
           'AltTitle.other':altTitleOther,
           'AltTitle.uniform':uniformTitle,
           'Place of origin':placeOfO,
           'Date.normalized': Date_normalized,
           'Date binding':row['Date binding'],
           'Date.creation':humandate,
           'Scribe': scribeText,
           'Illuminator': IlluminatorText,
           'Rubricator':RubricatorText,
           'Author': AuthorText,
           'Commentator': CommentatorText,
           'Compiler': CompilerText,
           'Translator': TranslatorText,
           'Summary':row['Summary'],
           'Contents note':row['Contents note'],
           'Colophon':row['Colophon'],
           'Incipit':IncipitText,
           'Explicit':ExplicitText,
           'Motif':row['Motif'],
           'Bibliography':BibliographyText,
           'References':referenceText,
           'Provenance':row['Provenance'],
           'Signature':row['Signature'],
           'General note':row['General note'],
           'Physical Description':row['Physical Description'],
           'Format.extent': formatExtentValue,
           'Format': formatValue,
           'Format.dimensions': formatDimensionsValue,
           'Support': supportValue,
           'Foliation':row['Foliation'],
           'Collation':row['Collation'],
           'Page layout':row['Page layout'],
           'Writing and hands':row['Writing and hands'],
           'Illustrations note':row['Illustrations note'],
           'Inscription':row['Inscription'],
           'Additions':row['Additions'],
           'Binding note':row['Binding note'],
           'Ink color':row['Ink color'],
           'Features':row['Features'],
           'Condition note':row['Condition note'],
           'Type.typeOfResource': row['Type.typeOfResource'],
           'Type.genre': genreText,
           'Language': languageValue,
           'Text direction':row['Text direction'],
           'Writing system':row['Writing system'],
           'Script':row['Script'],
           'Script note':row['Script note'],
           'Rights.statementLocal': row['Rights.statementLocal'],
           'Rights contact':Rights_contact,
           'Name.repository': row['Name.repository'],
           'AltIdentifier.local':row['AltIdentifier.local'],
           'Series':row['Series'],
           'Collection (physical)':row['Collection (physical)'],
           'Undertext object(s)':row['Undertext object(s)'],
           'Overtext mss':row['Overtext mss'],
           'Other version':row['Other version'],
           'Ms cataloger/scholar':row['Ms cataloger/scholar'],
           '(originator of the digitized object)':row['(originator of the digitized object)'],
           'Lens make | Lens model':row['Lens make | Lens model'],
           'Aperature':row['Aperature'],
           'Camera Operator': cameraOperatorValue,
           'IIIF Manifest URL': row['IIIF Manifest URL']
          }

    dfWorkbook = dfWorkbook.append(new_row, ignore_index=True)

dfWorkbook.to_csv("works{batchNum}.csv".format(batchNum = batchNum), quoting=csv.QUOTE_ALL, index=False)
