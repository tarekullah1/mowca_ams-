# Setup Windows Task Scheduler to run BioTime Cloud Sync completely SILENTLY every 10 minutes
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VbsFile = Join-Path $ScriptDir "run_silent.vbs"
$TaskName = "BioTime_Neon_Sync"

Write-Host "Registering Silent Windows Scheduled Task: $TaskName" -ForegroundColor Cyan
Write-Host "Target script: $VbsFile"

$TaskRun = "wscript.exe `"$VbsFile`""
& schtasks.exe /create /tn $TaskName /tr "$TaskRun" /sc minute /mo 10 /f

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nTask '$TaskName' registered successfully (100% SILENT, runs every 10 minutes)!" -ForegroundColor Green
    & schtasks.exe /query /tn $TaskName /fo list
} else {
    Write-Host "`nFailed to register task." -ForegroundColor Red
}
