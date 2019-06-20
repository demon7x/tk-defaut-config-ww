"""
Hook that loads defines all the available actions, broken down by publish type.
Copied from tk-maya_actions
"""
import sgtk
import os
import sys
import NodegraphAPI

HookBaseClass = sgtk.get_hook_baseclass()

class KatanaActions(HookBaseClass):

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
        app = self.parent
        app.log_debug("Generate actions called for UI element %s. "
                      "Actions: %s. Publish Data: %s" % (ui_area, actions, sg_publish_data))
        
        action_instances = []
        
        if "open_project" in actions:
            action_instances.append( {"name": "open_project", 
                                      "params": None,
                                      "caption": "Open Project", 
                                      "description": "This will open the Katana project file."} )

        if "import_look_file" in actions:
            action_instances.append( {"name": "import_look_file", 
                                      "params": None,
                                      "caption": "Import Look File", 
                                      "description": "This will create an LookFileAssign node corresponding to this published Look File."} )

        if "create_node_Alembic_In" in actions:
            action_instances.append( {"name": "create_node_Alembic_In", 
                                      "params": None,
                                      "caption": "Import Alembic", 
                                      "description": "This will create an Alembic_In node corresponding to this cache."} )

        if "create_node_ImageRead" in actions:
            action_instances.append( {"name": "create_node_ImageRead",
                                      "params": None, 
                                      "caption": "Import image", 
                                      "description": "Creates an ImageRead node for the selected item."} )

        if "create_pxrusd_in" in actions:
            action_instances.append( {"name": "create_pxrusd_in",
                                      "params": None, 
                                      "caption": "Import usd", 
                                      "description": "Creates a Usd."} )

        if "create_scenegraphXml" in actions:
            action_instances.append( {"name": "create_scenegraphXml",
                                      "params": None, 
                                      "caption": "Import XML", 
                                      "description": "Creates a XML."} )

        if "viewer" in actions:
            action_instances.append( {"name": "viewer", 
                                      "params": None,
                                      "caption": "View File", 
                                      "description": "launch usdviewer."} )

        if "copy_path" in actions:
            action_instances.append( {"name": "copy_path", 
                                      "params": None,
                                      "caption": "Copy Path to clipboard", 
                                      "description": "Copy path to clipboard."} )

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
        
        # resolve path
        path = self.get_publish_path(sg_publish_data)
        
        if name == "open_project":
            self._open_project(path, sg_publish_data)

        if name == "import_look_file":
            self._open_project(path, sg_publish_data)

        if name == "create_node_Alembic_In":
            self._create_node("ABC", path, sg_publish_data, asset_parameter="abcAsset")
        
        if name == "create_node_ImageRead":
            self._create_node("ImageRead", path, sg_publish_data, asset_parameter="file")

        if name == "create_pxrusd_in":

            self._create_node("USD", path, sg_publish_data, asset_parameter="fileName")

        if name == "create_scenegraphXml":
            self._create_node("XML", path, sg_publish_data, asset_parameter="asset")

        if name == "viewer":

            rez_path = self._get_rez_module()
            sys.path.append(rez_path)
            from rez import resolved_context
            packages = ("usd","PySide")
            context = resolved_context.ResolvedContext(packages)
            command = "usdview"
            command  +=' {path}'.format(path=path)
            context.execute_shell(command = command,
                                 stdin = False,
                                 block=False,
                                 )

        if name == "copy_path":

            rez_path = self._get_rez_module()
            sys.path.append(rez_path)
            from rez import resolved_context
            packages = ("pyperclip",)
            context = resolved_context.ResolvedContext(packages)
            sys.path.append(context.get_environ()['PYTHONPATH'])
            import pyperclip
            pyperclip.copy(path)
            
    ##############################################################################################################
    # helper methods which can be subclassed in custom hooks to fine tune the behaviour of things

    def _open_project(self, path, sg_publish_data):
        """
        """
        return

    def _create_node(self, file_type, path, sg_publish_data, asset_parameter="file"):
        """
        Generic node creation method.
        """
        if not os.path.exists(path):
            raise Exception("File not found on disk - '%s'" % path)
        
        select = {"ABC":2,"USD":1,"XML":0}
        version = sg_publish_data.get("version_number")
        entity_type = sg_publish_data.get("entity").get("type")
        root = NodegraphAPI.GetRootNode()
        pos=NodegraphAPI.GetViewPortPosition(root) 

        if entity_type == "Asset":
            
            name = sg_publish_data.get("entity").get("name")
            node = NodegraphAPI.CreateNode("Asset_In", parent=root)
            NodegraphAPI.SetNodePosition(node, (pos[0][0], pos[0][1]))
            file_type_param = node.getParameters().getChild("user").getChild("Pubfile_Type")
            file_type_param.setValue(select[file_type],0)
            name_param = node.getParameters().getChild("user").getChild("name")
            name_param.setValue(name,0)

            version_param = node.getParameters().getChild("user").getChild("version")
            version_param.setValue("v%03d"%version,0)
            
            if not file_type == "XML":

                path_param = node.getParameters().getChild("user").getChild(file_type)
                path_param.setValue(path,0)
            else:
                path_param = node.getParameters().getChild("user").getChild("sgxml")
                path_param.setValue(path,0)
        
        else:

        # Create node

            name = sg_publish_data.get("name")
            node = NodegraphAPI.CreateNode("Geo_In", parent=root)
            NodegraphAPI.SetNodePosition(node, (pos[0][0], pos[0][1]))
            file_type_param = node.getParameters().getChild("user").getChild("fileType")
            file_type_param.setValue(select[file_type],0)
            path_param = node.getParameters().getChild("user").getChild("asset")
            path_param.setValue(path,0)
            name_param = node.getParameters().getChild("user").getChild("rename")
            name_param.setValue(name,0)

        return node


    def _get_rez_module(self):
        
        import subprocess

        command = 'rez-env rez -- printenv REZ_REZ_ROOT'
        module_path, stderr = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()
        module_path = module_path.strip()
        if not stderr and module_path:
            return module_path
        
        return ""
