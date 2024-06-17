import discord

from media.media import Media
from utilities import youtube


class YoutubeVideo(Media):
    def __init__(self, url: str, title: str=None, info=None, is_video: bool=False):
        super().__init__("youtube", url, title, is_video)
        self.info = info
        
        if not info:
            self.get_info()

    def check_info(self):
        """Get the info about the current video."""
        if not self.info:
            self.get_info()

    def get_info(self):
        """Get the JSON info about a youtube video."""
        self.info = youtube.get_info(self.url)
        self.title = self.info["title"]

    def get_audio_source(self):
        """Set the FFmpeg info for audio only on the current video."""
        self.check_info()

        audio_url:str = self.info["url"]

        audio = discord.FFmpegPCMAudio(
            source=audio_url,
            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            options="-filter:a loudnorm"
        )
        return audio
