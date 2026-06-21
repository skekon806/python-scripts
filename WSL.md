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
wsl --install
wsl --set-default-version 2
wsl --update
wsl --set-version Debian 2
```


### 更改安装的默认 Linux 分发版

默认情况下，已安装的 Linux 分发版将为 Ubuntu。 可以通过使用-d标志来更改这一点。

若要更改安装的分发版，请输入：

```PowerShell
wsl.exe --install -d [Distro]
```

将 [Distro] 替换为您想要安装的分发版名称。

若要查看可通过在线商店下载的可用 Linux 分发版列表，请输入：

```PowerShell
wsl.exe --list --online
```

若要安装未列为可用的 Linux 分发版，可以使用 TAR 文件 导入任何 Linux 分发 版。 或者在某些情况下，您可以使用 .appx 文件进行安装。 还可以创建自己的 自定义 Linux 分发版 ，以便与 WSL 一起使用。

## Docker Desktop 安装

[教程](https://docs.docker.com/desktop/features/wsl/#turn-on-docker-desktop-wsl-2)

