import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, TypeVar

# ========== 全局配置 ==========
VIDEO_DIR = Path.cwd()
MKVMERGE = Path(r"mkvmerge")
MKVPROREDIT = Path(r"mkvpropedit")
EPISODES_TXT = "episodes.txt"
LOG_FILE: Path = VIDEO_DIR / f"mkv_tool_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# 全局变量
_dry_run = False
_log_buffer: List[str] = []


# ========== 日志工具 ==========
def log(msg: str) -> None:
    print(msg)
    _log_buffer.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def save_log() -> None:
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(_log_buffer))
    print(f"\n📝 日志已保存: {LOG_FILE.name}")


# ========== 基础检查工具 ==========
def check_tools() -> None:
    missing = [(tool, path) for tool, path in
               [("mkvmerge", MKVMERGE), ("mkvpropedit", MKVPROREDIT)]
               if not path.exists()]
    if missing:
        log("❌ 未找到必需的工具，请检查路径：")
        for tool, path in missing:
            log(f"   {tool}: {path}")
        sys.exit(1)


def confirm(prompt: str = "确认执行？(Y/N): ") -> bool:
    while True:
        match input(prompt).strip().upper():
            case "Y" | "YES":
                return True
            case "N" | "NO":
                return False
            case _:
                print("请输入 Y 或 N。")


# ========== 核心工具函数 ==========
def extract_sxxexx(filename: str) -> Optional[str]:
    m = re.search(r"S(\d{2})E(\d{2})", filename, re.IGNORECASE)
    return f"S{m.group(1)}E{m.group(2)}" if m else None


def parse_season_episode(filename: str) -> Optional[Tuple[int, int]]:
    m = re.search(r"S(\d+)E(\d+)", filename, re.IGNORECASE)
    return (int(m.group(1)), int(m.group(2))) if m else None


def parse_episode_number(filename: str) -> Optional[int]:
    m = re.search(r"(?:S00)?E(\d{2})|EP?(\d{2})|第(\d{1,2})集|(\d{2})\s*\.[^\\]", filename, re.IGNORECASE)
    if m:
        for g in m.groups():
            if g is not None:
                return int(g)
    return None


def run_command(cmd: List[str], hide_output: bool = True) -> bool:
    if _dry_run:
        log(f"  [DRY RUN] {' '.join(cmd)}")
        return True
    try:
        kwargs = dict(check=True, encoding='utf-8', errors='replace')
        kwargs['stdout'] = kwargs['stderr'] = subprocess.DEVNULL if hide_output else None
        subprocess.run(cmd, **kwargs)
        return True
    except subprocess.CalledProcessError:
        return False


def set_mkv_title(file_path: Path, title: str) -> bool:
    cmd = [str(MKVPROREDIT), str(file_path), "--edit", "info", "--set", f"title={title}"]
    return run_command(cmd)


def get_mkv_files(recursive: bool = False) -> List[Path]:
    files = list((VIDEO_DIR.rglob if recursive else VIDEO_DIR.glob)("*.mkv"))
    files.sort(key=lambda p: str(p).lower())
    return files


# ========== 功能一：合并字幕 ==========
def merge_subtitles() -> None:
    mkv_files = get_mkv_files()
    ass_files = list(VIDEO_DIR.glob("*.ass"))

    mkv_map = {extract_sxxexx(f.name): f for f in mkv_files if extract_sxxexx(f.name)}
    ass_map = {extract_sxxexx(f.name): f for f in ass_files if extract_sxxexx(f.name)}

    common_keys = sorted(set(mkv_map) & set(ass_map))
    if not common_keys:
        log("❌ 未找到任何匹配的 SxxExx 视频-字幕对。")
        return

    log(f"🔍 找到 {len(common_keys)} 对可处理的视频与字幕\n")
    log("📋 即将处理的文件：")
    for key in common_keys:
        log(f"   {key}: {mkv_map[key].name} + {ass_map[key].name}")
    print()

    if not confirm("确认开始合并？删除原始文件不可恢复！(Y/N): "):
        log("❌ 用户取消操作")
        return

    success_count = 0
    for i, key in enumerate(common_keys, 1):
        video, ass = mkv_map[key], ass_map[key]
        output = VIDEO_DIR / ass.with_suffix(".mkv").name

        log(f"\n[{i}/{len(common_keys)}] 📦 处理 {key}")

        if output.exists() and not confirm(f"   ⚠️ 输出已存在: {output.name}\n   覆盖？(Y/N): "):
            log(f"   ⏭️ 跳过 {key}")
            continue

        cmd = [
            str(MKVMERGE), "--ui-language", "zh_CN", "--priority", "lower",
            "--output", str(output), "--no-subtitles", str(video),
            "--language", "0:zh", str(ass)
        ]

        if not run_command(cmd, hide_output=False):
            log(f"   ❌ 失败: mkvmerge 错误")
            output.unlink(missing_ok=True)
            continue

        if _dry_run:
            log(f"   ✅ [模拟] 成功: {output.name}")
            success_count += 1
        elif output.stat().st_size > 0:
            ass.unlink(missing_ok=True)
            video.unlink(missing_ok=True)
            log(f"   ✅ 成功: {output.name}")
            success_count += 1
        else:
            log(f"   ❌ 失败: 输出文件无效")
            output.unlink(missing_ok=True)

    log(f"\n🎉 合并完成: {success_count}/{len(common_keys)} 成功")


