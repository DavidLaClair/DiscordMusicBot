import discord
import discord.ext.commands
import yaml
from discord.ext import commands

import discord.ext
from guild.guild import Guild
from utilities import url

# TODO: Goodbye
# TODO: Move things in queue
# TODO: removing something from the queue
# TODO: Spotify?


intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix='#', intents=intents)

config_file_name = "config.yaml"
config_file = open(config_file_name, "r")
config_file_yaml = yaml.safe_load(config_file)

prod = config_file_yaml["prod"]
bot_token = config_file_yaml["bot_token"]
pafy_api = config_file_yaml["pafy_api"]

guilds: dict[int, Guild] = {}

@client.event
async def on_ready():
    for guild in client.guilds:
        print(guild.name)
        guilds[guild.id] = Guild(guild, client)

    print("Client is done initializing!")


@client.command()
async def play(context: discord.ext.commands.Context, *, play_url: str=None):
    voice_channel = guilds[context.guild.id].get_voice_channel(context.author)
    
    if not voice_channel:
        await guilds[context.guild.id].send_embed(context.channel, "Error", "Could not find you in any voice channels!")
        return

    await guilds[context.guild.id].check_player(voice_channel)

    if url.is_search(play_url):
        await guilds[context.guild.id].add_media("search", play_url, context.author, context.channel)
    elif url.is_playlist(play_url):
        await guilds[context.guild.id].add_media("playlist", play_url, context.author, context.channel)
    else:
        await guilds[context.guild.id].add_media("single", play_url, context.author, context.channel)


@client.command()
async def pause(context: discord.ext.commands.Context):
    guilds[context.guild.id].pause()


@client.command()
async def resume(context: discord.ext.commands.Context):
    guilds[context.guild.id].resume()


@client.command()
async def skip(context: discord.ext.commands.Context):
    guilds[context.guild.id].skip()


@client.command()
async def queue(context: discord.ext.commands.Context):
    await guilds[context.guild.id].queue(context.channel)


client.run(token=bot_token)
