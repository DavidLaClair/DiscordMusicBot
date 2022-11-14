import asyncio
from datetime import datetime

import discord
import yt_dlp
from discord_ui import Button

from request.request import Request


class Player:
    def __init__(self, client, voice_channel, api_key, ui):
        self.client = client
        self.ui = ui
        self.voice_channel = voice_channel
        self.playlist = []
        self.playlist_index = 0
        self.play_queue = asyncio.Queue()
        self.is_playing_event = asyncio.Event()
        self.music_player = self.client.loop.create_task(self.audio_player())
        self.last_play = None

        # YouTube DL
        ydl_opts = {
            "clean_infojson": True,
            "default_search": "ytsearch",
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio"
            }],
            "extract_flat": "in_playlist",
            "subtitleslangs": ["en-us"]
        }
        self.yt_dlp = yt_dlp.YoutubeDL(ydl_opts)

    def get_vendor(self, url):
        if "youtube" in url:
            return "youtube"

        if "spotify" in url:
            return "spotify"

        return None

    def get_info(self, vendor, url):
        if vendor == "youtube":
            info = self.yt_dlp.extract_info(url, download=False)
            return info
        elif vendor == "spotify":
            return "not_supported_yet"
        else:
            return None

    def get_playlist_info(self, vendor, url):
        if vendor == "youtube":
            return self.yt_dlp.extract_info(url, download=False)
        elif vendor == "spotify":
            return "not_supported_yet"
        else:
            return None

    def get_title(self, vendor, info):
        if vendor == "youtube":
            return info["title"]
        elif vendor == "spotify":
            return "not_supported_yet"
        else:
            return None

    def get_playlist_length(self, info):
        return len(info["entries"])

    def get_best_audio_url(self, vendor, info):
        if vendor == "youtube":
            return info["url"]
        elif vendor == "spotify":
            return "not_supported_yet"
        else:
            return None

    def get_audio_source(self, request):
        info = request.info

        audio_url = self.get_best_audio_url(request.vendor, info)

        audio = discord.FFmpegPCMAudio(
            source=audio_url,
            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
        )
        return audio

    def check_search(self, url):
        vendor = self.get_vendor(url)

        # If the vendor is none, assume a search query
        if not vendor:
            url = "ytsearch:" + url
            return url

        return None

    async def send_queued_embed(self, request):
        vendor = request.vendor
        url = request.url
        channel = request.channel
        info = request.info

        play_title = self.get_title(vendor, info)

        message_title = "Queued!"
        message_description = "[{title}]({link})".format(
            title=play_title,
            link=url
        )

        embed = discord.Embed(title=message_title, description=message_description)

        await channel.send(embed=embed)

    async def send_playing_embed(self, request, next_up=None):
        vendor = request.vendor
        url = request.url
        info = request.info
        requester_mention = request.member.mention
        channel = request.channel

        play_title = self.get_title(vendor, info)

        message_title = "Now Playing!"
        message_description = "[{title}]({link}) {mention}".format(
            title=play_title,
            link=url,
            mention=requester_mention
        )

        embed = discord.Embed(title=message_title, description=message_description)

        if next_up:
            next_vendor = next_up.vendor
            next_info = next_up.info
            next_url = next_up.url

            next_title = self.get_title(next_vendor, next_info)

            embed.add_field(
                name="Up Next",
                value="[{title}]({link})".format(
                    title=next_title,
                    link=next_url
                ),
                inline=False
            )

        await channel.send(embed=embed)

    async def send_playlist_embed(self, length, channel):
        message_title = "Queued!"
        message_description = "Successfully added {length} tracks!".format(
            length=length
        )

        embed = discord.Embed(title=message_title, description=message_description)

        await channel.send(embed=embed)

    def get_next(self):
        try:
            next_index = self.playlist_index + 1
            return self.playlist[next_index]
        except IndexError:
            return None

    async def audio_player(self):
        while True:
            # Reset the playing flag if it is set
            self.is_playing_event.clear()

            # This will block waiting for a new item in the queue
            now_playing = await self.play_queue.get()

            # Give a preview of what's next
            next_up = self.get_next()

            # Send the "Now Playing" message
            await self.send_playing_embed(now_playing, next_up)

            # Get the audio source that we are going to play
            audio_source = self.get_audio_source(now_playing)

            # Play the audio!
            self.voice_channel.play(audio_source, after=self.play_next)

            # This will block until play_next has been called (song is over)
            await self.is_playing_event.wait()

            # After the song is over, set our last played timer for the idle counter
            self.last_play = datetime.now()

    def play_next(self, error):
        # Set the flag letting us know that song is over so we can keep playing
        self.playlist_index += 1
        self.client.loop.call_soon_threadsafe(self.is_playing_event.set)

    async def add_song(self, url, member, request_channel, send_embed=True):
        search_url = self.check_search(url)

        if search_url:
            vendor = "youtube"
            search_info = self.get_info(vendor, search_url)
            url = search_info["entries"][0]["url"]
            info = self.get_info(vendor, url)
        else:
            vendor = self.get_vendor(url)
            info = self.get_info(vendor, url)

        song_request = Request(vendor, url, member, request_channel, info)

        # Add to the playlist
        self.playlist.append(song_request)

        # Send the embed if we are playing something right now
        if self.voice_channel.is_playing() and send_embed:
            await self.send_queued_embed(song_request)

        # Add to the play queue
        await self.play_queue.put(song_request)

    async def add_playlist(self, url, member, request_channel):
        vendor = self.get_vendor(url)
        playlist_info = self.get_playlist_info(vendor, url)
        length = self.get_playlist_length(playlist_info)
        songs = playlist_info["entries"]

        for song in songs:
            await self.add_song(song["url"], member, request_channel, send_embed=False)

        await self.send_playlist_embed(length, request_channel)

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

        info = self.get_info(vendor, url)

        if search:
            url = info["entries"][0]["url"]
            info = self.get_info(vendor, url)

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

    def pause(self):
        self.voice_channel.pause()

    def resume(self):
        self.voice_channel.resume()

    def skip(self):
        if self.voice_channel.is_playing():
            self.voice_channel.stop()

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

        await channel.send(queue_text, components=[
            Button("First"),
            Button("Previous"),
            Button("Next"),
            Button("Last")
        ])
