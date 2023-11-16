# Copyright (c) 2017 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

#import os
#import sys
#import re
#import pprint
#import traceback

import sgtk
from sgtk.util.shotgun import download_and_unpack_attachment
#from sgtk.util.filesystem import copy_file, ensure_folder_exists


HookBaseClass = sgtk.get_hook_baseclass()


class PipelineConfigInitPlugin(HookBaseClass):

    def can_cache_bundle( self, descriptor ):
        print( '\n' )
        print( '+' * 50 )
        print( descriptor  )
        print( '+' * 50 )
        print( '\n' )
        pass
    def populate_bundle_cache_entry( self,  destination, descriptor, **kwargs )
        attachment = self._get_bundle_attachment(descriptor)
        download_and_unpack_attachment(self.shotgun, attachment, destination)
        self.logger.info(
            "Bundle %s was downloaded from %s.",
            descriptor.get_uri(),
            self.shotgun.base_url,
        )
        print( '\n' )
        print( '+' * 50 )
        print( attachment  )
        print( '+' * 50 )
        print( '\n' )

    def _get_bundle_attachment( self, descriptor ):
        print( '\n' )
        print( '+' * 50 )
        print( descriptor  )
        print( '+' * 50 )
        print( '\n' )

    def execute( self, **kwargs ):
        result = kwargs
        print( '\n' )
        print( '+' * 50 )
        print( result  )
        print( '+' * 50 )
        print( '\n' )

    def run_action( self, action, sg_data ):
        result = sg_data
        print( '\n' )
        print( '+' * 50 )
        print( result  )
        print( '+' * 50 )
        print( '\n' )

    
    def list_actions( self, sg_publish_data ):
        result = sg_publish_data
        print( '\n' )
        print( '+' * 50 )
        print( result  )
        print( '+' * 50 )
        print( '\n' )

    def run_action( self, action, sg_data ):
        result = sg_data
        print( '\n' )
        print( '+' * 50 )
        print( result  )
        print( '+' * 50 )
        print( '\n' )
