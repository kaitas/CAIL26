#!/usr/bin/env python3
"""
NobelEngine サンプル画像ジェネレータ（GPT-Image-2）
=====================================================
留学生が後で自分のキャラに差し替える前提の「プレースホルダ」サンプルを生成する。

手順:
  1) こむぎ / あおい / ゆず の立ち絵を images.generate で生成（オリジナルキャラ）
  2) その3枚を参照として images.edit でカバー / エンディング / タイトルを生成
     （キャラの見た目を一貫させるため）

出力: assets/samples/*.png
実行: OPENAI_API_KEY を設定して `python3 scripts/gen_samples.py`
"""
import base64, io, json, os, sys, urllib.request, urllib.error
from PIL import Image

API_KEY = os.environ.get("OPENAI_API_KEY")
if not API_KEY:
    print("ERROR: OPENAI_API_KEY 未設定", file=sys.stderr); sys.exit(1)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "samples")
os.makedirs(OUT, exist_ok=True)

NEG = "\n\nテキストや文字・タイトル・ロゴ・透かしは画像に絶対に含めないでください。"

# おおよそのコスト（¥145/$換算）
COST = {("1024x1024","low"):3,("1024x1024","medium"):6,("1024x1024","high"):12,
        ("1024x1536","medium"):10,("1024x1536","high"):23,
        ("1536x1024","medium"):10,("1536x1024","high"):23}

def to_rgb_png_bytes(path):
    img = Image.open(path).convert("RGBA")
    bg = Image.new("RGB", img.size, (255,255,255))
    bg.paste(img, mask=img.split()[3])
    buf = io.BytesIO(); bg.save(buf, "PNG"); return buf.getvalue()

# 横長(landscape)で出す画像。それ以外は縦長ポートレート扱い
LAND = {"ending-comic-fair", "title-key-visual"}

def save_b64(b64, name):
    """生成画像を web 最適化(縮小+JPEG)して assets/samples/ に保存。
    HTML側は .jpg を参照するため、ここでは常に .jpg で書き出す（スマホ表示で軽量）。"""
    stem = os.path.splitext(name)[0]
    img = Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")
    w, h = img.size
    target_w = 1000 if stem in LAND else 600
    if w > target_w:
        img = img.resize((target_w, round(h * target_w / w)), Image.LANCZOS)
    p = os.path.join(OUT, stem + ".jpg")
    img.save(p, "JPEG", quality=82, optimize=True, progressive=True)
    kb = os.path.getsize(p) // 1024
    print(f"  saved {stem}.jpg ({kb} KB, {img.size[0]}x{img.size[1]})", flush=True)
    return p

