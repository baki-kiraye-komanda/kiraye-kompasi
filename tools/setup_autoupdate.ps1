# setup_autoupdate.ps1 - hefelik avtomatik yenilemeni qurur (setup_autoupdate.bat isledir)
$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$repo = 'https://github.com/baki-kiraye-komanda/kiraye-kompasi.git'
$task = 'Kiraye Kompasi - hefelik yenileme'

function Fail($msg) { Write-Host ''; Write-Host "XETA: $msg" -ForegroundColor Red; exit 1 }

Write-Host '[1/4] Git yoxlanilir...'
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Fail 'Git tapilmadi. https://git-scm.com/download/win -> yukleyin, qurun (her yerde Next), sonra bu fayli yeniden isledin.'
}

Write-Host '[2/4] Qovluq GitHub reposu ile elaqelendirilir (fayllariniz deyismir)...'
if (-not (Test-Path '.git')) {
  git init -q -b main
  git remote add origin $repo
}
git config core.autocrlf false
git config user.name 'Kiraye Kompasi (avtoyenileme)'
git config user.email 'hemidshamilov-web@users.noreply.github.com'
git fetch -q origin main
if ($LASTEXITCODE -ne 0) { Fail 'GitHub-a qosulmaq olmadi. Internet var? Sonra yeniden isledin.' }
git reset -q origin/main          # yalniz git-in yaddasi yenilenir, fayllara toxunulmur
git branch -q --set-upstream-to=origin/main main 2>$null
$changed = @(git status --porcelain --untracked-files=no)
Write-Host ("    GitHub-dakindan ferqli fayl: {0}" -f $changed.Count)

Write-Host '[3/4] GitHub-a giris yoxlanilir (lazim olsa brauzer acilacaq - hemidshamilov-web ile daxil olun)...'
git push --dry-run -q origin main
if ($LASTEXITCODE -ne 0) {
  Fail ('GitHub icaze vermedi. Windows axtarisinda "Credential Manager" -> Windows Credentials -> ' +
        '"git:https://github.com" silin, sonra bu fayli yeniden isledin.')
}
Write-Host '    Giris ugurludur.'

Write-Host '[4/4] Task Scheduler-de tapsiriq yaradilir: her bazar 12:00...'
$ps1 = Join-Path $root 'tools\run_hidden.ps1'
$action = New-ScheduledTaskAction -Execute 'powershell.exe' `
  -Argument ("-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ps1`"") -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At '12:00'
# Komputer o vaxt sonulu olsa - acilan kimi isleyecek
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
  -ExecutionTimeLimit (New-TimeSpan -Hours 3)
try {
  Register-ScheduledTask -TaskName $task -Action $action -Trigger $trigger -Settings $settings -Force `
    -Description 'bina.az -> temizleme -> Oracle -> CSV -> GitHub (sayt). Log: logs\pipeline.log' -ErrorAction Stop | Out-Null
} catch { Fail ("Tapsiriq yaradilmadi: " + $_.Exception.Message) }

$info = Get-ScheduledTaskInfo -TaskName $task
Write-Host ''
Write-Host 'HAZIRDIR.' -ForegroundColor Green
Write-Host ("Novbeti avtomatik yenileme: {0}" -f $info.NextRunTime)
Write-Host 'Netice her defe logs\pipeline.log faylina yazilir.'
Write-Host ''
$ans = Read-Host 'Indi bir defe yoxlamaq ucun isledim? 20-30 deqiqe cekir, arxa planda gedir (b = beli, Enter = yox)'
if ($ans -eq 'b') {
  Start-ScheduledTask -TaskName $task
  Write-Host 'Basladi. Bitende logs\pipeline.log-un sonunda "ugurla bitdi" yazilacaq.' -ForegroundColor Green
}
