import curses
import time
import wcwidth
from typing import *
import sys

MAX_LEN = 100
PROMPT_SIZE = 100
DISPLAY_SIZE = 100
MAX_HISTORY = 10

class Display:
   def __init__( self, win: curses.window, initial_width: int,
      start_pos: int ):
      self.win: curses.window = win
      self.lines: list = []
      self.pos: int = 0
      self.start_pos: int = start_pos

   def add_line( self, line: str ):
      if len( self.lines ) >= DISPLAY_SIZE:
         self.lines.pop( 0 )
      self.lines.append( line )


   def render( self ):
      max_lines = self.start_pos + 1
      lines_written = 0
      for pos in reversed( self.lines ):
         if lines_written >= max_lines:
            break
         self.win.move( self.start_pos - lines_written, 0 )
         self.win.addstr( self.lines[ len( self.lines ) - 1 - lines_written ] )
         self.win.clrtoeol()
         lines_written += 1

class Prompt:
   def __init__( self, win: curses.window, y: int ):
      self._win: curses.window = win
      self._y = y
      self._line = []
      self._history: list = []
      self._cursor_pos = 0
      self._history_pos = -1
      self._pos = 0
      self._prefix = ''

   def handle_input( self ) -> Optional[ str ]:
      step = 0
      key = self._win.get_wch()
      if isinstance( key, str ):
         keyCode = ord( key )
         if keyCode == 127:
            step -= 1
            if len( self._line ) > 0:
               self._line.pop()
            pass
         elif key == "\n":
            self._add_history( self._line )
            line = "".join( self._line )
            self._line = []
            self._cursor_pos = 0
            self._history_pos = -1
            self._pos = 0
            return line
         else:
            step = wcwidth.wcwidth( key )
            if self._pos < MAX_LEN:
               self._line.append( key )
               self._pos += 1
      else:
         if key == curses.KEY_UP:
            if self._history_pos == -1:
               self._history_pos = len( self._history )
               self._history_pos -= 1
            else:
               if self._history_pos > 0:
                  self._history_pos -= 1
            self._set_line( self._history_pos )
         elif key == curses.KEY_DOWN:
            if self._history_pos >= 0:
               self._history_pos += 1
               if self._history_pos < len( self._history ):
                  self._set_line( self._history_pos )
               else:
                  self._line = []
                  self._pos = 0
                  self._cursor_pos = 0
                  self._history_pos = -1
      self._cursor_pos += step
      if self._cursor_pos < 0:
         self._cursor_pos = 0
      elif self._cursor_pos >= PROMPT_SIZE or \
         len( self._line ) >= PROMPT_SIZE:
         self._cursor_pos = PROMPT_SIZE
      return None

   def _set_line( self, pos: int ) -> None:
      if pos >= 0:
         self._line = self._history[ pos ]
         self._pos = len( self._line )
         self._cursor_pos = len( self._line )
         if self._cursor_pos >= PROMPT_SIZE or \
            len( self._line ) >= PROMPT_SIZE:
            self._cursor_pos = PROMPT_SIZE

   def _add_history( self, line: list ) -> None:
      if len( self._history ) >= MAX_HISTORY:
         self._history.pop( 0 )
      self._history.append( line )

   def set_prefix( self, prefix: str ) -> None:
      self._prefix = prefix

   def render( self ) -> None:
      x = 0
      self._win.move( self._y, x )

      if self._prefix != '':
         self._win.addstr( self._prefix )
         x += len( self._prefix )
         self._win.move( self._y, x )

      start = self._line
      if len( start ) >= PROMPT_SIZE:
         start = start[ -PROMPT_SIZE : ]
      self._win.addstr( "".join( start ) )

      self._win.move( self._y, x + self._cursor_pos )
      self._win.clrtoeol()

class Console:
   def __init__( self, prefix: str = '' ):
      win = curses.initscr()
      win.keypad( True )
      curses.cbreak()
      curses.noecho()
      
      self._win: curses.window = win
      max_y, max_x = win.getmaxyx()
      self._display: Display = Display( win, max_x, max_y - 2 )
      self._prompt: Prompt = Prompt( win, max_y - 1 )
      self._prompt.set_prefix( prefix )
      self._lines: list = []

      self.render()

   def handle_input( self ):
      line = self._prompt.handle_input()
      if isinstance( line, str ):
         self._lines.append( line )
      self.render()

   def add_line( self, line ):
      self._display.add_line( line )
      self.render()

   def get_line( self )-> Optional[ str ]:
      if len( self._lines ) > 0:
         return self._lines.pop( 0 )
      return None

   def render( self ):
      self._display.render()
      self._prompt.render()
      self._win.refresh()

   def __del__( self ):
      curses.endwin()
