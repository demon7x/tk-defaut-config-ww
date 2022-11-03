# By Sam Saxon sam.saxon@thefoundry.com
# Copied from the equivalent Nuke file.

import os
import sys
from Katana import KatanaFile

import sgtk
from sgtk.platform.qt import QtGui

HookClass = sgtk.get_hook_baseclass()

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from execute_command import run_command

class SceneOperation(HookClass):
    """
    Hook called to perform an operation with the
    current scene
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
        user_name    = context.user['name']
        project_name = context.project['name']
        shot_name    = context.entity['name']
        tool         = 'Katana'
        if file_path:
            file_path = file_path.replace("/", os.path.sep)
            file_name = os.path.basename(file_path)
        else :
            file_name    = shot_name
        if operation == "current_path":
            # return the current scene path
            return file_path

        elif operation == "open":
            KatanaFile.Load(file_path)
            run_command( user_name, tool, project_name, shot_name, file_name, 'OPEN' )

        elif operation == "save":
            if not os.path.exists(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path))
            KatanaFile.Save(file_path)
            run_command( user_name, tool, project_name, shot_name, file_name, 'SAVE' )

        elif operation == "save_as":
            if not os.path.exists(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path))
            KatanaFile.Save(file_path)
            run_command( user_name, tool, project_name, shot_name, file_name, 'SAVE_AS' )
            
        elif operation == "prepare_new":
            run_command( user_name, tool, project_name, shot_name, file_name, 'NEW_FILE' )


        elif operation == "reset":

            while KatanaFile.IsFileDirty():
                # Changes have been made to the scene
                res = QtGui.QMessageBox.question(None,
                                                "Save your scene?",
                                                "Your scene has unsaved changes. Save before proceeding?",
                                                QtGui.QMessageBox.Yes|QtGui.QMessageBox.No|QtGui.QMessageBox.Cancel)
            
                if res == QtGui.QMessageBox.Cancel:
                    return False
                elif res == QtGui.QMessageBox.No:
                    break
                else:
                    if not os.path.exists(os.path.dirname(file_path)):
                        os.makedirs(os.path.dirname(file_path))
                KatanaFile.Save(file_path) # TODO: warning: this may not work...
            return True
            