# ========== 功能二：episodes.txt 模式 ==========
def parse_episodes_txt(txt_path: Path) -> Dict[str, List[str]]:
    if not txt_path.is_file():
        log(f"❌ 找不到 {txt_path}")
        sys.exit(1)

    season_data: Dict[str, List[str]] = {}
    current_season = None

    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if m := re.match(r"(?:S|Season)\s*(\d+)", line, re.IGNORECASE):
                current_season = f"S{int(m.group(1))}"
                season_data[current_season] = []
            elif current_season and re.match(r"^\d+\.", line):
                season_data[current_season].append(re.sub(r"^\d+\.\s*", "", line))

    return season_data


# ========== 功能二、三：通用标题设置流程 ==========
def process_mkv_titles(pending: List[Tuple[Path, str]], action_label: str) -> None:
    """通用标题设置流程：扫描→确认→执行"""
    if not pending:
        log("\n❌ 没有可处理的文件")
        return

    print()
    if not confirm(f"确认设置 {len(pending)} 个文件的标题？(Y/N): "):
        log("❌ 用户取消操作")
        return

    processed = 0
    for path, title in pending:
        if set_mkv_title(path, title):
            log(f"  ✅ {path.relative_to(VIDEO_DIR)}")
            processed += 1
        else:
            log(f"  ❌ 失败: {path.relative_to(VIDEO_DIR)}")

    log(f"\n🎉 {action_label}: {processed}/{len(pending)} 成功")


def set_episode_titles() -> None:
    use_prefix = confirm('是否在标题前添加"第X集 - "前缀？(Y/N): ')
    print()

    txt_path = VIDEO_DIR / EPISODES_TXT
    log(f"📁 当前目录: {VIDEO_DIR}")
    log(f"📄 读取: {txt_path}")

    season_titles = parse_episodes_txt(txt_path)
    log(f"✅ 成功解析 {len(season_titles)} 个季: {list(season_titles.keys())}")

    pending: List[Tuple[Path, str]] = []
    log("\n📋 检测到的文件：")
    for file_path in get_mkv_files(recursive=True):
        se = parse_season_episode(file_path.name)
        if not se:
            log(f"   ⚠️ 跳过（无法识别 SxxExx）: {file_path.relative_to(VIDEO_DIR)}")
            continue

        s_num, e_num = se
        titles = season_titles.get(f"S{s_num}")
        if not titles:
            log(f"   ⚠️ 跳过（无 S{s_num} 标题数据）: {file_path.relative_to(VIDEO_DIR)}")
            continue
        if e_num < 1 or e_num > len(titles):
            log(f"   ⚠️ 跳过（集数超出范围 [1-{len(titles)}]）: {file_path.relative_to(VIDEO_DIR)} → E{e_num}")
            continue

        title = titles[e_num - 1]
        full_title = f"第{e_num}集 - {title}" if use_prefix else title
        pending.append((file_path, full_title))
        log(f"   {file_path.relative_to(VIDEO_DIR)} → {full_title}")

    process_mkv_titles(pending, "标题设置完成")


# ========== 功能三：国产剧模式 ==========
def set_chinese_drama_titles() -> None:
    log("🇨🇳 进入国产剧模式：自动设置 '第xx集' 标题...")

    pending: List[Tuple[Path, str]] = []
    log("\n📋 检测到的文件：")
    for file_path in get_mkv_files(recursive=True):
        e_num = parse_episode_number(file_path.name)
        if e_num:
            pending.append((file_path, f"第{e_num}集"))
            log(f"   {file_path.relative_to(VIDEO_DIR)} → 第{e_num}集")
        else:
            log(f"   ⚠️ 跳过（无法识别集数）: {file_path.relative_to(VIDEO_DIR)}")

    process_mkv_titles(pending, "国产剧模式处理完成")


# ========== 模式选择 ==========
def select_mode() -> int:
    log("\n" + "=" * 40)
    log("请选择操作模式：")
    log("  1. 合并字幕 (.ass + .mkv)")
    log("  2. 设置标题 (需 episodes.txt)")
    log("  3. 国产剧模式（自动识别集数）")
    log("  0. 退出")
    log("=" * 40)

    while True:
        choice = input("\n请输入选项 (0-3): ").strip()
        if choice in ("0", "1", "2", "3"):
            return int(choice)
        print("无效输入，请输入 0-3")


# ========== 主程序 ==========
def main() -> None:
    global _dry_run

    log("🚀 MKV 批量处理工具 启动")
    check_tools()

    print()
    if len(sys.argv) > 1 and sys.argv[1].lower() in ("--dry-run", "--dry"):
        _dry_run = True
        log("🔧 启用 DRY RUN 模式（仅模拟不执行实际操作）")

    try:
        while True:
            mode = select_mode()
            print()

            if mode == 0:
                log("👋 退出")
                break
            elif mode == 1:
                merge_subtitles()
            elif mode == 2:
                set_episode_titles()
            elif mode == 3:
                set_chinese_drama_titles()

            print()
            if not confirm("继续其他操作？(Y/N): "):
                break
    finally:
        save_log()
        input("\n按回车键退出...")


if __name__ == "__main__":
    main()
