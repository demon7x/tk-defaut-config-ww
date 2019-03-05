import sgtk
import os
import subprocess
from sgtk.platform.qt import QtCore, QtGui


HookBaseClass = sgtk.get_hook_baseclass()

class MyActions(HookBaseClass):

    def generate_actions(self, sg_data, actions, ui_area):



        action_instances = []
        
        try:
            # call base class first
            action_instances += HookBaseClass.generate_actions(self, sg_data, actions, ui_area)
        except AttributeError, e:
            # base class doesn't have the method, so ignore and continue
            pass        


        if "play_in_rv" in actions:
            action_instances.append( {"name": "play_in_rv",
                "params": None,
                "caption": "Play In Rv",
                "description": "Play In Rv."} )
    
        return action_instances




    def execute_action(self, name, params, sg_data):

        if name == "play_in_rv":
#           temp =""" -sendEvent \'gma-play-entity\' \'{"protocol_version":1,"server":\
#"https://westworld.shotgunstudio.com","type":"Version","ids":[%s]}"""%sg_data['id']
#            print temp
#            cmd = "rv rvlink://baked/%s"%temp.encode("hex")
            engine = sgtk.platform.current_engine()
            sg = engine.shotgun
            search = [['id','is',sg_data['id']]]
            data = sg.find_one("Version",search,['sg_path_to_movie'])
            path = data['sg_path_to_movie']
 
            if path:
                cmd = "rv %s"%path
                subprocess.Popen(cmd, shell=True)
            else:
                sg_data.get("sg_uploaded_movie")
                sg_url = self.sgtk.shotgun_url
                url = "%s/page/media_center?type=Version&id=%d" % (sg_url, sg_data["id"])
                QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))



        else:
            super(MyActions, self).execute_action(name, params, sg_data)



