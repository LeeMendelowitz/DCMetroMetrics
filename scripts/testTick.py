import sys
import os
import time

OUTPUT_DIR = os.environ.get('OPENSHIFT_DATA_DIR', os.getcwd())
OUTPUT = os.path.join(OUTPUT_DIR, 'temp.log')

while True:
    fout = open(OUTPUT, 'a')
    fout.write('Here!\n')
    sys.stderr.write('Tick!\n')
    time.sleep(2)
    fout.close()
