param(
    [string]$StarterExe = "C:\Program Files\voice-control-usb\voice-control-usb-starter.exe",
    [string]$ConfigPath = "C:\ProgramData\voice-control-usb\starter.json",
    [string]$TaskName = "voice-control-usb-starter"
)

$ErrorActionPreference = "Stop"

$action = New-ScheduledTaskAction -Execute $StarterExe -Argument "--config `"$ConfigPath`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Trusted USB starter for voice-control-usb" `
    -Force | Out-Null

Write-Host "Installed scheduled task '$TaskName' for starter '$StarterExe'."
