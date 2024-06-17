def is_search(url: str) -> bool:
    """Checks to see if a given URL is a search."""
    if "youtube" in url:
        return False
    else:
        return True


def is_playlist(url: str) -> bool:
    """Checks to see if a given URL is a playlist."""
    # YouTube Playlists
    if "/playlist?list" in url:
       return True
    elif "&list=" in url:
        return True
    return False
