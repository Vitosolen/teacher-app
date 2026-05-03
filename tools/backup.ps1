# 班级养宠物系统 · SQLite 数据库自动备份（Windows）
#
# 用法：
#   1. 双击 backup.ps1（或 PowerShell 里运行）
#   2. 备份文件存到 backups/class_pet_yyyyMMdd_HHmm.db
#   3. 保留 30 天，超期自动清理
#
# 定时备份：用 Windows 任务计划程序设每天定时跑（见末尾说明）

$ErrorActionPreference = "Stop"

# 项目根（脚本所在目录的上一级）
$Root = Split-Path -Parent $PSScriptRoot
$Src = Join-Path $Root "class-pet-backend\class_pet.db"
$BackupDir = Join-Path $Root "backups"
$KeepDays = 30

# 检查源文件
if (-Not (Test-Path $Src)) {
    Write-Host "[错误] 数据库不存在：$Src" -ForegroundColor Red
    exit 1
}

# 备份目录
if (-Not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
}

# 文件名带时间戳
$Timestamp = Get-Date -Format "yyyyMMdd_HHmm"
$Dst = Join-Path $BackupDir "class_pet_$Timestamp.db"

# 复制（SQLite 单文件可直接 cp，比 dump 快）
Copy-Item $Src $Dst
$Size = (Get-Item $Dst).Length / 1KB
Write-Host "[OK] 备份成功 → $Dst ($([math]::Round($Size, 1)) KB)" -ForegroundColor Green

# 清理超期备份
$Cutoff = (Get-Date).AddDays(-$KeepDays)
$OldBackups = Get-ChildItem (Join-Path $BackupDir "class_pet_*.db") |
    Where-Object { $_.LastWriteTime -lt $Cutoff }
if ($OldBackups.Count -gt 0) {
    Write-Host "[清理] 删除 $($OldBackups.Count) 个超 $KeepDays 天的旧备份"
    $OldBackups | Remove-Item
}

# 显示当前所有备份
Write-Host "`n现有备份："
Get-ChildItem (Join-Path $BackupDir "class_pet_*.db") |
    Sort-Object LastWriteTime -Descending |
    Select-Object Name, @{N="大小KB"; E={[math]::Round($_.Length/1KB, 1)}}, LastWriteTime |
    Format-Table -AutoSize

# === 设置每日自动备份 ===
#
# 任务计划程序里加一项（管理员 PowerShell 一次执行）：
#
#   $action = New-ScheduledTaskAction -Execute "powershell.exe" `
#       -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$PSScriptRoot\backup.ps1`""
#   $trigger = New-ScheduledTaskTrigger -Daily -At 2:00am
#   Register-ScheduledTask -TaskName "ClassPetBackup" -Action $action -Trigger $trigger
#
# 取消：Unregister-ScheduledTask -TaskName "ClassPetBackup" -Confirm:$false
