# -*- coding: utf-8 -*-

import os 
import sys
import maya.cmds as cmds
import sgtk


class MayaToTractor(object):

    def __init__(self,item):

        self.item = item
        self._temp_file = os.path.splitext(item.properties["path"])[0]+".py"

    def create_add_frame_script(self,mel_command,sf,ef):
        
        version = cmds.about(version=1)

        original = mel_command
        mel_split  = original.split()
        orignal_file = mel_split[-1]
        original_path = os.path.dirname(orignal_file)
        original_file_name =os.path.basename(orignal_file)
        temp_path = os.path.join(original_path,os.path.basename(orignal_file).split(".")[0]+"_fr")

        script = ''
        script += 'import maya.standalone\n'
        script += 'maya.standalone.initialize()\n'
        script += 'import maya.cmds as cmds\n'
        script += 'import maya.mel as mel\n'
        script += 'import os\n'

        script += '\n'
        script += '\n'

        script += 'cmds.file("{}",open=1,force=1,iv=1)\n'.format(cmds.file(query=True, sn=True))

        if not self.item.properties['name'].find("setgrp") == -1:
            cache_grp = [x for x in cmds.listRelatives(
                self.item.properties['name'],ad=1) 
                         if not x.find("cache_grp") == -1]
            if cache_grp:
                script += 'cache_grp = [x for x in cmds.listRelatives("{}",ad=1) if not x.find("cache_grp") == -1 ]\n'.format(self.item.properties['name'])
                script += 'cmds.select(cache_grp)\n'
            else:
                script += 'cmds.select("{}")\n'.format(self.item.properties['name'])
        else:
            script += 'cmds.select("{}")\n'.format(self.item.properties['name'])

        if version == "2022":
            script += 'cmds.loadPlugin("mayaUsdPlugin.so")\n'
        else:
            script += 'cmds.loadPlugin("pxrUsd.so")\n'
            script += 'cmds.loadPlugin("cvJiggle.so")\n'
            script += 'cmds.loadPlugin("cvwrap.so")\n'
            script += 'cmds.loadPlugin("iDeform.so")\n'
            script += 'cmds.loadPlugin("weightDriver.so")\n'
        script += 'cmds.loadPlugin("AbcExport.so")\n'
        
        for frame in range(sf,ef+1):

            mel_split  = original.split()
            #if not frame == sf:
            #    append_index = mel_split.index("usdExport") + 1
            #    mel_split.insert(append_index,"-a")
            #    mel_split.insert(append_index+1,"1")
            frame_index = mel_split.index("-fr")+1
            mel_split[frame_index] = "{}".format(frame)
            mel_split[frame_index + 1] = "{}".format(frame)
            file_name = mel_split[-1]
            frame_file_name = original_file_name.split(".")[0] + '_{}.usd"'.format(frame)
            frame_file_name = os.path.join(temp_path,frame_file_name)
            mel_split[-1] = frame_file_name
            mel_command = " ".join(mel_split)
            script += 'mel.eval(\'{}\')\n'.format(mel_command)
        
        
        script += 'os.system("usdstitch {0}/*.usd -o {1}")\n'.format(temp_path[1:],orignal_file[1:-1])
        

        with open( self._temp_file, 'w' ) as f:
            f.write(script)

    def create_script(self,mel_command):

        version = cmds.about(version=1)
        script = ''
        script += 'import maya.standalone\n'
        script += 'maya.standalone.initialize()\n'
        script += 'import maya.cmds as cmds\n'
        script += 'import maya.mel as mel\n'

        script += '\n'
        script += '\n'

        script += 'cmds.file("{}",open=1,force=1,iv=1)\n'.format(cmds.file(query=True, sn=True))
        script += 'cmds.select("{}")\n'.format(self.item.properties['name'])
        if version == "2022":
            script += 'cmds.loadPlugin("mayaUsdPlugin.so")\n'
        else:
            script += 'cmds.loadPlugin("pxrUsd.so")\n'
            script += 'cmds.loadPlugin("cvJiggle.so")\n'
            script += 'cmds.loadPlugin("cvwrap.so")\n'
            script += 'cmds.loadPlugin("iDeform.so")\n'
            script += 'cmds.loadPlugin("weightDriver.so")\n'
        script += 'cmds.loadPlugin("AbcExport.so")\n'
        script += 'mel.eval(\'{}\')\n'.format(mel_command)
        
        

        with open( self._temp_file, 'w' ) as f:
            f.write(script)

    def create_camera_usd_script(self,mel_command):


        version = cmds.about(version=1)
        script = ''
        script += 'import maya.standalone\n'
        script += 'maya.standalone.initialize()\n'
        script += 'import maya.cmds as cmds\n'
        script += 'import maya.mel as mel\n'
        
        usd_attribute = ''
        usd_attribute

        script += '\n'
        script += '\n'
        
        script += 'cmds.file("{}",open=1,force=1,iv=1)\n'.format(cmds.file(query=True, sn=True))
        script += 'start = int(cmds.playbackOptions(q=True, min=True))\n'
        script += 'end = int(cmds.playbackOptions(q=True, max=True))\n'
        script += '''camera_shapes = [ x for x in cmds.listRelatives("{}",c=1,f=1,ad=1) 
                                    if cmds.nodeType(x) == "camera"]\n'''.format(self.item.properties['name'])
        script += 'for cam_shape in camera_shapes:\n'
        script += '    cmds.addAttr(cam_shape,ln="frameRange",dt="double2")\n'
        script += '    cmds.setAttr(cam_shape + ".frameRange",start ,end,type="double2")\n'
        script += '    cmds.addAttr(cam_shape,ln="USD_UserExportedAttributesJson",dt="string")\n'
        script += '''    cmds.setAttr(cam_shape+".USD_UserExportedAttributesJson",\
'{"filmFit": {},\
"filmFitOffset": {},\
"horizontalFilmOffset": {}, \
"focalLength": {},\
"postScale": {},\
"fStop": {},\
"horizontalFilmAperture": {},\
"overscan": {},\
"verticalFilmOffset": {},\
"lensSqueezeRatio": {},\
"verticalFilmAperture": {},\
"filmTranslate": {},\
"preScale": {},\
"focusDistance": {},\
"frameRange": {},\
"panZoomEnabled": {},\
"pan": {},\
"zoom": {},\
"cameraScale": {}}',type="string")\n'''
        script += 'cmds.select("{}")\n'.format(self.item.properties['name'])
        if version == "2022":
            script += 'cmds.loadPlugin("mayaUsdPlugin.so")\n'
        else:
            script += 'cmds.loadPlugin("pxrUsd.so")\n'
        script += 'cmds.loadPlugin("AbcExport.so")\n'

        script += 'for shape in camera_shapes:\n'
        script += '    cmds.setAttr(shape + ".overscan", 1.0)\n'
        script += '    if cmds.getAttr(shape + ".panZoomEnabled") == True:\n'
        script += '        cmds.setAttr(shape + ".pan", 0.0, 0.0, typ="float2")\n'
        script += '        cmds.setAttr(shape + ".zoom", 1.0)\n'
        script += '        if cmds.getAttr(shape + ".renderPanZoom") == True:\n'
        script += '            cmds.setAttr(shape + ".renderPanZoom", False)\n'
        script += '            cmds.setAttr(shape + ".panZoomEnabled", False)\n'
        script += 'mel.eval(\'{}\')\n'.format(mel_command)
        
        

        with open( self._temp_file, 'w' ) as f:
            f.write(script)

    def create_camera_abc_script(self,mel_command):

        script = ''
        script += 'import maya.standalone\n'
        script += 'maya.standalone.initialize()\n'
        script += 'import maya.cmds as cmds\n'
        script += 'import maya.mel as mel\n'
        
        usd_attribute = ''
        usd_attribute

        script += '\n'
        script += '\n'
        
        script += 'cmds.file("{}",open=1,force=1,iv=1)\n'.format(cmds.file(query=True, sn=True))
        script += 'start = int(cmds.playbackOptions(q=True, min=True))\n'
        script += 'end = int(cmds.playbackOptions(q=True, max=True))\n'
        script += '''camera_shapes = [ x for x in cmds.listRelatives("{}",c=1,f=1,ad=1) 
                                    if cmds.nodeType(x) == "camera"]\n'''.format(self.item.properties['name'])
        script += 'cmds.select("{}")\n'.format(self.item.properties['name'])
        script += 'cmds.loadPlugin("AbcExport.so")\n'

        script += 'for shape in camera_shapes:\n'
        script += '    cmds.setAttr(shape + ".overscan", 1.0)\n'
        script += '    if cmds.getAttr(shape + ".panZoomEnabled") == True:\n'
        script += '        cmds.setAttr(shape + ".pan", 0.0, 0.0, typ="float2")\n'
        script += '        cmds.setAttr(shape + ".zoom", 1.0)\n'
        script += '        if cmds.getAttr(shape + ".renderPanZoom") == True:\n'
        script += '            cmds.setAttr(shape + ".renderPanZoom", False)\n'
        script += '            cmds.setAttr(shape + ".panZoomEnabled", False)\n'
        script += 'mel.eval(\'{}\')\n'.format(mel_command)
        
        

        with open( self._temp_file, 'w' ) as f:
            f.write(script)

    def _get_default_command(self): 
        
        version = cmds.about(version=1)
        engine = sgtk.platform.current_engine()
        context = engine.context
        project = context.project
        sg = engine.shotgun
        if version == "2022":
            version="2022.1"


        filter_dict = [['code', 'is', 'Maya ' + version], ['projects', 'in', project]]
        packages = sg.find("Software", filter_dict, ['sg_rez'])
        if packages:
            packages = packages[0]['sg_rez']
            pkg_list = packages.split(',')
        else:
            filter_dict = [['code', 'is', "Maya " + version], ['projects', 'is', None]]
            packages = sg.find("Software", filter_dict, ['sg_rez'])
            packages = packages[0]['sg_rez']
            pkg_list = packages.split(',')

        #maya_ver = [pkg[:-4] for pkg in pkg_list if 'maya-' in pkg][0]
        #packages = [pkg for pkg in pkg_list if 'maya-' not in pkg]
        command = ['rez-env'] + pkg_list
        return command

    def to_tractor(self,start_frame,end_frame,file_type):
        
        version = cmds.about(version=1)
        if version == "2022":
            sys.path.append("/westworld/inhouse/tool/rez-packages/tractor/2.2.0/platform-linux/arch-x86_64/lib/python3.6/site-packages")
        else:
            sys.path.append("/westworld/inhouse/tool/rez-packages/tractor/2.2.0/platform-linux/arch-x86_64/lib/python2.7/site-packages")

        import tractor.api.author as author

        job = author.Job()
        job.service = "convert"
        job.priority = 50
        
        file_title = cmds.file(query=True, sn=True).split(".")[0].split("/")[-1]
        project_name =self.item.context.project['name']
        user_name = self.item.context.user['name']
        user_id = os.environ['USER']

        temp = "] ["
        title = []
        title.append(user_name)
        title.append(project_name)
        title.append(file_title)
        title.append(self.item.properties['name'])
        title.append("%d - %d"%(start_frame,end_frame))
        title.append(file_type)
        title = temp.join(title)
        title = "["+title+"]"
        job.title = str(title)

        master_command = self._get_default_command()
        command = master_command[:] + ['--', 'mayapy']

        command.append(self._temp_file)
        command = author.Command(argv=command)

        task = author.Task(title = str(self.item.properties['name']))
        task.addCommand(command)

        rm_command = ['/bin/rm','-f']
        rm_command.append(self._temp_file)
        rm_command = author.Command(argv=rm_command)
        rm_task = author.Task(title = "rm tmp")
        rm_task.addCommand(rm_command)
        
        rm_task.addChild(task)


        job.addChild(rm_task)

        job.spool(hostname="10.0.20.83",owner=user_id)

