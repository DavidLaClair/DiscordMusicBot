import discord

from media.media import Media


class Request:
    def __init__(self, vendor: str, media: Media, member: discord.Member, channel: discord.TextChannel):
        self.vendor: str = vendor
        self.media: Media = media
        self.member: discord.Member = member
        self.channel: discord.TextChannel = channel

    def get_info(self):
        """Get the info about the media inside the request."""
        self.media.get_info()
