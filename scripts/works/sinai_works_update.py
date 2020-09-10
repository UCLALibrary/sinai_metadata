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

# Looks up airtable values for linked tables
def airTableEntry (textEntry, fieldName, tableName):
    textEntry = str(textEntry)
    textHolder = []
    textEntry = textEntry.replace(', ', ',')
    textEntry = textEntry.replace('[', '')
    textEntry = textEntry.replace(']', '')
    textEntry = textEntry.replace("'", '')
    textLst = textEntry.split(',')
    for entry in textLst:
        if entry != 'nan':
            titleinfo = tableName.get(entry)
            textHolder.append(titleinfo['fields'][fieldName])
    textFinalOutput = '|~|'.join(textHolder)
    return textFinalOutput


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
textDirectionTableName = 'text direction'

personal_key = 'keyaMF47wU6DgwfO8'

print('Building from Airtables...')
allAirTable = Airtable(base_key, allAirTableName, personal_key)
NamesAirTable = Airtable(base_key, namesTableName, personal_key)
UniformTitlesAirTable = Airtable(base_key, uniformtitlesTableName, personal_key)
genresTable = Airtable(base_key, genresTableName, personal_key)
referencesTable =  Airtable(base_key, referencesTableName, personal_key)
featuresTable =  Airtable(base_key, featuresTableName, personal_key)
languagesTable =  Airtable(base_key, languagesTableName, personal_key)
writingsysTable =  Airtable(base_key, writingsysTableName, personal_key)
scriptsTable =  Airtable(base_key, scriptsTableName, personal_key)
formTable =  Airtable(base_key, formTableName, personal_key)
supportTable =  Airtable(base_key, supportTableName, personal_key)
textDirectionTable =  Airtable(base_key, textDirectionTableName, personal_key)



allAirRecords = allAirTable.get_all()
allAirdf = pd.DataFrame.from_records((r['fields'] for r in allAirRecords))

batchNum = input('Batch Number: ')
batchNum = batchNum.strip()


#clean up the airtable incase there are strange errors in the data, extra spaces, etc
allAirdf['Shelfmark'].replace('', np.nan, inplace=True)
allAirdf.dropna(subset=['Shelfmark'], inplace=True)
allAirdf = allAirdf.fillna('')
allAirdf['Author'] = allAirdf['Author'].astype(str)
allAirdf['Author'] = allAirdf['Author'].fillna('')
allAirdf['AltTitle.uniform'] = allAirdf['AltTitle.uniform'].astype(str)
allAirdf['AltTitle.uniform'] = allAirdf['AltTitle.uniform'].fillna('')
allAirdf['Scribe'] = allAirdf['Scribe'].astype(str)
allAirdf['Scribe'] = allAirdf['Scribe'].fillna('')

workbook_columns = ['File Name',
'Item Sequence',
'Visibility',
'Title',
'Thumbnail URL',
'viewingHint',
'Parent ARK',
'Item ARK',
'Object Type',
'AltTitle.other',
'AltTitle.uniform',
'Place of origin',
'Date.normalized',
'Date binding',
'Date.creation',
'Scribe',
'Author',
'Translator',
'Contents note',
'Colophon',
'Incipit',
'Explicit',
'References',
'Provenance',
'General note',
'Format.extent',
'Form',
'Format.dimensions',
'Support',
'Foliation',
'Page layout',
'Writing and hands',
'Illustrations note',
'Inscription',
'Additions',
'Binding note',
'Ink color',
'Features',
'Condition note',
'Type.typeOfResource',
'Type.genre',
'Language',
'Text direction',
'Writing system',
'Script',
'Script note',
'Rights.statementLocal',
'Rights.servicesContact',
'Name.repository',
'AltIdentifier.local',
'Collection (physical)',
'Other version',
'IIIF Manifest URL',
'delivery']


for col in workbook_columns:
    if col not in allAirdf.columns:
        allAirdf[col] = ''


#create the main dataframe
dfWorkbook = pd.DataFrame(columns=workbook_columns)


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


