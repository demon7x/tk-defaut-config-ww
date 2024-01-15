# :coding: utf-8
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
import sys
import re
import pprint
import traceback

import sgtk
from sgtk.util.filesystem import copy_file, ensure_folder_exists
from sgtk.platform.qt import QtGui, QtCore

from maya import cmds

HookBaseClass = sgtk.get_hook_baseclass()


class BasicFilePublishPlugin(HookBaseClass):

    @property
    def settings(self):

        settings = super(BasicFilePublishPlugin, self).settings or {}


        sframe = int( cmds.playbackOptions( q = 1, min = 1 ) )
        eframe = int( cmds.playbackOptions( q = 1, max = 1 ) )
        tpos_frame = sframe - 50
        stable_frame = sframe -30 


        ## Defining Path information
        scene_path = cmds.file( sn = 1 , q = 1 )
        if not scene_path:
            return
        part = scene_path.partition( '/dev/' )
        pipeline_step = part[0].split( os.sep )[-1]
        pub_path = part[0] + os.sep + 'pub'



        # get version
        p = re.compile( '%s_v[0-9]{3}' % pipeline_step )
        m = p.search( scene_path )
        version = re.search('(?<=_v)\d{2,3}' , scene_path).group() if re.search('(?<=_v)\d{2,3}' , scene_path) else ''
        ver_part = scene_path.rpartition( version )
        subject_grp = re.search("(?<=_).+?(?=\.mb)" , os.path.splitext( scene_path )[0] )
        subject = subject_grp.group() if subject_grp else ''
        if subject:
            version = version + '_' + subject
        basename = os.path.splitext( os.path.basename( scene_path ) )[0]

        pub_cache_path  = os.path.join( pub_path , 'caches' )
        usd_path        = os.path.join( pub_cache_path , 'usd' )
        abc_path        = os.path.join( pub_cache_path , 'abc' )
        maya_path       = os.path.join( pub_path, 'maya' )
        info_path       = os.path.join( maya_path, 'info' )
        usd_ver_path    = os.path.join( usd_path, version )
        usd_ver_py_folder = os.path.join( usd_ver_path , 'python' )
        abc_ver_path      = os.path.join( abc_path, version )
        abc_ver_py_folder = os.path.join( abc_ver_path , 'python' )

        ## Note Contents Creation


        settings['scene_path'] = {
            'type' : 'str',
            'default' : scene_path
        }
        settings['basename'] = {
            'type' : 'str',
            'default' : basename
        }
        settings['usd_path'] = {
            'type' : 'str',
            'default' : usd_path
        }
        settings['usd_ver_path'] = {
            'type' : 'str',
            'default' : usd_ver_path
        }
        settings['usd_ver_py_folder'] = {
            'type' : 'str',
            'default' : usd_ver_py_folder
        }
        settings['abc_ver_path'] = {
            'type' : 'str',
            'default' : abc_ver_path
        }
        settings['abc_ver_py_folder'] = {
            'type' : 'str',
            'default' : abc_ver_py_folder
        }



        # define the settings the custom plugin UI will set
        settings["job_location"] = {
            "type": "int",
            "default": 1,
            "description": "Send job to local or farm"
        }
        settings["tpose_frame"] = {
            "type": "int",
            "default": tpos_frame,
            #"default": 950,
            "description": "Tpose Frame",
        }
        settings["stable_frame"] = {
            "type": "int",
            "default": stable_frame,
            #"default": 980,
            "description": "Stable Frame",
        }
        settings["sframe"] = {
            "type": "int",
            "default": sframe,
            #"default": 1001,
            "description": "Srart Frame",
        }
        settings["eframe"] = {
            "type": "int",
            "default": eframe,
            #"default": 1100,
            "description": "End Frame",
        }
        settings["handle_frame"] = {
            "type": "int",
            "default": 5,
            "description": "Handle Frame",
        }
        settings["cache_step"] = {
            "type": "float",
            "default": 0.25,
            "description": "Cache Step",
        }

        settings["farm"] = {
            "type": "bool",
            "default": True,
            "description": "Submitting job to farm",
        }
        settings["note"] = {
            "type": "bool",
            "default": True,
            "description": "Adding note in version note",
        }
        settings["farm_grp"] = {
            "type": "str",
            "default": 'cfx|cfx2',
            "description": "Adding note in version note",
        }


        return settings

    @property
    def name( self ):
        return "Global Settings"

    @property
    def item_filters( self ):
        return ["maya.session"]

    def accept( self, settings, item ):
        return {'accepted': True, 'checked':True}

    def validate( self, settings, item  ):

        return True

    def create_settings_widget(self, parent):
        self.global_settings = GlobalSettings(parent, self.parent.shotgun)

        return self.global_settings


    def get_ui_settings(self, widget):
        return {
                "job_location"  : widget.job_location,
                "tpose_frame"   : widget.tpose_frame,
                "stable_frame"  : widget.stable_frame,
                'sframe'        : widget.sframe,
                'eframe'        : widget.eframe,
                'handle_frame'  : widget.handle_frame,
                'cache_step'    : widget.cache_step,
                #'asset_transform' : widget.asset_transform,
                'farm'          : widget.farm,
                'note'          : widget.note,
                'farm_grp'      : widget.farm_grp,
                }


    def set_ui_settings(self, widget, settings):
        for setting_block in settings:
            job_location = setting_block.get("job_location")
            if job_location:
                widget.job_location = job_location

            tpose_frame = setting_block.get("tpose_frame")
            if tpose_frame:
                widget.tpose_frame = tpose_frame

            stable_frame = setting_block.get("stable_frame")
            if stable_frame:
                widget.stable_frame = stable_frame

            sframe = setting_block.get("sframe")
            if sframe:
                widget.sframe = sframe

            eframe = setting_block.get("eframe")
            if eframe:
                widget.eframe = eframe

            handle_frame = setting_block.get("handle_frame")
            if handle_frame:
                widget.handle_frame = handle_frame

            cache_step = setting_block.get("cache_step")
            if cache_step:
                widget.cache_step = cache_step

            farm = setting_block.get( 'farm' )
            if farm:
                widget.farm = farm

            note = setting_block.get( 'note' )
            if note:
                widget.note = note

            farm_grp = setting_block.get( 'farm_grp' )
            if farm_grp:
                widget.farm_grp = farm_grp


    def publish( self, settings, item ):
        
        if not settings['note'].value :
            print( '\n')
            print( '@'*50 )
            print( 'none note value' )
            print( '@'*50 )
            print( '\n')

            return
        proj            = item.context.project['name'] 
        pipeline_step   = item.context.task['name']
        basename        = settings['basename'   ].value
        sframe          = settings['sframe'     ].value
        eframe          = settings['eframe'     ].value
        assembled_usd   = settings['usd_path'   ].value + os.sep + basename + '.usd'
        if item.context.task == 'mm':
            mmCam_usd       = settings['usd_ver_path' ].value + os.sep + 'mmCam.usd'
            mmGeom_usd      = settings['usd_ver_path' ].value + os.sep + 'mmGeom.usd'
            mmCam_abc       = settings['abc_ver_path' ].value + os.sep + 'mmCam.abc'
            mmGeom_abc      = settings['abc_ver_path' ].value + os.sep + 'mmGeom.abc'
        else:
            mmCam_usd       = ''
            mmGeom_usd      = ''
            mmCam_abc       = ''
            mmGeom_abc      = ''



        
        usd_asset_list =  mmGeom_usd 
        abc_asset_list =  mmGeom_abc 
        ## Getting usd_asset_list
        
        note_content = note_content_body(
            proj, pipeline_step, basename, sframe, eframe, 
            assembled_usd, mmCam_usd, usd_asset_list,
            mmCam_abc, abc_asset_list
        )
       

        print( '\n')
        print( '@'*50 )
        print( note_content )
        print( '@'*50 )
        print( '\n')
        
        filters = [
                ['project'  , 'is' , item.context.project   ],
                ['entity'   , 'is' , item.context.entity    ],
                ['sg_task'  , 'is' , item.context.task      ],
        ]

        sg = item.context.sgtk.shotgun
        version = sg.find_one( 'Version', filters, )
        if not version:
            return

        ## assignees
        filters = [[ 'entity', 'is', item.context.entity ] ]
        task_list = sg.find( 'Task', filters , [ 'task_assignees', 'step' ] )
        assignees = []

        dm_ani = [ {'id':4147 , 'name':'dm_ani', 'type': 'Group' } ]
        dm_rig = [ {'id':6092 , 'name':'dm_rig', 'type': 'Group' } ]
        dm_lgt = [ {'id':4145 , 'name':'dm_lgt', 'type': 'Group' } ]
        dm_fx = [ {'id':4080 , 'name':'dm_fx', 'type': 'Group' } ]
        dm_mm = [ {'id':4146 , 'name':'dm_mm', 'type': 'Group' } ]
        lgt_sup = [ {'id':133 , 'name':'강성일 LGT', 'type': 'HumanUser' } ]

        assignees += dm_ani
        assignees += dm_rig
        assignees += dm_lgt
        assignees += dm_fx

        if pipeline_step in ['mm', 'layout' ]:
            to_step_list = ['ani', 'lgt', 'fx', 'sim', 'rig', 'mm']
            assignees += dm_mm
        else:
            to_step_list = ['ani', 'lgt', 'fx', 'sim', 'rig']
            assignees += lgt_sup

        for task in task_list:
            for step in to_step_list:
                if task['step']['name'] == step:
                    assignees += task['task_assignees']


        note = {
                    'project' : item.context.project,
                    'note_links' : [version, item.context.entity ] ,
                    'subject' : '{} publish note'.format( basename ),
                    'content' : note_content,
                    'user' : item.context.user,
                    'addressings_to' : assignees,
        }
        note_result = sg.create( 'Note' ,  note )
        print( '_' * 50 )                
        pprint.pprint( note_result )
        print( '_' * 50 )                

        print( '@'*50 )
        print( '\n')
        return True


    def finalize(self, settings, item):
        return True



