import discord
from player.player import Player


class Guild:
    def __init__(self, guild: discord.Guild, client: discord.Client):
        self.guild: discord.Guild = guild
        self.client: discord.Client = client
        self.voice_client: discord.VoiceClient = None

        # Core Music
        self.audio_player: Player = None

    # Core functions
    def is_connected(self) -> bool:
        """Checks to see if we are already connected inside the guild."""
        if not self.voice_client:
            return False

        if not self.audio_player or self.audio_player.is_reset:
            return False

        return self.voice_client.is_connected()

    async def connect_voice_channel(self, voice_channel: discord.VoiceChannel):
        """Connect the bot to a voice channel."""
        try:
            if self.is_connected():
                return
            
            # Connect to the voice channel
            self.voice_client = await voice_channel.connect()

        except discord.ClientException:
            print("Bot is already in a voice channel")

    def get_voice_channel(self, member: discord.Member) -> discord.VoiceChannel:
        """Return the voice channel that the member is in."""
        for voice_channel in self.guild.voice_channels:
            if member in voice_channel.members:
                return voice_channel

        return None

    def create_player(self):
        """Create a new player if one does not exist.
        If a player exists, but is in a 'dead' state, make a new one."""
        if not self.audio_player or self.audio_player.is_reset:
            self.audio_player = Player(self.client, self.voice_client)
            self.audio_player.start_player()

    async def check_player(self, voice_channel: discord.VoiceChannel):
        """Connects to a voice channel if we aren't already connected.
        Creates an audio player if one doesn't exist.
        """
        # Join the voice channel
        await self.connect_voice_channel(voice_channel)

        # Start the player
        self.create_player()

        return True

    async def add_media(self, media_type: str, url: str, member: discord.Member, request_channel: discord.TextChannel):
        """Adds a specific media to the play queue.
        
        Valid media types are:
        - search
        - playlist
        - single"""
        if media_type == "search":
            await self.audio_player.add_search(url, member, request_channel)
        elif media_type == "playlist":
            await self.audio_player.add_playlist(url, member, request_channel)
        elif media_type == "single":
            await self.audio_player.add_youtube_url(url, member, request_channel)
        else:
            pass

    def pause(self):
        """Pauses the current audio player."""
        if self.audio_player:
            self.audio_player.pause()

    def resume(self):
        """Resume the current audio player."""
        if self.audio_player:
            self.audio_player.resume()

    def skip(self):
        """Skip the currently playing media."""
        if self.audio_player:
            self.audio_player.skip()

    async def queue(self, channel: discord.TextChannel):
        """Get the current play queue."""
        if self.audio_player:
            await self.audio_player.get_queue(channel)
    
    async def send_embed(self, request_channel: discord.TextChannel, title:str, message:str):
        """Send an embed."""
        embed = discord.Embed(title=title, description=message)

        await request_channel.send(embed=embed)
