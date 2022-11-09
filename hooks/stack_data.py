# -*- coding: utf-8 -*-

import sys
import psycopg2

class Databases():
    def __init__( self, data_list ):
        '''
        data_list
                data_list[0] == user_id
                data_list[1] == tool
                data_list[2] == project
                data_list[3] == shot_name
                data_list[4] == file_name
                data_list[5] == operation
                data_list[6] == system os
        '''
        self.sql = self.set_sql( data_list )
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

    def insertDB( self ):
        self.cursor.execute( self.sql )
        self.db.commit()            

    def set_sql( self, data_list ):
        if data_list[5] == 'NEW_FILE' or data_list[5] == 'OPEN':
            operation_type = 'START'
        elif data_list[5] == 'SAVE' or data_list[5] == 'SAVE_AS':
            operation_type = 'END'
        else:
            operation_type = None
        user_id   = data_list[0]
        tool      = data_list[1]
        project   = data_list[2]
        shot_name = data_list[3]
        file_name = data_list[4]
        operation = data_list[5]
        sys_os    = data_list[6]
        sql =   '''
                    INSERT INTO logs ( user_id, tool, project, shot_name, file_name, operation, operation_type, log_time, os )
                    VALUES (\'{0}\', \'{1}\', \'{2}\', \'{3}\', \'{4}\', \'{5}\', \'{6}\', current_timestamp, \'{7}\');
                '''.format( user_id, tool, project, shot_name, file_name, operation, operation_type, sys_os )
        return sql

if __name__ == '__main__':
    argument = sys.argv
    data_list = argument[1:]
    DB = Databases( data_list )
    DB.insertDB()