class GlobalSettings(QtGui.QWidget):

    def __init__(self, parent, sg):

        super( GlobalSettings, self).__init__(parent)

        self.__setup_ui()
        # Add the reviewers to the reviewer combo box

        self.main_diag = parent.parent().parent().parent().parent().parent().parent().parent().parent().parent().parent().parent().parent().parent()
        size = self.main_diag.size()
        resize = ( size.width(), size.height() + 70 )
        self.main_diag.resize( resize[0], 700 )

    
    @property
    def tpos_frame( self ):
        return self.tpose_edt.value()


    @property
    def stable_frame( self ):
        return self.stable_frame_spin.get_value()

    @stable_frame.setter
    def stable_frame( self, value ):
        return self.stable_frame_spin.set_value( value )

    @property
    def tpose_frame( self ):
        return self.tpose_spin.get_value()


    @tpose_frame.setter
    def tpose_frame( self, value ):
        return self.tpose_spin.set_value( value )

    @property
    def sframe( self ):
        return self.sframe_spin.get_value()

    @sframe.setter
    def sframe( self, value ):
        return self.sframe_spin.set_value( value )
    
    @property
    def eframe( self ):
        return  self.eframe_spin.get_value()
        
    @eframe.setter
    def eframe( self, value ):
        return self.eframe_spin.set_value( value )

    @property
    def handle_frame( self ):
        return self.handle_frame_spin.get_value()

    @handle_frame.setter
    def handle_frame( self, value ):
        return self.handle_frame_spin.set_value( value )

    @property
    def cache_step( self ):
        return self.cache_step_spin.get_value()

    @cache_step.setter
    def cache_step( self, value ):
        return self.cache_step_spin.set_value( value )

    @property
    def farm( self ):
        return self.farm_chk.isChecked()

    @farm.setter
    def farm( self, value ):
        return self.farm_chk.setChecked( value )

    @property
    def note( self ):
        return self.add_note_chk.isChecked()

    @note.setter
    def note( self, value ):
        return self.add_note_chk.setChecked( value )

    @property
    def farm_grp( self ):
        return self.farm_grp_edt.get_value( )

    @farm_grp.setter
    def farm_grp( self, value ):
        return self.farm_grp_edt.set_value( value )
        

    def __setup_ui(self):
        """
        Creates and lays out all the Qt widgets
        :return:
        """


        info_grp = QtGui.QGroupBox( 'Frame Info' )
        self.tpose_spin        = NamedLineEdit( 'T Pose Frame'   , 950   )
        self.stable_frame_spin = NamedLineEdit( 'Stable Frame'   , 980   )
        self.sframe_spin       = NamedLineEdit( 'Start Frame'    , 1001  )
        self.eframe_spin       = NamedLineEdit( 'End Frame'      , 1100  )
        self.handle_frame_spin = NamedLineEdit( 'Handle Frame'   , 5     )
        self.cache_step_spin   = NamedLineEdit( 'Cache Step'     , 0.25  )


        frame_info_lay = QtGui.QVBoxLayout()
        frame_info_lay.addWidget( self.tpose_spin         )
        frame_info_lay.addWidget( self.stable_frame_spin  )
        frame_info_lay.addWidget( self.sframe_spin        )
        frame_info_lay.addWidget( self.eframe_spin        )
        frame_info_lay.addWidget( self.handle_frame_spin  )
        frame_info_lay.addWidget( self.cache_step_spin    )

        info_grp.setLayout( frame_info_lay )

        shotgrid_grp     = QtGui.QGroupBox( 'Shotgrid' )
        self.add_note_chk    = QtGui.QCheckBox( 'Add Note on Version' )
        shotgrid_lay = QtGui.QVBoxLayout()

        shotgrid_lay.addWidget( self.add_note_chk )

        shotgrid_grp.setLayout( shotgrid_lay )
        
        network_grp     = QtGui.QGroupBox( 'Export job' )
        self.farm_chk    = QtGui.QCheckBox( 'Farm' )
        self.farm_grp_edt     = NamedLineEdit( 'Farm Group'     , 'cfx|cfx2' )
        network_lay = QtGui.QVBoxLayout()
        network_lay.addWidget( self.farm_chk )
        network_lay.addWidget( self.farm_grp_edt )
        network_grp.setLayout( network_lay )


        vlay = QtGui.QVBoxLayout()
        vlay.addWidget( info_grp )
        vlay.addWidget( shotgrid_grp )
        vlay.addWidget( network_grp )
        self.setLayout( vlay )




