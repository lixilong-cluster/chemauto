# chk_remote_formchk_v7_jump_node16.ps1  (FIXED)
# 跨节点跳转模式 (Node00 -> Node16):
# - Upload CHK directly to the configured remote work directory on the login node
# - SSH into node00, and from there SSH -t into node16
# - Run existing c2f on node16
# - Download FCHK from node00
# - Delete temporary files
#
# FIX: 嵌套 ssh 的内层命令改用单引号包裹（原来用 ""..."" 双引号，
#      PowerShell 调用原生 ssh.exe 时会吞掉内嵌双引号，导致 && 链在
#      登录节点上被拆开，命令跑到了 node00 而不是 node16。

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$ChkPath
)

$ErrorActionPreference = "Stop"

function Fail($msg) {
    Write-Host ""
    Write-Host "ERROR: $msg" -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

function Info($msg) {
    Write-Host "[INFO] $msg" -ForegroundColor Cyan
}

function Ok($msg) {
    Write-Host "[OK] $msg" -ForegroundColor Green
}

function Read-Config($configPath) {
    if (!(Test-Path $configPath)) {
        Fail "Config file not found: $configPath"
    }
    $cfg = @{}
    Get-Content $configPath -Encoding UTF8 | ForEach-Object {
        $line = $_.Trim()
        if ($line -eq "" -or $line.StartsWith("#")) { return }
        $idx = $line.IndexOf("=")
        if ($idx -lt 1) { return }
        $key = $line.Substring(0, $idx).Trim()
        $val = $line.Substring($idx + 1).Trim()
        $cfg[$key] = $val
    }
    return $cfg
}

function Require-Cfg($cfg, $key) {
    if (!$cfg.ContainsKey($key) -or [string]::IsNullOrWhiteSpace($cfg[$key])) {
        Fail "Missing required config key: $key"
    }
    return $cfg[$key]
}

try {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $cfg = Read-Config (Join-Path $scriptDir "remote_formchk_config.ini")

    $remoteUser = Require-Cfg $cfg "REMOTE_USER"
    $remoteHost = Require-Cfg $cfg "REMOTE_HOST"
    $remotePort = Require-Cfg $cfg "REMOTE_PORT"
    $remoteWorkdir = Require-Cfg $cfg "REMOTE_WORKDIR"
    $remoteExecNode = Require-Cfg $cfg "REMOTE_EXEC_NODE"
    $remoteCommand = Require-Cfg $cfg "REMOTE_COMMAND"

    $chk = (Resolve-Path -LiteralPath $ChkPath).Path
    if (!(Test-Path -LiteralPath $chk)) { Fail "File not found: $chk" }
    if ([System.IO.Path]::GetExtension($chk).ToLower() -ne ".chk") {
        Fail "Input file is not .chk: $chk"
    }

    $localDir = Split-Path -Parent $chk
    $chkName = [System.IO.Path]::GetFileName($chk)
    $stem = [System.IO.Path]::GetFileNameWithoutExtension($chkName)
    $fchkName = "$stem.fchk"

    $remoteWorkdir = $remoteWorkdir.TrimEnd("/")
    $remoteChk = "$remoteWorkdir/$chkName"
    $remoteFchk = "$remoteWorkdir/$fchkName"

    $overwriteLocal = "no"
    if ($cfg.ContainsKey("OVERWRITE_LOCAL_FCHK")) { $overwriteLocal = $cfg["OVERWRITE_LOCAL_FCHK"].ToLower() }

    $localFchk = Join-Path $localDir $fchkName
    if ((Test-Path -LiteralPath $localFchk) -and ($overwriteLocal -ne "yes")) {
        $i = 1
        do {
            $localFchk = Join-Path $localDir ("{0}_{1:D3}.fchk" -f $stem, $i)
            $i++
        } while (Test-Path -LiteralPath $localFchk)
    }

    $sshCmd = "ssh"
    $scpCmd = "scp"
    if ($cfg.ContainsKey("SSH_EXE") -and $cfg["SSH_EXE"].Trim() -ne "") { $sshCmd = $cfg["SSH_EXE"].Trim() }
    if ($cfg.ContainsKey("SCP_EXE") -and $cfg["SCP_EXE"].Trim() -ne "") { $scpCmd = $cfg["SCP_EXE"].Trim() }

    $null = Get-Command $sshCmd -ErrorAction Stop
    $null = Get-Command $scpCmd -ErrorAction Stop

    $scpArgsCommon = @()
    $scpForceLegacy = "no"
    if ($cfg.ContainsKey("SCP_FORCE_LEGACY")) { $scpForceLegacy = $cfg["SCP_FORCE_LEGACY"].ToLower() }
    if ($scpForceLegacy -eq "yes") { $scpArgsCommon += "-O" }

    $session = "${remoteUser}@${remoteHost}"

    Info "Local CHK        : $chk"
    Info "Remote server    : $session"
    Info "Remote workdir   : $remoteWorkdir"
    Info "Execution node   : $remoteExecNode (Will Jump)"
    Info "Remote CHK       : $remoteChk"
    Info "Remote FCHK      : $remoteFchk"
    Info "Local output     : $localFchk"
    Write-Host ""

    Info "Checking remote workdir on login node..."
    & $sshCmd -p $remotePort $session "mkdir -p $remoteWorkdir && cd $remoteWorkdir && echo [LOGIN NODE] && hostname && pwd"
    if ($LASTEXITCODE -ne 0) { Fail "Remote workdir check failed." }

    Info "Uploading chk to login node..."
    & $scpCmd @scpArgsCommon -P $remotePort -p "$chk" "${session}:$remoteChk"
    if ($LASTEXITCODE -ne 0) { Fail "Upload failed." }

    # ========================================================
    # 核心跳转区：node00 -> node16
    # 关键修复：内层命令用单引号 '...' 包裹（不要用 ""..."" ）。
    # 单引号在传给 ssh.exe 时不会被 PowerShell 破坏，登录节点 bash
    # 会把整条 && 链作为一个参数原样发给 node16。
    # 注意：文件名不能再加内层单引号（bash 单引号无法嵌套）。
    # ========================================================
    Info "Jumping from login node to execution node ($remoteExecNode)..."
    Info ">> BE READY TO ENTER YOUR PASSWORD FOR $remoteExecNode <<"

    $innerCmd = "cd $remoteWorkdir && echo [EXEC NODE] && hostname && pwd && ls -lh $chkName && $remoteCommand && echo [AFTER CONVERT] && ls -lh $fchkName"
    $jumpCmd = "ssh -t $remoteExecNode '$innerCmd'"

    & $sshCmd -tt -p $remotePort $session $jumpCmd
    if ($LASTEXITCODE -ne 0) { Fail "Remote conversion failed on execution node." }
    # ========================================================

    Info "Downloading fchk..."
    & $scpCmd @scpArgsCommon -P $remotePort -p "${session}:$remoteFchk" "$localFchk"
    if ($LASTEXITCODE -ne 0) { Fail "Download failed." }

    $cleanRemote = "yes"
    if ($cfg.ContainsKey("CLEAN_REMOTE_FILES")) { $cleanRemote = $cfg["CLEAN_REMOTE_FILES"].ToLower() }

    if ($cleanRemote -eq "yes") {
        Info "Deleting remote chk/fchk from the configured remote work directory..."
        & $sshCmd -p $remotePort $session "cd $remoteWorkdir && rm -f '$chkName' '$fchkName'"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[WARN] Remote cleanup failed. Please check manually." -ForegroundColor Yellow
        }
    } else {
        Info "Remote files kept:"
        Info "  $remoteChk"
        Info "  $remoteFchk"
    }

    Ok "Created: $localFchk"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 0
}
catch {
    Fail $_.Exception.Message
}
