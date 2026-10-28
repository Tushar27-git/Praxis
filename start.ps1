$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
. (Join-Path $PSScriptRoot 'scripts/native-runtime.ps1')
$runtimeCandidates = @(
    (Join-Path $PSScriptRoot '.venv\Scripts\python.exe'),
    (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe'),
    (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'),
    (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe')
)
$runtime = $null
foreach ($candidate in $runtimeCandidates) {
    if (Test-NativePython $candidate) { $runtime = $candidate; break }
}
if (-not $runtime) {
    $installedPython = Get-Command python -ErrorAction SilentlyContinue
    if ($installedPython -and $installedPython.Source -notlike '*\WindowsApps\*' -and (Test-NativePython $installedPython.Source)) {
        $runtime = $installedPython.Source
    }
}
if (-not $runtime) {
    Write-Error 'Python 3.11+ with Tkinter and Pillow was not found. Install requirements-native.txt, then run: python -m coc_advisor'
    exit 1
}
$windowedRuntime = Join-Path (Split-Path -Parent $runtime) 'pythonw.exe'
if (Test-Path -LiteralPath $windowedRuntime -PathType Leaf) {
    Start-Process -FilePath $windowedRuntime -ArgumentList '-m','coc_advisor' -WorkingDirectory $PSScriptRoot -WindowStyle Normal
} else {
    & $runtime -m coc_advisor
    exit $LASTEXITCODE
}
