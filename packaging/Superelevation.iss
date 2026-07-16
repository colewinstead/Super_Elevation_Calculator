#ifndef MyAppVersion
  #define MyAppVersion "0.0.0-dev"
#endif

[Setup]
AppId={{519538DB-65A7-48DF-9AC5-2EC0F26071FB}
AppName=Superelevation Calculator
AppVersion={#MyAppVersion}
AppPublisher=Cole Winstead
DefaultDirName={autopf}\Superelevation Calculator
DefaultGroupName=Superelevation Calculator
OutputDir=..\dist
OutputBaseFilename=SuperelevationCalculator-{#MyAppVersion}-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\SuperElevation.exe

[Files]
Source: "..\dist\SuperElevation.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Superelevation Calculator"; Filename: "{app}\SuperElevation.exe"
Name: "{autodesktop}\Superelevation Calculator"; Filename: "{app}\SuperElevation.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
Filename: "{app}\SuperElevation.exe"; Description: "Launch Superelevation Calculator"; Flags: nowait postinstall skipifsilent
