#ifndef SRC_CONSOLE_H
#define SRC_CONSOLE_H

struct console;

struct console* console_init();
void console_show( struct console* console );
void console_deinit( struct console* console );

#endif
