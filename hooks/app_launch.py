# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
App Launch Hook

This hook is executed to launch the applications.
"""

import os
import re
import sys
import subprocess
import platform
import tank

#rez append 
#sys.path.append("/westworld/inhouse/rez/lib/python2.7/site-packages/rez-2.23.1-py2.7.egg")

ENGINES = {
    'tk-houdini':'houdini',
    'tk-maya': 'maya' ,
    'tk-nuke': 'nuke',
    'tk-katana': 'katana',
    'tk-mari' : 'mari'
}


REZ_SETTINGS = {
    'maya-2017':('maya-2017','ww_maya_shelf','nodeAuth','golaem','fracture'),
    'maya-2018':('maya-2018','ww_maya_shelf','nodeAuth',),
    'maya-2019':('maya-2019','ww_maya_shelf',),
    'nuke-10.0v5':('nuke-10.0.5',),
    'nuke-11.2v5':('nuke-11.2.5',),
    'katana-3.0v5':('katana-3.0.5','renderman'),
    'katana-3.1v2':('katana-3.1.2','renderman')
    }

class AppLaunch(tank.Hook):
    """
    Hook to run an application.
    """
    
    def execute(self, app_path, app_args, version, engine_name, **kwargs):
        """
        The execute functon of the hook will be called to start the required application
        
        :param app_path: (str) The path of the application executable
        :param app_args: (str) Any arguments the application may require
        :param version: (str) version of the application being run if set in the
            "versions" settings of the Launcher instance, otherwise None
        :param engine_name (str) The name of the engine associated with the
            software about to be launched.

        :returns: (dict) The two valid keys are 'command' (str) and 'return_code' (int).
        """

        system = sys.platform
        
        adapter = get_adapter(platform.system())

        try:
            import rez as _
        except ImportError:
            rez_path = adapter.get_rez_module_root()
            if not rez_path:
                raise EnvironmentError('rez is not installed and could not be automatically found. Cannot continue.')

            sys.path.append(rez_path)
        
        from rez import resolved_context
        
        app_name = ENGINES[engine_name]
        
        packages = REZ_SETTINGS[app_name+"-"+version]

        if not packages:
            self.logger.debug('No rez packages were found. The default boot, instead.')
            command = adapter.get_command(app_path, app_args)
            return_code = os.system(command)
            return {'command': command, 'return_code': return_code}

        context = resolved_context.ResolvedContext(packages)
        return adapter.execute(context, app_args,app_name)
        




class BaseAdapter(object):


    shell_type = 'bash'

    @staticmethod
    def get_command(path, args):

        return '"{path}" {args} &'.format(path=path, args=args)

    @staticmethod
    def get_rez_root_command():

        return 'rez-env rez -- printenv REZ_REZ_ROOT'

    @classmethod
    def get_rez_module_root(cls):

        command = cls.get_rez_root_command()
        module_path, stderr = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()

        module_path = module_path.strip()

        if not stderr and module_path:
            return module_path

        return ''

    @classmethod
    def execute(cls, context, args,command):

        os.environ['USE_SHOTGUN'] = "OK"

        if args:
            command += ' {args}'.format(args=args)

        proc = context.execute_shell(
            command=command,
            stdin=False,
            block=False
        )
        
        return_code = 0
        context.print_info(verbosity=True)

        return {
            'command': command,
            'return_code': return_code,
        }


class LinuxAdapter(BaseAdapter):


    pass


class WindowsAdapter(BaseAdapter):


    shell_type = 'cmd'

    @staticmethod
    def get_command(path, args):
        return 'start /B "App" "{path}" {args}'.format(path=path, args=args)

    @staticmethod
    def get_rez_root_command():

        return 'rez-env rez -- echo %REZ_REZ_ROOT%'






def get_adapter(system=''):
    if not system:
        system = platform.system()
    
    options = {
        'Linux' : LinuxAdapter,
        'Windows' : WindowsAdapter
        }


    try :
        return options[system]

    except KeyError:
        raise NotImplementedError('system "{system}" is currently unsupported. Options were, "{options}"'
                                  ''.format(system=system, options=list(options)))
