from utilities import youtube


class YoutubePlaylist:
    def __init__(self, url: str):
        self.url: str = url
        self.info: dict[str, any] = youtube.get_info(url)

    def get_length(self):
        """Get the length of a youtube playlist."""
        return len(self.info["entries"])

    def get_name(self):
        """Get the name of a playlist."""
        return self.info["title"]
