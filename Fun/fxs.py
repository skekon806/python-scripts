import os
import shutil
import subprocess
import json

SPINE_CONVERTER = r"D:\Work\Darkest Dungeon\SpineConverter.exe"

# 定义要跳过的关键词列表（仅用于skel文件）
SKIP_KEYWORDS = ["afflicted", "camp", "combat", "defend", "heroic", "idle", "investigate", "walk"]

def ensure_bak(dirpath):
    bak_dir = os.path.join(dirpath, "bak")
    os.makedirs(bak_dir, exist_ok=True)
    return bak_dir

def find_matching_png(atlas_path):
    """在目录中查找与target_anim匹配的PNG文件"""
    atlas_dir = os.path.dirname(atlas_path)
    atlas_basename = os.path.splitext(os.path.basename(atlas_path))[0]
    target_anim = atlas_basename.split(".")[-1]
    
    # 在目录中查找所有PNG文件
    png_files = [f for f in os.listdir(atlas_dir) if f.endswith('.png')]
    
    # 查找包含target_anim的PNG文件
    matching_pngs = [f for f in png_files if target_anim in f]
    
    if matching_pngs:
        # 返回第一个匹配的PNG文件名
        return matching_pngs[0]
    
    # 如果没找到，返回基于target_anim的默认名称
    return target_anim + ".png"

def fix_atlas_png(atlas_path):
    """修复atlas文件中的PNG引用"""
    correct_png_name = find_matching_png(atlas_path)
    
    with open(atlas_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    png_lines = [i for i, line in enumerate(lines) if line.strip().endswith(".png")]
    needs_fix = any(lines[i].strip() != correct_png_name for i in png_lines)

    if needs_fix:
        
        for i in png_lines:
            lines[i] = correct_png_name + "\n"
        
        with open(atlas_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"修复 atlas: {atlas_path} → {correct_png_name}")
    else:
        print(f"atlas 已正确: {atlas_path}")

def fix_json_animation(json_path, atlas_path):
    atlas_basename = os.path.splitext(os.path.basename(atlas_path))[0]
    target_anim = atlas_basename.split(".")[-1]

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "animations" in data and isinstance(data["animations"], dict):
        anim_keys = list(data["animations"].keys())
        if anim_keys:
            first_key = anim_keys[0]
            if first_key != target_anim:
                data["animations"][target_anim] = data["animations"].pop(first_key)
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"修复 json: {json_path} 动画名 {first_key} → {target_anim}")
            else:
                print(f"json 动画已正确: {json_path}")

def should_skip_file(filename):
    """检查文件名是否包含需要跳过的关键词"""
    return any(keyword in filename for keyword in SKIP_KEYWORDS)

def process_files(root_dir="."):
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".atlas"):
                atlas_path = os.path.join(dirpath, filename)
                
                # 正常处理所有 atlas 文件
                fix_atlas_png(atlas_path)

                # 对应 skel 文件
                skel_path = atlas_path.replace(".atlas", ".skel")
                if os.path.exists(skel_path):
                    # 检查是否需要跳过 skel 文件
                    if should_skip_file(filename):
                        print(f"跳过 skel 文件: {os.path.basename(skel_path)} (包含跳过关键词)")
                        continue
                    
                    # 备份 skel
                    bak_dir = ensure_bak(dirpath)
                    shutil.copy2(skel_path, os.path.join(bak_dir, os.path.basename(skel_path)))
                    print(f"已备份 skel: {skel_path}")
                    subprocess.run([SPINE_CONVERTER, skel_path])

                    # 对应 json 文件
                    json_path = atlas_path.replace(".atlas", ".json")
                    if os.path.exists(json_path):
                        fix_json_animation(json_path, atlas_path)
                        subprocess.run([SPINE_CONVERTER, json_path])
                        os.remove(json_path)
                        print(f"已删除 JSON 文件: {json_path}")

if __name__ == "__main__":
    process_files(".")