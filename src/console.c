#define NCURSES_WIDECHAR 1
#define _XOPEN_SOURCE

#include <stdlib.h>
#include <unistd.h>

#include <curses.h>

#include "console.h"

enum { MAX_LEN = 10 };
enum { PROMPT_SIZE = 5 };

struct output {
   int first_line;
   int total_lines;
   int height; // In rows.
};

struct console {
   WINDOW* main_win;
   wchar_t line[ MAX_LEN + 1 ];
   int max_x;
   int max_y;
   int pos;
   int cursor_pos;
};

struct console* console_init() {
   struct console* console = malloc( sizeof( *console ) );
   console->main_win = initscr();
   getmaxyx( console->main_win, console->max_y, console->max_x );
   for ( int i = 0; i < MAX_LEN; ++i ) {
      console->line[ i ] = '\0';
   }
   console->pos = 0;
   console->cursor_pos = 0;
   cbreak();
   noecho();
   return console;
}

void console_show( struct console* console ) {
   move( 5, 15 );
   refresh();
   printf( "a\n" );
   sleep( 2 );
}

void console_handle_input( struct console* console ) {
   int y = console->max_y - 1;
   int step = 0;

   int key;
   wget_wch( console->main_win, &key );
   switch ( key ) {
   case 127:
   case 330:
      step = -1;
      if ( console->pos > 0 ) {
         console->line[ --console->pos ] = '\0';
      }
      break;
   default:
      step = wcwidth( key );
      if ( console->pos < MAX_LEN ) {
         console->line[ console->pos++ ] = key;
         console->line[ console->pos ] = '\0';
      }
   }

   move( y, 0 );

   const wchar_t* start = console->line;
   if ( console->pos >= PROMPT_SIZE ) {
      start = console->line + console->pos - PROMPT_SIZE;
   }
   waddwstr( console->main_win, start );
   clrtoeol();

   console->cursor_pos += step;
   if ( console->cursor_pos < 0 ) {
      console->cursor_pos = 0;
   }
   else if ( console->cursor_pos >= PROMPT_SIZE ||
      console->pos >= PROMPT_SIZE ) {
      console->cursor_pos = PROMPT_SIZE;
   }
   move( y, console->cursor_pos );

   refresh();
}

void console_add_line( struct console* console, const char* line ) {

}  

void console_deinit( struct console* console ) {
   endwin();
}
