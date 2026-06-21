import os
import shutil
from pathlib import Path

# ===== 配置 =====
ROOT = Path(r"D:\Files\Music")   # 要清理的根目录
AUDIO_EXTS = {
    ".flac", ".mp3", ".wav", ".m4a", ".aac", ".ogg", ".ape"
}
# =================


def has_audio_file(path: Path) -> bool:
    """
    判断目录及其所有子目录中是否存在音频文件
    """
    for root, _, files in os.walk(path):
        for name in files:
            if Path(name).suffix.lower() in AUDIO_EXTS:
                return True
    return False


def find_deletable_dirs(root: Path) -> list[Path]:
    """
    找出可以删除的目录（不含任何音乐文件）
    """
    deletable = []

    for current_root, _, _ in os.walk(root, topdown=False):
        p = Path(current_root)
        if not has_audio_file(p):
            deletable.append(p)

    return deletable


def main():
    print("🔍 扫描目录中，请稍候...\n")

    deletable_dirs = find_deletable_dirs(ROOT)

    if not deletable_dirs:
        print("🎉 没有发现可删除的目录")
        return

    print("⚠️ 以下目录 **不包含任何音乐文件**，将被递归删除：\n")

    for d in deletable_dirs:
        print(" -", d)

    print(f"\n📦 共 {len(deletable_dirs)} 个目录")

    confirm = input("\n❓ 是否删除以上目录？(y/n): ").strip().lower()
    if confirm != "y":
        print("\n❌ 已取消，未执行删除")
        return

    print("\n🗑 开始删除...\n")

    for d in deletable_dirs:
        try:
            shutil.rmtree(d)
            print(f"🗑 已删除: {d}")
        except Exception as e:
            print(f"⚠️ 删除失败: {d} ({e})")

    print("\n✅ 删除完成")


if __name__ == "__main__":
    main()
