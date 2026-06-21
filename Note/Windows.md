## Windows 11
### 跳过账号登陆
`Shift+F10`打开控制台

```powershell
start ms-cxh:localonly
```
### 右键菜单
```powershell
reg.exe add "HKCU\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32" /f /ve
```

### winget 
winget默认为静默安装，可使用winget download下载安装包后手动安装

## 安装Scoop

### 下载Scoop
```Powershell
# 设置用户安装路径
$env:SCOOP='D:\Software\Scoop' 
[Environment]::SetEnvironmentVariable('USERSCOOP', $env:SCOOP, 'User')

# 设置允许 PowerShell 执行本地脚本
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 安装 Scoop
Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression
```

### 同步配置
```Powershell
cd D:\Software\Scoop\
git clone https://github.com/skekon806/scoop-persist.git persist
```
### 删除旧版本
```powershell
scoop cleanup --all
```

### 重装Scoop
```powershell
# Scoop 自动修复
scoop reset *
```

## Python环境
```powershell
python3 -m venv .venv
.venv/Scripts/python.exe -m pip install --upgrade pip
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

## SSH
```powershell
# 生成SSH密钥
ssh-keygen -t rsa

# 查看公钥
cat ~/.ssh/id_rsa.pub
```

### github
To set this in your SSH configuration file, edit the file at ~/.ssh/config, and add this section:
```powershell
Host github.com
    Hostname ssh.github.com
    Port 443
    User git
```
## Git


### 配置Git
```powershell
# 配置用户名和邮箱
git config --global user.name "skekon806"
git config --global user.email "skekon806@qq.com"
# 配置换行符
git config --global core.autocrlf true
```

### Git恢复
```powershell
cd ..
# 1. 在 D 盘临时目录克隆仓库
git clone https://github.com/skekon806/5G-TSN-BenKeBiShe.git temp

# 2. 进入你最终想要放代码的目标目录
cd your-target-dir

# 3. 将临时目录中的所有内容（包括隐藏文件）复制到当前目录
robocopy ..\temp . /E /COPY:DAT /DCOPY:T
# 复制隐藏文件（robocopy 默认会处理，但确保 .git 等已复制）

# 4. 确认无误后，删除临时目录
Remove-Item -Recurse -Force ..\temp
```

## PowerShell
```powershell
# 安装PowerShell 7
winget install Microsoft.Powershell
# Administrator运行，为Poweshell5.1安装PSReadLine，win11不用
Install-Module -Name PSReadLine -Force -AllowClobber
```

```powershell
# 清空PSReadLine的历史记录
Clear-Content (Get-PSReadLineOption).HistorySavePath
```