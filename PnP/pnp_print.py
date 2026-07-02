import os, re, math, sys, tempfile
from PIL import Image, ImageDraw, ImageFilter
import fitz

INPUT_FOLDER = "cards"
ROWS, COLS = 3, 3
CARDS_PER_PAGE = ROWS * COLS
BLEED_MARGIN = 41
A4_SIZE = {"v": (2480, 3508), "h": (3508, 2480)}
SIZES = {"bridge": (673, 1039), "poker": (744, 1039)}

def ask_bool(question, default=False):
    while True:
        val = input(f"{question} (y/n) [默认{'y' if default else 'n'}]: ").strip().lower()
        if val == "":
            return default
        if val in ("y","yes"):
            return True
        if val in ("n","no"):
            return False
        print("请输入 y 或 n")

def progress(current, total, prefix="进度"):
    if total == 0:
        return
    bar = "█" * int(30 * current / total) + "-" * (30 - int(30 * current / total))
    sys.stdout.write(f"\r{prefix}: [{bar}] {current}/{total} {current/total*100:.1f}%")
    sys.stdout.flush()
    if current == total:
        sys.stdout.write("\n")

def scan_cards():
    if not os.path.exists(INPUT_FOLDER):
        print(f"错误：找不到文件夹 '{INPUT_FOLDER}'")
        return []
    ex = {"card back", "card backs", "backs"}
    files = []
    for root, dirs, fs in os.walk(INPUT_FOLDER):
        dirs[:] = [d for d in dirs if d.lower() not in ex]
        if any(k in root.lower() for k in ex):
            continue
        for f in fs:
            if f.lower().endswith((".png",".jpg",".jpeg")):
                fp = os.path.join(root, f)
                if any(k in fp.lower() for k in ex):
                    continue
                files.append(fp)
    return sorted(files)

def load_card_backs():
    folder = os.path.join(INPUT_FOLDER, "Card back")
    if not os.path.exists(folder):
        return {}
    m = {}
    for f in os.listdir(folder):
        if f.lower().endswith((".png",".jpg",".jpeg")):
            m[os.path.splitext(f)[0].lower()] = os.path.join(folder, f)
    return m

def parse_filename(path):
    try:
        rel = os.path.relpath(path, INPUT_FOLDER)
    except ValueError:
        rel = os.path.basename(path)
    d = os.path.dirname(rel)
    name = os.path.splitext(os.path.basename(rel))[0]
    m = re.match(r"^(.+?)_(front|back)_(\d+)\s*$", name)
    if not m:
        return None
    grp = f"{d.replace(os.sep, '_')}_{m.group(1)}" if d else m.group(1)
    return {"group": grp, "side": m.group(2), "index": int(m.group(3))}

def prefix_match(path):
    m = re.match(r"^[a-z]+", os.path.splitext(os.path.basename(path).lower())[0])
    return m.group() if m else None

def choose_size(ratio):
    return "bridge" if abs(ratio - 673/1039) < abs(ratio - 744/1039) else "poker"

def classify(img_w, img_h, force_type=None):
    orient = "vertical" if img_h >= img_w else "horizontal"
    size = force_type if force_type else choose_size(img_w / img_h)
    return orient, size

