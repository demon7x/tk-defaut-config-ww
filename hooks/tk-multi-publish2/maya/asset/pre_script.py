# Copyright (c) 2017 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import copy
import pprint
import maya.cmds as cmds
import maya.mel as mel
from pxr import Kind, Sdf, Usd, UsdGeom
import sgtk
from tank_vendor import six

HookBaseClass = sgtk.get_hook_baseclass()


class MayaSessionPreScriptPublishPlugin(HookBaseClass):
    """
    Plugin for publishing an open maya session.

    This hook relies on functionality found in the base file publisher hook in
    the publish2 app and should inherit from it in the configuration. The hook
    setting for this plugin should look something like this::

        hook: "{self}/publish_file.py:{engine}/tk-multi-publish2/basic/publish_session.py"

    """

    # NOTE: The plugin icon and name are defined by the base file plugin.

    @property
    def description(self):
        """
        Verbose, multi-line description of what the plugin does. This can
        contain simple html for formatting.
        """

        return """
        <p>When publishing, this plugin creates an attribute on the mesh object and input the current file version value on it
        </p>
        """

    @property
    def settings(self):
        """
        Dictionary defining the settings that this plugin expects to receive
        through the settings parameter in the accept, validate, publish and
        finalize methods.

        A dictionary on the following form::

            {
                "Settings Name": {
                    "type": "settings_type",
                    "default": "default_value",
                    "description": "One line description of the setting"
            }

        The type string should be one of the data types that toolkit accepts as
        part of its environment configuration.
        """
        # inherit the settings from the base publish plugin
        base_settings = super(MayaSessionPreScriptPublishPlugin, self).settings or {}

        # settings specific to this class
#        maya_publish_settings = {
#            "Publish Template": {
#                "type": "template",
#                "default": None,
#                "description": "Template path for published work files. Should"
#                               "correspond to a template defined in "
#                               "templates.yml.",
#            }
#        }
#
#        # update the base settings
#        base_settings.update(maya_publish_settings)
#
#
#        file_type = {
#            "File Types": {
#                "type": "list",
#                "default": [
#                    ["Pre Script", "script"],
#                ],
#                "description": (
#                    "List of file types to include. Each entry in the list "
#                    "is a list in which the first entry is the Shotgun "
#                    "published file type and subsequent entries are file "
#                    "extensions that should be associated."
#                )
#            },
#        }
#
#        base_settings.update(file_type)
        
        return base_settings

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.

        Only items matching entries in this list will be presented to the
        accept() method. Strings can contain glob patters such as *, for example
        ["maya.*", "file.maya"]
        """
        return ["maya.session"]

    @property
    def name( self ):
        return "Pre Script"

    def accept(self, settings, item):
        """
        Method called by the publisher to determine if an item is of any
        interest to this plugin. Only items matching the filters defined via the
        item_filters property will be presented to this method.

        A publish task will be generated for each item accepted here. Returns a
        dictionary with the following booleans:

            - accepted: Indicates if the plugin is interested in this value at
                all. Required.
            - enabled: If True, the plugin will be enabled in the UI, otherwise
                it will be disabled. Optional, True by default.
            - visible: If True, the plugin will be visible in the UI, otherwise
                it will be hidden. Optional, True by default.
            - checked: If True, the plugin will be checked in the UI, otherwise
                it will be unchecked. Optional, True by default.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process

        :returns: dictionary with boolean keys accepted, required and enabled
        """
        
        return {'accepted': True, 'checked':True}


    def validate(self, settings, item):
        """
        Validates the given item to check that it is ok to publish. Returns a
        boolean to indicate validity.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        :returns: True if item is valid, False otherwise.
        """
        return True 

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """

        if item.context.step['name'] == 'model' :
            path = _session_path()

            import re
            ver = 'v' + re.search('(?<=_v)\d{2,3}' , path ).group() if re.search('(?<=_v)\d{2,3}' , path ) else ''
            
            sh_list = cmds.ls(type='mesh')
            for sh in sh_list:
                if not cmds.objExists('%s.version'%sh):
                    cmds.addAttr(sh, ln='version', dt='string')
                    
                cmds.setAttr('%s.version'%sh, ver, type='string')

        print( '+' * 50 )
        print( '[ Shape Version ] ' , ver )
        print( '--- item ----' )
        print( item )
        print( item.context.step['name'] ) 
        print( '+' * 50 )

        return True

    def finalize( self , settings, item ):
        return True



def _session_path():
    """
    Return the path to the current session
    :return:
    """
    path = cmds.file(query=True, sn=True)

    if path is not None:
        path = six.ensure_str(path)

    return path