def generate(name, prompt, size, quality="high"):
    print(f"[generate] {name} ({size} {quality}, ≈¥{COST.get((size,quality),'?')})", flush=True)
    body = json.dumps({"model":"gpt-image-2","prompt":prompt+NEG,
                       "size":size,"quality":quality,"n":1}).encode()
    req = urllib.request.Request("https://api.openai.com/v1/images/generations", data=body)
    req.add_header("Authorization", f"Bearer {API_KEY}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=240) as r:
        data = json.loads(r.read())
    return save_b64(data["data"][0]["b64_json"], name)

def edit(name, prompt, ref_paths, size, quality="high"):
    print(f"[edit] {name} ({size} {quality}, refs={len(ref_paths)}, ≈¥{COST.get((size,quality),'?')})", flush=True)
    boundary = "----NobelEngineBound"
    parts = []
    def field(n, v):
        return (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{n}\"\r\n\r\n{v}\r\n").encode()
    body = b""
    body += field("model","gpt-image-2")
    body += field("prompt", prompt+NEG)
    body += field("size", size)
    body += field("quality", quality)
    for i, rp in enumerate(ref_paths):
        rb = to_rgb_png_bytes(rp)
        body += f"--{boundary}\r\n".encode()
        body += (f"Content-Disposition: form-data; name=\"image[]\"; filename=\"ref{i}.png\"\r\n"
                 "Content-Type: image/png\r\n\r\n").encode() + rb + b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    req = urllib.request.Request("https://api.openai.com/v1/images/edits", data=body)
    req.add_header("Authorization", f"Bearer {API_KEY}")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(req, timeout=300) as r:
        data = json.loads(r.read())
    return save_b64(data["data"][0]["b64_json"], name)

# ---- キャラ立ち絵（オリジナル）----------------------------------------
KOMUGI = ("A cheerful Japanese middle-school girl named Komugi, the manga artist of the trio. "
  "Short fluffy wheat-blonde hair with a small ahoge, bright amber eyes, wearing a cozy cream-and-pink "
  "hoodie with a tiny bread/wheat motif, holding a drawing pen and a small sketchbook, energetic friendly smile. "
  "Anime illustration style, soft warm pastel colors, clean line art, doujinshi cover quality. "
  "Full upper-body portrait, centered, simple plain solid white background.")
AOI = ("A calm thoughtful Japanese middle-school girl named Aoi, the scenario writer and accountant of the trio. "
  "Long straight dark-blue hair, deep blue eyes, thin-framed glasses, neat navy cardigan over a white blouse, "
  "holding a manuscript notebook and a mechanical pencil, quiet gentle expression. "
  "Anime illustration style, soft cool blue palette, clean line art, doujinshi quality. "
  "Full upper-body portrait, centered, simple plain solid white background.")
YUZU = ("A supportive older-sister-type Japanese girl named Yuzu, the experienced printing advisor of the trio. "
  "Medium wavy citrus orange and yellow-green hair, warm hazel eyes, a mustard-yellow apron over a casual shirt, "
  "holding a stack of printed booklets, knowing reassuring smile, slightly mature look. "
  "Anime illustration style, warm citrus yellow-green palette, clean line art, doujinshi quality. "
  "Full upper-body portrait, centered, simple plain solid white background.")

k = generate("char-komugi.png", KOMUGI, "1024x1536", "medium")
a = generate("char-aoi.png",    AOI,    "1024x1536", "medium")
y = generate("char-yuzu.png",   YUZU,   "1024x1536", "medium")
refs = [k, a, y]

# ---- カバー / エンディング / タイトル（3キャラ参照で一貫性確保）--------
COVER = ("A cute magical-girl doujinshi front-cover illustration, theme 'Magical Bakery'. "
  "The three girls from the reference images (wheat-blonde artist, blue-haired writer with glasses, "
  "citrus-haired advisor) as magical pastry bakers in a warm sunny bakery full of glowing magical bread "
  "and pastries, sparkles and soft light, dynamic cheerful composition. "
  "Anime illustration style, vivid warm colors, high detail, portrait orientation. "
  "Keep each character's appearance consistent with the references.")
ENDING = ("A heartwarming ending illustration: the three girls from the reference images standing proudly behind "
  "a doujinshi sales table at a crowded indie comic fair, holding up their finished printed book together with "
  "joyful tearful smiles, neat stacks of their booklet on the table, warm golden afternoon light, celebratory mood. "
  "Anime illustration style, warm emotional colors, high detail, landscape orientation. "
  "Keep characters consistent with the references.")
TITLE = ("A cozy game title key-visual about making a first doujinshi: a creative desk with manga manuscript pages "
  "showing registration crop marks, screen-tone sheets, ink pens and a drawing tablet, and the three girls from the "
  "reference images gathered around excitedly planning their first book, soft warm studio lighting, wholesome inviting mood. "
  "Anime illustration style, warm inviting colors, landscape orientation, leave clean empty space in the upper area. "
  "Keep characters consistent with the references.")

edit("cover-magical-bakery.png", COVER, refs, "1024x1536", "high")
edit("ending-comic-fair.png",    ENDING, refs, "1536x1024", "high")
edit("title-key-visual.png",     TITLE,  refs, "1536x1024", "high")

print("ALL DONE. outputs in assets/samples/", flush=True)
