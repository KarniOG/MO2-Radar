import ctypes
import os
import psutil

# check for privileges on import
if os.getuid() != 0 or os.geteuid() != 0:
    raise RuntimeError("This program requires root privileges!")


class iovec(ctypes.Structure):  # pylint: disable=too-few-public-methods,invalid-name
    _fields_ = [("iov_base", ctypes.c_void_p), ("iov_len", ctypes.c_size_t)]


try:
    libc = ctypes.CDLL("libc.so.6")
except OSError:
    libc = ctypes.CDLL("libc.so")

libc.process_vm_readv.restype = ctypes.c_ssize_t
libc.process_vm_readv.argtypes = [
    ctypes.c_int,  # pid
    ctypes.POINTER(iovec),  # local_iov
    ctypes.c_ulong,  # liovcnt
    ctypes.POINTER(iovec),  # remote_iov
    ctypes.c_ulong,  # riovcnt
    ctypes.c_ulong,  # flags
]


def rpm(pid: int, address: int, size: int) -> bytes:
    if size > 0x1FFFFFFF:  # 512 MB
        raise MemoryError("You just tried to read WAY too much memory!")
    buf = ctypes.create_string_buffer(size)
    local_iov = iovec(ctypes.cast(buf, ctypes.c_void_p), size)
    remote_iov = iovec(address, size)

    nread = libc.process_vm_readv(pid, local_iov, 1, remote_iov, 1, 0)
    if nread != size:
        # it might be better to raise an exception (NOT MemoryError)
        # here since this usually leads to a TypeError anyway.
        return b""
    return buf.raw


def pidof(pname: str):
    """Basically pidof's one-shot mode."""
    for proc in psutil.process_iter(["name", "cmdline"]):
        if (
            proc.info["name"] == pname
            or proc.info["cmdline"]
            and proc.info["cmdline"][0].endswith(pname)
        ):
            return proc.pid
    raise RuntimeError("Process not found!")


def baseof_exe(pid: int, module_name: str) -> tuple[int, int]:
    """Return the start and end of a mapped file's first executable region."""
    p = psutil.Process(pid)
    base_addr = None
    for m in p.memory_maps(grouped=False):
        if m.path.endswith(module_name) and m.perms == "r--p" and base_addr is None:
            base_str = m.addr.split("-")[0]
            base_addr = int(base_str, 16)
        if base_addr and m.perms[2] == "x":
            exe_start, exe_end = m.addr.split("-")
            return int(exe_start, 16), int(exe_end, 16)
    raise RuntimeError(f'Could not find executable region for "{module_name}"!')
