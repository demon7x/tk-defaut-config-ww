# -*- coding: utf-8 -*-

import os
import sys
import platform
import subprocess as sp
from datetime import datetime

import sgtk
from sgtk import Hook
from sgtk import TankError
from sgtk.platform.qt import QtGui

class TimeLogManager():
    def __init__( self, user, tool, project_name, shot_name, file_name, operation ):
        self.user       =  user
        self.user_id    =  user.login
        self.file_path  =  os.path.dirname(os.path.realpath(__file__)) 
        self.sys_os     =  platform.system()
        now             =  datetime.now()
        now_str         =  now.strftime( "%Y-%m-%d %H:%M:%S" )

        if self.sys_os == 'Windows' :
            try:
                cmd            =  'rez-env psycopg2 -- python {0} -id {1}'.format( os.path.join( self.file_path, 'stack_data.py'), self.user_id )
                os.chdir(r'{}'.format( self.file_path ))
                output, stderr =  sp.Popen( cmd, stdout = sp.PIPE, stderr = sp.PIPE, shell = False, cwd = self.file_path ).communicate()
                lines          =  output.decode('utf-8')
            except Exception as err :
                pass
        else :
            cmd            =  'rez-env psycopg2 -- python {0} -id {1}'.format( os.path.join( self.file_path, 'stack_data.py'), self.user_id )
            output, stderr =  sp.Popen( cmd, stdout = sp.PIPE, stderr = sp.PIPE, shell = True, cwd = self.file_path ).communicate()
            lines          =  output.decode('utf-8')
        
        if lines :
            log_list = lines.split(" ")
            QtGui.QMessageBox.information(None,
                                                "타임로그",
                                                "cmd = {0}\n log_list = {1}, err = {2}".format( cmd, log_list,stderr )
                                            )
            user_status     = log_list[1]
            log_shot        = log_list[3]
            datetime_str    = "{0} {1}".format(log_list[4], log_list[5])
            datetime_object = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
            QtGui.QMessageBox.information(None,
                                                "타임로그",
                                                "user_status = {0}\n log_shot = {1}\n datetime_str = {2}\n datetime_object = {3}\n".format( user_status, log_shot,datetime_str,datetime_object)
                                            )
        else :
            user_status     = "RESTING"
            log_shot        = ""

        ### 1. OPEN 또는 NEW FILE을 선택했을 때 ###
        if operation == "OPEN" or operation == "NEW_FILE" :
            ### 1-1. 타임로그 작업중인 경우
            if user_status == "WORKING" and log_shot == shot_name:
                res = QtGui.QMessageBox.question(None,
                                                    "타임로그 충돌",
                                                    "이미 동일한 {0}의 타임로그를 기록중입니다.\n".format( log_shot ) +
                                                    "{0}에 시작된 기록을 취소하고 새로운 로그를 시작할까요?".format( datetime_str ),
                                                    QtGui.QMessageBox.Yes|QtGui.QMessageBox.No|QtGui.QMessageBox.Cancel 
                                                    )
                if res == QtGui.QMessageBox.Yes:
                    QtGui.QMessageBox.information(None,
                                                        "타임로그 시작 안내",
                                                        "타임로그 기록 시작\n" + 
                                                        "Time : {0} Shot/Asset Name : {1}".format( now_str, shot_name )
                                                        )
                    user_status = "WORKING"
                    self.stack_data( user_status, tool, project_name, shot_name, file_name, operation )
                elif res == QtGui.QMessageBox.No:
                    pass
                else:
                    pass
            
            elif user_status == "WORKING" and log_shot != shot_name:
                res = QtGui.QMessageBox.question(None,
                                                    "타임로그 충돌",
                                                    "{0}의 타임로그를 기록중입니다.\n".format( log_shot ) +
                                                    "기존의 기록을 취소하고\n{0}을 기록할까요?".format( shot_name ),
                                                    QtGui.QMessageBox.Yes|QtGui.QMessageBox.No|QtGui.QMessageBox.Cancel 
                                                    )
                if res == QtGui.QMessageBox.Yes:
                    QtGui.QMessageBox.information(None,
                                                        "타임로그 시작 안내",
                                                        "타임로그 기록 시작\n" + 
                                                        "Time : {0} Shot/Asset Name : {1}".format( now_str, shot_name )
                                                        )
                    user_status = "WORKING"
                    self.stack_data( user_status, tool, project_name, shot_name, file_name, operation )
                elif res == QtGui.QMessageBox.No:
                    pass
                else:
                    pass
                
            ### 1-2. 타임로그 작업중이 아닌 경우
            else :
                res = QtGui.QMessageBox.question(None,
                                                    "타임로그 안내",
                                                    "{0}의 타임로그를 기록하겠습니까?".format( shot_name ),
                                                    QtGui.QMessageBox.Yes|QtGui.QMessageBox.No|QtGui.QMessageBox.Cancel 
                                                )
                if res == QtGui.QMessageBox.Yes:
                    QtGui.QMessageBox.information(None,
                                                    "타임로그 시작",
                                                    "{0}의 타임로그 기록을 시작합니다.".format( shot_name )
                                                    )
                    user_status = "WORKING"
                    self.stack_data( user_status, tool, project_name, shot_name, file_name, operation )
                elif res == QtGui.QMessageBox.No:
                    pass
                else:
                    pass
            
        ### 2. SAVE 또는 SAVE AS를 선택했을 때 ###
        elif operation == "SAVE" or operation == "SAVE_AS" :
            ### 2-1. 기록중인 타임로그가 없는 경우 ###
            ### user_info.user_status == "RESTING" ###
            if user_status == "WORKING" and log_shot == shot_name :
                res = QtGui.QMessageBox.question(None,
                                                    "타임로그 안내",
                                                    "{0}의 타임로그를 종료하겠습니까?".format( log_shot ),
                                                    QtGui.QMessageBox.Yes|QtGui.QMessageBox.No|QtGui.QMessageBox.Cancel 
                                                )
                if res == QtGui.QMessageBox.Yes:
                    work_time = ( now - datetime_object )
                    work_time_str = "{0}:{1}:{2}".format( work_time.seconds//3600, work_time.seconds//60 , work_time.seconds%60 )
                    work_time_kor = "{0}시간 {1}분 {2}초".format( work_time.seconds//3600, work_time.seconds//60 , work_time.seconds%60 )
                    QtGui.QMessageBox.information(None,
                                                        "타임로그 종료",
                                                        "{0}의 타임로그가 종료되었습니다\n{1} 기록".format( file_name, work_time_kor )
                                                        )
                    user_status = "RESTING"
                    self.stack_data( user_status, tool, project_name, shot_name, file_name, operation, work_time_str )
                ### 2-2-a. shot 정보가 다른 경우)
            elif user_status == "WORKING" and log_shot != shot_name :
                    user_status = "RESTING"
                    QtGui.QMessageBox.information(None,
                                                        "타임로그 안내",
                                                        "현재 기록중인 타임로그는 {0}입니다.\n타임로그가 저장되지 않습니다.".format( log_shot ),
                                                        )
            else :
                QtGui.QMessageBox.information(None,
                                                    "타임로그 안내",
                                                    "기록중인 타임로그가 없습니다.\n" + 
                                                    "타임로그 저장 시 툴킷으로 작업을 진행해주세요.\n\n" +
                                                    "파일은 정상적으로 저장됩니다.")

    def get_shotgrid_info( self ):
        engine = sgtk.platform.current_engine()
        shotgun = engine.shotgun
        filter = [[ 'login', 'is', self.user_id ]]
        fields = [ 'login', 'name', 'department.Department.name' ]
        sg_data = shotgun.find_one( "HumanUser", filter, fields )
        return sg_data

    def stack_data( self, user_status, tool, project_name, shot_name, file_name, operation, work_time = "" ):
        sg_data         =  self.get_shotgrid_info( )
        # user_name  =  sg_data[ 'name' ].split(' ')[0]
        department =  sg_data[ 'department.Department.name' ]

        cmd  = 'rez-env psycopg2 -- python {0} '.format( os.path.join( self.file_path, 'stack_data.py') )
        cmd += '-log {0} {1} {2} {3} {4} {5} {6} '.format( self.user_id, tool, project_name, shot_name, file_name, operation, self.sys_os )
        cmd += '-user {0} {1} {2} {3}'.format( self.user_id, user_status, department, shot_name )
        if work_time:
            cmd += ' -timelog {0}'.format( work_time )
        if self.sys_os == 'Windows':
            try:
                os.chdir(r'{}'.format( self.file_path ))
                os.system( cmd )
            except Exception as err :
                QtGui.QMessageBox.information(None, "!! Windows os error !!", "{}".format( err ))
        else :
            os.system( cmd )