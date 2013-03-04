from datetime import datetime
import sys
import os

outputDir = os.environ.get('OPENSHIFT_DATA_DIR', None)
if outputDir is None:
    outputDir = os.getcwd()

outputFile = os.path.join(outputDir, 'myFile.txt')

n = datetime.now()
timeStr = n.strftime('%H:%M:%S')
myStr = 'The time is now %s\n'%timeStr

fout = open(outputFile, 'a')
fout.write(myStr)
fout.close()
