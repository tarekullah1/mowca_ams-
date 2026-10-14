Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
ScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
PythonW = ScriptDir & "\venv\Scripts\pythonw.exe"
Worker = ScriptDir & "\sync_worker.py"

' Run pythonw.exe completely hidden (0 = SW_HIDE, True = wait for completion)
WshShell.Run """" & PythonW & """ """ & Worker & """ --once", 0, True
