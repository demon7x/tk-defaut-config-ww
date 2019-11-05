# Copyright (c) 2015 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Hook that loads defines all the available actions, broken down by publish type. 
"""
import os
import re
import glob
import sys
import nuke

import sgtk

HookBaseClass = sgtk.get_hook_baseclass()

class NukeAddActions(HookBaseClass):
    
    ##############################################################################################################
    # public interface - to be overridden by deriving classes 
    
    def generate_actions(self, sg_publish_data, actions, ui_area):
        """
        Returns a list of action instances for a particular publish.
        This method is called each time a user clicks a publish somewhere in the UI.
        The data returned from this hook will be used to populate the actions menu for a publish.
    
        The mapping between Publish types and actions are kept in a different place
        (in the configuration) so at the point when this hook is called, the loader app
        has already established *which* actions are appropriate for this object.
        
        The hook should return at least one action for each item passed in via the 
        actions parameter.
        
        This method needs to return detailed data for those actions, in the form of a list
        of dictionaries, each with name, params, caption and description keys.
        
        Because you are operating on a particular publish, you may tailor the output 
        (caption, tooltip etc) to contain custom information suitable for this publish.
        
        The ui_area parameter is a string and indicates where the publish is to be shown. 
        - If it will be shown in the main browsing area, "main" is passed. 
        - If it will be shown in the details area, "details" is passed.
        - If it will be shown in the history area, "history" is passed. 
        
        Please note that it is perfectly possible to create more than one action "instance" for 
        an action! You can for example do scene introspection - if the action passed in 
        is "character_attachment" you may for example scan the scene, figure out all the nodes
        where this object can be attached and return a list of action instances:
        "attach to left hand", "attach to right hand" etc. In this case, when more than 
        one object is returned for an action, use the params key to pass additional 
        data into the run_action hook.
        
        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        :param actions: List of action strings which have been defined in the app configuration.
        :param ui_area: String denoting the UI Area (see above).
        :returns List of dictionaries, each with keys name, params, caption and description
        """

        action_instances = super(NukeAddActions, self).generate_actions(sg_publish_data, actions, ui_area)

        if "read_channel" in actions:
            action_instances.append( {"name": "read_channel", 
                                      "params": None,
                                      "caption": "Create Read Node By Channel", 
                                      "description": "This will add a read node to the current scene."} )
        if "rv" in actions:
            action_instances.append( {"name": "rv", 
                                      "params": None,
                                      "caption": "RV view version", 
                                      "description": "This will view version by RV."} )
        
        return action_instances

    def execute_multiple_actions(self, actions):
        """
        Executes the specified action on a list of items.

        The default implementation dispatches each item from ``actions`` to
        the ``execute_action`` method.

        The ``actions`` is a list of dictionaries holding all the actions to execute.
        Each entry will have the following values:

            name: Name of the action to execute
            sg_publish_data: Publish information coming from Shotgun
            params: Parameters passed down from the generate_actions hook.

        .. note::
            This is the default entry point for the hook. It reuses the ``execute_action``
            method for backward compatibility with hooks written for the previous
            version of the loader.

        .. note::
            The hook will stop applying the actions on the selection if an error
            is raised midway through.

        :param list actions: Action dictionaries.
        """
        for single_action in actions:
            name = single_action["name"]
            sg_publish_data = single_action["sg_publish_data"]
            params = single_action["params"]
            self.execute_action(name, params, sg_publish_data)

    def execute_action(self, name, params, sg_publish_data):
        """
        Execute a given action. The data sent to this be method will
        represent one of the actions enumerated by the generate_actions method.
        
        :param name: Action name string representing one of the items returned by generate_actions.
        :param params: Params data, as specified by generate_actions.
        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        :returns: No return value expected.
        """
        app = self.parent
        
        app.log_debug("Execute action called for action %s. "
                      "Parameters: %s. Publish Data: %s" % (name, params, sg_publish_data))
        
        # resolve path - forward slashes on all platforms in Nuke
        path = self.get_publish_path(sg_publish_data).replace(os.path.sep, "/")
        
        if name == "read_channel":
            self._select_channel_view(path, sg_publish_data)
        
        if name == "rv":

            rez_path = self._get_rez_module()
            sys.path.append(rez_path)
            from rez import resolved_context
            packages = ("rv",)
            context = resolved_context.ResolvedContext(packages)
            command = "rv"
            command  +=' {path}'.format(path=path)
            context.execute_shell(command = command,
                                 stdin = False,
                                 block=False,
                                 )

        else:
            super(NukeAddActions, self).execute_action(name, params, sg_publish_data)


    ##############################################################################################################
    # helper methods which can be subclassed in custom hooks to fine tune the behavior of things


    def _select_channel_view(self,path,sg_publish_data):
        channels = os.listdir(os.path.dirname(os.path.dirname(path)))
        print channels
        panel = nuke.Panel("select channel")
        for channel in channels:
            panel.addBooleanCheckBox(channel,True)
        ret=panel.show()
        select_channels = []
        for channel in channels:
            if panel.value(channel):
                select_channels.append(channel)

        xpos , ypos = self._find_position()
        ex_x = xpos
        ex_y = ypos -150
        
        if "DeepID" in select_channels :
            select_channels.remove("DeepID")
            select_channels.append("DeepID")

        for channel in select_channels:
            if channel == "Extra":
                extra_path = os.path.dirname(path.replace("primary",channel))
                for extra in os.listdir(extra_path):
                    default_path = os.path.join(extra_path,
                    extra,os.path.basename(path))
                    self._create_channel_read_node(default_path,extra,ex_x,ex_y,sg_publish_data)
                    ex_x = ex_x + 100
            else:
                self._create_channel_read_node(path,channel,xpos,ypos,sg_publish_data)
                xpos = xpos + 100



    
    def _create_channel_read_node(self,default_path,channel,x,y,sg_publihs_data):

        import nuke

        path = default_path.replace("primary",channel)
        
        
        
        if channel == "DeepID":
            temp = os.path.dirname(path)
            deep_path = nuke.getFileNameList(temp)[0]
            deep_path = os.path.join(temp,deep_path)
            
            DeepRead = nuke.createNode("DeepRead")
            DeepRead.knob('file').fromUserText(deep_path)
            DeepRead['xpos'].setValue(x)
            DeepRead['ypos'].setValue(y+100)
            nuke.Layer( 'other', ['id'] )
            deep_exp = nuke.nodes.DeepExpression()
            deep_exp['xpos'].setValue(x)
            deep_exp['ypos'].setValue(y+150)
            deep_exp.setInput(0,DeepRead)
            deep_exp['chans0'].setValue('other')
            deep_exp['chans1'].setValue('none')
            deep_exp['other.id'].setValue('exponent(id)')

            DRC = nuke.nodes.DeepRecolor()
            DRC['xpos'].setValue(x)
            DRC['ypos'].setValue(y+200)
            DRC.setInput(0,deep_exp)
            constant = nuke.nodes.Constant()
            constant['xpos'].setValue(DRC.xpos()+200)
            constant['ypos'].setValue(DRC.ypos()-23)
            DRC.setInput(1,constant)
            DP = nuke.nodes.DeepPicker()
            DP['xpos'].setValue(x)
            DP['ypos'].setValue(y+250)
            DP.setInput(0,DRC)

        else:

            read_node = nuke.createNode("Read")
            read_node["file"].fromUserText(path)
            seq_range = self._find_sequence_range(path)
            read_node['xpos'].setValue(x)
            read_node['ypos'].setValue(y+100)
            if self._get_colorspace() == "ACES2065-1":
                read_node['colorspace'].setValue("ACES - ACEScg")

            if seq_range:
                read_node["first"].setValue(seq_range[0])
                read_node["last"].setValue(seq_range[1])

    
    def _get_colorspace(self):

        engine = sgtk.platform.current_engine()
        context = engine.context
        project = context.project
        shot = context.entity

        shotgun = engine.shotgun
        output_info = shotgun.find_one("Project",[['id','is',project['id']]],
                                ['sg_colorspace','sg_mov_codec',
                                'sg_out_format','sg_fps','sg_mov_colorspace'])
        
        return output_info['sg_colorspace']


    def _find_position(self):
        import nuke
        all_nodes = nuke.allNodes()
        xpos_t , ypos_t = 0,0

        for node in all_nodes:
            if node.xpos() < xpos_t:
                xpos_t = node.xpos()
            if node.ypos() > ypos_t:
                y_pos_t = node.ypos()
        return xpos_t - 300 , ypos_t + 300


    def _rv(self,path,sg_publish_data):
        pass

    def _create_read_node(self, path, sg_publish_data):
        """
        Create a read node representing the publish.
        
        :param path: Path to file.
        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.        
        """        
        import nuke
        
        (_, ext) = os.path.splitext(path)
        
        colorspace = self._get_colorspace()

        # If this is an Alembic cache, use a ReadGeo2 and we're done.
        if ext.lower() == ".abc":
            nuke.createNode("ReadGeo2", "file {%s}" % path)
            return

        valid_extensions = [".png", 
                            ".jpg", 
                            ".jpeg", 
                            ".exr", 
                            ".cin", 
                            ".dpx", 
                            ".tiff", 
                            ".tif", 
                            ".mov",
                            ".mp4",
                            ".psd",
                            ".tga",
                            ".ari",
                            ".gif",
                            ".iff"]

        if ext.lower() not in valid_extensions:
            raise Exception("Unsupported file extension for '%s'!" % path)

        # `nuke.createNode()` will extract the format and frame range from the
        # file itself (if possible), whereas `nuke.nodes.Read()` won't. We'll
        # also check to see if there's a matching template and override the
        # frame range, but this should handle the zero config case. This will
        # also automatically extract the format and frame range for movie files.
        read_node = nuke.createNode("Read")
        read_node["file"].fromUserText(path)
        if sg_publish_data['published_file_type']['name'] in ["Plate",'Source']:
            if self._get_colorspace() == "ACES2065-1" and path.split(".")[-1] == "exr" :
                read_node['colorspace'].setValue("ACES - ACES2065-1")
            if self._get_colorspace() == "ACES2065-1" and path.split(".")[-1] == "dpx" :
                read_node['colorspace'].setValue("Output - Rec.709")

        # find the sequence range if it has one:
        seq_range = self._find_sequence_range(path)

        if seq_range:
            # override the detected frame range.
            read_node["first"].setValue(seq_range[0])
            read_node["last"].setValue(seq_range[1])

    def _sequence_range_from_path(self, path):
        """
        Parses the file name in an attempt to determine the first and last
        frame number of a sequence. This assumes some sort of common convention
        for the file names, where the frame number is an integer at the end of
        the basename, just ahead of the file extension, such as
        file.0001.jpg, or file_001.jpg. We also check for input file names with
        abstracted frame number tokens, such as file.####.jpg, or file.%04d.jpg.

        :param str path: The file path to parse.

        :returns: None if no range could be determined, otherwise (min, max)
        :rtype: tuple or None
        """
        # This pattern will match the following at the end of a string and
        # retain the frame number or frame token as group(1) in the resulting
        # match object:
        #
        # 0001
        # ####
        # %04d
        #
        # The number of digits or hashes does not matter; we match as many as
        # exist.
        frame_pattern = re.compile(r"([0-9#]+|[%]0\dd)$")
        root, ext = os.path.splitext(path)
        match = re.search(frame_pattern, root)

        # If we did not match, we don't know how to parse the file name, or there
        # is no frame number to extract.
        if not match:
            return None

        # We need to get all files that match the pattern from disk so that we
        # can determine what the min and max frame number is.
        glob_path = "%s%s" % (
            re.sub(frame_pattern, "*", root),
            ext,
        )
        files = glob.glob(glob_path)

        # Our pattern from above matches against the file root, so we need
        # to chop off the extension at the end.
        file_roots = [os.path.splitext(f)[0] for f in files]

        # We know that the search will result in a match at this point, otherwise
        # the glob wouldn't have found the file. We can search and pull group 1
        # to get the integer frame number from the file root name.
        frames = [int(re.search(frame_pattern, f).group(1)) for f in file_roots]
        return (min(frames), max(frames))

    def _find_sequence_range(self, path):
        """
        Helper method attempting to extract sequence information.
        
        Using the toolkit template system, the path will be probed to 
        check if it is a sequence, and if so, frame information is
        attempted to be extracted.
        
        :param path: Path to file on disk.
        :returns: None if no range could be determined, otherwise (min, max)
        """
        # find a template that matches the path:
        template = None
        try:
            template = self.parent.sgtk.template_from_path(path)
        except sgtk.TankError:
            pass
        
        if not template:
            # If we don't have a template to take advantage of, then 
            # we are forced to do some rough parsing ourself to try
            # to determine the frame range.
            return self._sequence_range_from_path(path)
            
        # get the fields and find all matching files:
        fields = template.get_fields(path)
        if not "SEQ" in fields:
            return None
        
        files = self.parent.sgtk.paths_from_template(template, fields, ["SEQ", "eye"])
        
        # find frame numbers from these files:
        frames = []
        for file in files:
            fields = template.get_fields(file)
            frame = fields.get("SEQ")
            if frame != None:
                frames.append(frame)
        if not frames:
            return None
        
        # return the range
        return (min(frames), max(frames))


    def _get_rez_module(self):
        
        import subprocess

        command = 'rez-env rez -- printenv REZ_REZ_ROOT'
        module_path, stderr = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()
        module_path = module_path.strip()
        if not stderr and module_path:
            return module_path
        
        return ""
