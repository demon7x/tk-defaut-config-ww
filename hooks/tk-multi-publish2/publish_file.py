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
import pprint
import traceback

import sgtk
from sgtk.util.filesystem import copy_file, ensure_folder_exists

HookBaseClass = sgtk.get_hook_baseclass()


class ThumbnailPublishPlugin(HookBaseClass):


    def publish(self, settings, item):


        # arguments for publish registration
        self.logger.info("Check Thumbmail...")
        
        if not item.get_thumbnail_as_path():
           self._set_thumbnail(item)

            


        super(ThumbnailPublishPlugin, self).publish(settings, item)
    
    #def _set_thumbnail(self,item):
