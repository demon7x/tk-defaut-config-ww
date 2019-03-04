
import glob
import os
import maya.cmds as cmds
import maya.mel as mel
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()



class WwMayaSessionCollector(HookBaseClass):
    


    def process_current_session(self, settings, parent_item):

        self._collect_shot_alembic(parent_item)
        super(WwMayaSessionCollector, self).process_current_session(settings,parent_item)
    
    def _collect_shot_alembic(self,parent_item):
        
        icon_path = os.path.join(
            self.disk_location,
            os.pardir,
            "icons",
            "alembic.png"
        )

        for object in cmds.ls(type="transform"):
            
            alembic_item = parent_item.create_item(
                "maya.session.alembic",
                "Alembic",
                object
                )
            
            alembic_item.set_icon_from_path(icon_path)

            alembic_item.properties['object'] = object



