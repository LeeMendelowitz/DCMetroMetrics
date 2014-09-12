#!/usr/bin/env python
import sys, os, subprocess, shutil

this_dir = os.path.split(os.path.abspath(__file__))[0]
target_dir = os.path.abspath(os.path.join(this_dir, "..", "app", "scripts"))

input_file_name = "rankingsSearchString.pegjs"
output_file_name = "rankingsSearchString.js"

input_file = os.path.join(this_dir, input_file_name)
output_file = os.path.join(this_dir, output_file_name)
temp_file = os.path.join(this_dir, ".tmp.out")

cmd = "pegjs -e searchStringParser %s %s"%(input_file, temp_file)
ret = subprocess.call(cmd.split())
assert(ret == 0)

script = open(temp_file).read().strip()

# Rewrite the file to use strict.
template = """"use strict";
var {script}"""

# Write to output js file.
output = template.format(script = script)
with open(output_file, 'w') as fout:
  fout.write(output)
print "Wrote to %s"%output_file

# Copy the output file
shutil.copy(output_file, target_dir)

# Delete the temporary file
os.remove(temp_file)

print "Copied to %s"%target_dir


