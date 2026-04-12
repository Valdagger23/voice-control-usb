param(
    [string]$Python = "python",
    [string]$DistRoot = "dist\windows"
)

$ErrorActionPreference = "Stop"

$assistantName = "voice-control-usb-assistant"
$starterName = "voice-control-usb-starter"

& $Python -m pip install pyinstaller

& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --name $assistantName `
    --paths src `
    --add-data "src\voice_control_usb\core\command_registry.json;voice_control_usb\core" `
    --add-data "src\voice_control_usb\core\workflow_registry.json;voice_control_usb\core" `
    --add-data "src\voice_control_usb\desktop\app_aliases.json;voice_control_usb\desktop" `
    src\voice_control_usb\__main__.py

& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --name $starterName `
    --paths src `
    src\voice_control_usb\starter\cli.py

$assistantTarget = Join-Path $DistRoot "assistant"
$starterTarget = Join-Path $DistRoot "starter"

New-Item -ItemType Directory -Force -Path $assistantTarget | Out-Null
New-Item -ItemType Directory -Force -Path $starterTarget | Out-Null

Copy-Item "dist\$assistantName.exe" (Join-Path $assistantTarget "$assistantName.exe") -Force
Copy-Item "dist\$starterName.exe" (Join-Path $starterTarget "$starterName.exe") -Force

Write-Host "Built Windows binaries:"
Write-Host "  Assistant: $(Join-Path $assistantTarget "$assistantName.exe")"
Write-Host "  Starter:   $(Join-Path $starterTarget "$starterName.exe")"
