import argparse
import re
import os
import shutil
import time
import zipfile
import subprocess

'''

1) Extract the zip file.
2) Perform directory walk.
3) Any files found in a single step sub-directory are appended to the existing .zip file archive.

'''
def main(args):
    print('Running ZipFlatten...')

    #Grade each zip file submission.
    startTime = time.time()
    assignmentFile = None
    zipFileList = sorted(os.listdir('./assignments'))
    iteration = 0

    for zipFileName in zipFileList:
        iteration += 1
        if '.zip' not in zipFileName:
            #If file isn't a zip file, continue.
            print('Iteration: ' + str(iteration) + ' Non zip file')
            continue
        else:
            print('Iteration: ' + str(iteration))
            #Read zip file.
            #try:
            with zipfile.ZipFile(args.path + '/' + zipFileName) as myzip:
                #Extract all files.
                myzip.extractall(args.path + '/extracted/')
            #Initialize os directory for walking over folders.
            entryList = os.listdir(args.path + '/extracted/')
            for entry in entryList:
                if os.path.isdir(args.path + '/extracted/' + entry +'/'):
                    fileList = os.listdir(args.path + '/extracted/' + entry)
                    for file in fileList:
                        if os.path.isfile(args.path + '/extracted/' + entry+'/' + file):
                            #Append file to existing zip file.
                            with zipfile.ZipFile(args.path + '/' + zipFileName, 'a') as zipFile:
                                zipFile.write(args.path + '/extracted/' + entry+'/' + file, arcname=file)
            #Remove the extracted zip folder files.
            shutil.rmtree(args.path + '/extracted/')
            # except:
            #     print('Bad Zip File Structure.')
            #     continue


if __name__ == '__main__':
    #Parse command line arguments
    parser = argparse.ArgumentParser(description='Moves all files to the root of a zip file.')
    parser.add_argument('path', metavar='f', type=str, help="path")
    args = parser.parse_args()
    main(args)





























