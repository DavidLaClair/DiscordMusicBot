import asyncio
import discord
import yt_dlp

from datetime import datetime
from discord.ext import tasks

from request.request import Request
from play_queue.play_queue import PlayQueue
from youtube_playlist.youtube_playlist import YoutubePlaylist
from youtube_video.youtube_video import YoutubeVideo


class Player:
    def __init__(self, client, voice_channel):
        self.client = client
        self.voice_channel = voice_channel
        self.play_queue = PlayQueue()
        self.is_playing_event = asyncio.Event()
        self.last_play_time = None

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
        self.yt_dlp_audio = yt_dlp.YoutubeDL(ydl_opts_audio_only)

    # <editor-fold desc="Queue Management">
    async def add_search(self, term, member, request_channel, send_embed=True):
        url = "ytsearch:" + term

        # Get the first result
        results = self.yt_dlp_audio.extract_info(url, download=False)
        first_result_url = results["entries"][0]["url"]

        await self.add_song(first_result_url, member, request_channel, send_embed)

    async def add_song(self, url, member, request_channel, send_embed=True):
        if "youtube" in url:
            media = YoutubeVideo(url, self.yt_dlp_audio)
        elif "spotify" in url:
            print("Spotify not supported!")
            return
        else:
            print("Unknown not supported!")
            return

        song_request = Request(media, member, request_channel)

        # Add to the playlist
        await self.play_queue.append(song_request)

        # Send the embed if we are playing something right now
        if self.voice_channel.is_playing() and send_embed:
            await self.send_queued_embed(song_request)

    async def add_playlist(self, url, member, request_channel):
        if "youtube" in url:
            playlist = await self.add_playlist_youtube(url)
        elif "spotify" in url:
            print("Spotify playlists not supported!")
            return
        else:
            print("Unknown playlist not supported!")
            return

        length = playlist.get_length()
        playlist_items = playlist.info["entries"]

        for song in playlist_items:
            url = song["url"]
            await self.add_song(url, member, request_channel, send_embed=False)

        await self.send_playlist_embed(length, request_channel)

    async def add_playlist_youtube(self, url):
        return YoutubePlaylist(url, self.yt_dlp_audio)
    # </editor-fold>

    # <editor-fold desc="Embeds">
    async def send_queued_embed(self, request):
        message_title = "Queued!"
        message_description = "[{title}]({link})".format(
            title=request.title,
            link=request.url
        )

        embed = discord.Embed(title=message_title, description=message_description)

        await request.channel.send(embed=embed)

    async def send_playing_embed(self, request, next_up=None):
        message_title = "Now Playing!"
        message_description = "[{title}]({link}) {mention}".format(
            title=request.title,
            link=request.url,
            mention=request.member.mention
        )

        embed = discord.Embed(title=message_title, description=message_description)

        if next_up:
            next_info = next_up.media.info
            next_url = next_up.media.url
            next_title = next_info["title"]

            embed.add_field(
                name="Up Next",
                value="[{title}]({link})".format(
                    title=next_title,
                    link=next_url
                ),
                inline=False
            )

        await request.channel.send(embed=embed)

    async def send_playlist_embed(self, length, channel):
        message_title = "Queued!"
        message_description = "Successfully added {length} tracks!".format(
            length=length
        )

        embed = discord.Embed(title=message_title, description=message_description)

        await channel.send(embed=embed)
    # </editor-fold>

    # <editor-fold desc="Player Control">
    def start_player(self):
        self.audio_player.start()

    def play_next(self, error):
        # Set the flag letting us know that song is over, so we may continue playing
        self.play_queue.index += 1
        self.is_playing_event.set()

    def pause(self):
        self.voice_channel.pause()

    def resume(self):
        self.voice_channel.resume()

    def skip(self):
        if self.voice_channel.is_playing():
            self.voice_channel.stop()
    # </editor-fold>

    @tasks.loop(seconds=1.0)
    async def audio_player(self):
        # Reset the playing flag if it is set
        self.is_playing_event.clear()

        print("running task")

        # We are currently playing audio, lets return and wait until we aren't
        if self.voice_channel.is_playing():
            return

        # There is nothing in the queue, so nothing to do
        if self.play_queue.is_empty():
            return

        # Get the next item in the queue
        now_playing = await self.play_queue.get()

        # Give a preview of what's next
        next_up = self.play_queue.get_next()

        # Send the "Now Playing" message
        await self.send_playing_embed(now_playing, next_up)

        # Get the audio source that we are going to play
        audio_source = now_playing.media.get_audio_source()

        # Play the audio!
        self.voice_channel.play(audio_source, after=self.play_next)

        # This will block until play_next has been called (song is over)
        await self.is_playing_event.wait()

        # After the song is over, set our last played timer for the idle counter
        self.last_play_time = datetime.now()

    async def return_playlist_info(self, request_channel, url):
        vendor = self.get_vendor(url)
        info = self.get_playlist_info(vendor, url)

        message_title = "Info"
        message_description = "URL: {url}".format(
            url=url
        )

        embed = discord.Embed(title=message_title, description=message_description)

        embed.add_field(
            name="Vendor",
            value=vendor,
            inline=False
        )

        embed.add_field(
            name="Playlist Length",
            value=len(info["entries"]),
            inline=False
        )

        await request_channel.send(embed=embed)

    async def return_info(self, request_channel, url):
        search = False
        vendor = self.get_vendor(url)

        # If vendor is None, assume it's a YouTube search
        if not vendor:
            vendor = "youtube"
            search = True
            url = "ytsearch:" + url

        info = await self.get_info(vendor, url)

        if search:
            url = info["entries"][0]["url"]
            info = await self.get_info(vendor, url)

        title = self.get_title(vendor, info)
        audio_url = self.get_best_audio_url(vendor, info)

        message_title = "Info"
        message_description = "URL: {url}".format(
            url=url
        )

        embed = discord.Embed(title=message_title, description=message_description)

        embed.add_field(
            name="Vendor",
            value=vendor,
            inline=False
        )

        embed.add_field(
            name="Title",
            value=title,
            inline=False
        )

        embed.add_field(
            name="Audio Only URL",
            value="Check output in program",
            inline=False
        )

        await request_channel.send(embed=embed)

        print(audio_url)

    async def get_queue(self, channel, start=0, end=9):
        # TODO: Give the queue a limit
        queue_text = "```\n"

        for index, song in enumerate(self.playlist):
            vendor = song.vendor
            info = song.info

            title = self.get_title(vendor, info)
            if len(title) > 40:
                title = title[:37] + "..."

            if index == self.playlist_index:
                queue_text += "\t⬇⬇⬇ Now Playing ⬇⬇⬇\n"

            queue_text += "{index}) {title}".format(
                index=index,
                title=title
            )

            if index == self.playlist_index:
                queue_text += "\n\t⬆⬆⬆ Now Playing ⬆⬆⬆"

            queue_text += "\n"

        queue_text += "```"
