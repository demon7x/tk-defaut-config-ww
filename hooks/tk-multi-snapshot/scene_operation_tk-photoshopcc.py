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

import sgtk
from sgtk import Hook
from sgtk import TankError

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from execute_command import TimeLogManager

class SceneOperation(Hook):
    """
    Hook called to perform an operation with the
    current scene
    """

    def execute(self, operation, file_path, context, **kwargs):
        """
        Main hook entry point

        :operation: String
                    Scene operation to perform

        :file_path: String
                    File path to use if the operation
                    requires it (e.g. open)

        :returns:   Depends on operation:
                    'current_path' - Return the current scene
                                     file path as a String
                    all others     - None
        """
        adobe = self.parent.engine.adobe
        if context:
            user      = sgtk.get_authenticated_user()
            project_name = context.project['name']
            shot_name    = context.entity['name']
            tool         = 'Photoshop'
            
        if file_path:
            file_path = file_path.replace("/", os.path.sep)
            file_name = os.path.basename(file_path)
        else :
            file_name = shot_name

        doc = adobe.get_active_document()
        if not doc:
            raise TankError("There is no active document!")

        if operation == "current_path":
            # return the current script path
            path = adobe.get_active_document_path()
            if not path:
                raise TankError("The active document must be saved!")

            return path

        elif operation == "open":
            # reopen the specified script
            doc.close()
            adobe.app.load(adobe.File(file_path))

        elif operation == "save":
            # save the current script
            doc.save()
            TimeLogManager( user, tool, project_name, shot_name, file_name, 'SAVE' )
