import re
import shutil
import subprocess
import sys
from pathlib import Path

VIDEO_DIR = Path.cwd()
MKVPROREDIT = "mkvpropedit"

_dry_run = True


def confirm(prompt: str = "确认执行？(Y/N): ") -> bool:
    while True:
        match input(prompt).strip().upper():
            case "Y" | "YES":
                return True
            case "N" | "NO":
                return False
            case _:
                print("请输入 Y 或 N。")


def run_command(cmd: list[str]) -> bool:
    if _dry_run:
        print(f"  [DRY RUN] {' '.join(cmd)}")
        return True
    try:
        subprocess.run(cmd, check=True, encoding='utf-8', errors='replace',
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False


def process_pasted_text(text: str) -> list[str]:
    text = re.sub(r"^(\d+)$\n(.+)", r"\1. \2", text, flags=re.MULTILINE)
    return [re.sub(r"^\d+\.\s*", "", line)
            for line in text.splitlines()
            if re.match(r"^\d+\. ", line)]


def paste_titles(label: str) -> list[str]:
    print(f"\n📋 {label}，粘贴完毕后输入 --- 并按回车：")
    print("-" * 40)
    pasted = []
    while True:
        line = input()
        if line.strip() == "---":
            break
        pasted.append(line)
    titles = process_pasted_text("\n".join(pasted))
    if titles:
        print(f"✅ 提取到 {len(titles)} 个标题")
    else:
        print("⚠️ 未能提取到剧集标题")
    return titles


def main() -> None:
    global _dry_run

    print("🚀 MKV 标题设置工具 启动")

    if not shutil.which(MKVPROREDIT):
        print(f"❌ 未找到 mkvpropedit，请确认已安装并加入 PATH")
        sys.exit(1)
    print()

    use_prefix = confirm('是否在标题前添加"第X集 - "前缀？(Y/N): ')
    print()

    mkv_files = sorted(VIDEO_DIR.rglob("*.mkv"), key=lambda p: str(p).lower())
    if not mkv_files:
        print("❌ 未找到 MKV 文件")
        sys.exit(1)

    print(f"📁 当前目录: {VIDEO_DIR}")
    print(f"🔍 找到 {len(mkv_files)} 个 MKV 文件\n")

    # auto-detect mode
    season_map: dict[int, set[int]] = {}
    for fp in mkv_files:
        if m := re.search(r"S(\d+)E(\d+)", fp.name, re.IGNORECASE):
            season_map.setdefault(int(m.group(1)), set()).add(int(m.group(2)))

    is_flat = not season_map
    pending: list[tuple[Path, str]] = []

    if is_flat:
        print("📄 检测为无季模式（国产剧，未发现 SxxExx 命名）")
        flat_titles = paste_titles("请粘贴剧集列表文本")
        if not flat_titles:
            sys.exit(1)

        print("\n📋 检测到的文件：")
        for fp in mkv_files:
            m = re.search(r"(?:EP|E)\s*(\d+)|第(\d+)集", fp.name, re.IGNORECASE)
            if not m:
                print(f"   ⚠️ 跳过（无法识别集数）: {fp.relative_to(VIDEO_DIR)}")
                continue
            e_num = int(m.group(1) or m.group(2))
            if e_num < 1 or e_num > len(flat_titles):
                print(f"   ⚠️ 跳过（集数超出范围 [1-{len(flat_titles)}]）: {fp.relative_to(VIDEO_DIR)} → 第{e_num}集")
                continue
            title = flat_titles[e_num - 1]
            full = f"第{e_num}集 - {title}" if use_prefix else title
            pending.append((fp, full))
            print(f"   {fp.relative_to(VIDEO_DIR)} → {full}")
    else:
        print(f"📄 检测到 {len(season_map)} 个季: {sorted(season_map)}")

        season_titles: dict[int, list[str]] = {}
        for s in sorted(season_map):
            titles = paste_titles(f"请粘贴第 {s} 季的剧集列表文本")
            if not titles:
                sys.exit(1)
            season_titles[s] = titles

        print("\n📋 检测到的文件：")
        for fp in mkv_files:
            m = re.search(r"S(\d+)E(\d+)", fp.name, re.IGNORECASE)
            if not m:
                print(f"   ⚠️ 跳过（无法识别 SxxExx）: {fp.relative_to(VIDEO_DIR)}")
                continue
            s_num, e_num = int(m.group(1)), int(m.group(2))
            titles = season_titles.get(s_num)
            if not titles:
                print(f"   ⚠️ 跳过（无 S{s_num} 标题数据）: {fp.relative_to(VIDEO_DIR)}")
                continue
            if e_num < 1 or e_num > len(titles):
                print(f"   ⚠️ 跳过（集数超出范围 [1-{len(titles)}]）: {fp.relative_to(VIDEO_DIR)} → E{e_num}")
                continue
            title = titles[e_num - 1]
            full = f"第{e_num}集 - {title}" if use_prefix else title
            pending.append((fp, full))
            print(f"   {fp.relative_to(VIDEO_DIR)} → {full}")

    if not pending:
        print("\n❌ 没有可处理的文件")
    else:
        print()
        if confirm(f"确认设置 {len(pending)} 个文件的标题？(Y/N): "):
            _dry_run = False
            processed = 0
            for path, title in pending:
                cmd = [MKVPROREDIT, str(path), "--edit", "info", "--set", f"title={title}"]
                if run_command(cmd):
                    print(f"  ✅ {path.relative_to(VIDEO_DIR)}")
                    processed += 1
                else:
                    print(f"  ❌ 失败: {path.relative_to(VIDEO_DIR)}")
            print(f"\n🎉 标题设置完成: {processed}/{len(pending)} 成功")
        else:
            print("❌ 用户取消操作")

    print()
    input("按回车键退出...")


if __name__ == "__main__":
    main()
