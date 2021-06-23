#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
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
viewingHintTableName = 'viewingHint'

airtableInfoFile = input('Airtable Login JSON file:')
#strip starting and trailing spaces so we can simply drag and drop
airtableInfoFile = airtableInfoFile.strip()
#open the file straightaway and read the object
airtable_file = open(airtableInfoFile)
airtableInfo = json.load(airtable_file)

base_key = airtableInfo['airtable']['base_key']
personal_key = airtableInfo['airtable']['personal_key']


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
viewingHintTable =  Airtable(base_key, viewingHintTableName, personal_key)



allAirRecords = allAirTable.get_all()
allAirdf = pd.DataFrame.from_records((r['fields'] for r in allAirRecords))

batchNum = input('Input batch number, or leave blank for a full export of all published works: ')
#clean up any extraneous characters
batchNum = batchNum.strip()


#clean up the airtable to catch any strange errors in the data, extra spaces, etc
allAirdf['Shelfmark'].replace('', np.nan, inplace=True)
allAirdf.dropna(subset=['Shelfmark'], inplace=True)
allAirdf = allAirdf.fillna('')
allAirdf['Author'] = allAirdf['Author'].astype(str)
allAirdf['Author'] = allAirdf['Author'].fillna('')
allAirdf['AltTitle.uniform'] = allAirdf['AltTitle.uniform'].astype(str)
allAirdf['AltTitle.uniform'] = allAirdf['AltTitle.uniform'].fillna('')
allAirdf['Scribe'] = allAirdf['Scribe'].astype(str)
allAirdf['Scribe'] = allAirdf['Scribe'].fillna('')
allAirdf['Associated name'] = allAirdf['Associated name'].astype(str)
allAirdf['Associated name'] = allAirdf['Associated name'].fillna('')
allAirdf['Contributors'] = allAirdf['Contributors'].astype(str)
allAirdf['Contributors'] = allAirdf['Contributors'].fillna('')



workbook_columns = ['File Name',
'Item Sequence',
#'Visibility',
'Title',
'Descriptive title',
'Thumbnail URL',
'viewingHint',
'Parent ARK',
'Item ARK',
'Object Type',
'AltTitle.other',
'AltTitle.uniform',
'Place of origin',
'Date.normalized',
'Date.creation',
'Scribe',
'Author',
'Associated name',
'Contributors',
'Contents note',
'Colophon',
'Incipit',
'Explicit',
'References',
'Provenance',
'General note',
'Format.extent',
'Format.weight',
'Form',
'Format.dimensions',
'Support',
'Foliation',
'Page layout',
'Hand note',
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
'Rights contact',
'Name.repository',
'Shelfmark',
'Collection (physical)',
'Other version(s)',
'IIIF Manifest URL',
'delivery',
'image count']


for col in workbook_columns:
    if col not in allAirdf.columns:
        allAirdf[col] = ''


#create the main dataframe
dfWorkbook = pd.DataFrame(columns=workbook_columns)


#strip out whitespace in column names so we can call columns
dfWorkbook = dfWorkbook.rename(columns=lambda x: x.strip())

#set the dataframe constants; this can be modified for a different project (or even better made a config)
parentArk = 'ark:/21198/z1bk2gmg'
#Visibility = 'sinai'
typeOfResource = 'text'
Rights_statementLocal = "Images: Contact the Monastery of St. Catherine's of the Sinai. Metadata: Unless otherwise indicated all metadata associated with this manuscript is copyright the authors and released under Creative Commons Attribution 4.0 International License."
Rights_contact = "To inquire about image rights, contact St. Catherine's Monastery, https://www.sinaimonastery.com, sinaimonastery@gmail.com."
Name_repository = "Saint Catherine (Monastery : Mount Sinai)"
Collection_physical = "Sinai. Old Collection"
originator = "Statement of responsibility: Imaging performed under the auspices of His Eminence Archbishop Damianos and The Holy Council, Father Justin Sinaites Librarian, Early Manuscripts Electronic Library. Phelps Michael B. Project Director; Kasotakis Damianos. Imaging Director"
objectType = 'Work'

if batchNum == '':
    dfDelivery = allAirdf[allAirdf['published']== 'true']
else:
    dfDelivery = allAirdf[allAirdf['delivery']== batchNum]


