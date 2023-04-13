import discord
from player.player import Player


class Guild:
    def __init__(self, guild, client):
        # Core Guild
        self.guild = guild
        self.client = client
        self.voice_channel = None

        # Core Music
        self.audio_player = None

    # Core functions
    def is_connected(self):
        if not self.voice_channel:
            return False

        if not self.audio_player:
            return False

        return self.voice_channel.is_connected()

    async def check_voice_channel(self, voice_channel):
        try:
            if not self.is_connected():
                self.voice_channel = await voice_channel.connect()
        except discord.ClientException:
            print("Bot is already in a voice channel")

    def get_voice_channel(self, member):
        voice_channels = self.guild.voice_channels

        for voice_channel in voice_channels:
            if member.id in voice_channel.voice_states.keys():
                return voice_channel

        return None

    def check_player(self):
        if not self.audio_player:
            self.audio_player = Player(self.client, self.voice_channel)
            self.audio_player.start_player()

    async def add_media(self, media_type, url, member, request_channel):
        # Get the voice channel the member is connected to
        voice_channel = self.get_voice_channel(member)

        if not voice_channel:
            # TODO: Warn user we couldn't find them
            return

        # Join the voice channel
        await self.check_voice_channel(voice_channel)

        # Start the player
        self.check_player()

        if media_type == "search":
            await self.audio_player.add_search(url, member, request_channel)
        elif media_type == "playlist":
            await self.audio_player.add_playlist(url, member, request_channel)
        elif media_type == "single":
            await self.audio_player.add_song(url, member, request_channel)
        else:
            pass

    async def get_playlist_info(self, request_channel, url):
        self.check_player()

        await self.audio_player.return_playlist_info(request_channel, url)

    async def get_info(self, request_channel, url):
        self.check_player()

        await self.audio_player.return_info(request_channel, url)

    def pause(self):
        if self.audio_player:
            self.audio_player.pause()

    def resume(self):
        if self.audio_player:
            self.audio_player.resume()

    def skip(self):
        if self.audio_player:
            self.audio_player.skip()

    async def queue(self, channel):
        if self.audio_player:
            await self.audio_player.get_queue(channel)
