# -*- coding: utf-8 -*-

import os
import sys
# sys.path.append('/show/RND/shotgun_toolkit_skm/install/core/python')
# import sgtk
import subprocess

# HookBaseClass = sgtk.get_hook_baseclass()

# class Databases(HookBaseClass):
class Databases():
    def __init__(self):
        # rez_path = self._get_rez_module()
        # sys.path.append(rez_path)
        # print('*'*100)
        # print(rez_path)
        # print(sys.path)
        # print('*'*100)
        # # sys.path.insert(0,'/westworld/inhouse/tool/rez-packages/rez/2.23.1/platform-linux/arch-x86_64/os-CentOS-7.5.1804')
        # from rez import resolved_context
        # packages = ["psycopg2"]
        # context = resolved_context.ResolvedContext(packages)
        # path = self.get_publish_path(sg_publish_data).replace(os.path.sep, "/")
        # command = "psycopg2"
        # command += path
        # print('*'*100)
        # print(context.execute_shell(command = command,
        #                         stdin = False,
        #                         block = False,
        #                     ))
        # # import nuke
        # # nuke.alert(context)
        # # print(context)
        # print('*'*100)
        # sys.path.append(context)
        # print(sys.path)
        if sys.version_info.major == 3 :
            sys.path.append('/westworld/inhouse/tool/rez-packages/psycopg2/2.8.6/platform-linux/arch-x86_64/lib/python3.7/site-packages')
        else:
            sys.path.append('/westworld/inhouse/tool/rez-packages/psycopg2/2.8.6/platform-linux/arch-x86_64/lib/python2.7/site-packages')
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

    # def insertDB( self, schema, table, colum, data ):
    #     sql = " INSERT INTO {schema}.{table}({colum}) VALUES ('{data}') ;".format( schema = schema, table = table, colum = colum, data = data )
    #     try:
    #         self.cursor.execute( sql )
    #         self.db.commit()
    #     except Exception as e :
    #         print( "insert DB  ", e ) 

    def insertDB( self, sql ):
        print(sql)
        try:
            self.cursor.execute( sql )
            self.db.commit()
            print('input')
        except Exception as e :
            print( "insert DB error : ", e ) 
    
    def set_sql( self, user_name, tool, project_name, shot_name, file_name, operation ):
        sql =   '''
                    INSERT INTO logs ( user_name, tool, project, shot_name, file_name, operation, log_time )
                    VALUES (\'{0}\', \'{1}\', \'{2}\', \'{3}\', \'{4}\', \'{5}\', current_timestamp);
                '''.format( user_name, tool, project_name, shot_name, file_name, operation)
        return sql

    def _get_rez_module(self):
        command = 'rez-env rez -- printenv REZ_REZ_ROOT'
        module_path, stderr = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()
        module_path = module_path.strip()
        if not stderr and module_path:
            return module_path
        
        return ""


# print('start')
# DB = Databases()
# sql = DB.set_sql("신경민TD", "Nuke", "RND", "E114", "E114_114", 'OPEN' )
# DB.insertDB(sql)
# print('end')