def process_card(img, card_w, card_h, black_bg, bleed):
    r = img.width / img.height
    cr = card_w / card_h
    if r > cr:
        nw, nh = card_w, int(card_w / r)
    else:
        nh, nw = card_h, int(card_h * r)
    if nw <= 0 or nh <= 0:
        return Image.new("RGB", (card_w, card_h), "black")
    img = img.resize((nw, nh), Image.LANCZOS)
    img = img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=150, threshold=3))
    card = Image.new("RGBA", (card_w, card_h), "black" if black_bg else "white")
    card.paste(img, ((card_w - nw)//2, (card_h - nh)//2))
    if bleed:
        bw, bh = card_w + BLEED_MARGIN*2, card_h + BLEED_MARGIN*2
        bg = Image.new("RGB", (bw, bh), "white" if black_bg else "black")
        bg.paste(card, (BLEED_MARGIN, BLEED_MARGIN), card)
        return bg
    return card.convert("RGB")

def make_page(files, size_type, orient, black_bg, bleed, mirror=False):
    bw, bh = SIZES[size_type]
    cw, ch = (bh, bw) if orient == "h" else (bw, bh)
    box_w = cw + BLEED_MARGIN*2 if bleed else cw
    box_h = ch + BLEED_MARGIN*2 if bleed else ch
    aw, ah = A4_SIZE[orient]
    page = Image.new("RGB", (aw, ah), "white")
    draw = ImageDraw.Draw(page)
    ox = (aw - COLS * box_w)//2
    oy = (ah - ROWS * box_h)//2
    for i, fp in enumerate(files):
        try:
            card = process_card(Image.open(fp).convert("RGB"), cw, ch, black_bg, bleed)
            col = (COLS - 1 - (i % COLS)) if mirror else (i % COLS)
            x = ox + col * box_w
            y = oy + (i // COLS) * box_h
            page.paste(card, (x, y))
        except Exception as e:
            print(f"\n处理文件出错 {fp}: {e}")
    if not bleed:
        grey = (120, 120, 120)
        for c in range(COLS + 1):
            draw.line((ox + c * box_w, 0, ox + c * box_w, ah), fill=grey, width=2)
        for r in range(ROWS + 1):
            draw.line((0, oy + r * box_h, aw, oy + r * box_h), fill=grey, width=2)
    if orient == "h":
        page = page.rotate(270, expand=True)
    return page

def save_pdf(pages, path):
    if not pages:
        return
    try:
        pdf = fitz.open()
        for img in pages:
            tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
            img.convert("RGB").save(tmp, format="JPEG", quality=85)
            tmp.close()
            p = pdf.new_page(width=img.width, height=img.height)
            p.insert_image(p.rect, filename=tmp.name)
            os.unlink(tmp.name)
        pdf.save(path, garbage=4, deflate=True, deflate_images=True)
        pdf.close()
        size = os.path.getsize(path)
        print(f"\n生成完成 → {path} ({size/1024:.0f}KB)")
    except Exception as e:
        print(f"\n保存 PDF 失败: {e}")

def build_paired(data, name, orient, black_bg, bleed, mirror):
    pages = []
    total = sum(len(v) for v in data.values())
    if not total:
        return
    done = 0
    for sz, pairs in data.items():
        if not pairs:
            continue
        for pi in range(math.ceil(len(pairs) / CARDS_PER_PAGE)):
            batch = pairs[pi * CARDS_PER_PAGE : (pi+1) * CARDS_PER_PAGE]
            pages.append(make_page([p[0] for p in batch], sz, orient, black_bg, bleed))
            done += len(batch)
            progress(done, total * 2, f"生成 {name}")
            pages.append(make_page([p[1] for p in batch], sz, orient, black_bg, bleed, mirror=mirror))
            done += len(batch)
            progress(done, total * 2, f"生成 {name}")
    save_pdf(pages, name)

def build_normal(data, name, orient, black_bg, bleed):
    pages = []
    total = sum(len(v) for v in data.values())
    if not total:
        return
    done = 0
    for sz, flist in data.items():
        if not flist:
            continue
        for pi in range(math.ceil(len(flist) / CARDS_PER_PAGE)):
            batch = flist[pi * CARDS_PER_PAGE : (pi+1) * CARDS_PER_PAGE]
            pages.append(make_page(batch, sz, orient, black_bg, bleed))
            done += len(batch)
            progress(done, total, f"生成 {name}")
    save_pdf(pages, name)

def sort_and_pair(files, back_map, force_type):
    unmatched = {"vertical": {"poker": [], "bridge": []}, "horizontal": {"poker": [], "bridge": []}}
    matched = {"vertical": {"poker": [], "bridge": []}, "horizontal": {"poker": [], "bridge": []}}
    store = {}
    remaining = []
    n = len(files)
    print("正在分析并配对卡牌...")
    for i, f in enumerate(files):
        progress(i+1, n, "扫描文件名")
        parsed = parse_filename(f)
        if parsed:
            try:
                img = Image.open(f)
                orient, size = classify(img.width, img.height, force_type)
                key = (orient, size, parsed["group"], parsed["index"])
                store.setdefault(key, {"front": None, "back": None})[parsed["side"]] = f
            except:
                remaining.append(f)
        else:
            remaining.append(f)
    for (orient, size, _, _), v in store.items():
        if v["front"] and v["back"]:
            matched[orient][size].append((v["front"], v["back"]))
        else:
            for side in ("front", "back"):
                if v[side]:
                    unmatched[orient][size].append(v[side])
    if remaining:
        print(f"\n发现 {len(remaining)} 个非标准命名文件，尝试匹配 Card back 文件夹...")
        for f in remaining:
            pf = prefix_match(f)
            try:
                img = Image.open(f)
                orient, size = classify(img.width, img.height, force_type)
                if pf and pf in back_map:
                    matched[orient][size].append((f, back_map[pf]))
                else:
                    unmatched[orient][size].append(f)
            except:
                unmatched[orient][size].append(f)
    for orient in ("vertical", "horizontal"):
        for size in ("poker", "bridge"):
            matched[orient][size].sort(key=lambda x: (0, parse_filename(x[0])["group"], parse_filename(x[0])["index"]) if parse_filename(x[0]) else (1, os.path.basename(x[0]), 0))
            unmatched[orient][size].sort(key=lambda x: (0, parse_filename(x)["group"], parse_filename(x)["index"]) if parse_filename(x) else (1, os.path.basename(x), 0))
    return unmatched, matched

def main():
    black_bg = ask_bool("是否使用黑底？", False)
    bleed = ask_bool("是否启用出血？", False)
    force = ask_bool("是否强制卡牌尺寸？", False)
    mirror = ask_bool("是否翻转背面页 (用于双面打印对齐)？", False)

    force_type = None
    if force:
        while True:
            t = input("选择尺寸 (poker / bridge) [默认poker]: ").strip().lower()
            if t == "":
                force_type = "poker"
                break
            if t in ("poker","bridge"):
                force_type = t
                break
            print("请输入 poker 或 bridge")

    print("正在扫描文件...")
    files = scan_cards()
    if not files:
        print("未找到任何图片文件。")
        return

    back_map = load_card_backs()
    if not back_map:
        print("提示：未在 'cards/Card back' 文件夹中找到牌背图片。")
    else:
        print(f"发现 {len(back_map)} 种旧式牌背样式。")
    if mirror:
        print(">> 已启用背面翻转模式 (适用于双面打印短边翻转)")

    unmatched, matched = sort_and_pair(files, back_map, force_type)

    tu = sum(len(unmatched[o][s]) for o in ("vertical","horizontal") for s in ("poker","bridge"))
    tm = sum(len(matched[o][s]) for o in ("vertical","horizontal") for s in ("poker","bridge"))
    print(f"\n统计结果:\n无牌背/单面卡牌数: {tu}\n已配对卡牌数: {tm}")

    if any(unmatched["vertical"].values()):
        print("\n[任务] 生成无牌背竖版 PDF")
        build_normal(unmatched["vertical"], "no_back_vertical.pdf", "v", black_bg, bleed)
    if any(unmatched["horizontal"].values()):
        print("\n[任务] 生成无牌背横版 PDF")
        build_normal(unmatched["horizontal"], "no_back_horizontal.pdf", "h", black_bg, bleed)
    if any(matched["vertical"].values()):
        print(f"\n[任务] 生成有牌背竖版 PDF{' (背面已翻转)' if mirror else ''}")
        build_paired(matched["vertical"], "paired_vertical.pdf", "v", black_bg, bleed, mirror)
    if any(matched["horizontal"].values()):
        print(f"\n[任务] 生成有牌背横版 PDF{' (背面已翻转)' if mirror else ''}")
        build_paired(matched["horizontal"], "paired_horizontal.pdf", "h", black_bg, bleed, mirror)

    print("\n全部完成！")
    if mirror:
        print("\n提示：打印请选择【双面打印】->【短边翻转】(Short Edge Binding)。")

if __name__ == "__main__":
    try:
        main()
        input("\n完成后按回车继续...")
    except KeyboardInterrupt:
        print("\n\n用户中断操作。")
    except Exception as e:
        import traceback
        print(f"\n发生未知错误: {e}")
        traceback.print_exc()
