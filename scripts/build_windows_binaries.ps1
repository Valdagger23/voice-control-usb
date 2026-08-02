param(
    [string]$Python = "python",
    [string]$DistRoot = "dist\windows",
    [Parameter(Mandatory = $true)]
    [string]$UsbId,
    [Parameter(Mandatory = $true)]
    [string]$ReleaseId,
    [Parameter(Mandatory = $true)]
    [string]$SigningPrivateKeyPath
)

$ErrorActionPreference = "Stop"

$assistantName = "voice-control-usb-assistant"
$starterName = "voice-control-usb-starter"

& $Python -m pip install -e ".[windows,packaging]"

& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --name $assistantName `
    --paths src `
    --add-data "src\voice_control_usb\core\command_registry.json;voice_control_usb\core" `
    --add-data "src\voice_control_usb\core\workflow_registry.json;voice_control_usb\core" `
    --add-data "src\voice_control_usb\desktop\app_aliases.json;voice_control_usb\desktop" `
    --add-data "src\voice_control_usb\discord\discord_targets.json;voice_control_usb\discord" `
    --collect-all playwright `
    --hidden-import pycaw.pycaw `
    --collect-all uiautomation `
    --hidden-import win32com.client `
    --hidden-import winrt.windows.media.control `
    src\voice_control_usb\__main__.py

& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --name $starterName `
    --paths src `
    --collect-all cryptography `
    src\voice_control_usb\starter\cli.py

$usbRoot = Join-Path $DistRoot "usb"
$releaseRoot = Join-Path $usbRoot (Join-Path "releases" $ReleaseId)
$assistantTarget = Join-Path $releaseRoot "assistant"
$starterTarget = Join-Path $DistRoot "starter"

New-Item -ItemType Directory -Force -Path $assistantTarget | Out-Null
New-Item -ItemType Directory -Force -Path $starterTarget | Out-Null

Copy-Item "dist\$assistantName.exe" (Join-Path $assistantTarget "$assistantName.exe") -Force
Copy-Item "dist\$starterName.exe" (Join-Path $starterTarget "$starterName.exe") -Force

& $Python scripts\release_tool.py create `
    --release-dir $releaseRoot `
    --usb-id $UsbId `
    --release-id $ReleaseId `
    --entrypoint "assistant/voice-control-usb-assistant.exe" `
    --private-key $SigningPrivateKeyPath

& $Python scripts\release_tool.py provision-usb `
    --usb-root $usbRoot `
    --usb-id $UsbId `
    --release-id $ReleaseId

Write-Host "Built Windows binaries:"
Write-Host "  Assistant: $(Join-Path $assistantTarget "$assistantName.exe")"
Write-Host "  Starter:   $(Join-Path $starterTarget "$starterName.exe")"
Write-Host "  USB image: $usbRoot"
