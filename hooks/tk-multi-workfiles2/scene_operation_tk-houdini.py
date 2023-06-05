# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import sys
import hou

import tank
from tank import Hook
from tank import TankError


import sgtk
from sgtk.platform.qt import QtGui

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from execute_command import TimeLogManager

class SceneOperation(Hook):
    """
    Hook called to perform an operation with the current scene
    """
    def execute(self, operation, file_path, context, parent_action, file_version, read_only, **kwargs):
        """
        Main hook entry point
        
        :param operation:       String
                                Scene operation to perform
        
        :param file_path:       String
                                File path to use if the operation
                                requires it (e.g. open)
                    
        :param context:         Context
                                The context the file operation is being
                                performed in.
                    
        :param parent_action:   This is the action that this scene operation is
                                being executed for.  This can be one of:
                                - open_file
                                - new_file
                                - save_file_as 
                                - version_up
                        
        :param file_version:    The version/revision of the file to be opened.  If this is 'None'
                                then the latest version should be opened.
        
        :param read_only:       Specifies if the file should be opened read-only or not
                            
        :returns:               Depends on operation:
                                'current_path' - Return the current scene
                                                file path as a String
                                'reset'        - True if scene was reset to an empty 
                                                state, otherwise False
                                all others     - None
        """
        user      = sgtk.get_authenticated_user()
        project_name = context.project['name']
        shot_name    = context.entity['name']
        tool         = 'Houdini'
        if file_path:
            file_path = file_path.replace(os.path.sep, '/')
            file_name = os.path.basename(file_path)
        else :
            file_name    = shot_name

        if operation == "current_path":
            return str(hou.hipFile.name())

        elif operation == "open":
            # give houdini forward slashes
            # file_path = file_path.replace(os.path.sep, '/')
            # hou.hipFile.load(file_path.encode("utf-8"))
            hou.hipFile.load(file_path)
            # TimeLogManager( user, tool, project_name, shot_name, file_name, 'OPEN' )

        elif operation == "save":
            hou.hipFile.save()
            # TimeLogManager( user, tool, project_name, shot_name, file_name, 'SAVE' )

        elif operation == "save_as":
            # give houdini forward slashes
            # file_path = file_path.replace(os.path.sep, '/')
            # hou.hipFile.save(str(file_path.encode("utf-8")))
            hou.hipFile.save(file_path)
            # TimeLogManager( user, tool, project_name, shot_name, file_name, 'SAVE_AS' )

        # elif operation == "prepare_new":
        #     TimeLogManager( user, tool, project_name, shot_name, file_name, 'NEW_FILE' )

        elif operation == "reset":
            hou.hipFile.clear()
            return True
