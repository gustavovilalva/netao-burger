import os
import requests
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

app = Flask(__name__)

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")

DEFAULT_HASHTAGS = [
    "hamburgueria", "hamburguer", "burger", "smashburger",
    "lanche", "foodporn", "hamburguerartesanal", "burgerlovers",
    "burgerbrasil", "comida"
]


@app.route("/")
def index():
    return render_template("index.html", hashtags=DEFAULT_HASHTAGS)


@app.route("/api/search")
def search():
    query    = request.args.get("hashtag", "hamburgueria").strip().lstrip("#")
    sort_by  = request.args.get("sort", "viewCount")   # viewCount | date | relevance
    count    = min(int(request.args.get("count", 20)), 50)

    if not YOUTUBE_API_KEY:
        return jsonify({
            "error": "Chave do YouTube não configurada. Adicione YOUTUBE_API_KEY no Render.",
            "videos": []
        }), 400

    return jsonify(search_youtube(query, sort_by, count))


def search_youtube(query: str, sort_by: str = "viewCount", count: int = 20) -> dict:
    """Busca vídeos/Shorts no YouTube por palavra-chave."""

    # 1️⃣ Busca os vídeos
    search_url = "https://www.googleapis.com/youtube/v3/search"
    search_params = {
        "key": YOUTUBE_API_KEY,
        "q": query,
        "part": "snippet",
        "type": "video",
        "videoDuration": "short",       # Shorts e vídeos curtos (< 4 min)
        "order": sort_by,
        "maxResults": count,
        "relevanceLanguage": "pt",
        "regionCode": "BR",
        "publishedAfter": "2025-01-01T00:00:00Z",  # Apenas 2025/2026
    }

    try:
        resp = requests.get(search_url, params=search_params, timeout=10)
        resp.raise_for_status()
        search_data = resp.json()
    except requests.exceptions.HTTPError as e:
        if resp.status_code == 403:
            return {"videos": [], "error": "Chave do YouTube inválida ou cota esgotada."}
        return {"videos": [], "error": f"Erro HTTP {resp.status_code}: {str(e)}"}
    except Exception as e:
        return {"videos": [], "error": str(e)}

    items = search_data.get("items", [])
    if not items:
        return {"videos": [], "total": 0, "hashtag": query}

    # 2️⃣ Busca estatísticas (likes, views) dos vídeos encontrados
    video_ids = [i["id"]["videoId"] for i in items if i.get("id", {}).get("videoId")]
    stats_map = {}
    if video_ids:
        stats_url = "https://www.googleapis.com/youtube/v3/videos"
        stats_params = {
            "key": YOUTUBE_API_KEY,
            "id": ",".join(video_ids),
            "part": "statistics,contentDetails",
        }
        try:
            stats_resp = requests.get(stats_url, params=stats_params, timeout=10)
            for v in stats_resp.json().get("items", []):
                stats_map[v["id"]] = {
                    "views":    int(v.get("statistics", {}).get("viewCount",    0)),
                    "likes":    int(v.get("statistics", {}).get("likeCount",   0)),
                    "comments": int(v.get("statistics", {}).get("commentCount", 0)),
                }
        except Exception:
            pass

    # 3️⃣ Monta a lista de vídeos
    videos = []
    for item in items:
        vid_id   = item.get("id", {}).get("videoId", "")
        snippet  = item.get("snippet", {})
        stats    = stats_map.get(vid_id, {})

        # Thumbnail — maior disponível
        thumbs   = snippet.get("thumbnails", {})
        thumb    = (thumbs.get("maxres") or thumbs.get("high") or thumbs.get("medium") or {}).get("url", "")

        # Data de publicação
        pub_raw  = snippet.get("publishedAt", "")
        try:
            pub_date = datetime.fromisoformat(pub_raw.replace("Z", "+00:00")).strftime("%d/%m/%Y")
        except Exception:
            pub_date = ""

        # URL — Shorts se for curto, senão watch normal
        video_url = f"https://www.youtube.com/shorts/{vid_id}"

        videos.append({
            "platform":     "YouTube",
            "id":           vid_id,
            "title":        snippet.get("title", ""),
            "description":  snippet.get("description", "")[:200],
            "author":       snippet.get("channelTitle", ""),
            "author_url":   f"https://www.youtube.com/channel/{snippet.get('channelId', '')}",
            "thumbnail":    thumb,
            "url":          video_url,
            "views":        stats.get("views",    0),
            "likes":        stats.get("likes",    0),
            "comments":     stats.get("comments", 0),
            "pub_date":     pub_date,
        })

    # Ordenar localmente pelo critério escolhido
    if sort_by == "viewCount":
        videos.sort(key=lambda x: x["views"], reverse=True)
    elif sort_by == "date":
        pass  # já vem ordenado pela API
    else:
        pass

    return {"videos": videos, "total": len(videos), "hashtag": query}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n🍔 Burger Viral rodando em: http://localhost:{port}\n")
    app.run(debug=True, host="0.0.0.0", port=port)
