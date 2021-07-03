from cx_Freeze import setup, Executable
import sys
import os

buildScriptDir = os.path.dirname(os.path.realpath(__file__))

base = "Win32GUI" if sys.platform=='win32' else None
packages = ["sqlalchemy"]
excluded = ["tkinter", "scipy", "notebook", "matplotlib", "numba"]
build_exe_opts = {
    "packages": packages,
    "excludes": excluded
}
execs = [
    Executable(script=f'{buildScriptDir}/main.py',base=base,target_name="DeadByDaylightMatchLog")
]

setup(name="DeadByDaylightMatchLog",version="1.0",executables=execs, options={"build_exe": build_exe_opts})