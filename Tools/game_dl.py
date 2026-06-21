#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import mmap
import subprocess
import sys
from pathlib import Path

def fast_json_search(json_path, target_keys):
    """使用 mmap 快速搜索 JSON 文件中的特定键"""
    results = {}
    remaining = set(target_keys)
    
    if not remaining:
        return results
    
    patterns = {}
    for depot_id in target_keys:
        pattern_str = rf'"{depot_id}"\s*:\s*"([a-fA-F0-9]+)"'
        patterns[depot_id] = re.compile(pattern_str.encode('utf-8'))
    
    with open(json_path, 'rb') as f:
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            for depot_id in list(remaining):
                match = patterns[depot_id].search(mm)
                if match:
                    results[depot_id] = match.group(1).decode('utf-8')
                    remaining.remove(depot_id)
                    print(f"  Found key for depot {depot_id} in depotkeys.json")
                    if not remaining:
                        break
    
    return results

def extract_keys_from_lua(depot_dir, needed_depots):
    """从 Lua 文件中提取密钥"""
    results = {}
    remaining = set(needed_depots)
    
    # 匹配格式: addappid(1145361, 1, "key")
    lua_pattern = re.compile(r'addappid\((\d+)(?:,\s*\d+,\s*"([a-fA-F0-9]+)")?\)')
    
    for lua_file in depot_dir.glob("*.lua"):
        print(f"  Checking {lua_file.name}...")
        with open(lua_file, 'r', encoding='utf-8') as f:
            content = f.read()
            for match in lua_pattern.finditer(content):
                depot_id = match.group(1)
                key = match.group(2)
                if depot_id in remaining and key:
                    results[depot_id] = key
                    remaining.remove(depot_id)
                    print(f"  Found key for depot {depot_id} in {lua_file.name}")
                    if not remaining:
                        break
        if not remaining:
            break
    
    return results

def main():
    print("=" * 60)
    print("  Depot Config.vdf Generator & Downloader")
    print("=" * 60)
    print()
    
    depot_dir = Path("./depot")
    output_dir = Path("./Game")
    output_dir.mkdir(exist_ok=True)
    
    # 1. 收集需要的 depot_id（从 manifest 文件）
    print("Step 1: Scanning manifest files...")
    needed_depots = set()
    for mf in depot_dir.glob("*.manifest"):
        parts = mf.stem.split('_')
        if len(parts) >= 1:
            needed_depots.add(parts[0])
    
    if not needed_depots:
        print("[Error] No manifest files found")
        sys.exit(1)
    
    print(f"Found {len(needed_depots)} depots: {sorted(needed_depots, key=int)}")
    
    # 2. 从 depotkeys.json 搜索密钥
    print("\nStep 2: Searching depotkeys.json...")
    json_path = depot_dir / "depotkeys.json"
    depot_keys = {}
    
    if json_path.exists():
        depot_keys = fast_json_search(json_path, needed_depots)
        print(f"Found {len(depot_keys)} keys in depotkeys.json")
    else:
        print("[Warning] depotkeys.json not found")
    
    # 3. 从 Lua 文件补充缺失的密钥
    missing_depots = needed_depots - set(depot_keys.keys())
    if missing_depots:
        print(f"\nStep 3: Searching Lua files for {len(missing_depots)} missing depots...")
        lua_keys = extract_keys_from_lua(depot_dir, missing_depots)
        depot_keys.update(lua_keys)
        print(f"Found {len(lua_keys)} keys in Lua files")
    
    # 4. 生成 config.vdf
    print("\nStep 4: Generating config.vdf...")
    vdf_path = depot_dir / "config.vdf"
    
    with open(vdf_path, 'w', encoding='utf-8') as f:
        f.write('"depots"\n{\n')
        for depot_id in sorted(needed_depots, key=int):
            f.write(f'\t"{depot_id}"\n\t{{\n')
            if depot_id in depot_keys:
                f.write(f'\t\t"DecryptionKey"\t\t"{depot_keys[depot_id]}"\n')
            f.write('\t}\n')
        f.write('}\n')
    
    print(f"[Success] Generated {vdf_path}")
    
    # 统计信息
    with_key = len(depot_keys)
    without_key = len(needed_depots) - with_key
    print(f"Stats: {with_key} depots with keys, {without_key} without keys")
    
    # 5. 启动下载器
    print("\nStep 5: Starting downloader...")
    cmd = [
        "ddv20.exe",
        "-lu", "China",
        "--use-http",
        "-o", str(output_dir),
        "app",
        "-p", str(depot_dir)
    ]
    
    print(f"Command: {' '.join(cmd)}")
    
    subprocess.Popen(
        cmd,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
    )
    
    print("\n[Success] Downloader started in new window")
    print("Tip: Check the new console window for download progress")

if __name__ == "__main__":
    main()