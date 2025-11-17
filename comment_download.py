import os
import json
import time
import traceback
from typing import List
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:33210"
os.environ["HTTP_PROXY"] = "http://127.0.0.1:33211"
# 配置
API_KEY = 'AIzaSyBX_Yz8CiSx-XQdPEEJYvBQQDxNH2buLXU'
INPUT_DIR = 'video_id'
OUTPUT_DIR = 'video_comment'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def build_service():
    return build('youtube', 'v3', developerKey=API_KEY)

def fetch_comments(youtube, video_id: str, max_per_page: int = 100, max_retries: int = 5, base_delay: float = 2.0) -> List[str]:
    comments: List[str] = []
    page_token = None
    page_index = 0
    while True:
        for attempt in range(max_retries):
            try:
                req = youtube.commentThreads().list(
                    part='snippet',
                    videoId=video_id,
                    maxResults=max_per_page,
                    pageToken=page_token,
                    textFormat='plainText'
                )
                resp = req.execute()
                items = resp.get('items', [])
                for it in items:
                    top_snippet = it['snippet']['topLevelComment']['snippet']
                    text = top_snippet.get('textDisplay', '').replace('\n', ' ').strip()
                    if text:
                        comments.append(text)
                page_token = resp.get('nextPageToken')
                page_index += 1
                break
            except HttpError as he:
                status = getattr(he, 'status_code', None)
                try:
                    detail = json.loads(he.content.decode('utf-8'))
                except Exception:
                    detail = {}
                code = detail.get('error', {}).get('code')
                msg = detail.get('error', {}).get('message')
                if code == 404:
                    print(f"{video_id}: not found (404)")
                elif code == 403:
                    print(f"{video_id}: 403 forbidden (comments disabled / quota) message={msg}")
                else:
                    print(f"{video_id}: HttpError code={code} message={msg}")
                return comments
            except Exception as e:
                print(f"{video_id}: attempt {attempt+1}/{max_retries} error: {repr(e)}")
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
                else:
                    print(f"{video_id}: give up after {max_retries} attempts")
                    return comments
        if not page_token:
            break
    return comments

def read_video_ids() -> List[str]:
    ids = []
    if not os.path.isdir(INPUT_DIR):
        print(f"Input dir {INPUT_DIR} missing.")
        return ids
    for fname in os.listdir(INPUT_DIR):
        if not fname.endswith('.txt'):
            continue
        path = os.path.join(INPUT_DIR, fname)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    v = line.strip()
                    if v:
                        ids.append(v)
        except Exception as e:
            print(f"Read error {path}: {e}")
    # 去重
    return list(set(ids))

def save_comments(video_id: str, comments: List[str]):
    out_path = os.path.join(OUTPUT_DIR, f"{video_id}.txt")
    if os.path.exists(out_path):
        print(f"{video_id}: file exists, skip")
        return
    if not comments:
        print(f"{video_id}: no comments, skip file creation")
        return
    with open(out_path, 'w', encoding='utf-8') as f:
        for c in comments:
            f.write(c + '\n')
    print(f"{video_id}: saved {len(comments)} comments")

def test_connection(youtube):
    try:
        resp = youtube.videos().list(part='id', id='dQw4w9WgXcQ').execute()
        if resp.get('items'):
            print("YouTube API OK")
        else:
            print("API reachable, test video not found")
    except Exception as e:
        print("Connection test failed:", repr(e))
        traceback.print_exc()

def main():
    youtube = build_service()
    test_connection(youtube)
    video_ids = read_video_ids()
    if not video_ids:
        print("No video IDs found.")
        return
    for vid in video_ids:
        save_comments(vid, fetch_comments(youtube, vid))

if __name__ == '__main__':
    main()