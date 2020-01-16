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

import glob
import os
import sys
import re
import pymel.core as pm
import maya.cmds as cmds
import maya.mel as mel
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class MayaUSDActions(HookBaseClass):
    
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
        
        action_instances = super(MayaUSDActions, self).generate_actions(sg_publish_data, actions, ui_area)
        
        if "usd_reference" in actions:
            action_instances.append( {"name": "usd_reference", 
                                      "params": None,
                                      "caption": "Create USD Reference", 
                                      "description": "This will add the item to the scene as a usd reference."} )

        if "viewer" in actions:
            action_instances.append( {"name": "viewer", 
                                      "params": None,
                                      "caption": "Viewer File", 
                                      "description": "This will add the item to the scene as a usd reference."} )

        if "merge" in actions:
            action_instances.append( {"name": "merge", 
                                      "params": None,
                                      "caption": "Merge to select node", 
                                      "description": "This will merge to select node."} )

        return action_instances


    def execute_action(self, name, params, sg_publish_data):
        """
        Execute a given action. The data sent to this be method will
        represent one of the actions enumerated by the generate_actions method.
        
        :param name: Action name string representing one of the items returned by generate_actions.
        :param params: Params data, as specified by generate_actions.
        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        :returns: No return value expected.
        """
        
        # resolve path
        # toolkit uses utf-8 encoded strings internally and Maya API expects unicode
        # so convert the path to ensure filenames containing complex characters are supported
        path = self.get_publish_path(sg_publish_data).decode("utf-8")
        
        if name == "usd_reference":
            usd_file = path
            usd_name = sg_publish_data.get("entity").get("name")
            usd_ref = cmds.createNode("pxrUsdReferenceAssembly",name=usd_name)
            cmds.setAttr(usd_ref+".filePath",usd_file,type="string")
            cmds.assembly(usd_ref,e=1 ,activeLabel="Playback")

        elif name == "reference":
            self._create_reference(path, sg_publish_data)

        elif name == "import":
            self._do_import(path, sg_publish_data)

        elif name == "merge":
            self._do_merge(path, sg_publish_data)
        
        elif name == "viewer":
            
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
                
            

        else:
            super(MayaUSDActions, self).execute_action(name, params, sg_publish_data)


    

    def _get_rez_module(self):
        
        import subprocess

        command = 'rez-env rez -- printenv REZ_REZ_ROOT'
        module_path, stderr = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()
        module_path = module_path.strip()
        if not stderr and module_path:
            return module_path
        
        return ""


    
    def _create_reference(self, path, sg_publish_data):
        if not os.path.exists(path):
            raise Exception("File not found on disk - '%s'" % path)
        
        namespace = sg_publish_data.get("entity").get('name')
                
        pm.system.createReference(path, 
                                  loadReferenceDepth= "all", 
                                  mergeNamespacesOnClash=False, 
                                  namespace=namespace)

    def _do_import(self, path, sg_publish_data):
        if not os.path.exists(path):
            raise Exception("File not found on disk - '%s'" % path)

        task_name = sg_publish_data['task']['name'] 
        published_file_type = sg_publish_data['published_file_type']['name'] 
        asset_name = sg_publish_data.get("entity").get("name")

        if task_name == "model" and published_file_type == "Maya Scene":
            create_parent_tr = cmds.confirmDialog( 
                title='Confirm', 
                message='Do you want to create cache transform node ?', 
                button=['Yes','No'], 
                defaultButton='Yes', 
                cancelButton='No', 
                dismissString='No' )
        node = cmds.file(path,rnn=1,i=1,rdn=1 ,rpr='clash',options="v=0",pr=1,lrd="all",iv=1)
        node = cmds.ls(node, assemblies=True)
        if create_parent_tr == "Yes":
            cache_tr = cmds.createNode("transform",n="{0}_cache_grp".format(node[0]))
            grp_tr = cmds.createNode("transform",n="{0}_grp".format(node[0]))
            cmds.parent(node[0],cache_tr)
            cmds.parent(cache_tr,grp_tr)

    def _do_merge(self, path, sg_publish_data):
        if not os.path.exists(path):
            raise Exception("File not found on disk - '%s'" % path)
        
        print path
        select_node = cmds.ls(sl=1)
        if not select_node and not len(select_node) == 1:
            return
        command = 'AbcImport -mode import -connect "%s" "%s"'%(select_node[0],path)
        mel.eval(command)
