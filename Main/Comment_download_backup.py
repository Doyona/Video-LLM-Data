import json
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from yt_dlp import YoutubeDL
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

# ==========================================
# 目录配置
# ==========================================
BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / 'video_id'
OUTPUT_DIR = BASE_DIR / 'video_comment'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ==========================================
# 读取视频 ID
# ==========================================
def read_video_ids():
    ids = []
    for fname in os.listdir(INPUT_DIR):
        if fname.endswith(".txt"):
            with open(INPUT_DIR / fname, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        ids.append(line.strip())
    return list(set(ids))

# ==========================================
# 保存评论
# ==========================================
def save_comments(video_id, comments):
    out_path = OUTPUT_DIR / f"{video_id}.txt"
    if os.path.exists(out_path):
        print(f"{video_id}: file exists, skip")
        return
    if not comments:
        print(f"{video_id}: no comments, skip")
        return
    with open(out_path, "w", encoding="utf-8") as f:
        for c in comments:
            f.write(c + "\n")
    print(f"{video_id}: saved {len(comments)} comments")

# ==========================================
# yt-dlp 抓取评论（快速抓顶层评论）
# ==========================================
def fetch_comments_ytdlp(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        "skip_download": True,
        "getcomments": True,
        "writeinfojson": True,
        "extract_flat": True,
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        info_path = f"{video_id}.info.json"
        if not os.path.exists(info_path):
            print(f"{video_id}: info.json not found")
            return []

        with open(info_path, "r", encoding="utf-8") as f:
            info = json.load(f)

        comments = info.get("comments", [])
        comments_text = [c.get("text", "").replace("\n", " ").strip() for c in comments if c.get("text")]
        os.remove(info_path)
        return comments_text
    except Exception as e:
        print(f"{video_id}: yt-dlp error: {e}")
        return []

# ==========================================
# selenium 抓取评论（保证抓到全部，包括嵌套回复）
# ==========================================
def fetch_comments_selenium(video_id, max_scrolls=50):
    url = f"https://www.youtube.com/watch?v={video_id}"

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)

    try:
        driver.get(url)
        time.sleep(3)

        # 滚动评论区
        last_height = driver.execute_script("return document.documentElement.scrollHeight")
        scrolls = 0
        while scrolls < max_scrolls:
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.documentElement.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            scrolls += 1

        # 获取评论文本
        comment_elements = driver.find_elements(By.CSS_SELECTOR, "#content #body #content-text")
        comments = [c.text.replace("\n", " ").strip() for c in comment_elements if c.text.strip()]
        return comments
    except Exception as e:
        print(f"{video_id}: selenium error: {e}")
        return []
    finally:
        driver.quit()

# ==========================================
# 单视频处理
# ==========================================
def process_video(video_id):
    # 先用 yt-dlp 快速抓取
    comments = fetch_comments_ytdlp(video_id)
    # 如果抓到数量少，可以用 selenium 补全
    if len(comments) < 500:  # 可根据视频评论量调整阈值
        print(f"{video_id}: using selenium to get more comments")
        comments_selenium = fetch_comments_selenium(video_id)
        # 合并去重
        comments = list(set(comments + comments_selenium))
    save_comments(video_id, comments)

# ==========================================
# 主函数，多线程抓取
# ==========================================
def main():
    video_ids = read_video_ids()
    if not video_ids:
        print("No video IDs found.")
        return

    print(f"Found {len(video_ids)} videos to fetch")

    max_workers = 3  # 可调线程数
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_video, vid): vid for vid in video_ids}
        for future in as_completed(futures):
            vid = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"{vid}: unexpected error {e}")

    print("Done!")

if __name__ == "__main__":
    main()
