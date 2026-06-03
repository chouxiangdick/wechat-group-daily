"""find_image_key_windows.py - Windows 版 find_image_key

移植自 vchat_native/find_image_key_macos.c：
- 取本地真实 .dat 的 CT block 0（前 16 加密字节）作 oracle
- 扫 Weixin.exe 进程所有 readable 内存 region
- 每个 16 字节对齐位置当 AES-128 key
- AES-ECB 解密 CT，看明文是否图片 magic
- 命中即 key，输出 hex
"""
import sys
import os
import struct
import ctypes
import ctypes.wintypes as wt
import time
from pathlib import Path
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Win32 常量（来自 find_keys_windows.py）
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
TH32CS_SNAPPROCESS = 0x00000002

MEM_COMMIT = 0x1000
PAGE_READWRITE = 0x04
PAGE_EXECUTE_READWRITE = 0x40
PAGE_READONLY = 0x02
PAGE_GUARD = 0x100
PAGE_NOACCESS = 0x01

# 图片 magic（移植自 macOS C 版本，加强版：多 oracle 交叉验证 + 严格 magic）
def is_image_magic(pt: bytes, strict: bool = True) -> bool:
    """检查前 16 字节是否图片 magic。strict=True 时要求更严的格式特征。"""
    if len(pt) < 16:
        return False
    # JPEG: FF D8 FF E0/E1 + 'JFIF'/'Exif' 或 FF D8 FF E0+ (JFIF marker)
    if pt[0] == 0xFF and pt[1] == 0xD8 and pt[2] == 0xFF:
        if pt[3] in (0xE0, 0xE1, 0xDB, 0xEE, 0xC0, 0xC2, 0xC4):
            # JFIF: 0xE0 + 'JFIF\0'
            if pt[3] == 0xE0 and pt[6:10] == b'JFIF':
                return True
            # Exif: 0xE1 + 'Exif\0'
            if pt[3] == 0xE1 and pt[6:10] == b'Exif':
                return True
            # DQT/SOF markers（无 JFIF/Exif 也可能是 JPEG）
            if strict and pt[3] in (0xDB, 0xC0, 0xC2):
                return True
            if not strict:
                return True
    # PNG: 89 50 4E 47 0D 0A 1A 0A (8 字节 magic) + IHDR chunk (4 字节 length + 'IHDR')
    if pt[:8] == b'\x89PNG\r\n\x1a\n':
        if pt[8:12] == b'\x00\x00\x00\x0d' and pt[12:16] == b'IHDR':
            return True
    # GIF87a/GIF89a
    if pt[:6] in (b'GIF87a', b'GIF89a'):
        # 后续 2 字节是 width (LE), 再 2 字节 height
        if not strict or (pt[6] < 0x10 and pt[8] < 0x10):
            return True
    # WebP: RIFF????WEBP
    if pt[:4] == b'RIFF' and pt[8:12] == b'WEBP':
        return True
    return False

# 32-bit ctypes
class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wt.DWORD),
        ("cntUsage", wt.DWORD),
        ("th32ProcessID", wt.DWORD),
        ("cntThreads", wt.DWORD),
        ("th32DefaultHeapID", ctypes.c_void_p),
        ("th32ModuleID", wt.DWORD),
        ("cntThreads2", wt.DWORD),
        ("th32ParentProcessID", wt.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wt.DWORD),
        ("szExeFile", ctypes.c_wchar * 260),
    ]

class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wt.DWORD),
        ("PartitionId", wt.WORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wt.DWORD),
        ("Protect", wt.DWORD),
        ("Type", wt.DWORD),
    ]


def find_weixin_pid():
    """通过 ToolHelp32Snapshot 找 Weixin.exe 主进程 pid。"""
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    snap = k.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap == -1:
        return None
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        if not k.Process32FirstW(snap, ctypes.byref(entry)):
            return None
        while True:
            if entry.szExeFile.lower() == "weixin.exe":
                return entry.th32ProcessID
            if not k.Process32NextW(snap, ctypes.byref(entry)):
                break
    finally:
        k.CloseHandle(snap)
    return None


def read_ct_block(dat_path: str) -> bytes:
    """读 V2 .dat 偏移 15 后的 16 字节作 CT block 0."""
    with open(dat_path, "rb") as f:
        hdr = f.read(15)
    # V2 magic = 07 08 'V' '2' 08 07
    if hdr[:6] != b'\x07\x08V2\x08\x07':
        raise ValueError(f"Not V2 format: magic={hdr[:6]!r}")
    with open(dat_path, "rb") as f:
        f.seek(15)
        return f.read(16)


def try_key(key: bytes, ct: bytes) -> bool:
    """AES-128-ECB 解密 CT，看明文是否图片 magic。"""
    if len(key) < 16:
        return False
    try:
        cipher = Cipher(algorithms.AES(key[:16]), modes.ECB(), backend=default_backend())
        dec = cipher.decryptor()
        pt = dec.update(ct) + dec.finalize()
    except Exception:
        return False
    return is_image_magic(pt)


