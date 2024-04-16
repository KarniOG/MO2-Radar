import struct
import re
from lib import native
from lib.native import rpm


class Reader:
    """Utility for reading memory from a process"""

    __slots__ = ("pid",)

    def __init__(self, process_name: str):
        self.pid = native.pidof(process_name)

    def read(self, address: int, structure: str):
        """
        Read bytes using a struct format string and return an object or tuple of objects.
        https://docs.python.org/3/library/struct.html#format-characters

        Formats:
            `b`: int8
            `B`: uint8
            `h`: int16
            `H`: uint16
            `i`: int32
            `I`: uint32
            `q`: int64
            `Q`: uint64
            `f`: float32
            `d`: float64
            `?`: bool
            `x`: pad byte
        """
        # this function reads primitives in under 3us,
        # so performance should never be a problem.

        # read sizeof(structure) bytes and then unpack using struct

        # setting the size/alignment with "<" is more correct,
        # but I haven't had a problem using native mode, and it's like 1% faster.
        raw = rpm(self.pid, address, struct.calcsize(structure))
        try:
            data = struct.unpack(structure, raw)
        except struct.error:
            # dynamic typing gore, just raise an exception
            return None

        # struct.unpack() always returns a tuple, I don't like that.
        if len(data) == 1:
            return data[0]
        return data

    def read_string(self, address: int, byte_len: int, encoding="utf-8"):
        """read string from memory. length argument is the length of
        the string in bytes, not character count."""
        byte_len = min(byte_len, 255)
        buf = rpm(self.pid, address, byte_len)
        # if encoding == "utf-16":
        #   i = buf.find(b"\x00\x00")
        #   if i % 2 == 1:
        #       i += 1  # deal with utf-16 chars that end with 0x00
        #   return buf[:i].decode("utf-16")

        # i = buf.find(b"\x00")
        # if i != -1:
        #    return buf[:i].decode()
        return buf.decode(encoding)


class PatternScanner:
    """Instruction pattern scanning utility"""

    __slots__ = "exe_start", "exe_mem"

    def __init__(self, process_name: str, exe_file: str):
        pid = native.pidof(process_name)
        self.exe_start, exe_end = native.baseof_exe(pid, exe_file)
        # NOTE: this will be around 100 MB. make sure it gets cleared later.
        self.exe_mem = rpm(
            pid,
            self.exe_start,
            exe_end - self.exe_start,
        )

    def pattern_to_regex(self, signature: str) -> bytes:
        """
        Create bytes regex from space-separated hex string.
        Invalid sequences are treated as wildcards.
        Example input: `"de ad ? ef"`
        """
        pattern = bytearray()
        for b in signature.split():
            try:
                pattern += re.escape(bytes.fromhex(b))
            except ValueError:
                # if it isn't valid hex, treat it as a wildcard
                pattern += b"."
        return bytes(pattern)

    def pattern_scan(self, pattern: str, offset_index: int) -> int:
        """Scan for instruction pattern and return operand address."""
        pattern_regex = self.pattern_to_regex(pattern)
        match = re.search(pattern_regex, self.exe_mem)

        inst_start = match.start() + offset_index
        rip = inst_start + 4
        offset = int.from_bytes(self.exe_mem[inst_start:rip], byteorder="little")
        return self.exe_start + rip + offset
