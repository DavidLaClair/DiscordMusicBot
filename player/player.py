import asyncio
import discord
import yt_dlp

from datetime import datetime, timedelta
from discord.ext import tasks

from request.request import Request
from play_queue.play_queue import PlayQueue
from youtube_playlist.youtube_playlist import YoutubePlaylist
from youtube_video.youtube_video import YoutubeVideo
from utilities import youtube


class Player:
    def __init__(self, client: discord.Client, voice_client: discord.VoiceClient):
        self.client: discord.Client = client
        self.voice_client: discord.VoiceClient = voice_client
        self.play_queue: PlayQueue = PlayQueue()
        self.is_playing_event: asyncio.Event = asyncio.Event()
        self.last_play_time: datetime = None
        self.is_reset: bool = False
        self.timeout: float = 10

        # YouTube DL
        ydl_opts_audio_only = {
            "clean_infojson": True,
            "default_search": "ytsearch",
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio"
            }],
            "extract_flat": "in_playlist",
            "subtitleslangs": ["-all"]
        }
        self.yt_dlp_audio: yt_dlp.YoutubeDL = yt_dlp.YoutubeDL(ydl_opts_audio_only)

    # <editor-fold desc="Queue Management">
    async def add_search(self, term: str, member: discord.Member, request_channel: discord.TextChannel, send_embed: bool=True):
        """Adds a search term to the queue."""
        url = "ytsearch:" + term

        # Get the first result
        results = youtube.get_info(url)

        # Check to make sure there is a result
        if not results["entries"]:
            await self.send_embed(request_channel, "Error", "No results found!")
            return

        first_result = results["entries"][0]

        await self.add_youtube_entry(first_result, member, request_channel, send_embed)

    async def add_youtube_entry(self, entry, member: discord.Member, request_channel: discord.TextChannel, send_embed:bool=True):
        """Adds a specific youtube entry (most likely from a search) to the queue."""
        media = YoutubeVideo(entry["url"], entry["title"])

        song_request = Request("youtube", media, member, request_channel)

        # Add to the playlist
        await self.play_queue.append(song_request)

        # Send the embed if we are playing something right now
        if self.voice_client.is_playing() and send_embed:
            await self.send_embed_queue(song_request)

    async def add_youtube_url(self, url: str, member: discord.Member, request_channel: discord.TextChannel, send_embed:bool=True):
        """Adds a specific youtube URL to the queue."""
        media = YoutubeVideo(url)

        song_request = Request("youtube", media, member, request_channel)

        # Add to the playlist
        await self.play_queue.append(song_request)

        # Send the embed if we are playing something right now
        if self.voice_client.is_playing() and send_embed:
            await self.send_embed_queue(song_request)

    async def add_playlist(self, url: str, member: discord.Member, request_channel:discord.TextChannel):
        """Adds a playlist to the queue."""
        if "youtube" in url:
            playlist = YoutubePlaylist(url)
        elif "spotify" in url:
            print("Spotify playlists not supported!")
            return
        else:
            print("Unknown playlist not supported!")
            return

        length: int = playlist.get_length()
        playlist_items: dict[str, any] = playlist.info["entries"]

        for song in playlist_items:
            url = song["url"]
            await self.add_youtube_url(url, member, request_channel, send_embed=False)

        await self.send_embed_playlist(length, request_channel)
    # </editor-fold>

    # <editor-fold desc="Embeds">
    async def send_embed(self, request_channel: discord.TextChannel, title: str, description: str):
        """Send a Discord 'embed' message to a specific channel."""
        embed = discord.Embed(title=title, description=description)

        await request_channel.send(embed=embed)

    async def send_embed_queue(self, request: Request):
        """Sends an 'queued' embed to a specific channel."""
        message_title = "Queued!"
        message_description = "[{title}]({link})".format(
            title=request.media.title,
            link=request.media.url
        )
        await self.send_embed(request.channel, message_title, message_description)

    async def send_embed_playing(self, request: Request, next_up: Request=None):
        """Send a 'now playing' embed to a specific channel."""
        message_title = "Now Playing!"
        message_description = "[{title}]({link}) {mention}".format(
            title=request.media.title,
            link=request.media.url,
            mention=request.member.mention
        )

        embed = discord.Embed(title=message_title, description=message_description)

        if next_up:
            next_url = next_up.media.url
            next_title = next_up.media.title

            embed.add_field(
                name="Up Next",
                value="[{title}]({link})".format(
                    title=next_title,
                    link=next_url
                ),
                inline=False
            )

        await request.channel.send(embed=embed)

    async def send_embed_playlist(self, length: int, channel: discord.TextChannel):
        """Send a 'playlist' embed to a specific channel."""
        message_title = "Queued!"
        message_description = "Successfully added {length} tracks!".format(
            length=length
        )

        embed = discord.Embed(title=message_title, description=message_description)

        await channel.send(embed=embed)
    # </editor-fold>

    # <editor-fold desc="Player Control">
    def start_player(self):
        """Start playing audio."""
        self.audio_player.start()

    def play_next(self, error):
        """Get ready for the next media."""
        # Set the flag letting us know that song is over, so we may continue playing
        self.play_queue.index += 1
        self.is_playing_event.set()

    def pause(self):
        """Pause the voice client."""
        self.voice_client.pause()

    def resume(self):
        """Resumes the voice client from a pause."""
        self.voice_client.resume()

    def skip(self):
        """Skip the current media."""
        if self.voice_client.is_playing():
            self.voice_client.stop()
    # </editor-fold>

    async def reset_player(self):
        self.is_reset = True
        await self.voice_client.disconnect()

    @tasks.loop(seconds=1.0)
    async def audio_player(self):
        # Reset the playing flag if it is set
        self.is_playing_event.clear()

        # We are currently playing audio, lets return and wait until we aren't
        if self.voice_client.is_playing():
            return

        # If nothing is playing and the queue is empty, start a 10-minute timer
        # At the end of the timer, kill the player
        if self.play_queue.is_empty():
            if self.last_play_time is None:
                self.last_play_time = datetime.now()

            time_diff = self.last_play_time + timedelta(minutes=self.timeout)
            if datetime.now() > time_diff:
                await self.reset_player()
            
            # Queue is empty and there is nothing for us to do at this time
            return

        # Get the next item to play in the queue
        now_playing: Request = await self.play_queue.get()

        # Give a preview of what's next
        next_up: Request = self.play_queue.get_next()

        # Make sure that both current and next songs have info available to them
        now_playing.media.check_info()
        if next_up:
            next_up.media.check_info()

        # Send the "Now Playing" message
        await self.send_embed_playing(now_playing, next_up)

        # Get the audio source that we are going to play
        audio_source = now_playing.media.get_audio_source()

        # Play the audio!
        try:
            self.voice_client.play(audio_source, after=self.play_next)
        except Exception as myException:
            print("Voice Client exception!")

        # This will block until play_next has been called (song is over)
        await self.is_playing_event.wait()

        # After the song is over, set our last played timer for the idle counter
        self.last_play_time = datetime.now()

    async def get_queue(self, channel: discord.TextChannel, start: int=0, end: int=9):
        """Print the queue to a specific channel"""
        # TODO: Give the queue a limit
        queue_text = "```\n"

        request: Request
        for index, request in enumerate(self.play_queue.playlist):
            vendor = request.vendor
            info = request.media.info

            title = request.media.title
            if len(title) > 40:
                title = title[:37] + "..."

            if index == self.play_queue.index:
                queue_text += "\t⬇⬇⬇ Now Playing ⬇⬇⬇\n"

            queue_text += "{index}) {title}".format(
                index=index,
                title=title
            )

            if index == self.play_queue.index:
                queue_text += "\n\t⬆⬆⬆ Now Playing ⬆⬆⬆"

            queue_text += "\n"

        queue_text += "```"

        await self.send_embed(channel, "Queue", queue_text)
