#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pandas as pd
import subprocess
import csv
import os
import exifread
from datetime import datetime
startTime = datetime.now()

sinsplit = '|~|'
#This is necessary to pull in long values from Pandas tables
pd.options.display.max_colwidth = 100000

#location of csv file
csvlocdir = input('Path to csv directory: ')
#strip starting and trailing spaces so we can simply drag and drop
csvlocdir = finaloutputDir.strip()
#image file directory
imgfiledir = input('Path to image folders: ')
#strip starting and trailing spaces so we can simply drag and drop
imgfiledir = textFileInput.strip()

#point to the exiftool Path
exifToolPath = input('exiftool Path (command): ')
infoDict = {} #Creating the dict to get the metadata tags

i3frange = ''

#iterate through the image directory and then subdirectories as necessary
if imgfiledir:
    imglister = os.listdir(imgfiledir)
    for directoryName in imglister:
        #we only want directories, as there can be extraneous files sometimes
        if os.path.isdir(os.path.join(imgfiledir,directoryName)):
            print(directoryName)
            #grab info for each file in the directory
            topcolumns = ['SourceFile','XMP-dc:Title','XMP-exif:Usercomment','LensInfo','LensMake','LensModel','ApertureValue','IPTC:Keywords','XMP-exif:Artist','XMP-dc:Identifier','XMP-dc:Language','XMP-dc:Description','XMP-dc:Publisher','XMP-dc:Rights','XMP-dc:Source','XMP-dc:Subject','XMP-dc:Format','XMP-dc:Relation','XMP-dc:Type']
            #dfendWorkbook = pd.DataFrame(columns=['File name','Visibility','Title','IIIF Range','viewingHint','Parent ARK','Item ARK','Object Type','Rights.statementLocal','Source'])
            dfWorkbook = []
            dfendWorkbook =[]
            csvlangName = csventryName.split("_")[0]

            #get the correct language and entry name that we are using
            langEntry = ''
            if ("ara" in csvlangName):
                langEntry ='ara/{name}/'.format(name = csventryName)
                langEntryPath =os.path.join('ara',csventryName)
            elif ("syr" in csvlangName):
                langEntry ='syr/{name}/'.format(name = csventryName)
                langEntryPath =os.path.join('syr',csventryName)
            elif ("gre" in csvlangName):
                langEntry ='grk/{name}/'.format(name = csventryName)
                langEntryPath =os.path.join('grk',csventryName)
            else:
                langEntry = ''

            if csvlangName != '':
                sequenceCounter = 1
                imgDirectory = os.path.join(mainDirectory,langEntry)
                df = pd.DataFrame(topcolumns)
                for sinaifilename in os.listdir(imgDirectory):
                    print(sinaifilename)
                    entryName = '{filenamepreamble}{langEntry}{sinaifilename}'.format(filenamepreamble = filenamepreamble,langEntry = langEntry, sinaifilename = sinaifilename )
                    #so we can open the image
                    imgPath = os.path.join(mainDirectory,langEntryPath,sinaifilename)
                    #subprocess to run the tool and get the outputs
                    process = subprocess.Popen([exifToolPath,imgPath],stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
                    for tag in process.stdout:
                        line = tag.strip().split(':')
                        infoDict[line[0].strip()] = line[-1].strip()
                    #get the correct entry name that we are using
                    #now to format the title
                    titlefinal = infoDict['Title'].replace(infoDict['Source'],'').strip()
                    if pd.isna(titlefinal):
                            titlefinal = ''
                    viewingHint = ''
                    if titlefinal == 'Spine' or titlefinal == 'Fore edge' or titlefinal == 'Head' or titlefinal == 'Tail':
                        viewingHint = 'non-paged'

                    #we need to add a .f to titles that are folios
                    if (sinaifilename.split("_")[0] == 'sld'):
                        if sinaifilename.split("_")[3] == 'a' or sinaifilename.split("_")[3] == 'b':
                            i3frange = 'Front matter'
                        elif sinaifilename.split("_")[3] == 'f':
                            i3frange = 'Text'
                            titlefinal = "f. " + titlefinal
                        elif sinaifilename.split("_")[3] == 'y':
                            i3frange = 'Back matter'
                        elif sinaifilename.split("_")[3] == 'z':
                            if str(sinaifilename.split("_")[4].split(".")[0]) == "1":
                                i3frange = 'Back matter'
                            else:
                                i3frange = ' '
                        else:
                            i3frange = ''
                    if sinaifilename.startswith("sld") and str(entryName).split('.')[-1] == 'tif':
                        dfWorkbook.append([str(entryName), sequenceCounter,'sinai',titlefinal, i3frange, viewingHint,'','','Page',RightsstatementLocal,infoDict['Source'].strip()])
                        sequenceCounter = sequenceCounter + 1
                    else:
                        if str(entryName).split('.')[-1] == 'tif':
                            dfendWorkbook.append([str(entryName), 'sinai',titlefinal, i3frange, 'non-paged','','','Page',RightsstatementLocal,infoDict['Source'].strip()])
                for row in dfendWorkbook:
                    dfWorkbook.append([row[0],sequenceCounter,row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9]])
                    sequenceCounter = sequenceCounter +1
                df = pd.DataFrame(dfWorkbook, columns = topcolumns)
                sourceValue = df['Source'].value_counts().idxmax()
                df = df.assign(Source=sourceValue)
                fileOutName =  os.path.join(finaloutputDir,csventryName)
                df.to_csv("{fileOutName}.csv".format(fileOutName = fileOutName),index=False)

print(datetime.now() - startTime)
