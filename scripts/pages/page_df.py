#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pandas as pd
import subprocess
import csv
import os
import exifread

sinsplit = '|~|'
#This is necessary to pull in long values from Pandas tables
pd.options.display.max_colwidth = 100000

#constants. We could probably pull all of these into a single .json or python file for all of our sctips....
filenamepreamble = 'Masters/sinaimasters/'
RightsstatementLocal = "Images: Contact the Monastery of St. Catherine's of the Sinai. Metadata: Unless otherwise indicated all metadata associated with this manuscript is copyright the authors and released under Creative Commons Attribution 4.0 International License."
visibility = 'discovery'
objectType = 'Page'
#directory where we get the images
mainDirectory = input('Folder Directory: ')
#strip starting and trailing spaces so we can simply drag and drop
mainDirectory = mainDirectory.strip()

#point to the exiftool Path
exifToolPath = input('exiftool Path (command): ')
infoDict = {} #Creating the dict to get the metadata tags
#exifToolPath = "exiftool"

i3frange = ''



#iterate through the directory
for root,dirs,files in os.walk(mainDirectory):
    for rootSub,dirsSub,filesSub in os.walk(root):
        counter = 1
        #grab info for each file in the directory
        topcolumns = ['File name','Item Sequence','Visibility','Title','IIIF Range','viewingHint','Parent ARK','Item ARK','Object Type','Rights.statementLocal','Source']
        #dfendWorkbook = pd.DataFrame(columns=['File name','Visibility','Title','IIIF Range','viewingHint','Parent ARK','Item ARK','Object Type','Rights.statementLocal','Source'])
        dfWorkbook = []
        dfendWorkbook =[]
        csvName = os.path.basename(os.path.normpath(rootSub))

        #get the correct language and entry name that we are using
        langEntry = ''
        if ("arb" in csvName):
            langEntry ='ara/{name}/'.format(name = csvName)
        elif ("syr" in csvName):
            langEntry ='syr/{name}/'.format(name = csvName)
        elif ("grk" in csvName):
            langEntry ='grk/{name}/'.format(name = csvName)
        else:
            langEntry = ''

        if csvName != 'tiff' and csvName != 'tiffs':
            sequenceCounter = 1
            df = pd.DataFrame(topcolumns)
            for sinaifilename in filesSub:
                print(sinaifilename)
                #so we can open the image
                imgPath = os.path.join(rootSub,sinaifilename)
                #subprocess to run the tool and get the outputs
                process = subprocess.Popen([exifToolPath,imgPath],stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
                for tag in process.stdout:
                    line = tag.strip().split(':')
                    infoDict[line[0].strip()] = line[-1].strip()
                #get the correct entry name that we are using
                entryName = '{filenamepreamble}{langEntry}{sinaifilename}'.format(filenamepreamble = filenamepreamble,langEntry = langEntry, sinaifilename = sinaifilename )
                #now to format the title
                titlefinal = infoDict['Title'].replace(infoDict['Source'],'').strip()
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
                if sinaifilename.startswith("sld"):
                    dfWorkbook.append([str(entryName), sequenceCounter,'discovery',titlefinal, i3frange, '','','','Page',RightsstatementLocal,infoDict['Source'].strip()])
                    sequenceCounter = sequenceCounter + 1
                else:
                    dfendWorkbook.append([str(entryName), 'non_paged',titlefinal, i3frange, '','','','Page',RightsstatementLocal,infoDict['Source'].strip()])
            for row in dfendWorkbook:
                dfWorkbook.append([row[0],sequenceCounter,row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9]])
                sequenceCounter = sequenceCounter +1
            df = pd.DataFrame(dfWorkbook, columns = topcolumns)
            df.to_csv("{batchNum}.csv".format(batchNum = csvName),index=False)
