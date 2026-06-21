# WSL使用

## WSL 安装

[Microsoft Learn](https://learn.microsoft.com/zh-cn/windows/wsl/install)

### 安装 WSL 命令

```Powershell
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
```

现在，可以使用单个命令安装运行 WSL 所需的所有内容。 右键单击并选择“以 管理员 身份运行”，在管理员模式下打开 PowerShell，输入 `wsl --install` 命令，然后重新启动计算机。

```PowerShell
wsl --install -d Debian
wsl --set-default-version 2
wsl --update
wsl --set-version Debian 2
```


## Docker Desktop 安装

[教程](https://docs.docker.com/desktop/features/wsl/#turn-on-docker-desktop-wsl-2)

