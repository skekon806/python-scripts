# Windows 笔记

> 个人 Windows 开发环境配置备忘，按场景分类，便于人类和 AI 检索。

---

## 目录

- [目录](#目录)
- [系统设置](#系统设置)
- [包管理 - Scoop](#包管理---scoop)
- [Python 环境](#python-环境)
- [SSH](#ssh)
- [Git](#git)
- [PowerShell](#powershell)
- [WSL](#wsl)
- [Docker](#docker)


---

## 系统设置

### 跳过 OOBE 账号登录

```powershell
# OOBE 界面按 Shift+F10 打开控制台，输入：
start ms-cxh:localonly
```

### 恢复 Windows 11 旧版右键菜单

```powershell
reg.exe add "HKCU\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32" /f /ve
```

### winget 使用

winget 默认为静默安装；如需离线安装，先用 `winget download` 下载安装包。

---

## 包管理 - Scoop

### 安装 Scoop

```powershell
# 设置用户安装路径
$env:SCOOP='D:\Software\Scoop'
[Environment]::SetEnvironmentVariable('USERSCOOP', $env:SCOOP, 'User')

# 允许 PowerShell 执行本地脚本
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 安装 Scoop
Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression
```

### 同步持久化配置

```powershell
cd D:\Software\Scoop\
git clone https://github.com/skekon806/scoop-persist.git persist
```

### 清理旧版本与缓存

```powershell
scoop cleanup --all
scoop cache rm --all
```

### 重装 / 修复 Scoop

```powershell
scoop reset *
```

---

## Python 环境

```powershell
python3 -m venv .venv
.venv/Scripts/python.exe -m pip install --upgrade pip
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

---

## SSH

```powershell
# 生成密钥
ssh-keygen -t rsa

# 查看公钥
cat ~/.ssh/id_rsa.pub
```

### GitHub SSH 配置

编辑 `~/.ssh/config`，添加：

```
Host github.com
    Hostname ssh.github.com
    Port 443
    User git
```

---

## Git

### 配置

```powershell
# 用户名和邮箱
git config --global user.name "skekon806"
git config --global user.email "skekon806@qq.com"

# 换行符（Windows）
git config --global core.autocrlf true
# 换行符（Linux）
# git config --global core.autocrlf input

git config --global core.safecrlf warn
git config --global advice.defaultbranchname false
```

### 克隆到指定目录

```powershell
cd ..
git clone https://github.com/skekon806/5G-TSN-BenKeBiShe.git temp
cd your-target-dir
robocopy ..\temp . /E /COPY:DAT /DCOPY:T
Remove-Item -Recurse -Force ..\temp
```

---

## PowerShell

### 安装与配置

```powershell
# 安装 PowerShell 7
winget install Microsoft.Powershell

# 为 PowerShell 5.1 安装 PSReadLine（Win11 不需要）
Install-Module -Name PSReadLine -Force -AllowClobber
```

```powershell
# 清空 PSReadLine 历史记录
Clear-Content (Get-PSReadLineOption).HistorySavePath
```

### UTF-8 编码设置

PowerShell 默认编码为 GB2312（中文 Windows），需显式设为 UTF-8 以避免乱码。

#### 方案一：Profile 配置（交互式终端）

每次打开终端自动加载：

```powershell
# 查看 profile 路径
$PROFILE

# 追加 UTF-8 编码设置
Add-Content -Path $PROFILE -Value @"

`$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
"@
```

#### 方案二：OpenCode 包装脚本（非交互式进程）

OpenCode 的 bash 工具以 `-Command` 模式运行 PowerShell，**不加载 profile**，需用包装脚本在进程层面设 UTF-8。

**文件 1** `~/.config/opencode/shell-utf8.cmd`：

```bat
@echo off
chcp 65001 > nul 2>&1
pwsh.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0shell-utf8-impl.ps1" %*
```

**文件 2** `~/.config/opencode/shell-utf8-impl.ps1`：

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$argsList = $args
$cmdIdx = [array]::IndexOf($argsList, '-Command')
if ($cmdIdx -lt 0) { $cmdIdx = [array]::IndexOf($argsList, '-c') }
if ($cmdIdx -ge 0 -and $cmdIdx + 1 -lt $argsList.Count) {
    Invoke-Expression $argsList[$cmdIdx + 1]
}
```

**文件 3** `~/.config/opencode/opencode.jsonc`（关键配置）：

```json
{
  "$schema": "https://opencode.ai/config.json",
  "shell": "C:\\Users\\<用户名>\\.config\\opencode\\shell-utf8.cmd"
}
```

---

## WSL

### 安装 WSL 与 Debian

```powershell
# 开启虚拟机和 WSL 可选功能
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
```

```powershell
# 下载安装 WSL 和 Debian
wsl --install -d Debian
wsl --set-default-version 2
wsl --update
wsl --set-version Debian 2
```

### Debian 换源（清华镜像）

```bash
cd /etc/apt/sources.list.d/
sudo vi debian.sources
```

粘贴以下内容：

```
Types: deb
URIs: https://mirrors.tuna.tsinghua.edu.cn/debian
Suites: trixie trixie-updates trixie-backports
Components: main contrib non-free non-free-firmware
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg

# 安全更新使用官方源
Types: deb
URIs: https://security.debian.org/debian-security
Suites: trixie-security
Components: main contrib non-free non-free-firmware
Signed-By: /usr/share/keyrings/debian-archive-keyring.gpg
```

---

## Docker

### Docker Desktop 安装

参见官方教程：[Turn on Docker Desktop WSL 2](https://docs.docker.com/desktop/features/wsl/#turn-on-docker-desktop-wsl-2)
