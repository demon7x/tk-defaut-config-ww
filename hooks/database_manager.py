# -*- coding: utf-8 -*-

import sys
import psycopg2
import argparse

import shotgun_api3

SG = shotgun_api3.Shotgun(
    'https://west.shotgunstudio.com',
    'eventTrigger',
    '6h&ziahfuGbqdubxrxeyopinl'
)

# Using in log time data
USERID          =    0
TOOL            =    1
PROJECT         =    2
SHOTNAME        =    3
FILENAME        =    4
OPERATION       =    5
OS              =    6
OPERATIONTYPE   =    7

# Using in user data
USERID          =    0
USERSTATUS      =    1
DEPARTMENT      =    2
SHOTNAME        =    3

class Databases():
    def __init__( self ):
        self.db = psycopg2.connect( host = '10.0.20.7', dbname = 'WorkFilesLogs', user = 'postgres', password = 'postgres', port = 5432 )
        self.cursor = self.db.cursor()

    def __del__( self ):
        self.db.close()
        self.cursor.close()

    def check_DB( self, sql ):
        self.cursor.execute( sql )
        rows = self.cursor.fetchall()
        return rows

    def insert_DB( self, sql ):
        self.cursor.execute( sql )
        self.db.commit()            

    def set_log_data_sql( self, data_list ):
        if data_list[ OPERATION ] == 'OPEN' or data_list[ OPERATION ] == 'NEW_FILE':
            operation_type = 'START'
        elif data_list[ OPERATION ] == 'SAVE' or data_list[ OPERATION ] == 'SAVE_AS':
            operation_type = 'END'
        else:
            operation_type = None
        user_id   = data_list[ USERID ]
        tool      = data_list[ TOOL ]
        project   = data_list[ PROJECT ]
        shot_name = data_list[ SHOTNAME ]
        file_name = data_list[ FILENAME ]
        operation = data_list[ OPERATION ]
        sys_os    = data_list[ OS ]
        log_data_sql =   '''
                    INSERT INTO 
                        logs ( user_id, tool, project, shot_name, file_name, operation, os, operation_type, log_time  )
                    VALUES 
                        (\'{0}\', \'{1}\', \'{2}\', \'{3}\', \'{4}\', \'{5}\', \'{6}\', \'{7}\', current_timestamp );
                '''.format( user_id, tool, project, shot_name, file_name, operation, sys_os, operation_type )
        return log_data_sql

    def set_status_sql( self, data_list ) :
        user_id     = data_list[ USERID ]
        user_status = data_list[ USERSTATUS ]
        department  = data_list[ DEPARTMENT ]
        shot_name   = data_list[ SHOTNAME ]
        sql =   '''
                    INSERT INTO 
                        user_info (  user_id, user_status, department, shot_name, log_time  )
                    VALUES 
                        ( \'{0}\', \'{1}\', \'{2}\', \'{3}\', current_timestamp )
                    ON CONFLICT 
                        ( user_id ) 
                    DO
                    UPDATE
                    SET
                        user_status = \'{1}\',
                        department  = \'{2}\', 
                        shot_name   = \'{3}\',
                        log_time    = current_timestamp
                '''.format( user_id, user_status, department, shot_name )
        return sql

    def set_work_time_data_sql( self, data_list, timelog_data ):
        user_id   = data_list[ USERID ]
        tool      = data_list[ TOOL ]
        project   = data_list[ PROJECT ]
        shot_name = data_list[ SHOTNAME ]
        file_name = data_list[ FILENAME ]
        work_time = timelog_data[0]

        work_time_data_sql ='''
                                INSERT INTO 
                                    timelogs ( date, user_id, tool, project, shot_name, file_name, work_time )
                                VALUES 
                                    (current_timestamp, \'{0}\', \'{1}\', \'{2}\', \'{3}\', \'{4}\', \'{5}\' );
                            '''.format( user_id, tool, project, shot_name, file_name, work_time )
        return work_time_data_sql

    def create_SG_timelog( self , data_list, timelog_data ):
        user_id       = data_list[ USERID ]
        tool          = data_list[ TOOL ]
        project_name  = data_list[ PROJECT ]
        task_name     = data_list[ SHOTNAME ]
        file_name     = data_list[ FILENAME ]
        work_time     = timelog_data[0]
        link          = None

        user    = SG.find_one( 'HumanUser', [[ 'login', 'is', user_id ]])
        project = SG.find_one( 'Project', [[ 'name', 'is', project_name ]])
        assets  = SG.find_one( 'Asset', [[ 'project', 'is', project ], [ 'code' , 'is', task_name ]] )
        shots   = SG.find_one( 'Shot', [[ 'project', 'is', project ], [ 'code' , 'is', task_name ]] )
        if assets:
            link = assets
        elif shots:
            link = shots
        
        data = {
            'sg_user': user,
            'project': project,
            'sg_tool': tool,
            'description': file_name,
            'sg_link': link,
            'sg_duration': work_time
        }

        SG.create( 'CustomEntity09', data )

    def get_user_info( self, user_id ):
        sql =   '''
                    SELECT
                        * from user_info info
                    WHERE
                        info.user_id = \'{0}\'
                '''.format( user_id )
        return sql

    def get_time_now( self ):
        sql =   '''
                    SELECT now()
                '''
        return sql

def main( ):
    parser = argparse.ArgumentParser( description = 'Stack Data' )
    parser.add_argument( '-now', '--now', action = 'store_true' )
    parser.add_argument( '-id', '--user_id',   type = str, nargs = 1 )
    parser.add_argument( '-log', '--log_data',  type = str, nargs = 7 )
    parser.add_argument( '-user', '--user_data',  type = str, nargs = 4 )
    parser.add_argument( '-timelog', '--timelog_data', type = str, nargs = 1)
    
    args = parser.parse_args()
    DB = Databases( )
    if args.now:
        time_sql  = DB.get_time_now()
        rows      = DB.check_DB( time_sql )
        first_row = rows[0]
        time_now  = first_row[0]
        string_info = '{0} '.format(time_now.strftime('%Y-%m-%d %H:%M:%S'))
        print(string_info)
    if args.user_id:
        user_info_sql = DB.get_user_info( args.user_id[0] )
        rows = DB.check_DB( user_info_sql )
        if rows :
            row = rows[0]
            string_info = ''
            for col in row:
                if row.index(col) != 4:
                    pass
                else:
                    col = col.strftime('%Y-%m-%d %H:%M:%S')
                string_info += '{} '.format(col)
            print( '{}'.format( string_info ))
    if args.log_data:
        log_data_sql = DB.set_log_data_sql( args.log_data )
        DB.insert_DB( log_data_sql )
    if args.user_data:
        status_sql = DB.set_status_sql( args.user_data )
        DB.insert_DB( status_sql )
    if args.timelog_data:
        timelog_sql = DB.set_work_time_data_sql( args.log_data, args.timelog_data )
        DB.insert_DB( timelog_sql )
        DB.create_SG_timelog( args.log_data, args.timelog_data )

if __name__ == '__main__':
    main( )
