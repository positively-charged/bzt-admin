#include <stdio.h>
#include <stdbool.h>
#include <signal.h>
#include <locale.h>

#include <unistd.h>
#include <sys/select.h>

#include "console.h"

static bool done;

void on_intr() {
   done = true;
}

int main() {
   setlocale( LC_CTYPE, "" );
   signal( SIGINT, on_intr );

   struct console* console = console_init();

   while ( ! done ) {
      fd_set read;
      FD_ZERO( &read );
      FD_SET( STDIN_FILENO, &read );
      int result = select( STDIN_FILENO + 1, &read, NULL, NULL, NULL );
      if ( result != -1 ) {
         if ( FD_ISSET( STDIN_FILENO, &read ) ) {
            console_handle_input( console );
         }
      }
   }
   fputs( "abc\n", stdout );
/*
   console_show( console );
*/

   printf( "done\n" );
   console_deinit( console );
   return 0;
}
