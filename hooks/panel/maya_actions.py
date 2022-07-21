import sgtk
import os

HookBaseClass = sgtk.get_hook_baseclass()
print(HookBaseClass)

class MyActions(HookBaseClass):

    def generate_actions(self, sg_data, actions, ui_area):



        action_instances = []
        
        try:
            # call base class first
            action_instances += HookBaseClass.generate_actions(self, sg_data, actions, ui_area)
        except AttributeError as e:
            # base class doesn't have the method, so ignore and continue
            pass        


        if "play_in_rv" in actions:
            action_instances.append( {"name": "play_in_rv",
                "params": None,
                "group": "Pipeline Utils",
                "caption": "Play In Rv",
                "description": "Play In Rv."} )
    
        return action_instances




    def execute_action(self, name, params, sg_data):

        if name == "play_in_rv":
            print(sg_data)
            os.system("rv")

        else:
            super(MyActions, self).execute_action(name, params, sg_data)



