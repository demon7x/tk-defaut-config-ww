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
import pprint
import maya.cmds as cmds
import maya.mel as mel
import sgtk
from tank_vendor import six
import sys
import re
from sgtk.platform.qt import QtGui, QtCore

HookBaseClass = sgtk.get_hook_baseclass()


class MayaSessionShotDummyUSDExportPlugin(HookBaseClass):
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
        <p>This plugin publishes session geometry for the current session. Any
        session geometry will be exported to the path defined by this plugin's
        configured "Publish Template" setting. The plugin will fail to validate
        if the "AbcExport" plugin is not enabled or cannot be found.</p>
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
        base_settings = super(MayaSessionShotDummyUSDExportPlugin, self).settings or {}

        # settings specific to this class
        maya_publish_settings = {
            "Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published work files. Should"
                               "correspond to a template defined in "
                               "templates.yml.",
            }
        }

        # update the base settings
        base_settings.update(maya_publish_settings)


        file_type = {
            "File Types": {
                "type": "list",
                "default": [
                    ["Guide USD", "usd"],
                ],
                "description": (
                    "List of file types to include. Each entry in the list "
                    "is a list in which the first entry is the Shotgun "
                    "published file type and subsequent entries are file "
                    "extensions that should be associated."
                )
            },
        }

        base_settings['pub_sg'] = {
            "type": "bool",
            "default": True,
            "description": "Publishing Shotgrid",
        }

        base_settings.update(file_type)
        
        return base_settings

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.

        Only items matching entries in this list will be presented to the
        accept() method. Strings can contain glob patters such as *, for example
        ["maya.*", "file.maya"]
        """
        return ["maya.session.dummy.usd"]

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

        accepted = True
        publisher = self.parent
        template_name = settings["Publish Template"].value

        # ensure a work file template is available on the parent item
        work_template = item.parent.parent.properties.get("work_template")
        if not work_template:
            self.logger.debug(
                "A work template is required for the session item in order to "
                "publish session geometry. Not accepting session geom item."
            )
            accepted = False

        # ensure the publish template is defined and valid and that we also have
        publish_template = publisher.get_template_by_name(template_name)
        if not publish_template:
            self.logger.debug(
                "The valid publish template could not be determined for the "
                "session geometry item. Not accepting the item."
            )
            accepted = False

        # we've validated the publish template. add it to the item properties
        # for use in subsequent methods
        item.properties["publish_template"] = publish_template
        if cmds.about(version=1) == "2022":
            if not mel.eval("exists \"mayaUSDExport\""):
                self.logger.debug(
                "Item not accepted because alembic export command 'usdExport' "
                "is not available. Perhaps the plugin is not enabled?"
                )
                accepted = False
        else:
            if not mel.eval("exists \"usdExport\""):

                self.logger.debug(
                "Item not accepted because alembic export command 'usdExport' "
                "is not available. Perhaps the plugin is not enabled?"
                )
                accepted = False


        # because a publish template is configured, disable context change. This
        # is a temporary measure until the publisher handles context switching
        # natively.
        item.context_change_allowed = False

        return {
            "accepted": accepted,
            "checked": True
        }

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

        path = _session_path()
        
        # ---- ensure the session has been saved

        if not path:
            # the session still requires saving. provide a save button.
            # validation fails.
            error_msg = "The Maya session has not been saved."
            self.logger.error(
                error_msg,
                extra=_get_save_as_action()
            )
            raise Exception(error_msg)

        if not settings['pub_sg'].value:
            return True
        # get the normalized path
        path = sgtk.util.ShotgunPath.normalize(path)



        # get the configured work file template
        work_template = item.parent.parent.properties.get("work_template")
        publish_template = item.properties.get("publish_template")

        # get the current scene path and extract fields from it using the work
        # template:

        work_fields = work_template.get_fields(path)
        work_fields["name"]= item.properties['name']
        work_fields["shot_file_extension"]= item.properties['file_extension']

        # ensure the fields work for the publish template
        missing_keys = publish_template.missing_keys(work_fields)
        if missing_keys:
            error_msg = "Work file '%s' missing keys required for the " \
                        "publish template: %s" % (path, missing_keys)
            self.logger.error(error_msg)
            raise Exception(error_msg)

        # create the publish path by applying the fields. store it in the item's
        # properties. This is the path we'll create and then publish in the base
        # publish plugin. Also set the publish_path to be explicit.
        item.properties["path"] = publish_template.apply_fields(work_fields)
        item.properties["publish_path"] = item.properties["path"]


        # use the work file's version number when publishing
        if "version" in work_fields:
            item.properties["publish_version"] = work_fields["version"]

        # run the base class validation
        return super(MayaSessionShotDummyUSDExportPlugin, self).validate(
            settings, item)

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """
        
        if settings['pub_sg'].value:
            publisher = self.parent

            # get the path to create and publish
            publish_path = item.properties["path"]

            # ensure the publish folder exists:
            publish_folder = os.path.dirname(publish_path)
            self.parent.ensure_folder_exists(publish_folder)


        if item.parent.parent:
            for x in item.parent.parent.tasks:
                if 'Global' in x.name:
                    global_settings = x.settings
        
        mmGeom = cmds.ls('mmGeom', r=1)
        if not mmGeom:
            raise "mmGeom does not exist"

        scene_path  = global_settings['scene_path'].value
        basename    = global_settings['basename'].value
        usd_ver_path      = global_settings['usd_ver_path'].value
        usd_ver_py_folder = global_settings['usd_ver_py_folder'].value
        if not os.path.exists( usd_ver_py_folder ):
            os.makedirs( usd_ver_py_folder ) 
            os.chmod( usd_ver_path, 0o0777 )
            os.chmod( usd_ver_py_folder, 0o0777 )


        # local usd export
        content = ''
        content += 'import maya.cmds as cmds\n'
        content += 'import maya.mel as mel\n'
        content += 'import pymel.core as pm\n' 
        content += 'import os\n'
        content += 'import sys\n'

        content += 'from pxr import Sdf, Usd, UsdGeom, Kind\n'

        content += 'plugin_list = ["AbcExport.so", "cvJiggle.so", "cvwrap.so", "weightDriver.so", "mayaUsdPlugin.so"]\n'
        content += 'for plugin in plugin_list:\n'
        content += '    try:\n'
        content += '        cmds.loadPlugin( plugin )\n'
        content += '    except:\n'
        content += '        print( "Error : " , plugin )\n'
        content += '        pass\n'

        content += 'sys.path.append( "/westworld/inhouse/ww_usd/Script/python/wwUsd/maya" )\n'
        content += 'import maUSDwwPub\n'

        usd_file_path_list = []
        assemble_task_list = []

        sframe = global_settings['sframe'].value
        eframe = global_settings['eframe'].value
        handle = global_settings['handle_frame'].value
        step   = global_settings['cache_step'].value
        farm   = global_settings['farm'].value

        mmGeom = mmGeom[0].replace( ':' , '_' ) 
        mmGeom_usd_path = os.path.join( usd_ver_path , mmGeom + '.usd' )
        content += f'maUSDwwPub.mkExportUsdStandalone( "{mmGeom}", "{mmGeom_usd_path}", '
        content += f'{sframe} - {handle}, {eframe} + {handle}, float( {step} ) )\n'
        content += f'os.chmod( "{mmGeom_usd_path}", 0o0777 )\n'

        if farm:

            farm_content  = '# :coding: utf-8\n'
            farm_content += 'import maya.standalone\n'
            farm_content += 'maya.standalone.initialize()\n'
            farm_content += 'import maya.cmds as cmds\n'
            farm_content += 'cmds.file( new=1, force = 1)\n'
            farm_content += 'cmds.file( "{}", o = 1 )\n'.format( scene_path )

            content = farm_content + content
            py_content_path = os.path.join( usd_ver_path ,'python',  basename + '.py' )

            if not os.path.exists( os.path.dirname( py_content_path ) ):
                os.makedirs( os.path.dirname( py_content_path ), exist_ok = True )
                os.chmod( os.path.dirname( py_content_path ), 0o0777 )
            with open( py_content_path, 'w', encoding= 'utf-8' ) as f:
                f.write( content )

            sys.path.append( '/westworld/inhouse/tool/rez-packages/tractor/2.2.0/platform-linux/arch-x86_64/lib/python3.6/site-packages' )
            import tractor.api.author as author

            job = author.Job()

            job.service = 'cfx|cfx2' 
            job.title = '[{}] Exporting Dummy USD '.format( basename )
            job.priority = 100
            job.projects = ['RND']
            job.spoolcwd = '/tmp'
            task = author.Task( title = 'Exporting Dummy USD ' )
            cmd = author.Command( argv = ['rez-env', 'maya-2022', 'mayausd-0.19','pymel-1.2', '--', 'mayapy', py_content_path ] )
            task.addCommand( cmd )
            job.addChild( task )

            result = job.spool( hostname = '10.0.20.82', owner = os.getenv( 'USER' ) )
            author.closeEngineClient()
            print( result )
        else:
            exec( content )


        return super(MayaSessionShotDummyUSDExportPlugin, self).publish(settings, item)

    def create_settings_widget( self , parent ):
        self.pub_shotgrid = PublishShotgrid( parent , self.parent.shotgun )
        return self.pub_shotgrid

    def get_ui_settings( self, widget ):
        return {
            'pub_sg': widget.pub_sg
        }

    def set_ui_settings( self, widget, settings ):
        for setting_block in settings:
            pub_sg = setting_block.get( 'pub_sg' )
            if pub_sg:
                widget.pub_sg = pub_sg






