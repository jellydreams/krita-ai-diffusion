from enum import Enum
from typing import Optional
from PyQt5.QtCore import QObject, pyqtSignal
from .. import Client, MissingResource, eventloop, settings, util


class ConnectionState(Enum):
    disconnected = 0
    connecting = 1
    connected = 2
    error = 3


class Connection(QObject):
    """ViewModel for the connection to the diffusion server."""

    _instance = None

    changed = pyqtSignal()

    state = ConnectionState.disconnected
    client: Optional[Client] = None
    error: Optional[str] = None
    missing_resource: Optional[MissingResource] = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        super().__init__()

    async def _connect(self):
        self.state = ConnectionState.connecting
        self.error = None
        self.missing_resource = None
        self.changed.emit()
        try:
            self.client = await Client.connect(settings.server_url)
            self.state = ConnectionState.connected
        except MissingResource as e:
            self.error = (
                f"Connection established, but the server is missing one or more {e.kind.value}s."
            )
            self.missing_resource = e
            self.state = ConnectionState.error
        except Exception as e:
            self.error = util.log_error(e)
            self.state = ConnectionState.error
        self.changed.emit()

    def connect(self):
        eventloop.run(self._connect())

    def interrupt(self):
        eventloop.run(self.client.interrupt())