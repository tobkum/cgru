# -*- coding: utf-8 -*-

import subprocess
import os
import sys
import signal
import tempfile
import traceback
import shutil

from optparse import OptionParser

tmpdir = None

def interrupt(signum, frame):
    """Interrupt function to delete temp directory:
    """
    if tmpdir is not None:
        if os.path.isdir(tmpdir):
            shutil.rmtree(tmpdir)
    exit('\nInterrupt received (hrender_separate.py)...')

# Set interrupt function:
signal.signal(signal.SIGTERM, interrupt)
signal.signal(signal.SIGABRT, interrupt)
if sys.platform.find('win') != 0:
    signal.signal(signal.SIGQUIT, interrupt)
signal.signal(signal.SIGINT, interrupt)

parser = OptionParser( usage="usage: %prog [options] hip_name rop_name", version="%prog 1.0")
parser.add_option('-s', '--start',     dest='start',     type='float',  help='Start frame number.')
parser.add_option('-e', '--end',       dest='end',       type='float',  help='End frame number.')
parser.add_option('-b', '--by',        dest='by',        type='float',  help='Frame increment.')
parser.add_option('-t', '--take',      dest='take',      type='string', help='Take name.')
parser.add_option('-o', '--out',       dest='output',    type='string', help='Output file.')
parser.add_option(      '--numcpus',   dest='numcpus',   type='int',    help='Number of CPUs.')
parser.add_option('-i', '--ignore_inputs', action='store_true', dest='ignore_inputs', default=False, help='Ignore inputs')

options, args = parser.parse_args()

start        = options.start
end          = options.end
by           = options.by
take         = options.take
numcpus      = options.numcpus
output       = options.output
ignoreInputs = options.ignore_inputs

if len(args) < 2:
    parser.error('At least one of mandatory rop_name or hip_name argument is missed.')
elif len(args) > 2:
    parser.error('Too many arguments provided.')
else:
    hip = args[0]
    rop = args[1]

# If end wasn't specified, render single frame
if end is None:
    end = start

# If by wasn't specified, render every frame
if by is None:
    by = 1

tmpdir = tempfile.mkdtemp('.afrender.houdini')
if os.path.exists(tmpdir):
    print('Generating files in temporary directory:')
    print(tmpdir)
else:
    print('Error creating temp directory.')
    print(traceback.format_exc())
    sys.exit(1)

hython = 'hython'
app_dir = os.getenv('APP_DIR')
if app_dir is not None:
    app_dir = os.path.join(app_dir, 'bin')
    hython = os.path.join(app_dir, 'hython')
    if sys.platform.find('win') == 0:
        hython += '.exe'

cmdgen_s = ['hrender_af', '-s']
cmdgen_e = []
if ignoreInputs:
    cmdgen_e.append('-i')

if take is not None:
    cmdgen_e.extend(['-t', take])

if output is not None:
    cmdgen_e.extend(['--output', str(output)])

if numcpus is not None:
    cmdgen_e.extend(['--numcpus', str(numcpus)])

cmdgen_e.append(hip)
cmdgen_e.append(rop)

cmdrnd = ['mantra']
cmdrnd.extend(['-V','1a','-f'])

frame = start
while frame <= end:
    # Construct ROP command:
    cmd = []
    cmd.extend(cmdgen_s)
    cmd.append(str(frame))
    cmd.append('--diskfile')
    afile = os.path.join(tmpdir, 'scene.' + str(frame) + '.ifd')
    cmd.append(afile)
    cmd.extend(cmdgen_e)

    # Run ROP command
    print('Launching command:')
    print(' '.join(cmd))
    sys.stdout.flush()

    p = subprocess.Popen(cmd)
    exitcode = p.wait()
    if exitcode != 0:
        break

    # Construct render command:
    cmd = []
    cmd.extend(cmdrnd)
    cmd.append(afile)

    # Launch render command:
    print('Launching command:')
    print(' '.join(cmd))
    sys.stdout.flush()

    p = subprocess.Popen(cmd)
    exitcode = p.wait()
    if exitcode != 0:
        break

    frame += by

if tmpdir is not None:
    print('Removing temp directory:')
    print(tmpdir)
    try:
        shutil.rmtree(tmpdir)
    except:
        print('Unable to remove temporary directory:')
        print(tmpdir)
        print(str(sys.exc_info()[1]))

sys.exit(exitcode)
