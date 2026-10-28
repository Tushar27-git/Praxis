function Test-NativePython {
    param([string]$Executable)
    if (-not (Test-Path -LiteralPath $Executable -PathType Leaf)) { return $false }
    $taskProbePreference = $ErrorActionPreference
    try {
        # Windows PowerShell 5.1 turns native stderr into terminating errors.
        # A missing dependency must reject this candidate, not abort fallback.
        $ErrorActionPreference = 'SilentlyContinue'
        & $Executable -c 'import sys, tkinter, PIL; assert sys.version_info >= (3,11)' 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    } finally {
        $ErrorActionPreference = $taskProbePreference
    }
}
