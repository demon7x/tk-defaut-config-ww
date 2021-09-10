# :coding: utf-8

import os
from pprint import pprint

import sgtk


engine  = sgtk.platform.current_engine()
sg      = engine.shotgun



def insert( item ):        

    ver_ent = sg.find_one( 
                        'Version',
                        [
                            ['project','is',item.context.project ] ,
                            ['code','is', item.name ]
                        ],
                        ['notes']
    )
    
    content = '\n[ ' + os.path.splitext( item.properties.path )[1][1:] + ' ]'
    content += '\n' + item.properties.path

    if ver_ent and ver_ent['notes']:
        print 'Update Note'
        sorted( ver_ent['notes'] )
        note_ent = sg.find(
                            'Note',
                            [
                                [ 'id', 'is', ver_ent['notes'][0]['id'] ]
                            ],
                            ['content']
        )
        origin_content = note_ent[0]['content'] + '\n' if note_ent[0]['content'] else ''
        content = origin_content + content
        if content in origin_content:
            return
        data = {
                'content': content
        }
        sg.update( 
                    'Note', note_ent[0]['id'],
                    data
        )

    else:
        print 'Create Note'
        data = {
                'project'    : item.context.project,
                'note_links' : [ item.context.entity, ver_ent ],
                'content'    : content,
                'subject'    : item.context.user['name'] + "'s Note on " + item.context.entity['name'] + ' and ' + item.name
        }
        sg.create( 'Note', data )



