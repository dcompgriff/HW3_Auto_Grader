import argparse
import re
import os
import time
import zipfile
import subprocess

'''
Overall program setup.

#Input args specified:
A) Directory holding all zip files (Assumed to be 'assignments/')
B) Assignment file name to grade within each zip (aka 'hw6_p3.txt')
C) Script to use for grading (aka 'HW6_P3_SCRIPT.lcs')
D) Grading rubric file? Each line represents a line that should be in the autograder output.

1) Loop through each zip file in a specified directory
	2) Open each zip and get the specified file to grade (Should be a file convertable to its .obj form)
	3) If a text file,
		3a) Append a newline to the file, and write with extension '.bin'
		3b) Start subprocess, and convert file from .bin to .obj (.obj file remains in the 'assignments/' folder
	4) If an assembly file,
		4a) Write assembly file to the 'assignments/' folder.

	5) Start subprocess, and run LC3 sim code with specified script.
	6) Retrieve output from subprocess pipe.
	7) Analyze pipe for specific lines in the grading rubric file.
	8) Output NET_ID name, pass into file PASS.txt, fail into file FAIL.txt
	9) Output NET_ID.txt program output for students that failed.

'''
def main(args):
	print('Running AutoGrader...')
	#Retrieve the grading rubric string list.
	rubricList = []
	with open(args.RubricFile) as myfile:
		for line in myfile:
			rubricList.append(line.strip())

	#Grade each zip file submission.
	startTime = time.time()
	assignmentFile = None
	zipFileList = sorted(os.listdir('./assignments'))
	zipFileList = zipFileList[args.StartIndex:]
	iteration = args.StartIndex

	for zipFileName in zipFileList:
		iteration += 1
		if '.zip' not in zipFileName:
			#If file isn't a zip file, continue.
			print('Iteration: ' + str(iteration) + ' Non zip file')
			continue
		else:
			#studentName = zipFileName.split('-')[2].strip()
			#with open('p4_submitted.txt', 'a') as myfile:
			#	myfile.write(studentName + '\n')
			#continue
			studentName = zipFileName.split('-')[2].strip()

			print(zipFileName)
			netID = zipFileName.split('-')[-1].strip()
			studentName = zipFileName.split('-')[2].strip()
			print(zipFileName)
			netID = netID.split('_')[0]
			print('Iteration: ' + str(iteration) + ', Grading: ' + netID)
			#If file to read is a text file, then extract from the zip file, and write to 'assignments/' dir.
			if '.txt' in args.AssignmentName:
				#Read zip file
				try:
					with zipfile.ZipFile('./assignments/' + zipFileName) as myzip:
						try:
							with myzip.open(args.AssignmentName) as myfile:
								assignmentFile = myfile.readlines()
						except:
							#Print student netID, failure message, and continue to next student.
							printFailure(netID, studentName, 'Incorrect assignment name, or missing assignment.')
							continue
				except:
					printFailure(netID, studentName, 'Bad Zip File Structure.')
					continue
				#If option to add breakpoint to script file is true, then find Halt command in binary file, and
				if args.AddFinalBreak == 'y':
					#Find location of Halt address in the binary file.
					startProgramAddress = 16384
					offset = -1
					for line in assignmentFile:
						if line.decode("utf-8").split(';')[0].strip() == '\n' or line.decode("utf-8").split(';')[0].strip() == '':
							continue
						binaryList = line.decode("utf-8").split(';')[0].strip().split(' ')
						binary = ''
						for term in binaryList:
							binary += term
						if binary == '1111000000100101':
							#Halt command found
							break
						else:
							#Continue to next address.
							offset += 1
					#Replace the {breakpoint} text in the script file with 'break set <startProgramAddress + offset>'
					with open(args.GradeScriptFile, 'r') as myfile:
						fileContents = myfile.read()
					hexAddr = 'x' + ((4 - len(hex(startProgramAddress + offset)[2:]))*'0') + hex(startProgramAddress + offset)[2:]
					fileContents = fileContents.replace('{breakpoint}', 'break set ' + hexAddr)
					with open('copy_' + args.GradeScriptFile, 'w') as myfile:
						for line in fileContents:
							myfile.write(line)

				#Add newline, and write assignmentFile as '.bin' to assignments folder.
				assignmentFile.append(b'\n')
				with open('./assignments/' + args.AssignmentName.split('.')[0] + '.bin', 'w') as myfile:
					for line in assignmentFile:
						myfile.write(line.decode("utf-8"))
				#Start subprocess to run the lc3convert program.
				binFileName = args.AssignmentName.split('.')[0] + '.bin'
				try:
					processResult = subprocess.check_output(["./lc3toolsbin/lc3convert", "-b2", "./assignments/" + binFileName])
				except:
					printFailure(netID, studentName, 'Incorrect assignment file content or structure')
					continue

			#Run subprocess to simulate results.
			try:
				if args.AddFinalBreak == 'y':
					simulationOutput = subprocess.check_output(["java", "-jar", "PennSim.jar", "-t", "-s", 'copy_' + args.GradeScriptFile])
					simulationOutput = simulationOutput.decode("utf-8")
				else:
					simulationOutput = subprocess.check_output(["java", "-jar", "PennSim.jar", "-t", "-s", args.GradeScriptFile])
					simulationOutput = simulationOutput.decode("utf-8")
			except:
				printFailure(netID, studentName, 'Failure running program in PennSim.')
				continue
			#Use rubric file to check if all necessary lines are in the output from the LC3 simulator process.
			gradePass = True
			for line in rubricList:
				if line.strip == '' or line.strip == '\n':
					continue
				if line not in simulationOutput:
					gradePass = False
					break
			if gradePass:
				with open("./results/PASS.txt", "a") as myfile:
					myfile.write(netID + ", " + studentName + "\n")
			else:
				printFailure(netID, studentName, 'Failed rubric.')
				with open("./results/rubric_fail/" + netID + "_err.txt", "w") as myfile:
					myfile.writelines(simulationOutput)

			#Clean up created .bin and .obj files in 'assignments/' before moving on.
			try:
				os.remove('./assignments/' + args.AssignmentName.split('.')[0] + '.bin')
				os.remove('./assignments/' + args.AssignmentName.split('.')[0] + '.obj')
			except:
				print('Issue cleaning up files on iteration, continuing...')

	endTime = time.time()
	print('Total time to run: %.2f minutes.' % ((endTime - startTime)/60))

'''
Print failure of student to file.
'''
def printFailure(netID, studentID, errMsg):
	#Print netID to failure file, along with error message if necessary.
	with open("./results/FAIL.txt", "a") as myfile:
		myfile.write(netID + ", " + studentID + ', ' + errMsg + "\n")


if __name__ == '__main__':
	#Parse command line arguments
	parser = argparse.ArgumentParser(description='LC3 AutoGrader.')
	parser.add_argument('AssignmentName', metavar='f1', type=str, help="AssignmentName")
	parser.add_argument('GradeScriptFile', metavar='f2', type=str, help="GradeScriptFile")
	parser.add_argument('RubricFile', metavar='f3', type=str, help="RubricFile")
	parser.add_argument('AddFinalBreak', metavar='b', type=str, help="Add a break point to the lcs script at the final binary Halt command? (y/n)")
	parser.add_argument('StartIndex', metavar='s', type=int, help="File address to start checking at")
	args = parser.parse_args()
	main(args)