def scan_process_memory(pid: int, ct_list: list) -> bytes:
    """扫进程内存所有 readable region，找 16 字节 key.
    ct_list: 多个 oracle 的 CT block 列表（要求 key 在所有 oracle 上都通过）"""
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    PROCESS_ALL_ACCESS = 0x1F0FFF
    h = k.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
    if not h:
        print(f"OpenProcess({pid}) failed: {ctypes.get_last_error()}")
        return None

    found_key = None
    regions_scanned = 0
    bytes_scanned = 0
    candidates_tried = 0
    start_time = time.time()
    n_oracle = len(ct_list)

    try:
        addr = ctypes.c_void_p(0)
        mbi = MEMORY_BASIC_INFORMATION()
        sz = ctypes.sizeof(mbi)

        while True:
            ret = k.VirtualQueryEx(h, addr, ctypes.byref(mbi), sz)
            if ret == 0:
                break
            if (mbi.State == MEM_COMMIT and
                (mbi.Protect & PAGE_READWRITE or mbi.Protect & PAGE_EXECUTE_READWRITE) and
                not (mbi.Protect & PAGE_GUARD) and
                not (mbi.Protect & PAGE_NOACCESS) and
                0 < mbi.RegionSize < 128 * 1024 * 1024):
                buf = (ctypes.c_ubyte * mbi.RegionSize)()
                read = ctypes.c_size_t(0)
                ok = k.ReadProcessMemory(h, ctypes.c_void_p(mbi.BaseAddress),
                                          buf, mbi.RegionSize, ctypes.byref(read))
                if ok and read.value > 0:
                    data = bytes(buf[:read.value])
                    regions_scanned += 1
                    bytes_scanned += len(data)
                    for i in range(0, len(data) - 16, 16):
                        candidates_tried += 1
                        key_candidate = data[i:i+16]
                        if len(key_candidate) == 16 and all(try_key(key_candidate, ct) for ct in ct_list):
                            found_key = key_candidate
                            elapsed = time.time() - start_time
                            print(f"\n[FOUND!] 耗时 {elapsed:.1f}s · 扫 {regions_scanned} regions · {bytes_scanned/1024/1024:.1f} MB · 试 {candidates_tried} keys")
                            print(f"  BaseAddr=0x{mbi.BaseAddress:x}  offset=0x{i:x}")
                            print(f"  Key hex: {found_key.hex()}")
                            print(f"  验证 {n_oracle} 个 oracle 全部通过")
                            return found_key

                if regions_scanned % 100 == 0:
                    elapsed = time.time() - start_time
                    print(f"  [{elapsed:.1f}s] regions={regions_scanned} bytes={bytes_scanned/1024/1024:.1f}MB candidates={candidates_tried}")

            next_addr = (mbi.BaseAddress or 0) + mbi.RegionSize
            if next_addr <= (addr.value or 0):
                break
            addr = ctypes.c_void_p(next_addr)
    finally:
        k.CloseHandle(h)

    elapsed = time.time() - start_time
    print(f"\n[NOT FOUND] 扫 {regions_scanned} regions · {bytes_scanned/1024/1024:.1f} MB · 试 {candidates_tried} keys · 耗时 {elapsed:.1f}s")
    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: find_image_key_windows.py <path-to-v2-dat1> [path-to-v2-dat2 ...]")
        print("Example: find_image_key_windows.py dat1.dat dat2.dat")
        sys.exit(1)

    dat_paths = sys.argv[1:]
    print(f"Reading CT blocks from {len(dat_paths)} .dat files (cross-validation)...")
    ct_list = []
    for dp in dat_paths:
        try:
            ct = read_ct_block(dp)
            print(f"  {Path(dp).name[:30]}: {ct.hex()}")
            ct_list.append(ct)
        except Exception as e:
            print(f"  Error: {e}")
            continue

    if not ct_list:
        print("No valid V2 .dat files")
        sys.exit(1)

    print("\nFinding Weixin.exe pid...")
    pid = find_weixin_pid()
    if not pid:
        print("Weixin.exe not running")
        sys.exit(1)
    print(f"Weixin.exe pid: {pid}")

    print(f"\nScanning process memory for AES-128 key (16 bytes) with {len(ct_list)}-oracle cross-validation...")
    key = scan_process_memory(pid, ct_list)
    if key:
        print(f"\nImage AES key: {key.hex()}")
        # 写 key 到 ~/.vchat/data/config.json
        cfg_path = Path.home() / '.vchat' / 'data' / 'config.json'
        if cfg_path.exists():
            import json
            cfg = json.loads(cfg_path.read_text())
            cfg['image_aes_key'] = key.hex()
            cfg_path.write_text(json.dumps(cfg, indent=2))
            print(f"  写入 {cfg_path}")
    else:
        print("\nFailed to find key.")


if __name__ == "__main__":
    main()
