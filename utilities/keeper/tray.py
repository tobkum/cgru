import os, sys
import subprocess

import cgrudocs
import cgruconfig

import info
import nimby

from dialog_nimby import DialogNimby

from PyQt4 import QtCore, QtGui

def getVar( var, title = 'Set Variable', label = 'Enter new value:'):
   oldvalue = ''
   if var in cgruconfig.VARS: oldvalue = cgruconfig.VARS[var]
   newvalue, ok = QtGui.QInputDialog.getText( None, title, label, text = oldvalue)
   if not ok: return
   cgruconfig.VARS[var] = newvalue
   variables = [var]
   cgruconfig.writeVars(variables)

class ActionCommand( QtGui.QAction):
   def __init__( self, parent, name, command):
      QtGui.QAction.__init__( self, name, parent)
      self.name = name
      self.cmd = command
   def runCommand( self): QtCore.QProcess.startDetached( self.cmd, [])

class Tray( QtGui.QSystemTrayIcon):
   def __init__( self, parent = None):
      QtGui.QSystemTrayIcon.__init__( self, parent)
      self.parent = parent

      # Menu:
      self.menu = dict()
      self.menu['menu'] = QtGui.QMenu()

      # Update item only if CGRU_UPDATE_CMD defined:
      if cgruconfig.VARS['CGRU_UPDATE_CMD'] is not None:
         action = QtGui.QAction('Update', self)
         QtCore.QObject.connect( action, QtCore.SIGNAL('triggered()'), self.update)
         self.menu['menu'].addAction( action)
         self.menu['menu'].addSeparator()
         
      # Load menu:
      menudir = os.path.join( os.environ['CGRU_KEEPER'], 'menu')
      for dirpath, dirnames, filenames in os.walk( menudir, True, None, True):
         if dirpath.find('/.') != -1: continue
         if dirpath.find('\\.') != -1: continue
         menuname = os.path.basename( dirpath)
         if menuname not in self.menu:
            self.menu[menuname] = QtGui.QMenu( menuname)
            self.menu['menu'].addMenu( self.menu[menuname])
         filenames.sort()
         for filename in filenames:
            if filename[0] == '.': continue
            if sys.platform[:3] == 'win':
               if filename[-4:] != '.cmd': continue
               itemname = filename[:-4]
            else:
               if filename[-3:] != '.sh': continue
               itemname = filename[:-3]
            action = ActionCommand( self, itemname, os.path.join( dirpath, filename))
            self.menu[menuname].addAction( action)
            QtCore.QObject.connect( action, QtCore.SIGNAL('triggered()'), action.runCommand)

      # Add permanent items:
      self.menu['AFANASY'].addSeparator()
      action = QtGui.QAction('Set nibmy', self)
      QtCore.QObject.connect( action, QtCore.SIGNAL('triggered()'), nimby.setnimby)
      self.menu['AFANASY'].addAction( action)
      action = QtGui.QAction('Set NIMBY', self)
      QtCore.QObject.connect( action, QtCore.SIGNAL('triggered()'), nimby.setNIMBY)
      self.menu['AFANASY'].addAction( action)
      action = QtGui.QAction('Set Free', self)
      QtCore.QObject.connect( action, QtCore.SIGNAL('triggered()'), nimby.setFree)
      self.menu['AFANASY'].addAction( action)
      action = QtGui.QAction('Eject Tasks', self)
      QtCore.QObject.connect( action, QtCore.SIGNAL('triggered()'), nimby.ejectTasks)
      self.menu['AFANASY'].addAction( action)
      self.menu['AFANASY'].addSeparator()
      action = QtGui.QAction('Nimby Schedule...', self)
      QtCore.QObject.connect( action, QtCore.SIGNAL('triggered()'), self.editNimby)
      self.menu['AFANASY'].addAction( action)

      self.menu['menu'].addSeparator()

      self.menu['Configure'].addSeparator()
      action = QtGui.QAction('Reload Config', self)
      QtCore.QObject.connect( action, QtCore.SIGNAL('triggered()'), self.confReload)
      self.menu['Configure'].addAction( action)
      action = QtGui.QAction('Set Docs URL...', self)
      QtCore.QObject.connect( action, QtCore.SIGNAL('triggered()'), self.setDocsURL)
      self.menu['Configure'].addAction( action)
      action = QtGui.QAction('Edit Config...', self)
      QtCore.QObject.connect( action, QtCore.SIGNAL('triggered()'), self.editCGRUConfig)
      self.menu['Configure'].addAction( action)
      action = QtGui.QAction('Set Text Editor...', self)
      QtCore.QObject.connect( action, QtCore.SIGNAL('triggered()'), self.setTextEditor)
      self.menu['Configure'].addAction( action)

      self.menu['menu'].addSeparator()

      action = QtGui.QAction('Show Info', self)
      QtCore.QObject.connect( action, QtCore.SIGNAL('triggered()'), self.cgruInfo)
      self.menu['menu'].addAction( action)
      self.menu['menu'].addSeparator()
      action = QtGui.QAction('Documentation', self)
      QtCore.QObject.connect( action, QtCore.SIGNAL('triggered()'), self.cgruDocs)
      self.menu['menu'].addAction( action)
      self.menu['menu'].addSeparator()
      action = QtGui.QAction('Restart', self)
      QtCore.QObject.connect( action, QtCore.SIGNAL('triggered()'), self.restart)
      self.menu['menu'].addAction( action)            
      action = QtGui.QAction('Quit', self)
      QtCore.QObject.connect( action, QtCore.SIGNAL('triggered()'), parent.quit)
      self.menu['menu'].addAction( action)            

      # Decorate and show:
      self.setContextMenu( self.menu['menu'])
      self.icon = QtGui.QIcon( os.path.join( os.path.join( os.getenv('CGRU_KEEPER', ''), 'icons'), 'keeper.png'))
      self.setIcon( self.icon)
      parent.setWindowIcon( self.icon)
   
      self.setToolTip('CGRU Keeper ' + os.getenv('CGRU_VERSION', ''))

      self.show()

   def confReload( self): cgruconfig.Config()
   def cgruDocs( self): cgrudocs.show()
   def cgruInfo( self): self.dialog_info = info.Window()
   def editNimby( self): self.dialog_nimby = DialogNimby()
   def setDocsURL( self): getVar('docshost','Set Docs Host','Enter host name or IP address:')
   def setTextEditor( self): getVar('editor','Set Text Editor','Enter command with "%s":')
   def startAfWatch( self): QtCore.QProcess.startDetached( os.path.join( os.path.join( os.getenv('AF_ROOT'), 'launch'), 'afwatch.sh'))
   def restart( self):
      QtCore.QProcess.startDetached( cgruconfig.VARS['CGRU_KEEPER_CMD'])
      self.parent.quit()

   def update( self):
      QtCore.QProcess.startDetached( cgruconfig.VARS['CGRU_UPDATE_CMD'])
      self.parent.quit()

   def editCGRUConfig( self):
      if QtCore.QProcess.execute( cgruconfig.VARS['editor'] % cgruconfig.VARS['HOME_CONFIGFILE']) == 0:
         cgruconfig.Config()
