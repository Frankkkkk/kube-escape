import bencoder

class Conn:
    socketid: int
    data: bytes

    def __init__(self, socketid: int, data: bytes):
        self.socketid = socketid
        self.data = data

    def to_ws_bytes(self) -> bytes:
        return bencoder.encode({b"socketid": self.socketid, b"data": self.data})

    @staticmethod
    def from_ws_bytes(b: bytes) -> 'Conn':
        d = bencoder.decode(b)
        return Conn(d[b"socketid"], d[b"data"])