def _session_path():
    """
    Return the path to the current session
    :return:
    """
    path = cmds.file(query=True, sn=True)

    if path is not None:
        path = six.ensure_str(path)

    return path


def _get_save_as_action():
    """
    Simple helper for returning a log action dict for saving the session
    """

    engine = sgtk.platform.current_engine()

    # default save callback
    callback = cmds.SaveScene

    # if workfiles2 is configured, use that for file save
    if "tk-multi-workfiles2" in engine.apps:
        app = engine.apps["tk-multi-workfiles2"]
        if hasattr(app, "show_file_save_dlg"):
            callback = app.show_file_save_dlg

    return {
        "action_button": {
            "label": "Save As...",
            "tooltip": "Save the current session",
            "callback": callback
        }
    }





class PublishShotgrid( QtGui.QWidget ):
    def __init__( self, parent , sg ):
        super( PublishShotgrid, self ).__init__( parent )

        self.__setup_ui()

    def __setup_ui( self ):
        self.pub_sg_chk = QtGui.QCheckBox( 'Publish to ShotGrid' )

        vlay = QtGui.QVBoxLayout()
        vlay.addWidget( self.pub_sg_chk )

        self.setLayout( vlay )

    @property
    def pub_sg( self ):
        return self.pub_sg_chk.isChecked()

    @pub_sg.setter
    def pub_sg( self , value):
        return self.pub_sg_chk.setChecked( value )

