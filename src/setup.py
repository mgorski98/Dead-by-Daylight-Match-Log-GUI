from cx_Freeze import setup, Executable
import sys

base = "Win32GUI" if sys.platform=='win32' else None
packages = ["sqlalchemy"]
excluded = ["tkinter", "scipy", "notebook", "matplotlib"]
build_exe_opts = {
    "packages": packages,
    "excludes": excluded
}
execs = [
    Executable(script='main.py',base=base,target_name="DeadByDaylightMatchLog")
]

setup(name="DeadByDaylightMatchLog",version="1.0",executables=execs, options={"build_exe": build_exe_opts})