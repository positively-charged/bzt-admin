use std::thread;
use std::sync::mpsc;
use std::os::unix::net::UnixStream;
use std::io::Write;
use std::io::Read;
use std::os::unix::thread::JoinHandleExt;

enum Event {
   ServerLine( String ),
   ServerDisconnected,
   TerminalLine( String ),
   TerminalDone,
}

struct EventQueue {

}

impl EventQueue {
   pub fn fetch() -> Event {
      Event::ServerLine( "".to_string() )
   }
}

struct Server {

}

impl Server {
   pub fn new( r: mpsc::Receiver<Event> ) -> Self {
      Self {}
   }
}

struct ServerThread {

}

impl ServerThread {
   pub fn new() -> Self {
      //let ( sender, receiver ) = mpsc::channel();
      ServerThread {}
   }
}

struct Console2 {
   read_thread: thread::JoinHandle<()>,
}

use std::io::stdout;
use crossterm::ExecutableCommand;
use crossterm::terminal;
use crossterm::event;
use crossterm::cursor;

impl Console2 {
   pub fn new( consumer: ConsoleConsumer ) -> Self {
      let mut terminal_reader = TerminalReader::new( consumer );
      let read_thread = thread::spawn( move || terminal_reader.run() );
      Self { read_thread }
   }

   pub fn print( &mut self, line: &str ) {
      stdout().execute( crossterm::style::Print( line ) );
   }
}

struct TerminalReader {
   consumer: ConsoleConsumer,
   buffer: String,
   done: bool,
   column: u16,
   row: u16,
}

impl TerminalReader {
   pub fn new( consumer: ConsoleConsumer ) -> Self {
      let pos = cursor::position().unwrap();
      Self { consumer, buffer: String::new(), done: false, column: pos.0,
         row: pos.1 }
   }

   pub fn run( &mut self ) {
      //terminal::enable_raw_mode();
      self.run_loop();
      //terminal::disable_raw_mode();
   }

   pub fn run_loop( &mut self ) {
      while ! self.done {
         stdout().execute( terminal::EnableLineWrap );
         stdout().execute( cursor::MoveTo( self.column, self.row ) );
         if let Ok( event::Event::Key( event ) ) = event::read() {
            self.handle_key( event );
         }
      }
   }

   fn handle_key( &mut self, event: event::KeyEvent ) {
      match event.code {
         event::KeyCode::Char( _ ) => self.handle_char_key( event ),
         event::KeyCode::Enter => self.handle_enter(),
         event::KeyCode::Backspace => self.handle_backspace(),
         _ => (),
      }
   }

   fn handle_char_key( &mut self, event: event::KeyEvent ) {
      if let event::KeyCode::Char( ch ) = event.code {
         if ch == 'c' && event.modifiers
            .contains( event::KeyModifiers::CONTROL ) {
            self.consumer.done();
            return;
         }
         self.buffer.push( ch );
         print!( "{}", ch );
         stdout().execute( cursor::MoveRight( 0 ) );
         self.update_pos();
      }
   }

   fn update_pos( &mut self ) {
      let pos = cursor::position().unwrap();
      self.column = pos.0;
      self.row = pos.1;
   }

   fn handle_enter( &mut self ) {
      let mut stdout = stdout();
      if self.consumer.give_line( self.buffer.clone() ) {
         stdout.execute( cursor::MoveToNextLine( 0 ) );
         print!( "bzt> " );
         self.update_pos();
      }
      else {
         self.done = true;
         return;
      }
      self.buffer.clear();
   }

   fn handle_backspace( &mut self ) {
      let mut stdout = stdout();
      stdout.execute( cursor::MoveLeft( 1 ) );
      stdout.execute( terminal::Clear( terminal::ClearType::FromCursorDown ) );
      self.update_pos();
      self.buffer.pop();
   }
}

