import subprocess
from pathlib import Path

# ================== 配置区 ==================

PC_MUSIC_DIR = Path(r"D:\Files\Music")
PHONE_LIST_FILE = Path(r"D:\Downloads\Android\music.txt")

OUTPUT_ZIP = Path(r"D:\Downloads\Android\music_sync.zip")

SEVEN_ZIP = Path(r"7z.exe")
FOOBAR = Path(r"foobar2000.exe")

PHONE_EXTS = {".m4a", ".mp3"}

# ================== 解析手机已有 ==================

def load_phone_track_basenames(mtxt: Path) -> set[str]:
    names = set()
    with mtxt.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.endswith(":"):
                continue

            p = Path(line)
            if p.suffix.lower() in PHONE_EXTS:
                names.add(p.stem)

    return names

# ================== 找未同步 FLAC ==================

def find_unsynced_flacs() -> list[Path]:
    phone_names = load_phone_track_basenames(PHONE_LIST_FILE)
    flacs = []

    for f in PC_MUSIC_DIR.rglob("*.flac"):
        if f.stem not in phone_names:
            flacs.append(f)

    return flacs

# ================== 打开 foobar2000 ==================

def open_flacs_in_foobar(flacs: list[Path]):
    if not flacs:
        print("[INFO] 没有需要转码的 FLAC")
        return

    print(f"[INFO] 向 foobar2000 发送 {len(flacs)} 个 FLAC")

    cmd = [
        str(FOOBAR),
        "/add",
        "/immediate",
    ]
    cmd.extend(str(f) for f in flacs)

    subprocess.Popen(cmd)

# ================== ZIP 打包 ==================

def zip_music():
    phone_names = load_phone_track_basenames(PHONE_LIST_FILE)

    files_to_zip = []
    aac_files = []

    for f in PC_MUSIC_DIR.rglob("*"):
        if not f.is_file():
            continue

        ext = f.suffix.lower()
        if ext not in PHONE_EXTS:
            continue

        # 手机已有则跳过
        if f.stem in phone_names:
            continue

        files_to_zip.append(f)

        if ext == ".m4a":
            aac_files.append(f)

    if not files_to_zip:
        print("[INFO] 没有需要打包的新文件")
        return

    print(f"[INFO] 打包文件数: {len(files_to_zip)}")

    cmd = [
        str(SEVEN_ZIP),
        "a",
        "-tzip",
        str(OUTPUT_ZIP),
    ]

    for f in files_to_zip:
        cmd.append(str(f.relative_to(PC_MUSIC_DIR)))

    subprocess.run(cmd, cwd=PC_MUSIC_DIR, check=True)
    print(f"[OK] ZIP 已生成: {OUTPUT_ZIP}")

    # ================== 清理 AAC ==================

    print("[INFO] 清理临时 AAC...")
    for f in aac_files:
        try:
            f.unlink()
            print(f"[DEL] {f.relative_to(PC_MUSIC_DIR)}")
        except Exception as e:
            print(f"[WARN] 删除失败: {f} ({e})")

# ================== 主流程 ==================

if __name__ == "__main__":
    flacs = find_unsynced_flacs()
    open_flacs_in_foobar(flacs)

    input("\n请在 foobar2000 中完成 AAC 转码后，按任意键继续...")

    zip_music()

    input("\n流程完成，按任意键退出 ")
