# copy from https://github.com/lmintlcx/pvzscripts/blob/master/pvz/core.py

import ctypes
import struct
from ctypes.wintypes import *
from ctypes import c_size_t as SIZE_T
import time

### win32 动态库
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
winmm = ctypes.windll.winmm
gdi32 = ctypes.windll.gdi32


# HWND FindWindowW(
#   LPCWSTR lpClassName,
#   LPCWSTR lpWindowName
# );
FindWindowW = user32.FindWindowW
FindWindowW.argtypes = [LPCWSTR, LPCWSTR]
FindWindowW.restype = HWND

# DWORD GetWindowThreadProcessId(
#   HWND    hWnd,
#   LPDWORD lpdwProcessId
# );
GetWindowThreadProcessId = user32.GetWindowThreadProcessId
GetWindowThreadProcessId.argtypes = [HWND, LPDWORD]
GetWindowThreadProcessId.restype = DWORD

# HANDLE OpenProcess(
#   DWORD dwDesiredAccess,
#   BOOL  bInheritHandle,
#   DWORD dwProcessId
# );
OpenProcess = kernel32.OpenProcess
OpenProcess.argtypes = [DWORD, BOOL, DWORD]
OpenProcess.restype = HANDLE

PROCESS_ALL_ACCESS = 0x001F0FFF

# BOOL WINAPI CloseHandle(
#   _In_ HANDLE hObject
# );
CloseHandle = kernel32.CloseHandle
CloseHandle.argtypes = [HANDLE]
CloseHandle.restype = BOOL

# BOOL WINAPI ReadProcessMemory(
#   _In_  HANDLE  hProcess,
#   _In_  LPCVOID lpBaseAddress,
#   _Out_ LPVOID  lpBuffer,
#   _In_  SIZE_T  nSize,
#   _Out_ SIZE_T  *lpNumberOfBytesRead
# );
ReadProcessMemory = kernel32.ReadProcessMemory
ReadProcessMemory.argtypes = [HANDLE, LPCVOID, LPVOID, SIZE_T, LPDWORD]
ReadProcessMemory.restype = BOOL

# BOOL PostMessageW(
#   HWND   hWnd,
#   UINT   Msg,
#   WPARAM wParam,
#   LPARAM lParam
# );
PostMessageW = user32.PostMessageW
PostMessageW.argtypes = [HWND, UINT, WPARAM, LPARAM]
PostMessageW.restype = BOOL

WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
VK_ESCAPE = 0x1B
VK_SPACE = 0x20
VK_RETURN = 0x0D
VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28
VK_CONTROL = 0x11

WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205

MK_LBUTTON = 0x0001
MK_RBUTTON = 0x0002

# 窗口句柄
hwnd = HWND()

# 进程标识
pid = DWORD()

# 进程句柄
handle = HANDLE()


def Info(msg: str):
    print(msg)


def Error(msg: str):
    raise Exception(msg)


def OpenProcessByWindow(className: str, windowName: str):
    """
    根据窗口的类名和标题打开进程.

    @参数 className(str): 窗口类名, 可省略为 None.

    @参数 windowName(str): 窗口标题, 可省略为 None.

    @返回值 (bool): 成功打开目标进程则返回 True.
    """

    global hwnd, pid, handle
    hwnd.value = FindWindowW(className, windowName)
    if hwnd.value is not None:
        GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        Info(f"找到窗口{windowName} 对应的进程, id 为{pid}")
    if pid.value != 0:
        handle.value = OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    else:
        Error(f"未找到窗口{windowName} 对应的进程")


def ReadMemory(dataType, *address, array=1):
    """
    读取内存数据.

    @参数 dataType(str): 数据类型, 取自 C/C++ 语言关键字, 可选值 ["char", "bool", "unsigned char", "short", "unsigned short", "int", "unsigned int", "long", "unsigned long", "long long", "unsigned long long", "float", "double"].

    @参数 address(int): 地址, 可为多级偏移.

    @参数 array(int): 数量. 默认一个, 大于一个时需要显式指定关键字参数.

    @返回值 (int/float/bool/tuple): 默认情况下返回单个数值, 获取多个数据则返回一个长度为指定数量的元组.

    @示例:

    >>> ReadMemory("int", 0x6a9ec0, 0x768, 0x5560)
    8000

    >>> ReadMemory("byte", 0x0041d7d0, array=3)
    (81, 131, 248)
    """

    # C/C++ 数据类型
    cppTypename = {
        "char": "b",
        "signed char": "b",
        "int8_t": "b",
        "unsigned char": "B",
        "byte": "B",
        "uint8_t": "B",
        "bool": "?",
        "short": "h",
        "int16_t": "h",
        "unsigned short": "H",
        "uint16_t": "H",
        "int": "i",
        "int32_t": "i",
        "intptr_t": "i",
        "unsigned int": "I",
        "uint32_t": "I",
        "uintptr_t": "I",
        "size_t": "I",
        "long": "l",
        "unsigned long": "L",
        "long long": "q",
        "int64_t": "q",
        "intmax_t": "q",
        "unsigned long long": "Q",
        "uint64_t": "Q",
        "uintmax_t": "Q",
        "float": "f",
        "double": "d",
    }

    level = len(address)  # 偏移级数
    offset = ctypes.c_void_p()  # 内存地址
    buffer = ctypes.c_uint()  # 中间数据缓冲
    bytesRead = ctypes.c_ulong()  # 已读字节数
    success = 0
    for i in range(level):
        offset.value = buffer.value + address[i]
        if i != level - 1:
            size = ctypes.sizeof(buffer)
            success = ReadProcessMemory(
                handle, offset, ctypes.byref(buffer), size, ctypes.byref(bytesRead)
            )
        else:
            fmtStr = "<" + str(array) + cppTypename[dataType]
            size = struct.calcsize(fmtStr)  # 目标数据大小
            buff = ctypes.create_string_buffer(size)  # 目标数据缓冲
            success = ReadProcessMemory(
                handle, offset, ctypes.byref(buff), size, ctypes.byref(bytesRead)
            )
            result = struct.unpack(fmtStr, buff.raw)
    if success == 0:
        print(f"错误 : 读取进程({pid})内存失败")

    if array == 1:
        return result[0]
    else:
        return result


# 毫秒级别睡眠
def Sleep(ms: float):
    time.sleep(ms / 1000)


def RightDown():
    PostMessageW(hwnd, WM_RBUTTONDOWN, 0, 0)


def RightUp():
    PostMessageW(hwnd, WM_RBUTTONUP, 0, 0)


def LeftClick():
    PostMessageW(hwnd, WM_LBUTTONDOWN, 0, 0)
    Sleep(50)
    PostMessageW(hwnd, WM_LBUTTONUP, 0, 0)


def KeyDown(key):
    PostMessageW(hwnd, WM_KEYDOWN, WPARAM(key), 0)


def KeyUp(key):
    PostMessageW(hwnd, WM_KEYUP, WPARAM(key), 0)
