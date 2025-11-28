import os
import csv
import time
import re
from typing import Dict, List
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# 可选代理（如不需要可删）
os.environ.setdefault("HTTPS_PROXY", "http://127.0.0.1:33210")
os.environ.setdefault("HTTP_PROXY", "http://127.0.0.1:33211")

API_KEY = 'AIzaSyBX_Yz8CiSx-XQdPEEJYvBQQDxNH2buLXU'
SOURCE_CSV = 'video_comment_top80_percent_overlap.csv'  # 输入原表
OUT_CSV = 'video_comment_top80_percent_overlap_enriched.csv'  # 输出增强表
REGION_CODE = 'US'  # 获取分类名使用

BATCH_SIZE = 50
RETRY = 3
SLEEP = 1.2
# 新增：频道批量大小（可与视频相同）
CHANNEL_BATCH_SIZE = 50

DUR_RE = re.compile(r'PT'  # 开头
                     r'(?:(\d+)H)?'
                     r'(?:(\d+)M)?'
                     r'(?:(\d+)S)?')

def parse_duration(iso_dur: str) -> int:
    if not iso_dur:
        return 0
    m = DUR_RE.match(iso_dur)
    if not m:
        return 0
    h, mnt, s = m.groups()
    h = int(h) if h else 0
    mnt = int(mnt) if mnt else 0
    s = int(s) if s else 0
    return h*3600 + mnt*60 + s

def build_service():
    return build('youtube', 'v3', developerKey=API_KEY)

def read_video_ids(csv_path: str) -> List[str]:
    ids = []
    with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
        r = csv.DictReader(f)
        for row in r:
            vid = row.get('video_id', '').strip()
            if vid:
                ids.append(vid)
    return list(dict.fromkeys(ids))  # 去重保持顺序

def fetch_categories(service, region: str) -> Dict[str, str]:
    mapping = {}
    try:
        req = service.videoCategories().list(part='snippet', regionCode=region)
        resp = req.execute()
        for it in resp.get('items', []):
            cid = it.get('id')
            title = it.get('snippet', {}).get('title', '')
            if cid:
                mapping[cid] = title
    except Exception as e:
        print('获取分类失败:', repr(e))
    return mapping

def fetch_videos_batch(service, ids: List[str]) -> Dict[str, Dict]:
    result = {}
    for attempt in range(RETRY):
        try:
            req = service.videos().list(part='snippet,contentDetails,statistics,topicDetails', id=','.join(ids))
            resp = req.execute()
            for it in resp.get('items', []):
                vid = it.get('id')
                snippet = it.get('snippet', {})
                stats = it.get('statistics', {})
                cdet = it.get('contentDetails', {})
                topic = it.get('topicDetails', {})
                result[vid] = {
                    'title': snippet.get('title', ''),
                    'tags': ','.join(snippet.get('tags', [])[:50]),
                    'publishedAt': snippet.get('publishedAt', ''),
                    'categoryId': snippet.get('categoryId', ''),
                    'durationISO': cdet.get('duration', ''),
                    'durationSeconds': parse_duration(cdet.get('duration', '')),
                    'viewCount': int(stats.get('viewCount', 0)) if stats.get('viewCount') else 0,
                    'likeCount': int(stats.get('likeCount', 0)) if stats.get('likeCount') else 0,
                    'commentCount': int(stats.get('commentCount', 0)) if stats.get('commentCount') else 0,
                    'topicCategories': '|'.join([u.rsplit('/', 1)[-1] for u in topic.get('topicCategories', [])]),
                    # 新增语言相关字段
                    'defaultLanguage': snippet.get('defaultLanguage', ''),
                    'defaultAudioLanguage': snippet.get('defaultAudioLanguage', ''),
                    'channelId': snippet.get('channelId', '')
                }
            return result
        except HttpError as he:
            print(f"HttpError batch {attempt+1}: {repr(he)}")
            time.sleep(SLEEP * (attempt+1))
        except Exception as e:
            print(f"Error batch {attempt+1}: {repr(e)}")
            time.sleep(SLEEP * (attempt+1))
    return result

def enrich():
    if not os.path.isfile(SOURCE_CSV):
        print('源文件不存在')
        return
    service = build_service()
    video_ids = read_video_ids(SOURCE_CSV)
    print(f'读取到 {len(video_ids)} 个 video_id')
    categories = fetch_categories(service, REGION_CODE)

    meta: Dict[str, Dict] = {}
    for i in range(0, len(video_ids), BATCH_SIZE):
        batch = video_ids[i:i+BATCH_SIZE]
        print(f'获取元数据 {i+1}-{i+len(batch)}')
        batch_meta = fetch_videos_batch(service, batch)
        meta.update(batch_meta)
        time.sleep(0.8)

    # 频道国家信息获取
    channel_ids = [m.get('channelId') for m in meta.values() if m.get('channelId')]
    channel_ids = list(dict.fromkeys(channel_ids))
    channel_country_map: Dict[str, str] = {}
    if channel_ids:
        print(f'获取频道信息，共 {len(channel_ids)} 个频道')
        for i in range(0, len(channel_ids), CHANNEL_BATCH_SIZE):
            ch_batch = channel_ids[i:i+CHANNEL_BATCH_SIZE]
            try:
                req = service.channels().list(part='snippet', id=','.join(ch_batch))
                resp = req.execute()
                for it in resp.get('items', []):
                    cid = it.get('id')
                    c_snippet = it.get('snippet', {})
                    country = c_snippet.get('country', '')
                    if cid:
                        channel_country_map[cid] = country
            except Exception as e:
                print('频道信息获取失败:', repr(e))
            time.sleep(0.5)

    with open(SOURCE_CSV, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        new_fields = ['duration_seconds','view_count','category_id','category_title','topic_categories','default_language','default_audio_language','channel_id','channel_country']
        out_fields = fieldnames + [c for c in new_fields if c not in fieldnames]

        with open(OUT_CSV, 'w', newline='', encoding='utf-8') as out_f:
            w = csv.DictWriter(out_f, fieldnames=out_fields)
            w.writeheader()
            for row in reader:
                vid = row.get('video_id','')
                m = meta.get(vid, {})
                row['duration_seconds'] = m.get('durationSeconds', '')
                row['view_count'] = m.get('viewCount', '')
                cid = m.get('categoryId','') if m else ''
                row['category_id'] = cid
                row['category_title'] = categories.get(cid, '')
                row['topic_categories'] = m.get('topicCategories','')
                # 新增：语言与频道地域
                row['default_language'] = m.get('defaultLanguage','')
                row['default_audio_language'] = m.get('defaultAudioLanguage','')
                row['channel_id'] = m.get('channelId','')
                row['channel_country'] = channel_country_map.get(m.get('channelId',''), '')
                w.writerow(row)
    print(f'完成 → {OUT_CSV}')

if __name__ == '__main__':
    enrich()
