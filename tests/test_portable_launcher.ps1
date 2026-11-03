#requires -Version 5.1
$ErrorActionPreference = 'Stop'
$script = Join-Path $PSScriptRoot '..\tools\start_matick_portable.ps1'
$tokens = $null
$parseErrors = $null
[System.Management.Automation.Language.Parser]::ParseFile(
    (Resolve-Path -LiteralPath $script).Path,
    [ref]$tokens, [ref]$parseErrors) | Out-Null
if ($parseErrors.Count -ne 0) {
    throw ('Launcher PowerShell syntax invalid: ' + ($parseErrors | Out-String))
}
$source = Get-Content -LiteralPath $script -Raw
foreach ($required in @('Push-Location -LiteralPath $exeDir',
                       'Pop-Location',
                       'Resolve-Path -LiteralPath $exe',
                        'Join-Path $PSScriptRoot ''MatickStudioLM.exe''')) {
    if (-not $source.Contains($required)) {
        throw "Missing portable launcher safeguard: $required"
    }
}
Write-Host 'PASS: launcher parses and preserves working directory safeguards'
