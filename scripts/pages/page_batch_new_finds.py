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

#constants. We could probably pull all of these into a single .json or python file for all of our sctips....
filenamepreamble = 'Masters/sinaimasters/'
RightsstatementLocal = "Images: Contact the Monastery of St. Catherine's of the Sinai. Metadata: Unless otherwise indicated all metadata associated with this manuscript is copyright the authors and released under Creative Commons Attribution 4.0 International License."
visibility = 'discovery'
objectType = 'Page'
#outputdirectory
finaloutputDir = input('Path to output directory: ')
#strip starting and trailing spaces so we can simply drag and drop
finaloutputDir = finaloutputDir.strip()
#filelist
textFileInput = input('Path to delivery directory: ')
#strip starting and trailing spaces so we can simply drag and drop
textFileInput = textFileInput.strip()
#directory where we get the images
mainDirectory = input('Image Masters Directory: ')
#strip starting and trailing spaces so we can simply drag and drop
mainDirectory = mainDirectory.strip()

#point to the exiftool Path
exifToolPath = input('exiftool Path (command): ')
infoDict = {} #Creating the dict to get the metadata tags

i3frange = ''

#iterate through the directory
if textFileInput:
    imglister = os.listdir(textFileInput)
    for csventryName in imglister:
        #we only want directories, as there can be extraneous files sometimes
        if os.path.isdir(os.path.join(textFileInput,csventryName)):
            print(csventryName)
            #grab info for each file in the directory
            topcolumns = ['File Name','Item Sequence','Visibility','Title','IIIF Range','viewingHint','Parent ARK','Item ARK','Object Type','Rights.statementLocal','Source']
            #dfendWorkbook = pd.DataFrame(columns=['File name','Visibility','Title','IIIF Range','viewingHint','Parent ARK','Item ARK','Object Type','Rights.statementLocal','Source'])
            dfWorkbook = []
            dfendWorkbook =[]
            csvlangName = csventryName.split("_")[0]

            #get the correct language and entry name that we are using
            langEntryPath = ''
            if ("ara" in csvlangName):
                if ("nfm" in csvlangName):
                    #langEntry ='aranf/{name}/'.format(name = csventryName)
                    langEntryPath = os.path.join('aranf',csventryName)
                else:
                    #langEntry ='ara/{name}/'.format(name = csventryName)
                    langEntryPath =os.path.join('ara',csventryName)
            elif ("syr" in csvlangName):
                if ("nfm" in csvlangName):
                    #langEntry ='syrnf/{name}/'.format(name = csventryName)
                    langEntryPath =os.path.join('syrnf',csventryName)
                else:
                    #langEntry ='syrnf/{name}/'.format(name = csventryName)
                    langEntryPath =os.path.join('syr',csventryName)

            elif ("gre" in csvlangName):
                if ("nfm" in csvlangName):
                    #langEntry ='grknf/{name}/'.format(name = csventryName)
                    langEntryPath =os.path.join('grknf',csventryName)
                else:
                    langEntryPath =os.path.join('grk',csventryName)

            else:
                langEntryPath = ''

            if csvlangName != '':
                sequenceCounter = 1
                #imgDirectory = os.path.join(mainDirectory,langEntry)
                imgDirectory = os.path.join(mainDirectory,langEntryPath)
                df = pd.DataFrame(topcolumns)
                for sinaifilename in os.listdir(imgDirectory):
                    print(sinaifilename)
                    #entryName = '{filenamepreamble}{langEntry}{sinaifilename}'.format(filenamepreamble = filenamepreamble,langEntry = langEntry, sinaifilename = sinaifilename )
                    entryName = '{filenamepreamble}{langEntryPath}{sinaifilename}'.format(filenamepreamble = filenamepreamble,langEntryPath = langEntryPath, sinaifilename = sinaifilename )
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
                    if 'lcc' not in str(sinaifilename).lower():
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
