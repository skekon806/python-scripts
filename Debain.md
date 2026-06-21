## 挂载盘

```bash

sudo apt update
#支持ntfs格式的分区
sudo apt install ntfs-3g 
#查看分区信息，拷贝UUID
lsblk -f
# 记得备份 sudo cp /etc/fstab /etc/fstab.bak
sudo vi /etc/fstab

# <UUID>        <挂载点>        <文件系统>    <选项>                    <转储> <检查>
UUID=你的UUID   /data   ntfs-3g       defaults,uid=1000,gid=1000,umask=0022   0      0

```
## 挂载移动硬盘出现问题
```bash
sudo mkdir -p /media/NEWSMY


UUID=746CE1476CE104A8 /media/NEWSMY ntfs-3g defaults,uid=1000,gid=1000,umask=0022,x-gvfs-show,nofail 0 0


```


## 软连接到数据盘

```bash
rmdir ~/下载
ln -s /data/Downloads ~/下载

rmdir ~/文档
ln -s /data/Files/Documents ~/文档

rmdir ~/桌面
ln -s /data/Files/Desktop ~/桌面

rmdir ~/图片
ln -s /data/Files/Pictures ~/图片
```

## WPS字体

```bash
sudo cp *.ttc /usr/share/fonts/wps-office/
sudo cp *.ttf /usr/share/fonts/wps-office/

sudo chmod 644 /usr/share/fonts/wps-office/*

sudo fc-cache -fv
```


## 下载idea

```bash
tar -zxvf ideaIC.tar.gz -C ~/tools/

mv ~/tools/ideaIC ~/tools/idea

```

## gnome设置

```bash
sudo apt install gnome-tweaks gnome-shell-extensions

dconf dump / > ~/gnome-settings-backup.ini
```

下载gnome扩展

[customize-ibus](https://extensions.gnome.org/extension/4112/customize-ibus/)

[appindicatorsupport](https://extensions.gnome.org/extension/615/appindicatorsupport/)

[clipboard-indicator](https://extensions.gnome.org/extension/779/clipboard-indicator/)


## dotfiles 备份 .config

```bash
# 用 git 管理配置文件
cd ~
git init --bare ~/.dotfiles
alias dotfiles='/usr/bin/git --git-dir=$HOME/.dotfiles/ --work-tree=$HOME' #仅在临时会话生效
dotfiles config --local status.showUntrackedFiles no
dotfiles add .bashrc 
dotfiles commit -m "Backup configs"

# 链接github
dotfiles remote -v
dotfiles remote add origin git@github.com:你的用户名/dotfiles.git
dotfiles push origin master  # 推送到 GitHub/GitLab
```

```bash
# 后续add commit push
dotfiles add -u
dotfiles add ~/.config/mpv

```

```bash
git clone --bare <git-repo-url> $HOME/.dotfiles
alias dotfiles='/usr/bin/git --git-dir="$HOME/.dotfiles/" --work-tree="$HOME"'
dotfiles checkout
dotfiles config --local status.showUntrackedFiles no
```
