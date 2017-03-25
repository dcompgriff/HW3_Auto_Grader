import argparse
import re
import glob
import os
import time
import zipfile
import subprocess
import sys
import shutil

providedInputFiles = ['../train1.csv', '../test1.csv', '10']
providedOutputSampleFiles = ['out01.txt', 'out11.txt', 'out21.txt', 'out31.txt']
privateInputFiles = ['../train2.csv', '../test2.csv', '20']
privateOutputSampleFiles = ['out02.txt', 'out12.txt', 'out22.txt', 'out32.txt']

'''
Output file format:
#If success running all parts of the program.
<Student Name>, <Total>, <Provided Mode 0 score>, <Provided Mode 1 score>, <Provided Mode 2 score>, <Provided Mode 3 score>,
	<Private Mode 0 score>, <Private Mode 1 score>, <Private Mode 2 score>, <Private Mode 3 score>, additional comments on failures
#If failure in opening or finding files, Total = -1.
<Student Name>, <Total>, additional comments on failure

'''
def main():
	print('Running AutoGrader...')
	#Grade each zip file submission.
	startTime = time.time()
	assignmentFile = None
	zipFileList = sorted(os.listdir('./assignments'))
	iteration = 0
	with open('./Results/Results.txt', 'w') as f:

		for zipFileName in zipFileList:
			iteration += 1

			if '.zip' not in zipFileName:
				#If file isn't a zip file, continue.
				continue
			else:
				#Get the Student Name from the file name. (Andrew Petti_136409_assignsubmission_file_apetti-HW2-P3.zip)
				studentName = zipFileName.split('_')[0].strip()
				print('Iteration: ' + str(iteration) + ', Grading: ' + studentName)

				#Read zip file
				try:
					with zipfile.ZipFile('./assignments/' + zipFileName) as myzip:
						try:
							myzip.extractall(path='./workingdir/')
						except:
							#Print student netID, failure message, and continue to next student.
							printFailure(studentName, 'Error extracting files from zip.', f)
							cleanWorkingDir()
							continue
				except:
					printFailure(studentName, 'Error opening zip.')
					cleanWorkingDir()
					continue


				#Make an output dir for student's program outputs.
				try:
					os.mkdir('./Results/StudentOutputs/' + studentName)
				except FileExistsError:
					continue

				#Grade provided data operation.
				os.chdir('./workingdir/')
				providedGradeString, providedComments = gradeProgram(studentName, 11, providedInputFiles, providedOutputSampleFiles)
				#Grade private data operation.
				privateGradeString, privateComments = gradeProgram(studentName, 5.5, privateInputFiles, privateOutputSampleFiles)
				os.chdir('..')

				#Output graded results to the results file.
				totalScore = 0
				for score in providedGradeString.split(','):
					if score == '':
						continue
					totalScore += float(score)
				for score in privateGradeString.split(','):
					if score == '':
						continue
					totalScore += float(score)
				f.write(studentName + ',' + str(totalScore) + ',' + providedGradeString + privateGradeString + providedComments + '/' + privateComments + '\n')
				f.flush()

				#Clean up created .bin and .obj files in 'assignments/' before moving on.
				cleanWorkingDir()

	endTime = time.time()
	print('Total time to run: %.2f minutes.' % ((endTime - startTime)/60))

def cleanWorkingDir():
	shutil.rmtree('./workingdir/')
	os.mkdir('./workingdir/')

def gradeProgram(studentName, baseGradeScore, inputFiles, outputFiles):
	gradeString = ''
	errorString = ''

	#Compile student code.
	try:
		processResult = subprocess.check_output(["javac *.java"], shell=True)
	except:
		errorString = '/Unable to compile java code'
		return '0,', errorString

	#Loop through all of the sample output files, read the text, run the student program, compare resulting output, and grade.
	mode = -1
	for file in outputFiles:
		mode += 1
		actualOutput = ''
		with open('../example_output/' + file) as f:
			actualOutput = f.readlines()

		#Run program and test.
		try:
			processResult = subprocess.check_output(['java HW3 ' + str(mode) + ' ' + inputFiles[0] + ' ' + inputFiles[1] +' ' + inputFiles[2]],
													shell=True, universal_newlines=True, timeout=10)
			processResult = processResult.split('\n')
		except:
			gradeString += '0,'
			errorString += '/(' + file + ')' + 'Error running \'java HW3\''
			#print(sys.exc_info()[0])
			continue

		#Write student output to file.
		with open('../Results/StudentOutputs/' + studentName + '/' + file, 'w') as f:
			for line in processResult:
				f.write(line + '\n')

		#Check output result, compare line by line.
		initialTotal = baseGradeScore
		kUnmatchingOutputs = 0
		for i in range(0, len(actualOutput)):
			try:
				if processResult[i].strip() != actualOutput[i].strip():
					initialTotal -= .5
					kUnmatchingOutputs += 1
				if initialTotal < 0:
					initialTotal = 0
					break
			except IndexError:
				initialTotal -= .5
				kUnmatchingOutputs += 1
				if initialTotal < 0:
					initialTotal = 0
					break
		gradeString += str(initialTotal) + ','
		if kUnmatchingOutputs > 0:
			errorString += '/(' + file + ')' + str(kUnmatchingOutputs) + ' non-matching outputs'

	#Return the 4 part, comma separated grades, and any error comments
	return gradeString, errorString


'''
Print failure of student to file.
'''
def printFailure(studentID, errMsg, f):
	#Print netID to failure file, along with error message if necessary.
	f.write(studentID + ',0,' + errMsg + "\n")


if __name__ == '__main__':
	main()





