import os
import re
import glob


def merge_all_novels():
    # 获取当前目录（上级目录）
    current_dir = os.getcwd()

    # 遍历所有子目录
    for root, dirs, files in os.walk(current_dir):
        # 跳过当前目录，只处理子目录
        if root == current_dir:
            continue

        # 检查目录中是否有txt文件
        txt_files = glob.glob(os.path.join(root, "*.txt"))
        if not txt_files:
            continue

        # 获取目录名作为书名（带书名号，仅用于输出文件名）
        dir_name = os.path.basename(root)
        book_name = f"《{dir_name}》"
        output_file = os.path.join(current_dir, f"{book_name}.txt")

        print(f"处理目录: {dir_name}")
        print(f"找到 {len(txt_files)} 个txt文件")

        # 按文件名前的数字排序
        def extract_number(filename):
            basename = os.path.basename(filename)
            match = re.match(r"(\d+)", basename)
            return int(match.group(1)) if match else 99999

        txt_files.sort(key=extract_number)

        with open(output_file, "w", encoding="utf-8") as outfile:
            for i, filename in enumerate(txt_files):
                # 直接从文件名提取章节名（去掉前面的数字和空格）
                basename = os.path.basename(filename)
                chapter_name = re.sub(r"^\d+\s*", "", basename)  # 去掉前面的数字和空格
                chapter_name = re.sub(r"\.txt$", "", chapter_name)  # 去掉.txt后缀

                print(f"  正在处理: {basename} -> {chapter_name}")

                # 写入章节标题
                outfile.write(f"{chapter_name}\n\n")

                # 写入文件内容
                try:
                    with open(filename, "r", encoding="utf-8") as infile:
                        content = infile.read().strip()
                        outfile.write(content)
                        outfile.write("\n\n")  # 章节间两个空行
                except Exception as e:
                    print(f"  读取文件出错: {filename} - {e}")

        print(f"合并完成: {book_name}.txt\n")


if __name__ == "__main__":
    print("开始遍历子目录合并小说文件...\n")
    merge_all_novels()
    print("所有目录处理完成！")
