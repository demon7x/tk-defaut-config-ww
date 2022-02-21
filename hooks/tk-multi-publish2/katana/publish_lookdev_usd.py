# Copyright (c) 2018 Shotgun Software Inc.
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
import sgtk
from tank_vendor import six

HookBaseClass = sgtk.get_hook_baseclass()
from Katana import FarmAPI , KatanaFile
from tank_vendor import six


class KatanaLookdevUsdPublishPlugin(HookBaseClass):
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
        base_settings = super(KatanaLookdevUsdPublishPlugin, self).settings or {}

        # settings specific to this class
        katana_publish_settings = {
            "Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published work files. Should"
                               "correspond to a template defined in "
                               "templates.yml.",
            }
        }

        # update the base settings
        base_settings.update(katana_publish_settings)

        return base_settings

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.

        Only items matching entries in this list will be presented to the
        accept() method. Strings can contain glob patters such as *, for example
        ["maya.*", "file.maya"]
        """
        return ["katana.session.lookdev.usd"]

    def accept(self, settings, item):

        accepted = True


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
        publisher = self.parent
        path = _session_path()

        # ---- ensure the session has been saved

        if not path:
            # the session still requires saving. provide a save button.
            # validation fails.
            error_msg = "The Natron session has not been saved."
            self.logger.error(
                error_msg,
                extra=_get_save_as_action()
            )
            raise Exception(error_msg)

        # ---- check the session against any attached work template

        # get the path in a normalized state. no trailing separator,
        # separators are appropriate for current os, no double separators,
        # etc.
        path = sgtk.util.ShotgunPath.normalize(path)

        # if the session item has a known work template, see if the path
        # matches. if not, warn the user and provide a way to save the file to
        # a different path

        work_template = item.parent.properties.get("work_template")
        if work_template:
            if not work_template.validate(path):
                self.logger.warning(
                    "The current session does not match the configured work "
                    "file template.",
                    extra={
                        "action_button": {
                            "label": "Save File",
                            "tooltip": "Save the current Natron session to a "
                                       "different file name",
                            # will launch wf2 if configured
                            "callback": _get_save_as_action()
                        }
                    }
                )
            else:
                self.logger.debug(
                    "Work template configured and matches session file.")
        else:
            self.logger.debug("No work template configured.")

        # ---- see if the version can be bumped post-publish

        # check to see if the next version of the work file already exists on
        # disk. if so, warn the user and provide the ability to jump to save
        # to that version now
        (next_version_path, version) = self._get_next_version_info(path, item)
        if next_version_path and os.path.exists(next_version_path):

            # determine the next available version_number. just keep asking for
            # the next one until we get one that doesn't exist.
            while os.path.exists(next_version_path):
                (next_version_path, version) = self._get_next_version_info(
                    next_version_path, item)

            error_msg = "The next version of this file already exists on disk."
            self.logger.error(
                error_msg,
                extra={
                    "action_button": {
                        "label": "Save to v%s" % (version,),
                        "tooltip": "Save to the next available version number, "
                                   "v%s" % (version,),
                        "callback": lambda: _save_session(next_version_path)
                    }
                }
            )
            raise Exception(error_msg)

        # ---- populate the necessary properties and call base class validation

        # populate the publish template on the item if found
        publish_template_setting = settings.get("Publish Template")
        publish_template = publisher.engine.get_template_by_name(
            publish_template_setting.value)
        if publish_template:
            item.properties["publish_template"] = publish_template

        # set the session path on the item for use by the base plugin validation
        # step. NOTE: this path could change prior to the publish phase.

        work_fields = work_template.get_fields(path)
        item.properties["path"] = publish_template.apply_fields(work_fields)
        item.properties["publish_path"] = item.properties["path"]
        item.properties['work_fields']  = work_fields


        # run the base class validation
        return super(KatanaLookdevUsdPublishPlugin, self).validate(settings, item)
      

    def publish(self, settings, item):
        

        publisher = self.parent
        current_engine = sgtk.platform.current_engine()
        context = current_engine.context
        from WWUSD_KATANA import Look
        from WWUSD_KATANA.Exporter import LookExporter

        LookExporter.update_usd_tags()
        return super(KatanaLookdevUsdPublishPlugin, self).publish(settings, item)

        work_fields = item.properties['work_fields']
        export_args = {
            "project" :  context.project['name'],
            "asset_type" : work_fields['sg_asset_type'],
            "asset" :  work_fields['Asset'],
            "dept" :  work_fields["Step"],
            "name" : work_fields['Asset'],
            "ver" : work_fields['version'],
            "renderer": "prman"
        }



        usd_pub_path = "/show/{0}/_3d/assets/{1}".format(context.project['name'],work_fields['Asset'])
        Look.export(export_args, usd_pub_path)

        publish_path = item.properties["path"]

        def _create_usd_library(publish_path):

            current_engine = sgtk.platform.current_engine()
            tk = current_engine.sgtk
            sg = tk.shotgun
            
            project = {"type":"Project","id":884}
            key = [
                    ['project','is',project],
                    ['code','is',os.path.basename(publish_path)],
                    ['sg_project_name','is',context.project['name']]
                ]
            usd_lib_ent = sg.find_one("CustomEntity06",key)

            if usd_lib_ent:
                return

            url = {
                    'content_type': "string",
                    'link_type': "local" ,
                    'name': os.path.basename(publish_path),
                    'local_path':os.path.dirname(publish_path),
                    'url': "string"}

            desc = {"project":project,
                        'code':os.path.basename(publish_path),
                        'sg_path':url,
                        'sg_project_name':context.project['name']}
    
            sg.create("CustomEntity06",desc)
        
        _create_usd_library(publish_path)

        super(KatanaLookdevUsdPublishPlugin, self).publish(settings, item)




def _save_session(path):
    """
    Save the current session to the supplied path.
    """

    # Ensure that the folder is created when saving
    KatanaFile.Save( path )

# TODO: method duplicated in all the natron hooks
def _get_save_as_action():
    """
    Simple helper for returning a log action dict for saving the session
    """

    engine = sgtk.platform.current_engine()

    callback = _save_as

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


def _save_as():
    scene_path = FarmAPI.GetKatanaFileName()
    KatanaFile.Save( scene_path )

def _session_path():

    path = FarmAPI.GetKatanaFileName()

    if path is not None:
        path = six.ensure_str(path)
    
    return path