for index, row in dfDelivery.sort_values('Shelfmark').iterrows():

    final_file_name = ''
    final_item_sequence = ''

    final_delivery = 'delivery ' + row['delivery']

    shelfmarkFinal = row['Shelfmark']
    print(shelfmarkFinal)
    #strip Sinai from shelfmark for the title
    shelffmark_for_title = shelfmarkFinal.replace('Sinai', '')
    final_title = 'Sinai, St. Catherine’s Monastery,' + shelffmark_for_title

    final_descriptive_title = ''
    if row['Descriptive title']:
        final_descriptive_title = row['Descriptive title']

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

    final_Date_creation =''
    if row['Date.creation']:
        final_Date_creation = row['Date.creation']
        final_Date_creation = final_Date_creation + ' CE'

    final_viewingHint =''
    if row['viewingHint']:
        final_viewingHint = airTableEntry(row['viewingHint'], 'Name', viewingHintTable)

    final_scribeText =''
    if row['Scribe']:
        final_scribeText = airTableEntry(row['Scribe'], 'Name', NamesAirTable)

    final_AuthorText = ''
    if row['Author']:
        final_AuthorText = airTableEntry(row['Author'], 'Name', NamesAirTable)

    final_AssociatedText = ''
    if row['Associated name']:
        final_AssociatedText = airTableEntry(row['Associated name'], 'Name', NamesAirTable)

    final_ContributorsText = ''
    if row['Contributors']:
        final_ContributorsText = airTableEntry(row['Contributors'], 'Name', NamesAirTable)


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

    final_Format_weight = ''
    if row['Format.weight']:
        final_Format_weight = row['Format.weight']

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
    if row['Hand note']:
        final_Writing_and_hands = row['Hand note']

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
    if row['Other version(s)']:
        final_Other_version = row['Other version(s)']

    final_IIIF_Manifest_URL = ''
    if row['IIIF Manifest URL']:
        final_IIIF_Manifest_URL = row['IIIF Manifest URL']

    final_image_count = ''
    if row['image count']:
        final_image_count = int(row['image count'])

    new_row = {
    'File Name': final_file_name.rstrip('\r\n'),
    'Item Sequence': final_item_sequence.rstrip('\r\n'),
    #'Visibility': Visibility.rstrip('\r\n'),
    'Title': final_title.rstrip('\r\n'),
    'Descriptive title': final_descriptive_title.rstrip('\r\n'),
    'Thumbnail URL': final_Thumbnail_URL.rstrip('\r\n'),
    'viewingHint': final_viewingHint.rstrip('\r\n'),
    'Parent ARK': parentArk.rstrip('\r\n'),
    'Item ARK': final_Item_ARK.rstrip('\r\n'),
    'Object Type': objectType.rstrip('\r\n'),
    'AltTitle.other': final_AltTitle_other.rstrip('\r\n'),
    'AltTitle.uniform': uniformTitle.rstrip('\r\n'),
    'Place of origin': final_Place_of_origin.rstrip('\r\n'),
    'Date.normalized': final_Date_normalized.rstrip('\r\n'),
    'Date.creation': final_Date_creation.rstrip('\r\n'),
    'Scribe': final_scribeText.rstrip('\r\n'),
    'Author': final_AuthorText.rstrip('\r\n'),
    'Associated name': final_AssociatedText .rstrip('\r\n'),
    'Contributors': final_ContributorsText .rstrip('\r\n'),
    'Contents note': final_Contents_note.rstrip('\r\n'),
    'Colophon': final_Colophon.rstrip('\r\nfr'),
    'Incipit': final_Incipit.rstrip('\r\n'),
    'Explicit': final_Explicit.rstrip('\r\n'),
    'References': final_References.rstrip('\r\n'),
    'Provenance': final_Provenance.rstrip('\r\n'),
    'General note': final_General_note.rstrip('\r\n'),
    'Format.extent': final_Format_extent.rstrip('\r\n'),
    'Format.weight': final_Format_weight.rstrip('\r\n'),
    'Form': final_form.rstrip('\r\n'),
    'Format.dimensions': final_Format_dimensions.rstrip('\r\n'),
    'Support': final_Support.rstrip('\r\n'),
    'Foliation': final_Foliation.rstrip('\r\n'),
    'Page layout': final_Page_layout.rstrip('\r\n'),
    'Hand note': final_Writing_and_hands.rstrip('\r\n'),
    'Illustrations note': final_Illustrations_note.rstrip('\r\n'),
    'Inscription': final_Inscription.rstrip('\r\n'),
    'Additions': final_Additions.rstrip('\r\n'),
    'Binding note': final_Binding_note.rstrip('\r\n'),
    'Ink color': final_Ink_color.rstrip('\r\n'),
    'Features': final_Features.rstrip('\r\n'),
    'Condition note': final_Condition_note.rstrip('\r\n'),
    'Type.typeOfResource': typeOfResource.rstrip('\r\n'),
    'Type.genre': final_Type_genre.rstrip('\r\n'),
    'Language': final_Language.rstrip('\r\n'),
    'Text direction': final_Text_direction.rstrip('\r\n'),
    'Writing system': final_Writing_system.rstrip('\r\n'),
    'Script': final_Script.rstrip('\r\n'),
    'Script note': final_Script_note.rstrip('\r\n'),
    'Rights.statementLocal': Rights_statementLocal.rstrip('\r\n'),
    'Rights contact': Rights_contact.rstrip('\r\n'),
    'Name.repository': Name_repository.rstrip('\r\n'),
    'Shelfmark': shelfmarkFinal.rstrip('\r\n'),
    'Collection (physical)': Collection_physical.rstrip('\r\n'),
    'Other version(s)': final_Other_version.rstrip('\r\n'),
    'IIIF Manifest URL': final_IIIF_Manifest_URL.rstrip('\r\n'),
    'delivery': final_delivery.rstrip('\r\n'),
    'image count': str(final_image_count).rstrip('\r\n')}

    dfWorkbook = dfWorkbook.append(new_row, ignore_index=True)

batchNum = batchNum.replace(".", "-")

dfWorkbook.to_csv("works{batchNum}.csv".format(batchNum = batchNum), quoting=csv.QUOTE_ALL, index=False, line_terminator='\n', encoding='utf-8')
