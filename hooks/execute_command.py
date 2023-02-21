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
        now_str         =  ""  
        now_datetime    =  ""   
        # get user information
        output          =  self.get_database_data( "id" )
        lines = output.decode("utf-8")
        if lines :
            log_list        = lines.split(" ")
            user_status     = log_list[1]
            log_shot        = log_list[3]
            datetime_str    = "{0} {1}".format(log_list[4], log_list[5])
            datetime_object = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
        else :
            user_status     = "RESTING"
            log_shot        = ""
        # get time now
        output          =   self.get_database_data( "now" )
        lines           =   output.decode("utf-8")
        if lines : 
            try :
                log_list        =  lines.split("\n")[0].split(" ")
                # log_list        =  log_list.split(" ")
                now_str         =  "{0} {1}".format(log_list[0], log_list[1])
                now_datetime    =  datetime.strptime(now_str, "%Y-%m-%d %H:%M:%S")
                # res = QtGui.QMessageBox.information(None,
                #                                             u"Time data",
                #                                             "{0} {1} {2}".format( now_str, now_datetime, type(now_datetime) )
                #                                             )
            except :
                pass
        if not lines and not now_datetime : 
            now_str         =  datetime.now().strftime( "%Y-%m-%d %H:%M:%S" )
            now_datetime    =  datetime.now()


        ### 1. OPEN 또는 NEW FILE을 선택했을 때 ###
        if operation == "OPEN" or operation == "NEW_FILE" :
            ### 1-1. 타임로그 작업중인 경우
            if user_status == "WORKING" and log_shot == shot_name:
                if tool == '3de4' :
                    res = QtGui.QMessageBox.question(None,
                                                        "TimeLog conflict",
                                                        "{0} is already being recorded.\n".format( log_shot ) +
                                                        "Cancle your log started at {0} and start new?".format( datetime_str ),
                                                        QtGui.QMessageBox.Yes|QtGui.QMessageBox.No|QtGui.QMessageBox.Cancel 
                                                        )
                else :
                    res = QtGui.QMessageBox.question(None,
                                                        "타임로그 충돌",
                                                        "이미 동일한 {0}의 타임로그를 기록 중입니다.\n".format( log_shot ) +
                                                        "{0}에 시작된 기록을 취소하고 새로운 로그를 시작할까요?".format( datetime_str ),
                                                        QtGui.QMessageBox.Yes|QtGui.QMessageBox.No|QtGui.QMessageBox.Cancel 
                                                        )
                if res == QtGui.QMessageBox.Yes:
                    if tool == '3de4' :
                        QtGui.QMessageBox.information(None,
                                                            "Start TimeLog",
                                                            "Start TimeLog at {0}\n".format( now_str ) + 
                                                            "Shot/Asset : {0}".format( shot_name )
                                                            )
                    else :
                        QtGui.QMessageBox.information(None,
                                                            "타임로그 시작 안내",
                                                            "타임로그 기록 시작\n" + 
                                                            "시간 : {0} Shot/Asset : {1}".format( now_str, shot_name )
                                                            )
                    user_status = "WORKING"
                    self.stack_data( user_status, tool, project_name, shot_name, file_name, operation )
                elif res == QtGui.QMessageBox.No:
                    pass
                else :
                    pass
            
            elif user_status == "WORKING" and log_shot != shot_name:
                if tool == '3de4' :
                    res = QtGui.QMessageBox.question(None,
                                                        "TimeLog conflict",
                                                        "Your another log {0} is already being recorded.\n".format( log_shot ) +
                                                        "Cancle log {0} and start {1}?".format( log_shot, shot_name ),
                                                        QtGui.QMessageBox.Yes|QtGui.QMessageBox.No|QtGui.QMessageBox.Cancel 
                                                        )
                else :
                    res = QtGui.QMessageBox.question(None,
                                                        "타임로그 충돌",
                                                        "{0}의 타임로그를 기록 중입니다.\n".format( log_shot ) +
                                                        "기존의 기록을 취소하고 {0}을 기록할까요?".format( shot_name ),
                                                        QtGui.QMessageBox.Yes|QtGui.QMessageBox.No|QtGui.QMessageBox.Cancel 
                                                        )
                if res == QtGui.QMessageBox.Yes:
                    if tool == '3de4' :
                        QtGui.QMessageBox.information(None,
                                                            "Start TimeLog",
                                                            "Start at {0}\n".format( now_str ) + 
                                                            "Shot/Asset name : {0}".format( shot_name )
                                                            )
                    else :
                        QtGui.QMessageBox.information(None,
                                                            "타임로그 시작 안내",
                                                            "타임로그 기록 시작\n" + 
                                                            "시간 : {0} Shot/Asset : {1}".format( now_str, shot_name )
                                                            )
                    user_status = "WORKING"
                    self.stack_data( user_status, tool, project_name, shot_name, file_name, operation )
                elif res == QtGui.QMessageBox.No:
                    pass
                else :
                    pass
                
            ### 1-2. 타임로그 작업중이 아닌 경우
            else :
                if tool == '3de4' :
                    res = QtGui.QMessageBox.question(None,
                                                        "TimeLog",
                                                        "Want to record timelog {0}?".format( shot_name ),
                                                        QtGui.QMessageBox.Yes|QtGui.QMessageBox.No|QtGui.QMessageBox.Cancel 
                                                    )
                else :
                    res = QtGui.QMessageBox.question(None,
                                                        "타임로그 안내",
                                                        "{0}의 타임로그를 기록하겠습니까?".format( shot_name ),
                                                        QtGui.QMessageBox.Yes|QtGui.QMessageBox.No|QtGui.QMessageBox.Cancel 
                                                    )
                if res == QtGui.QMessageBox.Yes:
                    if tool == '3de4' :
                        QtGui.QMessageBox.information(None,
                                                            "Start TimeLog",
                                                            "Start at {0}\n".format( now_str ) + 
                                                            "Shot/Asset name : {0}".format( shot_name )
                                                            )
                    else :
                        QtGui.QMessageBox.information(None,
                                                            "타임로그 시작 안내",
                                                            "타임로그 기록 시작\n" + 
                                                            "시간 : {0} Shot/Asset : {1}".format( now_str, shot_name )
                                                            )
                    user_status = "WORKING"
                    self.stack_data( user_status, tool, project_name, shot_name, file_name, operation )
                elif res == QtGui.QMessageBox.No:
                    pass
                else :
                    pass
            
        ### 2. SAVE 또는 SAVE AS를 선택했을 때 ###
        elif operation == "SAVE" or operation == "SAVE_AS" :
            ### 2-1. 기록 중인 타임로그가 없는 경우 ###
            ### user_info.user_status == "RESTING" ###
            if user_status == "WORKING" and log_shot == shot_name :
                if tool == '3de4' :
                    res = QtGui.QMessageBox.question(None,
                                                        "TimeLog",
                                                        "Are you sure end the TimeLog {0}?".format( log_shot ),
                                                        QtGui.QMessageBox.Yes|QtGui.QMessageBox.No|QtGui.QMessageBox.Cancel 
                                                    )
                else :
                    res = QtGui.QMessageBox.question(None,
                                                        "타임로그 안내",
                                                        "{0}의 타임로그를 종료하겠습니까?".format( log_shot ),
                                                        QtGui.QMessageBox.Yes|QtGui.QMessageBox.No|QtGui.QMessageBox.Cancel 
                                                    )
                if res == QtGui.QMessageBox.Yes:
                    work_time = ( now_datetime - datetime_object )
                    work_time_hour = work_time.seconds//3600
                    work_time_min  = (work_time.seconds - (work_time_hour*3600))//60
                    work_time_str = "{0}:{1}:{2}".format( work_time_hour, work_time_min , work_time.seconds%60 )
                    if tool == '3de4' :
                        work_time_eng = "{0}hours {1}minutes {2}seconds".format( work_time.seconds//3600, work_time_min , work_time.seconds%60 )
                        QtGui.QMessageBox.information(None,
                                                            "TimeLog end",
                                                            "TimeLog {0} has ended\n{1} recorded".format( file_name, work_time_eng )
                                                            )
                    else :
                        work_time_kor = "{0}시간 {1}분 {2}초".format( work_time.seconds//3600, work_time_min , work_time.seconds%60 )
                        QtGui.QMessageBox.information(None,
                                                            "타임로그 종료",
                                                            "{0}의 타임로그가 종료되었습니다\n{1} 기록".format( file_name, work_time_kor )
                                                            )
                    user_status = "RESTING"
                    self.stack_data( user_status, tool, project_name, shot_name, file_name, operation, work_time_str )
                ### 2-2-a. shot 정보가 다른 경우)
            elif user_status == "WORKING" and log_shot != shot_name :
                    user_status = "RESTING"
                    if tool == '3de4' :
                        QtGui.QMessageBox.information(None,
                                                            "TimeLog",
                                                            "The TimeLog now you being recorded is {0}.\n".format( log_shot ) +
                                                            "TimeLog is not saved.\n\n"+
                                                            "File is saved completely.",
                                                            )
                    else:    
                        QtGui.QMessageBox.information(None,
                                                            "타임로그 안내",
                                                            "현재 기록 중인 타임로그는 {0}입니다.\n".format( log_shot ) +
                                                            "타임로그가 저장되지 않습니다.\n\n"+
                                                            "파일은 정상적으로 저장됩니다.",
                                                            )
            else :
                if tool == '3de4' :
                    QtGui.QMessageBox.information(None,
                                                        "TimeLog",
                                                        "No time log being recorded.\n" + 
                                                        "Use toolkit Open if you want record TimeLog\n\n" +
                                                        "File is saved completely.")
                else:
                    QtGui.QMessageBox.information(None,
                                                        "타임로그 안내",
                                                        "기록 중인 타임로그가 없습니다.\n" + 
                                                        "타임로그 저장 시 툴킷으로 작업을 진행해주세요.\n\n" +
                                                        "파일은 정상적으로 저장됩니다.")

    def get_shotgrid_info( self ):
        engine = sgtk.platform.current_engine()
        shotgun = engine.shotgun
        filter = [[ 'login', 'is', self.user_id ]]
        fields = [ 'login', 'name', 'department.Department.name' ]
        sg_data = shotgun.find_one( "HumanUser", filter, fields )
        return sg_data

    def get_database_data( self, opt ):
        if opt == 'id':
            cmd =  'rez-env psycopg2 shotgunapi -- python {0} -id {1}'.format( os.path.join( self.file_path, 'database_manager.py'), self.user_id )
        elif opt == 'now':
            cmd =  'rez-env psycopg2 shotgunapi -- python {0} -now'.format( os.path.join( self.file_path, 'database_manager.py') )

        if self.sys_os == 'Windows' :
            try:
                output, stderr =  sp.Popen( cmd, stdout = sp.PIPE, stderr = sp.PIPE, shell = False, cwd = self.file_path ).communicate()
            except Exception as err :
                pass
        else :
            output, stderr =  sp.Popen( cmd, stdout = sp.PIPE, stderr = sp.PIPE, shell = True, cwd = self.file_path ).communicate()
        return output

    def stack_data( self, user_status, tool, project_name, shot_name, file_name, operation, work_time = "" ):
        sg_data     =  self.get_shotgrid_info( )
        department  =  sg_data[ 'department.Department.name' ]

        cmd  = 'rez-env psycopg2 shotgunapi -- python {0} '.format( os.path.join( self.file_path, 'database_manager.py') )
        cmd += '-log {0} {1} {2} {3} {4} {5} {6} '.format( self.user_id, tool, project_name, shot_name, file_name, operation, self.sys_os )
        cmd += '-user {0} {1} {2} {3}'.format( self.user_id, user_status, department, shot_name )
        if work_time:
            cmd += ' -timelog {0}'.format( work_time )
        if self.sys_os == 'Windows':
            try:
                os.chdir(r'{}'.format( self.file_path ))
                os.system( cmd )
            except Exception as err :
                QtGui.QMessageBox.information(None, "!! Windows os error Ask to Pipeline TD !!", "{}".format( err ))
        else :
            os.system( cmd )