import os, shutil
import fitz
import numpy as np
from PIL import Image

TEMP_DIR = "temp"
CARD_DIR = "cards"

def split_vertical(img, threshold=245, min_gap=30):
    gray = np.array(img.convert("L"))
    mask = gray < threshold
    col_sum = mask.sum(axis=0)
    splits = []
    start = None
    for i, v in enumerate(col_sum):
        if v > 0 and start is None:
            start = i
        if v == 0 and start is not None and i - start > min_gap:
            splits.append((start, i))
            start = None
    if start is not None:
        splits.append((start, len(col_sum)))
    return [img.crop((s, 0, e, img.height)) for s, e in splits]

def split_content_blocks(img, threshold=245, min_height=100):
    gray = np.array(img.convert("L"))
    mask = gray < threshold
    coords = np.argwhere(mask)
    if coords.size == 0:
        return [img]
    y0, x0 = coords.min(axis=0)
    y1, x1 = coords.max(axis=0)
    cropped = img.crop((x0, y0, x1, y1))
    row_sum = (np.array(cropped.convert("L")) < threshold).sum(axis=1)
    splits = []
    start = None
    for i, v in enumerate(row_sum):
        if v > 0 and start is None:
            start = i
        if v == 0 and start is not None:
            splits.append((start, i))
            start = None
    if start is not None:
        splits.append((start, len(row_sum)))
    return [cropped.crop((0, s, cropped.width, e)) for s, e in splits if e - s >= min_height]

def convert_pdf():
    pdfs = [f for f in os.listdir(".") if f.lower().endswith(".pdf")]
    if not pdfs:
        return []
    os.makedirs(TEMP_DIR, exist_ok=True)
    images = []
    for pdf in pdfs:
        print("转换 PDF:", pdf)
        doc = fitz.open(pdf)
        base = os.path.splitext(pdf)[0]
        for i in range(len(doc)):
            pix = doc.load_page(i).get_pixmap(dpi=600)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            path = f"{TEMP_DIR}/{base}_page{i+1}.png"
            img.save(path)
            images.append(path)
            print("生成:", path)
    return images

def process_temp():
    outputs = []
    for f in os.listdir(TEMP_DIR):
        if not f.lower().endswith((".png", ".jpg", ".jpeg")):
            continue
        path = os.path.join(TEMP_DIR, f)
        print("拆分页面:", path)
        img = Image.open(path)
        blocks = []
        for vb in split_vertical(img):
            blocks.extend(split_content_blocks(vb))
        base = os.path.splitext(f)[0]
        for i, block in enumerate(blocks):
            name = f"{base}_block{i+1}.png"
            block.save(name)
            outputs.append(name)
            print("输出:", name)
    return outputs

def split_grid(image_files):
    os.makedirs(CARD_DIR, exist_ok=True)
    for file in image_files:
        print()
        print("=" * 40)
        print("处理图片:", file)
        img = Image.open(file)
        width, height = img.size
        print("尺寸:", width, "x", height)
        while True:
            try:
                rows = int(input("行数: "))
                cols = int(input("列数: "))
                if rows > 0 and cols > 0:
                    break
            except ValueError:
                pass
            print("请输入有效整数")
        card_w = width // cols
        card_h = height // rows
        print("单卡尺寸:", card_w, "x", card_h)
        base = os.path.splitext(os.path.basename(file))[0]
        count = 1
        for r in range(rows):
            for c in range(cols):
                crop = img.crop((c * card_w, r * card_h, (c+1) * card_w, (r+1) * card_h))
                crop.save(os.path.join(CARD_DIR, f"{base}_{count:03d}.png"))
                count += 1
        print("生成", count - 1, "张")

def get_images():
    return [f for f in os.listdir(".") if f.lower().endswith((".png", ".jpg", ".jpeg"))]

def main():
    print("==== PDF 检测 ====")
    convert_pdf()
    if os.path.exists(TEMP_DIR):
        print("\n==== 拆内容块 ====")
        process_temp()
    input("\n请手动删除不要的图片，完成后按回车继续...")
    print("==== 扫描图片 ====")
    images = get_images()
    if not images:
        print("没有可处理图片")
        return
    print("检测到图片:")
    for f in images:
        print(" -", f)
    print("\n==== 卡牌切割 ====")
    split_grid(images)
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
        print("删除 temp/")
    print("\n全部完成")
    print("输出目录:", CARD_DIR)
    input("回车退出...")

if __name__ == "__main__":
    main()
