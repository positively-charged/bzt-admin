import signal

class IntSignal:
   def __init__( self ):
      def _on_interrupt( signum, frame ):
         raise KeyboardInterrupt()
      signal.signal( signal.SIGINT, _on_interrupt )

   def is_caught( self ) -> bool:
      pass