class NamedLineEdit( QtGui.QWidget ):
    def __init__( self , name = '',value = '' ):
        super( NamedLineEdit, self ).__init__()

        lay = QtGui.QHBoxLayout()

        self.lb  = QtGui.QLabel( '' )
        if type( value ) == type( 10 ):
            self.edt = QtGui.QSpinBox()
            self.edt.setMinimum( -1000 )
            self.edt.setMaximum( 10000 )
            self.edt.setValue( 1000 )
            self.wdg = 'spin'

        elif type( value ) == type(1.0):
            self.edt = QtGui.QDoubleSpinBox()
            self.edt.setMinimum( -1000 )
            self.edt.setMaximum( 10000 )
            self.edt.setValue( 0.25 )
            self.wdg = '2spin'

        else:
            self.edt = QtGui.QLineEdit()
            self.wdg = 'edt'


        lay.addWidget( self.lb )
        lay.addWidget( self.edt )
        self.setLayout( lay )

        lay.setContentsMargins( 5,0,5,0 )

        if name:
            self.set_name( name ) 

        if value:
            self.set_value( value )

    def set_name( self , name ):
        self.lb.setText( name )

    def set_value( self, value ):
        if self.wdg == 'edt':
            self.edt.setText( value )
        else:
            self.edt.setValue( value ) 

    def get_value( self ):
        if self.wdg == 'edt':
            return self.edt.text() 
        else:
            return self.edt.value() 


def note_content_body( 
            proj, pipeline_step, basename, sframe, eframe, 
            assembled_usd, mmCam_usd, usd_asset_list,
            mmCam_abc, abc_asset_list
            ):
    content = f'[{proj}] {pipeline_step} Publish\n\n'
    content += f'1.note\n'
    content += f'  {basename} 퍼블리쉬합니다.\n'
    content += f'2.Just frame\n'
    content += f'  {sframe} - {eframe}\n'
    content += f'3.Cache path\n\n'
    content += " ```\n"
    if mmCam_usd or usd_asset_list:
        content += '=========================='
        content += 'Assmebled USD path:\n'
        if assembled_usd:
            content += f'{assembled_usd}\n\n'
        if usd_asset_list:
            content += f'{usd_asset_list}\n'
    if mmCam_abc or abc_asset_list:
        content += '=========================='
        content += 'ABC Cache path:\n'
        if mmCam_abc:
            content += f'{mmCam_abc}\n'
        if abc_asset_list:
            content += f'{abc_asset_list}\n'
    content += " ```\n"
    return content
