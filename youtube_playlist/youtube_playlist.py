class YoutubePlaylist:
    def __init__(self, url, yt_dlp):
        self.url = url
        self.yt_dlp = yt_dlp
        self.info = None

        self.get_info()

    def get_info(self):
        self.info = self.yt_dlp.extract_info(self.url, download=False)

    def get_length(self):
        return len(self.info["entries"])

    def get_name(self):
        return self.info["title"]
