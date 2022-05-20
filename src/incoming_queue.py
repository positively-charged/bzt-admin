from typing import Optional
import socket

class IncomingQueue:
   def __init__( self, socket_handle: socket.socket ):
      self._socket: socket.socket = socket_handle
      self._received_data: bytes = b''

   def receive( self ) -> bool:
      bytes = self._socket.recv( 4096 )
      if bytes != b'':
         self._received_data += bytes
         return True
      return False

   def fetch( self ) -> Optional[ bytes ]:
      end_pos = self._received_data.find( b'\0' )
      if end_pos != -1:
         fragment = self._received_data[ : end_pos ]
         if end_pos + 1 < len( self._received_data ):
            self._received_data = self._received_data[ end_pos + 1 : ]
         else:
            self._received_data = b''
         return fragment
      return None
