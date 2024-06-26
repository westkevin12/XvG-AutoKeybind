[Files]
Source: "dist\XvGKeybind.exe"; DestDir: "{userappdata}\XvG Auto"
Source: "icon.ico"; DestDir: "{userappdata}\XvG Auto"
Source: "profiles.dat"; DestDir: "{userappdata}\XvG Auto"; Permissions: everyone-modify

[Dirs]
Name: "{userappdata}\XvG Auto"; Permissions: everyone-modify

[Icons]
Name: "{commondesktop}\Auto Keybind"; Filename: "{userappdata}\XvG Auto\XvG Keybind.exe"; Tasks: desktopicon

[Tasks]
Name: desktopicon; Description: "Create a shortcut"; GroupDescription: "Additional tasks:"

[Run]
Filename: "{app}\XvG Keybind.exe"; Parameters: "--icon_file={userappdata}\XvG Auto\icon.ico"; Flags: nowait postinstall

[Setup]
AppName=XvG AutoKeybind
DefaultDirName={userappdata}\XvG Auto
AppPublisher=XvG west
PrivilegesRequired=none
AppPublisherURL=http://www.extremevisiongaming.com
AppSupportURL=http://www.extremevisiongaming.com/support
AppUpdatesURL=http://www.extremevisiongaming.com/updates
AppVersion=1.0
AppVerName=XvG AutoKeybind 1.0
AppCopyright=© eXtreme Vision Gaming 2023
OutputBaseFilename=XvGAutoSetup