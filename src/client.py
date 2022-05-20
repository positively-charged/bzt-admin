import sys
import select
import time
from typing import Optional
from session import Session
from int_signal import IntSignal
from console import Console
import socket
from bot import Bot
from protocol import ConnectedMessage, LineMessage, OutputLineMessage, ReloadMessage
from incoming_queue import IncomingQueue

class Client:
   def __init__( self ):
      self._console = Console( '> ' )
      self._signal = IntSignal()
      self._socket: Optional[ socket.socket ] = None
      self._exit_requested: bool = False
      self._bot: Bot = Bot()
      
   def run( self ):
      while not self._is_done():
         self._tick()

   def _is_done( self ) -> bool:
      return self._exit_requested or self._signal.is_caught()

   def _tick( self ) -> None:
      try:
         streams: list[ object ] = [ sys.stdin ]
         if self._socket != None:
            streams.append( self._socket )
         readReady = select.select( streams, [], [] )[ 0 ]
         for stream in readReady:
            if stream is sys.stdin:
               self._handle_console_input()
            elif stream is self._socket:
               self._handle_bot_response()
      except KeyboardInterrupt:
         self._exit_requested = True

   def _handle_console_input( self ):
      self._console.handle_input()
      line = self._console.get_line()
      if line != None:
         line = line.strip().lower()
         if line in [ '.quit', '.q' ]:
            self._exit_requested = True
         elif line in [ '.c', '.connect' ]:
            self._connect()
         elif line in [ '.d', '.disconnect' ]:
            self._disconnect()
         else:
            self._handle_line( line )

   def _handle_line( self, line: str ) -> None:
      self._console.add_line( line )
      if self._socket != None:
         self._socket.send( line.encode() )
      else:
         self._console.add_line( 'error: not connected to bot' )

   def _connect( self ):
      if self._socket == None:
         try:
            addr = '/tmp/bzt.socket'
            self._console.add_line( f'connecting to {addr}...' )
            socket_handle = socket.socket( socket.AF_UNIX )
            socket_handle.connect( addr )
            self._socket = socket_handle
         except ConnectionError:
            self._console.add_line( 'failed to connect to bot' )

         #session = Session( self._signal, self._console, socket_handle )
         #session.run()
         #self._exit_requested = session._exit_requested
      else:
         self._console.add_line( 'error: already connected' )

   def _handle_bot_response( self ):
      if self._socket != None:
         queue = IncomingQueue( self._socket )
         if not queue.receive():
            self._disconnect()
            return
         while ( bytes := queue.fetch() ) != None:
            self._bot.handle_response( bytes )
            while ( event := self._bot.fetch_message() ) != None:
               self._process_message( event )

   def _process_message( self, message: object ):
      if isinstance( message, OutputLineMessage ):
         for line in message.lines:
            self._console.add_line( line )
      if isinstance( message, LineMessage ):
         line = message.content
         if message.severity != 'Plain':
            line = f"{message.severity}: {line}"
         self._console.add_line( line )
      elif isinstance( message, ConnectedMessage ):
         self._console.add_line( 'connected' )
      elif isinstance( message, ReloadMessage ):
         self._handle_reload()

   def _handle_reload( self ) -> None:
      self._console.add_line( 'bot is reloading, attempting to reconnect' )
      self._close_socket()
      tries_left = 3
      while tries_left > 0:
         try:
            addr = '/tmp/bzt.socket'
            self._console.add_line( f'connecting to {addr}...' )
            socket_handle = socket.socket( socket.AF_UNIX )
            socket_handle.settimeout( 1.0 )
            socket_handle.connect( addr )
            self._socket = socket_handle
            break
         except TimeoutError:
            pass
         except ConnectionError:
            time.sleep( 1.0 )
         tries_left -= 1
      else:
         self._console.add_line( 'failed to connect' )

   def _disconnect( self ) -> None:
      if self._socket != None:
         self._close_socket()
         self._console.add_line( 'disconnected' )
      else:
         self._console.add_line( 'error: not connected to bot' )

   def _close_socket( self ) -> None:
      if self._socket != None:
         self._socket.close()
         self._socket = None