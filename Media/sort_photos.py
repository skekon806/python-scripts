import os
import exifread
from pathlib import Path
import re

# === 配置 ===
PHOTO_DIR = Path(r"D:\Files\Pictures\Camera")  # 照片所在目录（也是整理目标目录）
# 如果你想让脚本自动使用当前工作目录，可改为：
# PHOTO_DIR = Path.cwd()

photo_exts = {'.jpg', '.jpeg', '.JPG', '.JPEG'}

def get_exif_datetime(file_path):
    try:
        with open(file_path, 'rb') as f:
            tags = exifread.process_file(f, stop_tag='EXIF DateTimeOriginal', details=False)
        dt = tags.get('EXIF DateTimeOriginal') or tags.get('EXIF ModifyDate')
        return str(dt).strip() if dt else None
    except Exception as e:
        print(f"⚠️ EXIF读取失败 {file_path.name}: {e}")
        return None

def standardize_filename(datetime_str):
    if not re.fullmatch(r'\d{4}:\d{2}:\d{2} \d{2}:\d{2}:\d{2}', datetime_str):
        return None
    clean = datetime_str.replace(':', '')
    return f"IMG_{clean[:8]}_{clean[9:15]}"

def main():
    if not PHOTO_DIR.exists():
        raise FileNotFoundError(f"目录不存在: {PHOTO_DIR}")

    # 获取所有照片文件（只处理顶层文件，避免处理已归类的子目录中的文件）
    files = [f for f in PHOTO_DIR.iterdir() 
             if f.is_file() and f.suffix in photo_exts]

    if not files:
        print("📁 当前目录无照片文件。")
        return

    print(f"🔍 找到 {len(files)} 张照片，开始整理...\n")

    for file_path in files:
        print(f"处理: {file_path.name}")
        exif_dt = get_exif_datetime(file_path)

        if not exif_dt:
            print(f"❌ 跳过 {file_path.name}：无有效 EXIF 日期\n")
            continue

        new_base = standardize_filename(exif_dt)
        if not new_base:
            print(f"❌ 跳过 {file_path.name}：日期格式无效\n")
            continue

        # 提取年月
        year = exif_dt[0:4]
        month = exif_dt[5:7]
        month_folder = f"{int(month)}月"

        # 目标路径（在当前目录下建年/月子目录）
        target_dir = PHOTO_DIR / year / month_folder
        target_dir.mkdir(parents=True, exist_ok=True)

        new_name = new_base + file_path.suffix.lower()
        target_path = target_dir / new_name

        # 避免重名
        counter = 1
        orig_target = target_path
        while target_path.exists():
            stem = orig_target.stem
            suffix = orig_target.suffix
            target_path = target_dir / f"{stem}_{counter}{suffix}"
            counter += 1

        # 移动文件（原地整理）
        try:
            file_path.rename(target_path)
            print(f"✅ 归档至: {target_path.relative_to(PHOTO_DIR)}\n")
        except Exception as e:
            print(f"❌ 移动失败 {file_path.name}: {e}\n")

    print("🎉 整理完成！")

if __name__ == "__main__":
    main()