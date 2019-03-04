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
import maya.cmds as cmds
import sgtk


# this method returns the evaluated hook base class. This could be the Hook
# class defined in Toolkit core or it could be the publisher app's base publish
# plugin class as defined in the configuration.
HookBaseClass = sgtk.get_hook_baseclass()


class WwMayaAlembicPublishPlugin(HookBaseClass):

    @property
    def description(self):

        return """
        <p>
        This plugin handles exporting and publishing Maya shader networks.
        Collected mesh shaders are exported to disk as .ma files that can
        be loaded by artists downstream. This is a simple, example
        implementation and not meant to be a robust, battle-tested solution for
        shader or texture management on production.
        </p>
        """

    @property
    def settings(self):

        # inherit the settings from the base publish plugin
        plugin_settings = super(WwMayaAlembicPublishPlugin, self).settings or {}

        # settings specific to this class
        alembic_publish_settings = {
            "Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published shader networks. "
                               "Should correspond to a template defined in "
                               "templates.yml.",
            }
        }

        # update the base settings
        plugin_settings.update(alembic_publish_settings)

        return plugin_settings

    @property
    def item_filters(self):
        # NOTE: this matches the item type defined in the collector.
        return ["maya.session.alembic"]

    ############################################################################
    # Publish processing methods

    def accept(self, settings, item):
        accepted = True

        publisher = self.parent

        template_name = settings["Publish Template"].value

        work_template = item.parent.properties.get("work_template")
        if not work_template:
            self.logger.debug(
                "A work template is required for the session item in order to "
                "publish session geometry. Not accepting session geom item."
            )
            accepted = False

        publish_template = publisher.get_template_by_name(template_name)
        self.logger.debug("TEMPLATE NAME: " + str(template_name))
        if not publish_template:
            self.logger.debug(
                "A valid publish template could not be determined for the "
                "session geometry item. Not accepting the item."
            )
            accepted = False

        item.properties["publish_template"] = publish_template

        item.context_change_allowed = False

        return {
            "accepted": accepted,
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

        # get the normalized path. checks that separators are matching the
        # current operating system, removal of trailing separators and removal
        # of double separators, etc.
        path = sgtk.util.ShotgunPath.normalize(path)

        object_name = item.properties["object"]

        # check that there is still geometry in the scene:
        if (not cmds.ls(assemblies=True) or
            not cmds.ls(object_name, dag=True, type="mesh")):
            error_msg = (
                "Validation failed because there are no meshes in the scene "
                "to export shaders for. You can uncheck this plugin or create "
                "meshes with shaders to export to avoid this error."
            )
            self.logger.error(error_msg)
            raise Exception(error_msg)

        # get the configured work file template
        work_template = item.parent.properties.get("work_template")
        publish_template = item.properties.get("publish_template")

        # get the current scene path and extract fields from it using the work
        # template:
        work_fields = work_template.get_fields(path)

        # we want to override the {name} token of the publish path with the
        # name of the object being exported. get the name stored by the
        # collector and remove any non-alphanumeric characters
        object_display = re.sub(r'[\W_]+', '', object_name)
        work_fields["name"] = object_display

        # set the display name as the name to use in SG to represent the publish
        item.properties["publish_name"] = object_display

        # ensure the fields work for the publish template
        missing_keys = publish_template.missing_keys(work_fields)
        if missing_keys:
            error_msg = "Work file '%s' missing keys required for the " \
                        "publish template: %s" % (path, missing_keys)
            self.logger.error(error_msg)
            raise Exception(error_msg)

        # create the publish path by applying the fields. store it in the item's
        # properties. Also set the publish_path to be explicit.
        item.properties["path"] = publish_template.apply_fields(work_fields)
        item.properties["publish_path"] = item.properties["path"]

        # use the work file's version number when publishing
        if "version" in work_fields:
            item.properties["publish_version"] = work_fields["version"]

        # run the base class validation
        return super(MayaShaderPublishPlugin, self).validate(
            settings, item)

    def publish(self, settings, item):

        publisher = self.parent

        # get the path to create and publish
        publish_path = item.properties["path"]

        # ensure the publish folder exists:
        publish_folder = os.path.dirname(publish_path)
        publisher.ensure_folder_exists(publish_folder)

        mesh_object = item.properties["object"]

        # now just export shaders for this item to the publish path. there's
        # probably a better way to do this.
        super(WwMayaAlembicPublishPlugin, self).publish(settings, item)

def _session_path():
    """
    Return the path to the current session
    :return:
    """
    path = cmds.file(query=True, sn=True)

    if isinstance(path, unicode):
        path = path.encode("utf-8")

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


