# run_hidden.ps1 - Task Scheduler run_pipeline.bat-i gizli pencerede bununla isledir
$root = Split-Path -Parent $PSScriptRoot
$bat = Join-Path $root 'run_pipeline.bat'
& cmd.exe /c "`"$bat`""
exit $LASTEXITCODE
