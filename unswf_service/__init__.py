# (c) 2015, Adam Polkosnik <adam.polkosnik@ny.frb.org>
#
import logging
import os
import io
import zlib
import pylzma

# for computing the MD5
from hashlib import md5

# for adding the extracted files
from crits.samples.handlers import handle_file

from django.conf import settings
from django.template.loader import render_to_string
from crits.services.core import Service, ServiceConfigError

#from . import forms

logger = logging.getLogger(__name__)
class unswfService(Service):
     
    """
    Uncompress flash files.
    """
     
    name = "unswf"
    version = '0.0.2'
    supported_types = ['Sample']
    description = "Uncompress flash files."

    @staticmethod
    def valid_for(obj):
        if obj.filedata.grid_id == None:
            raise ServiceConfigError("Missing filedata.")
        data = obj.filedata.read(4)
        if len(data) < 4:
            raise ServiceConfigError("Need at least 4 bytes.")
        # Reset the read pointer.
        obj.filedata.seek(0)
        'We only care about the compressed flash files'
        if not data[:3] in ['CWS','ZWS']:
            raise ServiceConfigError("Not a valid compressed Flash file.")


    def run(self, obj, config):
        self.config = config
        self.obj = obj
        data = io.BytesIO(obj.filedata.read())
        swf = bytearray()
        try:
            comp = data.read(3)
            header = data.read(5)
            if comp == 'CWS':
                swf = 'FWS' + header + zlib.decompress(data.read())
            if comp == 'ZWS':
                data.seek(12) # seek to LZMA props
                swf = 'FWS' + header + pylzma.decompress(data.read())
        except Exception as exc:
                self._error("unswf: (%s)." % exc)
                return

        if swf:
            h = md5(str(swf)).hexdigest()
            name = h
            self._info("New file: %s (%d bytes, %s)" % (name, len(swf), h))
            handle_file(name, swf, self.obj.source,
                related_id=str(self.obj.id),
                campaign=self.obj.campaign,
                method=self.name,
                relationship='Related_To',
                user=self.current_task.username)
            self._add_result("file_added", name, {'md5': h})


