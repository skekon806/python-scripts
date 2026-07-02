from PIL import Image
import sys
import os

def upscale_tiled_image(input_path, output_path, tile_size=16, scale=2.0, resample=Image.BILINEAR):
    img = Image.open(input_path).convert('RGBA')
    width, height = img.size

    crop_h = (height // tile_size) * tile_size
    if crop_h < height:
        img = img.crop((0, 0, width, crop_h))
        width, height = img.size
        print(f"  底部多余像素已裁掉，尺寸变为 {width}x{height}")

    cols = width // tile_size
    rows = height // tile_size

    new_tile_size = int(tile_size * scale)
    if new_tile_size != tile_size * scale:
        print(f"警告：放大后图块尺寸 {tile_size}*{scale} = {tile_size*scale} 不是整数，将截断为 {new_tile_size}")

    new_width = cols * new_tile_size
    new_height = rows * new_tile_size

    output_img = Image.new("RGBA", (new_width, new_height), (0, 0, 0, 0))

    for row in range(rows):
        for col in range(cols):
            left = col * tile_size
            top = row * tile_size
            box = (left, top, left + tile_size, top + tile_size)
            tile = img.crop(box)

            enlarged_tile = tile.resize((new_tile_size, new_tile_size), resample=resample)

            output_img.paste(enlarged_tile, (col * new_tile_size, row * new_tile_size), mask=enlarged_tile.split()[3])

    output_img.save(output_path)
    print(f"  处理完成！输出尺寸: {new_width}x{new_height}")
    print(f"  保存至: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("=" * 50)
        print("  NetHack Tileset 放大工具")
        print("=" * 50)
        print(f"  用法: python {os.path.basename(sys.argv[0])} <输入文件> [放大倍数]")
        print()
        print("  参数:")
        print("    输入文件      tileset 图片路径（支持 .png / .bmp）")
        print("    放大倍数      可选，默认 2.0（手动输入时直接回车也生效）")
        print()
        print("  示例:")
        print(f"    python {os.path.basename(sys.argv[0])} 129.png")
        print(f"    python {os.path.basename(sys.argv[0])} 129.png 2.0")
        print(f"    python {os.path.basename(sys.argv[0])} 129.bmp 3.0")
        print()
        print("  输出:")
        print("    自动生成到输入文件同目录，文件名格式: {原名}_{放大后图块尺寸}.bmp")
        print("    例如 129.png + 2.0x  →  129_32.bmp")
        print("    例如 129.png + 3.0x  →  129_48.bmp")
        print()
        print("  说明:")
        print("    适用于 NetHack 5.0 tileset（40列×58行，16×16 图块）")
        print("    自动裁掉底部多余像素，逐块放大后保存为 BMP")
        print("=" * 50)
        sys.exit(1)

    input_file = sys.argv[1]

    if not os.path.exists(input_file):
        print(f"错误：输入文件 '{input_file}' 不存在！")
        sys.exit(1)

    scale = float(sys.argv[2]) if len(sys.argv) >= 3 else float(input(f"请输入放大倍数（默认 2.0）: ") or "2.0")

    new_tile_size = int(16 * scale)
    base, _ = os.path.splitext(input_file)
    output_file = f"{base}_{new_tile_size}.bmp"

    try:
        upscale_tiled_image(
            input_path=input_file,
            output_path=output_file,
            tile_size=16,
            scale=scale,
            resample=Image.BILINEAR
        )
    except Exception as e:
        print(f"处理出错: {e}")
        sys.exit(1)