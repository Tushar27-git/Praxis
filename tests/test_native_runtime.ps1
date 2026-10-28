param([Parameter(Mandatory=$true)][string]$Python)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $taskRoot 'scripts/native-runtime.ps1')
$taskProbeFolder = Join-Path $taskRoot ('tmp/runtime-probe-' + [Guid]::NewGuid().ToString('N'))
& $Python -m venv --without-pip $taskProbeFolder
if ($LASTEXITCODE -ne 0) { throw 'Cannot create the isolated runtime fixture.' }
$taskBarePython = Join-Path $taskProbeFolder 'Scripts/python.exe'
if (Test-NativePython $taskBarePython) { throw 'A Python missing Pillow was incorrectly accepted.' }
if (-not (Test-NativePython $Python)) { throw 'The valid fallback Python was incorrectly rejected.' }
if ($ErrorActionPreference -ne 'Stop') { throw 'Runtime probe changed caller error handling.' }
Write-Output 'Native runtime fallback checks passed.'
