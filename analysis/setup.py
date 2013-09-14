"""
Setup sys path
"""
import sys, os

filePath = os.path.abspath(__file__)
TEST_DIR, fn = os.path.split(filePath)
HOME_DIR = os.path.split(TEST_DIR)[0]

def fixSysPath():
    print 'Setting sys.path to include the dcmetrometrics package at: %s'%HOME_DIR
    sys.path = [HOME_DIR] + sys.path

fixSysPath()
