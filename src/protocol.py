from dataclasses import dataclass
import dataclasses

@dataclass
class ConnectedMessage:
   pass

@dataclass
class LineMessage:
   severity: str
   content: str
   pass

@dataclass
class OutputLineMessage:
   lines: list[ str ] = dataclasses.field( default_factory = list[ str ] )

class ExecuteMessage:
   command: str

@dataclass
class ReloadMessage:
   pass