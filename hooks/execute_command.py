# -*- coding: utf-8 -*-

import os
import sys
import platform
import subprocess as sp

from sgtk import Hook
from sgtk import TankError
from sgtk.platform.qt import QtGui

def run_command( user_name, tool, project_name, shot_name, file_name, operation ):

    sys_os = platform.system()
    file_path = os.path.dirname(os.path.realpath(__file__)) 
    if sys_os == 'Windows':
        cmd = 'rez-env psycopg2 -- python {0} '.format( os.path.join( file_path, 'stack_data.py') )
        cmd += '{0} {1} {2} {3} {4} {5} {6}'.format( user_name.replace(' ', '_' ), tool, project_name, shot_name, file_name, operation, sys_os )
        try:
            os.chdir(r'{}'.format(file_path))
            os.system(cmd)
        #     output, stderr = sp.Popen( cmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True, cwd=file_path ).communicate()
        except Exception as err :
            res = QtGui.QMessageBox.question(None,
                                                    "!! os error !!",
                                                    "{}".format(err),
                                                    QtGui.QMessageBox.Yes|QtGui.QMessageBox.No|QtGui.QMessageBox.Cancel)
    else:
        cmd = 'rez-env python-2 psycopg2 -- python {0} '.format( os.path.join( os.path.dirname(__file__), 'stack_data.py') )
        cmd += '{0} {1} {2} {3} {4} {5} {6}'.format( user_name.replace(' ', '_' ), tool, project_name, shot_name, file_name, operation, sys_os )
        os.system(cmd)