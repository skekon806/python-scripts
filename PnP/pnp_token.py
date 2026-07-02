import os
import math
from PIL import Image, ImageDraw

INPUT_FOLDER = "no card"
OUTPUT_FILE = "tokens_circle.pdf"

# A4 横向
A4_W = 3508
A4_H = 2480

# token
TOKEN_SIZE = 295

ROWS = 7
COLS = 10
PER_PAGE = ROWS * COLS


def scan_tokens():
    files = []
    for f in os.listdir(INPUT_FOLDER):
        if f.lower().endswith((".png",".jpg",".jpeg")):
            files.append(os.path.join(INPUT_FOLDER,f))
    return sorted(files)


# ========= 圆形裁切 =========
def make_circle_token(path):

    with Image.open(path).convert("RGBA") as img:

        img_ratio = img.width / img.height

        if img_ratio > 1:
            new_w = TOKEN_SIZE
            new_h = int(new_w / img_ratio)
        else:
            new_h = TOKEN_SIZE
            new_w = int(new_h * img_ratio)

        img = img.resize((new_w,new_h),Image.LANCZOS)

        canvas = Image.new("RGBA",(TOKEN_SIZE,TOKEN_SIZE),(255,255,255,0))

        px = (TOKEN_SIZE-new_w)//2
        py = (TOKEN_SIZE-new_h)//2

        canvas.paste(img,(px,py),img)

        # 创建圆形 mask
        mask = Image.new("L",(TOKEN_SIZE,TOKEN_SIZE),0)
        draw = ImageDraw.Draw(mask)

        draw.ellipse(
            (0,0,TOKEN_SIZE,TOKEN_SIZE),
            fill=255
        )

        circle = Image.new("RGBA",(TOKEN_SIZE,TOKEN_SIZE),(255,255,255,255))
        circle.paste(canvas,(0,0),mask)

        return circle.convert("RGB")


def create_page(files):

    page = Image.new("RGB",(A4_W,A4_H),"white")
    draw = ImageDraw.Draw(page)

    total_w = COLS * TOKEN_SIZE
    total_h = ROWS * TOKEN_SIZE

    offset_x = (A4_W-total_w)//2
    offset_y = (A4_H-total_h)//2

    for i,f in enumerate(files):

        token = make_circle_token(f)

        r = i // COLS
        c = i % COLS

        x = offset_x + c*TOKEN_SIZE
        y = offset_y + r*TOKEN_SIZE

        page.paste(token,(x,y))

        # 画裁切辅助圆
        draw.ellipse(
            (
                x,
                y,
                x+TOKEN_SIZE,
                y+TOKEN_SIZE
            ),
            outline=(120,120,120),
            width=2
        )
    page=page.rotate(270, expand=True)
    return page


def main():

    files = scan_tokens()

    if not files:
        print("未找到 token 图片")
        return

    pages = []

    total_pages = math.ceil(len(files)/PER_PAGE)

    for p in range(total_pages):

        start = p*PER_PAGE
        end = start+PER_PAGE

        batch = files[start:end]

        page = create_page(batch)

        pages.append(page)

        print(f"生成页面 {p+1}/{total_pages}")

    pages[0].save(
        OUTPUT_FILE,
        save_all=True,
        append_images=pages[1:],
        resolution=300
    )

    print("完成 →",OUTPUT_FILE)


if __name__=="__main__":
    main()