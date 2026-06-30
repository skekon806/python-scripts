"""
小说爬虫 — 配置驱动简化版
用法:
  python novel_crawler.py <URL>
  python novel_crawler.py <URL> --update
  python novel_crawler.py --list
"""

import re, time, os, sys, json, glob
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "novels.json")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)


# ============================================================
# 工具函数
# ============================================================

def host_of(url):
    return urlparse(url).hostname or ""

def base_of(url):
    p = urlparse(url)
    return f"{p.scheme}://{p.hostname}"

def fetch(url, retries=3):
    for i in range(retries):
        try:
            r = SESSION.get(url, timeout=15)
            r.encoding = "utf-8"
            html = r.text
            # challenge 反爬
            if "验证" in html and "challenge" in html:
                m = re.search(r'token\s*=\s*"([^"]+)"', html)
                if m:
                    sep = "&" if "?" in url else "?"
                    r = SESSION.get(url + sep + "challenge=" + m.group(1), timeout=15)
                    r.encoding = "utf-8"
                    return r.text
            return html
        except Exception:
            if i == retries - 1:
                raise
            time.sleep(1)
    return ""

def soup_of(url):
    return BeautifulSoup(fetch(url), "html.parser")


# ============================================================
# 配置加载
# ============================================================

def load_configs():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def match_config(url):
    """按域名匹配配置"""
    configs = load_configs()
    host = host_of(url)
    for domain_key in configs:
        if domain_key in host:
            return domain_key, configs[domain_key]
    return None, None


# ============================================================
# 小说名提取
# ============================================================

def extract_name(config, base_url, soup=None):
    if soup is None:
        soup = soup_of(base_url)
    mode = config.get("name", "from:h1")

    if mode == "from:h1":
        el = soup.select_one("h1")
        if el and el.get_text(strip=True):
            return el.get_text(strip=True)

    if mode == "from:title" or mode == "from:h1":
        t = soup.select_one("title")
        if t:
            text = t.get_text(strip=True)
            for sep in ["_", "-", "—", "(", "（"]:
                if sep in text:
                    return text.split(sep)[0].strip()
            return text

    path = urlparse(base_url).path.rstrip("/")
    return path.split("/")[-1]


# ============================================================
# 分页解析 — 目录页 URL 列表
# ============================================================

def resolve_page_urls(config, base_url, soup=None):
    """从页面 <select> 下拉框解析所有分页 URL"""
    if soup is None:
        soup = soup_of(base_url)
    sel = config.get("page_from_select", "")
    select = soup.select_one(sel) if sel else None
    if not select:
        print(f"  Warning: selector '{sel}' not found, using single page")
        return [base_url.rstrip("/") + "/"]
    domain = base_of(base_url)
    seen = set()
    result = []
    for opt in select.select("option"):
        val = opt.get("value", "")
        if not val:
            continue
        url = val if val.startswith("http") else urljoin(domain, val)
        if url not in seen:
            seen.add(url)
            result.append(url)
    return result


# ============================================================
# 章节链接提取
# ============================================================

def collect_chapter_links(config, page_urls):
    """遍历所有目录页，提取 (url, title)"""
    list_sel = config.get("list_sel", "ul.section-list.fix")
    list_idx = config.get("list_idx", 0)
    link_sel = config.get("link_sel", "a")
    href_attr = config.get("href_attr", "href")
    domain = base_of(page_urls[0]) if page_urls else ""

    links = []
    for page_url in page_urls:
        try:
            soup = soup_of(page_url)
        except Exception as e:
            print(f"  Skip page: {page_url} ({e})")
            continue
        containers = soup.select(list_sel)
        if list_idx >= len(containers):
            continue
        for a in containers[list_idx].select(link_sel):
            href = a.get(href_attr, "")
            text = a.get_text(strip=True)
            if href:
                if not href.startswith("http"):
                    href = urljoin(domain, href)
                links.append((href, text))
    return links


# ============================================================
# 正文解析
# ============================================================

def _remove_selectors(soup, selectors):
    for sel in selectors:
        for el in soup.select(sel):
            el.decompose()


def parse_article(url, config, link_title=""):
    """解析单章正文，含多页合并"""
    body_sel = config.get("content_body", "div.content")
    next_text = config.get("next_page", "")
    max_pages = config.get("next_page_max", 10)
    clean = config.get("content_clean", {})

    soup = soup_of(url)
    title = link_title

    # 提取前：移除噪音元素
    _remove_selectors(soup, clean.get("remove_selectors", []))
    el = soup.select_one(body_sel)
    content = el.get_text("\n") if el else ""

    # 多页合并
    page_url = url
    for _ in range(max_pages - 1):
        a = soup.find("a", string=re.compile(re.escape(next_text))) if next_text else None
        if not a:
            break
        href = a.get("href", "")
        if not href or href.startswith("#"):
            break
        next_url = urljoin(page_url, href)
        if next_url == page_url:
            break
        page_url = next_url
        soup = soup_of(next_url)
        _remove_selectors(soup, clean.get("remove_selectors", []))
        el = soup.select_one(body_sel)
        if el:
            content += "\n" + el.get_text("\n")
        time.sleep(0.2)

    # 提取后：文本清洗
    lines = content.split("\n")
    if clean.get("remove_lines"):
        lines = [l for l in lines if not any(re.search(pat, l) for pat in clean["remove_lines"])]
    if clean.get("strip_empty"):
        lines = [l for l in lines if l.strip()]
    if clean.get("trim"):
        lines = [l.strip() for l in lines]
    content = "\n".join(lines).strip()

    return title, content


