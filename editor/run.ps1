# Start the PPL visual editor dev server.
param(
    [string]$ListenHost = "127.0.0.1",
    [int]$Port = 8765,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$EditorDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $EditorDir

function Resolve-Python {
    foreach ($candidate in @(
            @{ Cmd = "python"; Args = @() },
            @{ Cmd = "python3"; Args = @() },
            @{ Cmd = "py"; Args = @("-3") }
        )) {
        if (-not (Get-Command $candidate.Cmd -ErrorAction SilentlyContinue)) {
            continue
        }
        $versionArgs = $candidate.Args + @("-c", "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)")
        & $candidate.Cmd @versionArgs 2>$null
        if ($LASTEXITCODE -eq 0) {
            return @{ Cmd = $candidate.Cmd; Args = $candidate.Args }
        }
    }
    throw "Python 3.10+ is required. Install Python and ensure python or py is on PATH."
}

$Root = Split-Path -Parent $EditorDir
if (-not (Test-Path (Join-Path $Root "src\ppl\__init__.py"))) {
    throw "PPL source not found at $Root\src\ppl. Run this script from a full repository checkout."
}

$python = Resolve-Python
$serveArgs = $python.Args + @("serve.py", "--host", $ListenHost, "--port", "$Port")
$url = "http://${ListenHost}:$Port/"

Write-Host "PPL editor -> $url"
Write-Host "Press Ctrl+C to stop."

if (-not $NoBrowser) {
    Start-Job -ScriptBlock {
        param($OpenUrl)
        Start-Sleep -Seconds 1
        Start-Process $OpenUrl | Out-Null
    } -ArgumentList $url | Out-Null
}

& $python.Cmd @serveArgs
