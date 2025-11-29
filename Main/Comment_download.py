import os
import json
import time
import socket
import socks
from typing import List
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ==========================================
# SOCKS5 代理（可选）
# ==========================================
SOCKS_HOST = "127.0.0.1"
SOCKS_PORT = 7897

socks.set_default_proxy(socks.SOCKS5, SOCKS_HOST, SOCKS_PORT)
socket.socket = socks.socksocket

# ==========================================
# 目录配置
# ==========================================
BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / 'video_id'
OUTPUT_DIR = BASE_DIR / 'video_comment'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

KEY_FILE = BASE_DIR / "api_keys" / "api_keys.txt"

# ==========================================
# 加载所有 API Key + 自动轮换
# ==========================================
def load_api_keys():
    if not KEY_FILE.exists():
        raise FileNotFoundError("❌ 未找到 api_keys/api_keys.txt")
    with open(KEY_FILE, "r") as f:
        keys = [line.strip() for line in f if line.strip()]
    if not keys:
        raise ValueError("❌ api_keys.txt 内没有任何有效 key")
    print(f"🔑 Loaded {len(keys)} API keys.")
    return keys

API_KEYS = load_api_keys()
api_index = 0

def get_api_key():
    global api_index
    key = API_KEYS[api_index]
    api_index = (api_index + 1) % len(API_KEYS)
    return key

# ==========================================
# 构建 YouTube 客户端
# ==========================================
def build_service():
    key = get_api_key()
    print(f"🔄 Using API Key: {key[:12]}******")
    return build("youtube", "v3", developerKey=key, cache_discovery=False)

# ==========================================
# 读取视频 ID
# ==========================================
def read_video_ids() -> List[str]:
    ids = []
    for fname in os.listdir(INPUT_DIR):
        if fname.endswith(".txt"):
            with open(INPUT_DIR / fname, "r", encoding="utf-8") as f:
                for line in f:
                    vid = line.strip()
                    if vid and not (OUTPUT_DIR / f"{vid}.txt").exists():
                        ids.append(vid)
    return list(set(ids))

# ==========================================
# 保存评论
# ==========================================
def save_comments(video_id: str, comments: List[str]):
    out_path = OUTPUT_DIR / f"{video_id}.txt"
    if comments:
        with open(out_path, "w", encoding="utf-8") as f:
            for c in comments:
                f.write(c + "\n")
        print(f"💾 {video_id}: saved {len(comments)} comments")
    else:
        print(f"⚠️ {video_id}: No comments")

# ==========================================
# 抓取评论（单视频，多线程共享 API Key，API Key 失效等待）
# ==========================================
def fetch_comments(youtube, video_id: str) -> List[str]:
    comments = []
    page_token = None

    while True:
        try:
            req = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=100,
                pageToken=page_token,
                textFormat="plainText",
            )
            resp = req.execute()

            for item in resp.get("items", []):
                text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                text = text.replace("\n", " ").strip()
                if text:
                    comments.append(text)

            page_token = resp.get("nextPageToken")
            if not page_token:
                break

        except HttpError as he:
            try:
                err = json.loads(he.content.decode("utf-8"))
                code = err["error"]["code"]
                msg = err["error"]["message"]
            except:
                code = None
                msg = str(he)

            print(f"❌ {video_id}: HttpError {code} - {msg}")

            if code in (403, 429):
                print("⏱ API Key invalid or quota exceeded, waiting 60 seconds...")
                time.sleep(60)
                youtube = build_service()  # 重新构建客户端，使用新 Key
                continue

            return comments

        except Exception as e:
            print(f"⚠️ Unexpected error: {e}")
            return comments

    return comments

# ==========================================
# 单个视频处理
# ==========================================
def process_video(video_id: str):
    try:
        youtube = build_service()
        comments = fetch_comments(youtube, video_id)
        save_comments(video_id, comments)
    except Exception as e:
        print(f"🔥 {video_id}: Error {e}")

# ==========================================
# 主函数：多线程抓取
# ==========================================
def main():
    video_ids = read_video_ids()
    print(f"📌 Found {len(video_ids)} videos to fetch")
    if not video_ids:
        return

    max_workers = 3 # 可调线程数
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_video, vid): vid for vid in video_ids}
        for f in as_completed(futures):
            vid = futures[f]
            try:
                f.result()
            except Exception as e:
                print(f"🔥 {vid}: unexpected error {e}")

    print("🎉 Done!")

if __name__ == "__main__":
    main()
