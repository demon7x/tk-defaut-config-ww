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
import re
import pprint
import maya.cmds as cmds
import maya.mel as mel
from pxr import Kind, Sdf, Usd, UsdGeom
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class MayaSessionToTractorPlugin(HookBaseClass):
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
        base_settings = {}

        return base_settings

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.

        Only items matching entries in this list will be presented to the
        accept() method. Strings can contain glob patters such as *, for example
        ["maya.*", "file.maya"]
        """
        return ["maya.session.shot.component.usd"]

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

        return {
            "accepted": True,
            "checked": True
        }

    def validate(self, settings, item):

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

        # get the normalized path
        path = sgtk.util.ShotgunPath.normalize(path)



        # get the configured work file template
        work_template = item.parent.parent.properties.get("work_template")
        publish_template = item.properties.get("publish_template")

        # get the current scene path and extract fields from it using the work
        # template:

        work_fields = work_template.get_fields(path)
        work_fields["asset_namespace"]= item.properties['namespace']

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

        return True


    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """
        
        publisher = self.parent

        # get the path to create and publish
        publish_path = item.properties["path"]

        # ensure the publish folder exists:
        publish_folder = os.path.dirname(publish_path)
        self.parent.ensure_folder_exists(publish_folder)

        # set the alembic args that make the most sense when working with Mari.
        # These flags will ensure the export of an USD file that contains
        # all visible geometry from the current scene together with UV's and
        # face sets for use in Mari.
        
        usd_args = [
            '-shd "none"',
            '-dms "none"',
            '-uvs 1',
            '-cls 0',
            '-vis 1',
            '-mt 0',
            '-sl',
            '-sn 1',
            '-fs %f'%item.properties['sub_frame'],
            '-ft %f'%item.properties['sub_frame']
            
            ]



        # find the animated frame range to use:
        start_frame, end_frame = _find_scene_animation_range()
        if start_frame and end_frame:
            usd_args.append("-fr %d %d" % (start_frame, end_frame))

        # Set the output path: 
        # Note: The AbcExport command expects forward slashes!

        sub_components = [ x for x in cmds.ls(allPaths=1,ca=0,transforms=1,l=1) 
        if cmds.listRelatives(x,p=1) 
        and cmds.attributeQuery("Meshtype",node=x,exists=1) 
        and cmds.getAttr(x+".Meshtype", asString=True) == "component"]
        
        



        if not sub_components:

            usd_args.append('-f "%s"' % publish_path.replace("\\", "/"))
            usd_export_cmd = ("usdExport %s" % " ".join(usd_args))

        else:

            asset_usd_path = self._get_sub_component_path(item.properties['name'],item)
            usd_args.append('-f "%s"' % asset_usd_path.replace("\\", "/"))
            usd_export_cmd = ("usdExport %s" % " ".join(usd_args))
        
        script = ''
        script += 'import maya.standalone\n'
        script += 'maya.standalone.initialize()\n'
        script += 'import maya.cmds as cmds\n'
        script += 'import maya.mel as mel\n'

        script += '\n'
        script += '\n'

        script += 'cmds.file("{}",open=1,force=1,iv=1)\n'.format(cmds.file(query=True, sn=True))
        script += 'cmds.select("{}")\n'.format(item.properties['name'])
        script += 'cmds.loadPlugin("pxrUsd.so")\n'
        script += 'mel.eval(\'{}\')\n'.format(usd_export_cmd)
        
        tmp_path = os.path.splitext(item.properties["path"])[0]+".py"

        with open( tmp_path, 'w' ) as f:
            f.write(script)
        
        import sys
        sys.path.append("/westworld/inhouse/tool/rez-packages/tractor/2.2.0/platform-linux/arch-x86_64/lib/python2.7/site-packages")

        import tractor.api.author as author

        job = author.Job()
        job.service = "convert"
        job.priority = 50
        
        file_title = cmds.file(query=True, sn=True).split(".")[0].split("/")[-1]
        project_name =item.context.project['name']
        user_name = item.context.user['name']
        user_id = os.environ['USER']

        temp = "] ["
        title = []
        title.append(user_name)
        title.append(project_name)
        title.append(file_title)
        title.append(item.properties['name'])
        title.append("%d - %d"%(start_frame,end_frame))
        title = temp.join(title)
        title = "["+title+"]"
        job.title = str(title)

        command = ['rez-env','maya-2019vfarm','usd-19.03','--','mayapy']
        command.append(tmp_path)
        command = author.Command(argv=command)

        task = author.Task(title = str(item.properties['name']))
        task.addCommand(command)

        rm_command = ['/bin/rm','-f']
        rm_command.append(tmp_path)
        rm_command = author.Command(argv=rm_command)
        rm_task = author.Task(title = "rm tmp")
        rm_task.addCommand(rm_command)
        
        rm_task.addChild(task)


        job.addChild(rm_task)

        job.spool(hostname="10.0.20.82",owner=user_id)

        return

    def _get_sub_component_path(self,sub_component,item):
        path = os.path.splitext(item.properties["path"])[0]
        path = os.path.join(path,sub_component.replace("|","_")+'.usd')
        
        return path

    def finalize(self, settings, item):
        pass


def _find_scene_animation_range():
    """
    Find the animation range from the current scene.
    """
    # look for any animation in the scene:
    animation_curves = cmds.ls(typ="animCurve")

    # if there aren't any animation curves then just return
    # a single frame:
    if not animation_curves:
        return 1, 1

    # something in the scene is animated so return the
    # current timeline.  This could be extended if needed
    # to calculate the frame range of the animated curves.
    start = int(cmds.playbackOptions(q=True, min=True)) - 20
    end = int(cmds.playbackOptions(q=True, max=True)) + 20

    return start, end


def _session_path():
    """
    Return the path to the current session
    :return:
    """
    path = cmds.file(query=True, sn=True)

    if isinstance(path, unicode):
        path = path.encode("utf-8")

    return path



        

