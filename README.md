# Computer — 个人开发工具集与环境配置

个人工作环境配置笔记和实用 Python 脚本集合。

## 目录结构

```
├── Tools/              # Python 实用工具脚本
│   ├── clear_music.py      # 清理无音频文件的空目录
│   ├── fxs.py              # Spine 动画资源处理（Darkest Dungeon）
│   ├── game_dl.py          # Steam 游戏下载器
│   ├── mkv.py              # MKV 批量处理（章节、字体、轨道）
│   ├── novel_merge.py      # 小说目录合并工具
│   ├── pnp_cut.py          # PDF 卡片切割（Print & Play）
│   ├── pnp_print.py        # 卡片排布打印（A4）
│   ├── pnp_token.py        # 圆形容牌排版（A4 PDF）
│   ├── sort_photos.py      # 按 EXIF 日期整理照片
│   ├── sync_music.py       # 手机音乐同步工具
│   ├── tiles_upscale.py    # 像素图/瓦片图放大
│   ├── translatorGD.py     # 百度+腾讯翻译 CLI
│   └── config.json         # API 密钥配置（已 gitignore）
├── Windows.md          # Windows 11 装机与配置
├── WSL.md              # WSL 安装与 Docker 配置
├── Debain.md           # Debian 挂载盘、WPS 字体、dotfiles 等
├── requirements.txt    # Python 依赖
└── .venv/              # Python 虚拟环境
```

## 快速开始

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 系统环境

三份 `.md` 文件分别记录了 Windows 11、WSL 和 Debian 的配置步骤，包括：

- **Windows**: Scoop 包管理器、Python 环境、SSH/Git 配置、PowerShell 优化
- **WSL**: WSL2 安装与发行版管理、Docker Desktop
- **Debian**: 硬盘挂载、WPS 字体、Gnome 扩展、dotfiles 备份