# ============================================================
# 文件输出
# ============================================================

def sanitize(s):
    return re.sub(r'[<>:"/\\|?*]', "", s).strip()[:80]

def out_dir(config, novel_name):
    d = config.get("out_dir", "{script_dir}/{name}")
    d = d.replace("{script_dir}", SCRIPT_DIR).replace("{name}", novel_name)
    os.makedirs(d, exist_ok=True)
    return d

def out_path(config, novel_name, index, title):
    pattern = config.get("out_file", "{index:04d}_{title}.txt")
    fname = pattern.format(index=index, title=sanitize(title))
    return os.path.join(out_dir(config, novel_name), fname)

def combine_path(config, novel_name):
    pattern = config.get("out_combine", "{name}.txt")
    fname = pattern.replace("{name}", novel_name)
    d = config.get("out_combine_dir", "")
    if d:
        d = d.replace("{script_dir}", SCRIPT_DIR).replace("{name}", novel_name)
        os.makedirs(d, exist_ok=True)
    else:
        d = out_dir(config, novel_name)
    return os.path.join(d, fname)

def chapter_exists(config, novel_name, index):
    d = out_dir(config, novel_name)
    p = os.path.join(d, f"{index:04d}_*.txt")
    return bool(glob.glob(p))


# ============================================================
# 下载 Worker
# ============================================================

def download_chapter(url, index, link_title, config, novel_name):
    if chapter_exists(config, novel_name, index):
        return None
    try:
        title, content = parse_article(url, config, link_title)
        path = out_path(config, novel_name, index, title)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return (index, title, path)
    except Exception as e:
        print(f"  Error [{index}]: {e}")
        return None


def combine_chapters(config, novel_name):
    d = out_dir(config, novel_name)
    main_name = combine_path(config, novel_name)
    files = sorted(
        glob.glob(os.path.join(d, "*.txt")),
        key=lambda x: int(os.path.basename(x).split("_")[0])
        if os.path.basename(x).split("_")[0].isdigit()
        else 0,
    )
    count = 0
    with open(main_name, "w", encoding="utf-8") as out:
        for f in files:
            base = os.path.basename(f)
            if base == os.path.basename(main_name):
                continue
            title = base.split("_", 1)[-1].rsplit(".", 1)[0]
            if not re.search(r"第\d{1,4}[章节]", title):
                continue
            with open(f, "r", encoding="utf-8") as fh:
                out.write(title + "\n" + fh.read().strip() + "\n\n")
            count += 1
    return [main_name] if count else []


# ============================================================
# 主流程
# ============================================================

def run(url, update=False):
    key, config = match_config(url)
    if config is None:
        print(f"Error: no config for {host_of(url)}")
        sys.exit(1)

    print(f"Config: {key}")

    # 0. 抓一次目录页，复用给书名提取和分页解析
    index_soup = soup_of(url)

    # 1. 小说名
    novel_name = extract_name(config, url, index_soup)
    print(f"Novel: {novel_name}")

    # 2. 目录页列表
    page_urls = resolve_page_urls(config, url, index_soup)
    print(f"Pages: {len(page_urls)}")

    # 3. 章节链接 (url, title)
    links = collect_chapter_links(config, page_urls)
    print(f"Chapters: {len(links)}")
    if not links:
        return

    # 4. 筛选待下载
    tail = config.get("tail", 30) if update else 0
    total = len(links)
    todo = []
    for i, (link_url, link_title) in enumerate(links, 1):
        exists = chapter_exists(config, novel_name, i)
        if update and i < (total - tail + 1) and exists:
            continue
        if not exists:
            todo.append((link_url, i, link_title))

    if not todo:
        print("All done.")
        return

    print(f"Downloading {len(todo)}/{total}...")
    done = 0
    n = len(todo)

    with ThreadPoolExecutor(max_workers=config.get("workers", 4)) as pool:
        fut_map = {pool.submit(download_chapter, *item, config, novel_name): item for item in todo}
        for fut in as_completed(fut_map):
            done += 1
            r = fut.result()
            if r:
                print(f"[{done}/{n}] {r[1]}")
            else:
                print(f"[{done}/{n}] (skipped)")

    # 5. 合并
    for path in combine_chapters(config, novel_name):
        print(f"Combined -> {path}")


def main():
    import argparse
    ap = argparse.ArgumentParser(description="小说爬虫")
    ap.add_argument("url", nargs="?", help="小说目录页 URL")
    ap.add_argument("--update", action="store_true", help="增量更新")
    ap.add_argument("--list", action="store_true", help="列出可用配置")
    args = ap.parse_args()

    if args.list:
        for k in load_configs():
            print(f"  {k}")
        return

    if not args.url:
        print("Usage: python novel_crawler.py <URL> [--update]")
        sys.exit(1)

    run(args.url, args.update)


if __name__ == "__main__":
    main()
