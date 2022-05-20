import socket, sys, select
from console import Console
from int_signal import IntSignal
from bot import Bot
from protocol import ConnectedMessage, OutputLineMessage

class Session:
   """
   An established connection to the bot.
   """
   def __init__( self, signal: IntSignal, console: Console,
      socket_handle: socket.socket ):
      self._signal: IntSignal = signal
      self._console: Console = console
      self._socket: socket.socket = socket_handle
      self._reload: bool = False
      self._exit_requested: bool = False
      self._bot: Bot = Bot()

   def run( self ):
      while not self._is_done():
         self._tick()

   def _tick( self ):
      try:
         streams: list[ object ] = [ sys.stdin, self._socket ]
         readReady = select.select( streams, [], [] )[ 0 ]
         for stream in readReady:
            if stream is sys.stdin:
               self._handle_console_input()
            elif stream is self._socket:
               self._handle_bot_response()
      except KeyboardInterrupt:
         self._exit_requested = True

   def _is_done( self ) -> bool:
      return self._exit_requested or self._signal.is_caught()

   def _handle_console_input( self ):
      self._console.handle_input()
      line = self._console.get_line()
      if line != None:
         line = line.strip().lower()
         if line in [ '.quit', '.q' ]:
            self._exit_requested = True
         elif line in [ '.c', '.connect' ]:
            self._connect()
         else:
            self._handle_line( line )

   def _handle_line( self, line: str ) -> None:
      self._console.add_line( line )
      self._socket.send( line.encode() )

   def _connect( self ):
      self._console.add_line( 'error: already connected' )

   def _handle_bot_response( self ):
      bytes = self._socket.recv( 4096 )
      self._bot.handle_response( bytes )
      while ( event := self._bot.fetch_message() ) != None:
         if isinstance( event, OutputLineMessage ):
            for line in event.lines:
               self._console.add_line( line )
         elif isinstance( event, ConnectedMessage ):
            self._console.add_line( 'connected' )