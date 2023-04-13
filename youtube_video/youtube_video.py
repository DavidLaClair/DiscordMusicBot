import discord


class YoutubeVideo:
    def __init__(self, url, yt_dlp):
        self.url = url
        self.yt_dlp = yt_dlp
        self.info = None

        self.get_info()

    def get_info(self):
        self.info = self.yt_dlp.extract_info(self.url, download=False)

    def get_audio_source(self):
        audio_url = self.info["url"]

        audio = discord.FFmpegPCMAudio(
            source=audio_url,
            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            options="-filter:a loudnorm"
        )
        return audio
