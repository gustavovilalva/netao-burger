import os
import requests
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "")

# Hashtags padrão relacionadas a hamburgueria
DEFAULT_HASHTAGS = [
    "hamburgueria", "hamburguer", "burger", "smashburger",
    "artesanal", "lanche", "foodporn", "burgersofinstagram",
    "hamburguerartesanal", "burgerlovers"
]


@app.route("/")
def index():
    return render_template("index.html", hashtags=DEFAULT_HASHTAGS)


@app.route("/api/debug/instagram")
def debug_instagram():
    """Mostra resposta bruta da API do Instagram para debug."""
    hashtag = request.args.get("hashtag", "burger")
    if not RAPIDAPI_KEY:
        return jsonify({"error": "Sem API key"}), 400
    url = "https://instagram-scraper-stable-api.p.rapidapi.com/search_hashtag.php"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "instagram-scraper-stable-api.p.rapidapi.com"
    }
    try:
        resp = requests.get(url, headers=headers, params={"hashtag": hashtag}, timeout=15)
        return jsonify({"status": resp.status_code, "raw": resp.json()})
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/api/search")
def search():
    platform = request.args.get("platform", "tiktok")
    hashtag = request.args.get("hashtag", "hamburgueria").strip().lstrip("#")
    count = int(request.args.get("count", 20))

    if not RAPIDAPI_KEY:
        return jsonify({
            "error": "API key não configurada. Siga as instruções no README para obter sua chave gratuita.",
            "videos": []
        }), 400

    if platform == "tiktok":
        return jsonify(search_tiktok(hashtag, count))
    elif platform == "instagram":
        return jsonify(search_instagram(hashtag, count))
    elif platform == "both":
        tiktok = search_tiktok(hashtag, count // 2)
        instagram = search_instagram(hashtag, count // 2)

        all_videos = tiktok.get("videos", []) + instagram.get("videos", [])
        all_videos.sort(key=lambda x: x.get("likes", 0), reverse=True)

        errors = []
        if tiktok.get("error"):
            errors.append(f"TikTok: {tiktok['error']}")
        if instagram.get("error"):
            errors.append(f"Instagram: {instagram['error']}")

        return jsonify({
            "videos": all_videos,
            "total": len(all_videos),
            "errors": errors if errors else None
        })
    else:
        return jsonify({"error": "Plataforma inválida", "videos": []}), 400


def search_tiktok(hashtag: str, count: int = 20) -> dict:
    """Busca vídeos virais no TikTok por palavra-chave via RapidAPI."""
    url = "https://tiktok-scraper7.p.rapidapi.com/feed/search"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "tiktok-scraper7.p.rapidapi.com"
    }
    params = {
        "keywords": hashtag,
        "count": str(count),
        "cursor": "0",
        "region": "BR",
        "publish_time": "0",
        "sort_type": "0"
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        videos = []
        raw_videos = data.get("data", {}).get("videos", [])

        for item in raw_videos:
            author = item.get("author", {})

            # Stats: tenta objeto aninhado ou direto no item
            stats = item.get("statistics", {})
            likes    = stats.get("digg_count",    item.get("digg_count",    0))
            views    = stats.get("play_count",     item.get("play_count",    0))
            comments = stats.get("comment_count",  item.get("comment_count", 0))
            shares   = stats.get("share_count",    item.get("share_count",   0))

            # Thumbnail: tenta múltiplos caminhos
            video_info = item.get("video", {})
            cover = video_info.get("cover", {})
            if isinstance(cover, dict):
                url_list = cover.get("url_list", [])
                thumbnail = url_list[0] if url_list else ""
            elif isinstance(cover, str):
                thumbnail = cover
            else:
                thumbnail = ""
            if not thumbnail:
                thumbnail = item.get("cover", "")

            # Duração
            duration_raw = video_info.get("duration", item.get("duration", 0))
            duration = duration_raw // 1000 if duration_raw > 1000 else duration_raw

            videos.append({
                "platform": "TikTok",
                "platform_icon": "tiktok",
                "id": item.get("aweme_id", ""),
                "description": item.get("desc", "Sem descrição")[:200],
                "likes":    likes,
                "views":    views,
                "comments": comments,
                "shares":   shares,
                "thumbnail": thumbnail,
                "url": f"https://www.tiktok.com/@{author.get('unique_id', '')}/video/{item.get('aweme_id', '')}",
                "author": author.get("nickname", ""),
                "author_handle": f"@{author.get('unique_id', '')}",
                "duration": duration,
            })

        # Ordenar por curtidas
        videos.sort(key=lambda x: x["likes"], reverse=True)
        return {"videos": videos, "total": len(videos), "hashtag": hashtag}

    except requests.exceptions.HTTPError as e:
        if resp.status_code == 429:
            return {"videos": [], "error": "Limite de requisições atingido. Tente novamente amanhã."}
        return {"videos": [], "error": f"Erro HTTP {resp.status_code}: {str(e)}"}
    except Exception as e:
        return {"videos": [], "error": str(e)}


def search_instagram(hashtag: str, count: int = 20) -> dict:
    """Busca posts/reels do Instagram por hashtag via RapidAPI."""
    url = "https://instagram-scraper-stable-api.p.rapidapi.com/search_hashtag.php"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "instagram-scraper-stable-api.p.rapidapi.com"
    }
    params = {"hashtag": hashtag}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        videos = []
        items = data.get("data", {}).get("items", [])

        for item in items:
            # Apenas vídeos/reels (media_type 2 = vídeo)
            if item.get("media_type") not in [2, 8]:
                # Incluir também carrosséis que podem ter vídeo
                caption_obj = item.get("caption")
                caption = caption_obj.get("text", "") if caption_obj else ""
                # Pegar qualquer mídia para ter mais resultados
                like_count = item.get("like_count", 0)
                if like_count < 100:
                    continue

            caption_obj = item.get("caption")
            caption = caption_obj.get("text", "") if caption_obj else ""

            # Thumbnail
            thumbnail = ""
            img_versions = item.get("image_versions2", {})
            candidates = img_versions.get("candidates", [])
            if candidates:
                thumbnail = candidates[0].get("url", "")

            user = item.get("user", {})
            code = item.get("code", "")

            videos.append({
                "platform": "Instagram",
                "platform_icon": "instagram",
                "id": item.get("id", ""),
                "description": caption[:200] if caption else "Sem legenda",
                "likes": item.get("like_count", 0),
                "views": item.get("play_count", item.get("view_count", 0)),
                "comments": item.get("comment_count", 0),
                "shares": 0,
                "thumbnail": thumbnail,
                "url": f"https://www.instagram.com/p/{code}/",
                "author": user.get("full_name", user.get("username", "")),
                "author_handle": f"@{user.get('username', '')}",
                "duration": item.get("video_duration", 0),
            })

            if len(videos) >= count:
                break

        videos.sort(key=lambda x: x["likes"], reverse=True)
        return {"videos": videos, "total": len(videos), "hashtag": hashtag}

    except requests.exceptions.HTTPError as e:
        if resp.status_code == 429:
            return {"videos": [], "error": "Limite de requisições atingido. Tente novamente amanhã."}
        return {"videos": [], "error": f"Erro HTTP {resp.status_code}: {str(e)}"}
    except Exception as e:
        return {"videos": [], "error": str(e)}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n🍔 Burger Viral App rodando em: http://localhost:{port}\n")
    app.run(debug=True, host="0.0.0.0", port=port)
