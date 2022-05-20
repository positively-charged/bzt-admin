import protocol
from typing import Optional, Any
import json, time

class Bot:
   def __init__( self ):
      self._messages: list[ object ] = []

   def execute( self, command: str ):
      pass

   def handle_response( self, response: bytes ):
      message = protocol.OutputLineMessage()
      decoded_response = response.decode()
      json_message = json.loads( decoded_response )
      message = self._decode_message( json_message )
      self._messages.append( message )

   def _decode_message( self, data: Any ) -> object:
      if data[ 'type' ] == 'connected':
         return protocol.ConnectedMessage()
      elif data[ 'type' ] == 'output':
         message = protocol.OutputLineMessage()
         lines = data[ 'output' ].splitlines()
         for line in lines:
            message.lines.append( line )
         return message
      elif data[ 'type' ] == 'reload':
         return protocol.ReloadMessage()
      elif data[ 'type' ] == 'line':
         return protocol.LineMessage(
            data[ 'severity' ],
            data[ 'content' ],
         )
      else:
         raise Exception()
      
   def fetch_message( self ) -> Optional[ object ]:
      try:
         return self._messages.pop( 0 )
      except IndexError:
         return None