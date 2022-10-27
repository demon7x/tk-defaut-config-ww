# -*- coding: utf-8 -*-

import os
import sys
import platform
import subprocess

class Databases():
    def __init__(self):
        if platform.system() == 'Linux':
            if sys.version_info.major == 3 :
                sys.path.append('/westworld/inhouse/tool/rez-packages/psycopg2/2.8.6/platform-linux/arch-x86_64/lib/python3.7/site-packages')
            else:
                sys.path.append('/westworld/inhouse/tool/rez-packages/psycopg2/2.8.6/platform-linux/arch-x86_64/lib/python2.7/site-packages')
        elif platform.system() == 'Windows':
            if sys.version_info.major == 3 :
                # if python3 is installed in window_inhouse then need to change
                sys.path.append('\\\\10.0.40.42\\inhouse\\window_inhouse\\rez-packages\\psycopg2\\2.8.4\\platform-windows\\arch-AMD64\\lib')
            else:
                sys.path.append('\\\\10.0.40.42\\inhouse\\window_inhouse\\rez-packages\\psycopg2\\2.8.4\\platform-windows\\arch-AMD64\\lib')
        import psycopg2

        self.db = psycopg2.connect( host = '10.0.20.7', dbname = 'WorkFilesLogs', user = 'postgres', password = 'postgres', port = 5432 )
        self.cursor = self.db.cursor()

    def __del__( self ):
        self.db.close()
        self.cursor.close()

    def execute( self, query, args = {} ):
        self.cursor.execute( query, args )
        row = self.cursor.fetchall()
        return row

    def commit( self ):
        self.cursor.commit()

    def insertDB( self, sql ):
        print(sql)
        try:
            self.cursor.execute( sql )
            self.db.commit()
            print('input')
        except Exception as e :
            print( "insert DB error : ", e ) 
    
    def set_sql( self, user_name, tool, project_name, shot_name, file_name, operation ):
        if operation == 'NEW FILE' or operation == 'OPEN':
            operation_type = 'START'
        elif operation == 'SAVE' or operation == 'SAVE_AS':
            operation_type = 'END'
        else:
            operation_type = None
        sql =   '''
                    INSERT INTO logs ( user_name, tool, project, shot_name, file_name, operation, operation_type, log_time )
                    VALUES (\'{0}\', \'{1}\', \'{2}\', \'{3}\', \'{4}\', \'{5}\', \'{6}\', current_timestamp);
                '''.format( user_name, tool, project_name, shot_name, file_name, operation, operation_type )
        return sql

    def _get_rez_module(self):
        command = 'rez-env rez -- printenv REZ_REZ_ROOT'
        module_path, stderr = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()
        module_path = module_path.strip()
        if not stderr and module_path:
            return module_path
        
        return ""