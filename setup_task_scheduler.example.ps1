# setup_task_scheduler.example.ps1

# CHANGE THESE VALUES for your own computer:
$ProjectRoot = "C:\path\to\your\root\folder"
$PythonExe   = "C:\path\to\your\python\executable.exe"
$TaskName    = "regcheck production pipeline"

$Action = New-ScheduledTaskAction `
    -Execute $PythonExe `
    -Argument "`"$ProjectRoot\run_pipeline.py`" --mode production" `
    -WorkingDirectory $ProjectRoot

$Trigger = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Hours 3) `
    -RepetitionDuration (New-TimeSpan -Days 3650)

$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew

$Principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Runs the regcheck production pipeline every 3 hours." `
    -Force

Write-Host "Scheduled task '$TaskName' created successfully."