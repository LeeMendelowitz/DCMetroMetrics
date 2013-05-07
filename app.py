#!/usr/bin/env python
import imp
import os
import sys
import subprocess

PYCART_DIR = ''.join(['python-', '.'.join(map(str, sys.version_info[:2]))])
HOME = os.environ.get('OPENSHIFT_HOMEDIR', os.getcwd())

REPO_DIR = os.environ.get('OPENSHIFT_REPO_DIR', None)
if REPO_DIR is None:
    SCRIPT_DIR = os.getcwd()
else:
    SCRIPT_DIR = os.path.join(REPO_DIR, 'scripts')

try:
   zvirtenv = os.path.join(os.environ['OPENSHIFT_HOMEDIR'], PYCART_DIR,
                           'virtenv', 'bin', 'activate_this.py')
   execfile(zvirtenv, dict(__file__ = zvirtenv) )
except IOError:
   pass


def run_gevent_server(app, ip, port=8080):
   from gevent.pywsgi import WSGIServer
   w = WSGIServer((ip, port), app)
   return w


def run_simple_httpd_server(app, ip, port=8080):
   from wsgiref.simple_server import make_server
   w = make_server(ip, port, app)
   return w


#
# IMPORTANT: Put any additional includes below this line.  If placed above this
# line, it's possible required libraries won't be in your searchable path
# 
sys.path.append(SCRIPT_DIR)
import runTwitterApp

#
#  main():
#
if __name__ == '__main__':
   ip   = os.environ['OPENSHIFT_INTERNAL_IP']
   port = 8080
   zapp = imp.load_source('application', 'wsgi/application')

   #  Use gevent if we have it, otherwise run a simple httpd server.
   print 'Starting WSGIServer on %s:%d ... ' % (ip, port)

   # Note: we run the servers asynchronously
   w = None
   try:
      w = run_gevent_server(zapp.application, ip, port)
   except:
      print 'gevent probably not installed - using default simple server ...'
      w = run_simple_httpd_server(zapp.application, ip, port)
   w.start()

   # Run the Twitter App forever. Note: This blocks, since it's an infinite loop!
   runTwitterApp.runLoop()
