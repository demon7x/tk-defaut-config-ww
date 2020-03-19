# -*- coding: utf-8 -*-

import os 
import sys
import maya.cmds as cmds


class MayaToTractor(object):

    def __init__(self,item):

        self.item = item
        self._temp_file = os.path.splitext(item.properties["path"])[0]+".py"


    def create_script(self,mel_command):

        script = ''
        script += 'import maya.standalone\n'
        script += 'maya.standalone.initialize()\n'
        script += 'import maya.cmds as cmds\n'
        script += 'import maya.mel as mel\n'

        script += '\n'
        script += '\n'

        script += 'cmds.file("{}",open=1,force=1,iv=1)\n'.format(cmds.file(query=True, sn=True))
        script += 'cmds.select("{}")\n'.format(self.item.properties['name'])
        script += 'cmds.loadPlugin("pxrUsd.so")\n'
        script += 'cmds.loadPlugin("AbcExport.so")\n'
        script += 'cmds.loadPlugin("cvJiggle.so")\n'
        script += 'cmds.loadPlugin("cvwrap.so")\n'
        script += 'cmds.loadPlugin("iDeform.so")\n'
        script += 'mel.eval(\'{}\')\n'.format(mel_command)
        
        

        with open( self._temp_file, 'w' ) as f:
            f.write(script)

    def create_camera_usd_script(self,mel_command):

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
"cameraScale": {}}',type="string")\n'''
        script += 'cmds.select("{}")\n'.format(self.item.properties['name'])
        script += 'cmds.loadPlugin("pxrUsd.so")\n'
        script += 'cmds.loadPlugin("AbcExport.so")\n'
        script += 'mel.eval(\'{}\')\n'.format(mel_command)
        
        

        with open( self._temp_file, 'w' ) as f:
            f.write(script)

    def to_tractor(self,start_frame,end_frame,file_type):
        
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

        command = ['rez-env','maya-2019vfarm','usd-19.03','yeti','ideform','--','mayapy']
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

        job.spool(hostname="10.0.20.82",owner=user_id)

