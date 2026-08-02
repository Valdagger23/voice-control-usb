param(
    [string]$StarterExe = "C:\Program Files\voice-control-usb\voice-control-usb-starter.exe",
    [string]$ConfigPath = "C:\ProgramData\voice-control-usb\starter.json",
    [string]$TaskName = "voice-control-usb-starter"
)

$ErrorActionPreference = "Stop"

$action = New-ScheduledTaskAction -Execute $StarterExe -Argument "--config `"$ConfigPath`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Trusted USB starter for voice-control-usb" `
    -Force | Out-Null

Start-ScheduledTask -TaskName $TaskName

Write-Host "Installed and started scheduled task '$TaskName' for starter '$StarterExe'."
