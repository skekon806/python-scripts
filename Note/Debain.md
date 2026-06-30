# Debian 笔记

> 个人 Debian 开发环境配置备忘，按场景分类。

---

## 目录

- [系统初始化](#系统初始化)
- [磁盘挂载](#磁盘挂载)
- [目录软链接](#目录软链接)
- [WPS 字体](#wps-字体)
- [开发工具](#开发工具)
- [GNOME 设置](#gnome-设置)
- [Dotfiles 备份](#dotfiles-备份)

---

## 系统初始化

```bash
sudo apt update
```

---

## 磁盘挂载

### 挂载 NTFS 数据盘

```bash
# 安装 ntfs-3g 以支持 NTFS 格式
sudo apt install ntfs-3g

# 查看分区 UUID
lsblk -f

# 备份 fstab
sudo cp /etc/fstab /etc/fstab.bak

# 编辑 fstab 添加挂载项
sudo vi /etc/fstab
```

`/etc/fstab` 追加：

```
# <UUID>      <挂载点>   <文件系统>  <选项>                                  <转储> <检查>
UUID=<UUID>   /data      ntfs-3g     defaults,uid=1000,gid=1000,umask=0022   0      0
```

### 挂载移动硬盘

```bash
sudo mkdir -p /media/NEWSMY
```

`/etc/fstab` 追加：

```
UUID=<UUID>  /media/NEWSMY ntfs-3g defaults,uid=1000,gid=1000,umask=0022,x-gvfs-show,nofail 0 0
```

---

## 目录软链接

将用户目录链接到数据盘：

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

---

## WPS 字体

```bash
sudo cp *.ttc /usr/share/fonts/wps-office/
sudo cp *.ttf /usr/share/fonts/wps-office/
sudo chmod 644 /usr/share/fonts/wps-office/*
sudo fc-cache -fv
```

---

## 开发工具

### IDEA

```bash
tar -zxvf ideaIC.tar.gz -C ~/tools/
mv ~/tools/ideaIC ~/tools/idea
```

---

## GNOME 设置

```bash
sudo apt install gnome-tweaks gnome-shell-extensions

# 备份 GNOME 设置
dconf dump / > ~/gnome-settings-backup.ini
```

### 推荐扩展

- [Customize IBus](https://extensions.gnome.org/extension/4112/customize-ibus/)
- [AppIndicator Support](https://extensions.gnome.org/extension/615/appindicatorsupport/)
- [Clipboard Indicator](https://extensions.gnome.org/extension/779/clipboard-indicator/)

---

## Dotfiles 备份

用 `git --bare` 方式管理配置文件。

### 初始化

```bash
cd ~
git init --bare ~/.dotfiles
alias dotfiles='/usr/bin/git --git-dir=$HOME/.dotfiles/ --work-tree=$HOME'
dotfiles config --local status.showUntrackedFiles no
dotfiles add .bashrc
dotfiles commit -m "Backup configs"

# 关联远程仓库
dotfiles remote add origin git@github.com:<用户名>/dotfiles.git
dotfiles push origin master
```

### 日常使用

```bash
# 暂存更新
dotfiles add -u
dotfiles add ~/.config/mpv
dotfiles commit -m "update config"
dotfiles push
```

### 恢复配置

```bash
git clone --bare <git-repo-url> $HOME/.dotfiles
alias dotfiles='/usr/bin/git --git-dir="$HOME/.dotfiles/" --work-tree="$HOME"'
dotfiles checkout
dotfiles config --local status.showUntrackedFiles no
```
