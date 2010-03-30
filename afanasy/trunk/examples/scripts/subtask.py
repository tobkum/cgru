#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import subprocess
import sys

if len( sys.argv) <= 3:
   print 'Usage: %s processesnumber processesdepth command' % sys.argv[0]
   exit(1)

processesdepth = int( sys.argv[1])
processesnum   = int( sys.argv[2])
args = []
for i in range( 3, len( sys.argv)): args.append( sys.argv[i])

procs = []

for i in range( processesnum):
   if processesdepth > 1:
      args.insert( 0, sys.argv[0])
      args.insert( 1, str(processesdepth - 1))
      args.insert( 2, str(processesnum))
   print 'pid(%d) Launching Process: %s' % (os.getpid(), ' '.join( args))
   procs.append( subprocess.Popen(args))
   sys.stdout.flush()

for i in range( processesnum):
   procs[i].wait()
   sys.stdout.flush()
