import glob, sys, os
import subprocess
import shutil

DATA_DIR = os.environ['OPENSHIFT_DATA_DIR']
os.chdir(DATA_DIR)

logFiles = glob.glob('*.log')
logFiles = [os.path.abspath(l) for l in logFiles]

print 'Found %i log files'%len(logFiles)
print '\n'.join(logFiles)

def trimLog(logFile, numLines = 200000):
    path, fn = os.path.split(logFile)
    bn, ext = os.path.splitext(fn)
    tempFile = '%s.temp'%fn
    tempFile = os.path.join(path, tempFile)

    # Execute tail
    cmd = ['tail', '-n', str(numLines), logFile]
    out = open(tempFile, 'w')
    subprocess.call(cmd, stdout = out)
    out.close()

    # Remove original log file
    os.remove(logFile)
  
    # Copy the shortened log file
    os.rename(tempFile, logFile)

for logFile in logFiles:
    logFile = os.path.abspath(logFile)
    trimLog(logFile)