dfDelivery = allAirdf[allAirdf['delivery']== batchNum]
for index, row in dfDelivery.sort_values('Shelfmark').iterrows():

    final_file_name = ''
    final_item_sequence = ''

    #final_delivery = row['delivery'].to_string(index=False).strip()
    final_delivery = row['delivery']

    #shelfmarkFinal = row['Shelfmark'].to_string(index=False).strip()
    #shelfmarkFinal = title.replace('[', '')
    #shelfmarkFinal = title.replace(']', '')
    shelfmarkFinal = row['Shelfmark']
    print(shelfmarkFinal)
    final_title = shelfmarkFinal + '. ' + row['Title']
    #final_title = title.replace('[', '')
    #final_title = title.replace(']', '')
    final_title = final_title + ' : manuscript, '

    final_Thumbnail_URL = ''
    if row['Thumbnail URL']:
        final_Thumbnail_URL = row['Thumbnail URL']

    final_Item_ARK = ''
    if row['Item ARK']:
        final_Item_ARK = row['Item ARK']

    final_AltTitle_other = ''
    if row['AltTitle.other']:
        final_AltTitle_other = row['AltTitle.other']

    uniformTitle =''
    if row['AltTitle.uniform']:
        uniformTitle = airTableEntry(row['AltTitle.uniform'], 'Uniform title', UniformTitlesAirTable)

    final_Place_of_origin =''
    if row['Place of origin']:
        final_Place_of_origin = row['Place of origin']

    final_Date_normalized =''
    if row['Date.normalized']:
        final_Date_normalized = row['Date.normalized']

    final_Date_binding =''
    if row['Date binding']:
        final_Date_binding = row['Date binding']

    final_Date_creation =''
    if row['Date.creation']:
        final_Date_creation = row['Date.creation']
        #this part of the title is dependent on the date; we will only use it if it already is there
        if row['Date.creation'].isnumeric() == True:
            final_title = final_title + row['Date.creation'] + '.'
        else:
            final_title = final_title + '[' + row['Date.creation'] + '].'
    #the final part of the title is not dependent on the date
    final_title = final_title +" St. Catherine's Monastery, Sinai, Egypt"

    final_scribeText =''
    if row['Scribe']:
        final_scribeText = airTableEntry(row['Scribe'], 'Name', NamesAirTable)

    final_AuthorText = ''
    if row['Author']:
        final_AuthorText = airTableEntry(row['Author'], 'Name', NamesAirTable)

    final_TranslatorText = ''
    if row['Translator']:
        final_TranslatorText = airTableEntry(row['Translator'], 'Name', NamesAirTable)

    final_Contents_note =''
    if row['Contents note']:
        final_Contents_note = row['Contents note']

    final_Colophon = ''
    if row['Colophon']:
        final_Colophon = row['Colophon']

    final_Incipit =''
    if row['Incipit']:
        final_Incipit = row['Incipit']

    final_Explicit = ''
    if row['Explicit']:
        final_Explicit = row['Explicit']

    final_References = ''
    if row['References']:
        final_References = airTableEntry(row['References'], 'Reference', referencesTable)

    final_Provenance = ''
    if row['Provenance']:
        final_Provenance = row['Provenance']

    final_General_note = ''
    if row['General note']:
        final_General_note = row['General note']

    final_Format_extent = ''
    if row['Format.extent']:
        final_Format_extent = row['Format.extent']

    final_form = ''
    if row['Form']:
        final_form = airTableEntry(row['Form'],'Name', formTable)

    final_Format_dimensions = ''
    if row['Format.dimensions']:
        final_Format_dimensions = row['Format.dimensions']

    final_Support = ''
    if row['Support']:
        final_Support = airTableEntry(row['Support'], 'Name', supportTable)

    final_Foliation =''
    if row['Foliation']:
        final_Foliation = row['Foliation']

    final_Page_layout = ''
    if row['Page layout']:
        final_Page_layout = row['Page layout']

    final_Writing_and_hands = ''
    if row['Writing and hands']:
        final_Writing_and_hands = row['Writing and hands']

    final_Illustrations_note = ''
    if row['Illustrations note']:
        final_Illustrations_note = row['Illustrations note']

    final_Inscription = ''
    if row['Inscription']:
        final_Inscription = row['Inscription']

    final_Additions = ''
    if row['Additions']:
        final_Additions = row['Additions']

    final_Binding_note = ''
    if row['Binding note']:
        final_Binding_note = row['Binding note']

    final_Ink_color = ''
    if row['Ink color']:
        final_Ink_color = row['Ink color']

    final_Features = ''
    if row['Features']:
        final_Features = airTableEntry(row['Features'], 'Feature', featuresTable)

    final_Condition_note = ''
    if row['Condition note']:
        final_Condition_note = row['Condition note']

    final_Type_genre = ''
    if row['Type.genre']:
        final_Type_genre = airTableEntry(row['Type.genre'], 'Genre', genresTable)

    final_Language = ''
    if row['Language']:
        final_Language = airTableEntry(row['Language'], 'ISO code', languagesTable)

    final_Text_direction =''
    if row['Text direction']:
        final_Text_direction = airTableEntry(row['Text direction'], 'Name', textDirectionTable)

    final_Writing_system = ''
    if row['Writing system']:
        final_Writing_system = airTableEntry(row['Writing system'], 'Writing system', writingsysTable)

    final_Script = ''
    if row['Script']:
        final_Script = airTableEntry(row['Script'], 'Script', scriptsTable)

    final_Script_note = ''
    if row['Script note']:
        final_Script_note = row['Script note']

    final_Other_version = ''
    if row['Other version']:
        final_Other_version = row['Other version']

    final_IIIF_Manifest_URL = ''
    if row['IIIF Manifest URL']:
        final_IIIF_Manifest_URL = row['IIIF Manifest URL']

    new_row = {
    'File Name': final_file_name,
    'Item Sequence': final_item_sequence,
    'Visibility': Visibility,
    'Title': final_title,
    'Thumbnail URL': final_Thumbnail_URL,
    'viewingHint': viewingHint,
    'Parent ARK': parentArk,
    'Item ARK': final_Item_ARK,
    'Object Type': typeOfResource,
    'AltTitle.other': final_AltTitle_other,
    'AltTitle.uniform': uniformTitle,
    'Place of origin': final_Place_of_origin,
    'Date.normalized': final_Date_normalized,
    'Date binding': final_Date_binding,
    'Date.creation': final_Date_creation,
    'Scribe': final_scribeText,
    'Author': final_AuthorText,
    'Translator': final_TranslatorText,
    'Contents note': final_Contents_note,
    'Colophon': final_Colophon,
    'Incipit': final_Incipit,
    'Explicit': final_Explicit,
    'References': final_References,
    'Provenance': final_Provenance,
    'General note': final_Provenance,
    'Format.extent': final_Format_extent,
    'Form': final_form,
    'Format.dimensions': final_Format_dimensions,
    'Support': final_Support,
    'Foliation': final_Foliation,
    'Page layout': final_Page_layout,
    'Writing and hands': final_Writing_and_hands,
    'Illustrations note': final_Illustrations_note,
    'Inscription': final_Inscription,
    'Additions': final_Additions,
    'Binding note': final_Binding_note,
    'Ink color': final_Ink_color,
    'Features': final_Features,
    'Condition note': final_Condition_note,
    'Type.typeOfResource': typeOfResource,
    'Type.genre': final_Type_genre,
    'Language': final_Language,
    'Text direction': final_Text_direction,
    'Writing system': final_Writing_system,
    'Script': final_Script,
    'Script note': final_Script_note,
    'Rights.statementLocal': Rights_statementLocal,
    'Rights.servicesContact': Rights_contact,
    'Name.repository': Name_repository,
    'AltIdentifier.local': shelfmarkFinal,
    'Collection (physical)': Collection_physical,
    'Other version': final_Other_version,
    'IIIF Manifest URL': final_IIIF_Manifest_URL,
    'delivery': final_delivery}

    dfWorkbook = dfWorkbook.append(new_row, ignore_index=True)

dfWorkbook.to_csv("works{batchNum}.csv".format(batchNum = batchNum), quoting=csv.QUOTE_ALL, index=False)
