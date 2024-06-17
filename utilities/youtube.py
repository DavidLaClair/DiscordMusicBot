import yt_dlp

ydl_opts_audio_only = {
    "clean_infojson": True,
    "cachedir": False,
    "default_search": "ytsearch",
    "format": "bestaudio/best",
    "postprocessors": [{
        "key": "FFmpegExtractAudio"
    }],
    "extract_flat": "in_playlist",
    "subtitleslangs": ["-all"]
}


def get_info(url: str):
    with yt_dlp.YoutubeDL(ydl_opts_audio_only) as ydla:
        info = ydla.extract_info(url, download=False)
        json_info: dict[str, any] = ydla.sanitize_info(info)

    return json_info
