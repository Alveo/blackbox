; this part needs the Inno Setup Pre Processor add-in
[ISPP]
#define AppVersion "1.7"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{12720A6C-A089-43B2-89AC-F066C075515F}
AppName=Austalk BlackBox
AppVersion={#AppVersion}
;AppVerName=Austalk BlackBox 1.3
AppPublisher=Austalk Project
AppPublisherURL=http://austalk.edu.au/
AppSupportURL=http://austalk.edu.au/
AppUpdatesURL=http://austalk.edu.au/
DefaultDirName=D:\BlackBoxPrograms
DisableDirPage=auto
DefaultGroupName=Austalk BlackBox
DisableProgramGroupPage=yes
OutputBaseFilename=blackbox-setup-{#AppVersion}
Compression=lzma
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; get all of the python and compiled SW from here
Source: "src\*"; DestDir: "{app}\blackbox"; Excludes: "test,cpp,Local_config.ini"; Flags: ignoreversion recursesubdirs createallsubdirs
; ffmpeg and mencoder needed for file compression
Source: "programs\ffmpeg.exe"; DestDir: "{app}"; Flags: ignoreversion  
Source: "programs\mencoder.exe"; DestDir: "{app}"; Flags: ignoreversion  


[INI]
; add some paths to the INI file
Filename: "{app}\blackbox\config.ini"; Section: "DEFAULT"; Key: "FFMPEG_PROGRAM"; String: "{app}\ffmpeg.exe";
Filename: "{app}\blackbox\config.ini"; Section: "DEFAULT"; Key: "MENCODER_PROGRAM"; String: "{app}\mencoder.exe";
Filename: "{app}\blackbox\config.ini"; Section: "DEFAULT"; Key: "PATH_RECORDINGS"; String: "D:\recordings";
Filename: "{app}\blackbox\config.ini"; Section: "DEFAULT"; Key: "PATH_FINAL"; String: "D:\final";
Filename: "{app}\blackbox\config.ini"; Section: "DEFAULT"; Key: "HOST_FINAL"; String: "austalk.edu.au";
Filename: "{app}\blackbox\config.ini"; Section: "DEFAULT"; Key: "VERSION"; String: "{#AppVersion}";

[Icons]
Name: "{group}\{cm:ProgramOnTheWeb,Austalk BlackBox}"; Filename: "http://austalk.edu.au/"
Name: "{group}\{cm:UninstallProgram,Austalk BlackBox}"; Filename: "{uninstallexe}"
Name: "{group}\Austalk Recorder"; Filename: "C:\Python27\pythonw.exe"; Parameters: "{app}\blackbox\recorder.py"; WorkingDir: "{app}\blackbox";
Name: "{group}\Austalk Compresser"; Filename: "C:\Python27\python.exe"; Parameters: "{app}\blackbox\copier.py"; WorkingDir: "{app}\blackbox";
Name: "{group}\Austalk Explorer"; Filename: "C:\Python27\python.exe"; Parameters: "{app}\blackbox\explorermain.py"; WorkingDir: "{app}\blackbox";
; desktop icons
Name: "{commondesktop}\Austalk Start"; Filename: C:\Python27\pythonw.exe; Parameters: {app}\blackbox\recorder.py; WorkingDir: {app}\blackbox; IconFilename: {app}\blackbox\images\play_green_controls.ico; 
Name: "{commondesktop}\Austalk Compresser"; Filename: C:\Python27\python.exe; Parameters: {app}\blackbox\copier.py; WorkingDir: {app}\blackbox; IconFilename: {app}\blackbox\images\database_green.ico; 
Name: "{commondesktop}\Austalk Explorer"; Filename: C:\Python27\python.exe; Parameters: {app}\blackbox\explorermain.py; WorkingDir: {app}\blackbox; IconFilename: {app}\blackbox\images\folder_green.ico; 

[Tasks]
Name: uninstallold; Description: "Uninstall previous versions of the software";

[InstallDelete]

Type: filesandordirs; Name: "D:\SSCP-GUI-1.0L"; Tasks: uninstallold;
Type: files; Name: "{userdesktop}\Austalk_Start.lnk"; Tasks: uninstallold;
Type: files; Name: "{commondesktop}\Blackbox Compresser.lnk"; Tasks: uninstallold;
Type: files; Name: "{commondesktop}\Blackbox Recorder.lnk"; Tasks: uninstallold;
; delete this if present, accidentally included in 1.3 distro
Type: files; Name: "{app}\blackbox\Local_config.ini";

