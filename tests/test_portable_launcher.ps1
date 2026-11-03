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

# Behavioral regression: execute the launcher from a directory with spaces and
# require a clear error when the EXE is missing. No user installation is touched.
$fixtureRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('Matick launcher fixture ' + [guid]::NewGuid().ToString('N'))
$fixture = Join-Path $fixtureRoot 'portable with spaces'
New-Item -ItemType Directory -Path $fixture -Force | Out-Null
try {
    $fixtureScript = Join-Path $fixture 'start_matick_portable.ps1'
    Copy-Item -LiteralPath $script -Destination $fixtureScript
    $pwsh = (Get-Process -Id $PID).Path
    $savedLocation = (Get-Location).Path
    $output = & $pwsh -NoProfile -NonInteractive -File $fixtureScript 2>&1 | Out-String
    $exitCode = $LASTEXITCODE
    if ($exitCode -eq 0 -or $output -notmatch 'MatickStudioLM.exe no encontrado') {
        throw "Missing-EXE smoke test failed (exit=$exitCode): $output"
    }
    if ((Get-Location).Path -ne $savedLocation) {
        throw 'Launcher smoke test changed the caller working directory'
    }
    # The negative test expects a nonzero native exit code; clear it after validation.
    # Otherwise pwsh -File propagates the child failure as the test script exit code.
    $global:LASTEXITCODE = 0
    Write-Host 'PASS: missing executable reports an error from a path with spaces'
    # Positive smoke test: execute a harmless compiled EXE from a path with spaces.
    $probeExe = Join-Path $fixture 'MatickStudioLM.exe'
    $probeResult = Join-Path $fixtureRoot 'launch-probe.txt'
    $probeSource = @'
using System;
using System.IO;
public static class MatickLauncherProbe {
    public static int Main() {
        File.WriteAllText(Environment.GetEnvironmentVariable("MATICK_LAUNCH_PROBE"),
                          Environment.CurrentDirectory);
        return 0;
    }
}
'@
    Add-Type -TypeDefinition $probeSource -OutputAssembly $probeExe -OutputType ConsoleApplication
    $oldProbe = $env:MATICK_LAUNCH_PROBE
    try {
        $env:MATICK_LAUNCH_PROBE = $probeResult
        $output = & $pwsh -NoProfile -NonInteractive -File $fixtureScript 2>&1 | Out-String
        $exitCode = $LASTEXITCODE
        if ($exitCode -ne 0 -or -not (Test-Path -LiteralPath $probeResult)) {
            throw "Launcher did not start probe executable (exit=$exitCode): $output"
        }
        $observed = (Get-Content -LiteralPath $probeResult -Raw).Trim()
        if ($observed -ne $fixture) {
            throw "Launcher working directory mismatch: expected '$fixture', got '$observed'"
        }
        $global:LASTEXITCODE = 0
        Write-Host 'PASS: launcher executes a real EXE from its own directory'
    } finally {
        $env:MATICK_LAUNCH_PROBE = $oldProbe
    }
} finally {
    Remove-Item -LiteralPath $fixtureRoot -Recurse -Force -ErrorAction SilentlyContinue
}