fn main() {
   let ( sender, receiver ) = mpsc::channel();
   let ( keep_going, keep_going_receiver ) = mpsc::channel();

   let consumer = ConsoleConsumer::new( sender, keep_going_receiver );
   let mut console = Console2::new( consumer );
   console.print( "Hello, World!" );

   loop {
      if let Ok( line ) = receiver.recv() {
         match line {
            Event::TerminalLine( mut line ) => {
               if line.trim() == "exit" {
                  keep_going.send( false );
                  break;
               }
               println!( "got: {}", line );
               keep_going.send( true );
            }
            _ => break,
         }
      }
      else {
         break;
      }
   }

   println!( "waiting for console thread" );
   console.read_thread.join();
   println!( "exiting" );

   return;

   unsafe {
   libc::write( libc::STDIN_FILENO, b"hello".as_ptr()  as *const libc::c_void, 5 );
      let mut new_action: libc::sigaction = std::mem::uninitialized();
     new_action.sa_sigaction = libc::SIG_IGN;
     libc::sigemptyset (&mut new_action.sa_mask);
     new_action.sa_flags = 0;
      libc::sigaction( libc::SIGINT, &mut new_action, std::ptr::null_mut() );

      let mut set: libc::sigset_t = std::mem::uninitialized();
      libc::sigemptyset( &mut set );
      libc::sigaddset( &mut set, libc::SIGINT );
      libc::pthread_sigmask( libc::SIG_BLOCK, &set, std::ptr::null_mut() );
   }

   let mut stream = UnixStream::connect( "/tmp/bzt.socket" ).unwrap();
   let mut stream_reader = stream.try_clone().unwrap();

   let server_sender = sender.clone();
   let server_thread = thread::spawn( move || {
      let mut output = [ 0; 1000 ];
      loop {
         let num_bytes = stream_reader.read( &mut output ).unwrap();
         if num_bytes == 0 {
            break;
         }
         server_sender.send( Event::ServerLine(
            String::from_utf8_lossy( &output[ .. num_bytes ] ).to_string() ) );
         println!( "{}", num_bytes );
      }
      server_sender.send( Event::ServerDisconnected );
      println!( "done" );
   } );


   //let server_thread = ServerThread::new();
   //server_thread.execute( b"hello" );

   let ( console_keep_going, console_term_receiver ) = mpsc::channel();
   let console_thread = thread::spawn( move || run_console( sender,
      console_term_receiver ) );

   let mut disconnected = false;
   loop {
      if let Ok( line ) = receiver.recv() {
         match line {
            Event::ServerLine( line ) => {
               println!( "{}", line );
               console_keep_going.send( true );
            },
            Event::TerminalLine( mut line ) => {
               if line.trim() == "exit" {
                  console_keep_going.send( false );
                  break;
               }
               if ( disconnected ) {
               console_keep_going.send( true );
                  println!( "cant send, server disconnected" );
               }
               else {
                  line.push( '\n' );
                  stream.write( line.as_bytes() ).unwrap();
                  console_keep_going.send( true );
               }
            },
            Event::ServerDisconnected => {
               println!( "Server disconnected" );
               unsafe {
              libc::killpg( libc::getpgrp(),
                  libc::SIGINT );
                  println!( "sending signal to thread: {}", console_thread.as_pthread_t() );
               }
               disconnected = true;
            }
            Event::TerminalDone => {
               println!( "terminal done" );
               break;
            }
         }
      }
      else {
         break;
      }
   }
   println!( "waiting for console thread" );
   console_thread.join();
   println!( "exiting" );
}

fn run_console( sender: mpsc::Sender<Event>,
   keep_going: mpsc::Receiver<bool> ) {
   unsafe {
      println!( "console thread: {}", libc::pthread_self() );
   }


   unsafe {
      let mut set: libc::sigset_t = std::mem::uninitialized();
      libc::sigemptyset( &mut set );
      libc::sigaddset( &mut set, libc::SIGINT );
     // libc::pthread_sigmask( libc::SIG_UNBLOCK, &set, std::ptr::null_mut() );
   }

   let consumer = ConsoleConsumer::new( sender, keep_going );
   let mut console = Console::new( consumer );
   console.run();
   println!( "console thread terminating" );
}

struct ConsoleConsumer {
   sender: mpsc::Sender<Event>,
   keep_going: mpsc::Receiver<bool>,
}

impl ConsoleConsumer {
   pub fn new( sender: mpsc::Sender<Event>,
      keep_going: mpsc::Receiver<bool> ) -> Self {
      ConsoleConsumer { sender, keep_going }
   }

   pub fn give_line( &mut self, line: String ) -> bool {
      self.sender.send( Event::TerminalLine( line ) );
      match self.keep_going.recv() {
         Ok( true ) => true,
         _ => false,
      }
   }

   pub fn done( &mut self ) {
      self.sender.send( Event::TerminalDone );
   }
}

struct Console {
   consumer: ConsoleConsumer,
}

impl Console {
   pub fn new( consumer: ConsoleConsumer ) -> Self {
      Console { consumer }
   }

   pub fn run( &mut self ) {
      let mut editor = rustyline::Editor::<()>::new();
      loop {
         println!( "reading line" );
         let line = editor.readline( "bzt> " );
         println!( "got line" );
         match line {
            Ok( line ) => {
               println!( "give_line" );
               editor.add_history_entry( &line );
               if ! self.consumer.give_line( line.clone() ) {
                  break;
               }
            },
            Err( rustyline::error::ReadlineError::Interrupted ) |
            Err( rustyline::error::ReadlineError::Eof ) => {
               self.consumer.done();
               println!( "signal" );
               break;
            }
            Err( _ ) => {}
         }
      }
   }
}
