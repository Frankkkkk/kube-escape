from typing import Optional
import bencoder
from enum import Enum
import hashlib



class MsgType(Enum):
    CONNECT = 0
    DISCONNECT = 1
    DATA = 2


class WSMsg:
    socketid: int
    msg: MsgType
    payload: Optional[bytes]

    def __init__(self, socketid: int, msg: MsgType, payload: Optional[bytes] = None):
        self.socketid = socketid
        self.msg = msg
        self.payload = payload


    @staticmethod
    def from_bytes(b: bytes) -> 'WSMsg':
        d = bencoder.decode(b)
        socketid = d[b"sid"]
        mtype = MsgType(d[b"mt"])

        if mtype == MsgType.CONNECT:
            return WSMsg(socketid, mtype)
        elif mtype == MsgType.DISCONNECT:
            return WSMsg(socketid, mtype)
        elif mtype == MsgType.DATA:
            return WSMsg(socketid, mtype, d[b"data"])

    def to_bytes(self) -> bytes:
        d = {b"sid": self.socketid, b"mt": self.msg.value}
        if self.payload:
            d[b"data"] = self.payload
        return bencoder.encode(d)

    def __repr__(self):
        ret = f"MSG ({self.socketid}, {self.msg}"
        if self.msg == MsgType.DATA:
            ret += f", {hashlib.md5(self.payload).hexdigest()}"
        ret += ")"
        return ret
