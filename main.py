import discord
import yaml
from discord.ext import commands

from guild.guild import Guild

# TODO: Goodbye
# TODO: Make it faster getting the info from the video
# TODO: Move things in queue
# TODO: removing something from the queue
# TODO: Timeout after inactivity (not playing anything)
# TODO: Timeout after no one else is in voice channel
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

if prod:
    print("Starting prod")
    log_name = "prod.log"
else:
    print("Starting dev")
    log_name = "dev.log"

guilds = {}


@client.event
async def on_ready():
    for guild in client.guilds:
        print(guild.name)
        guilds[guild.id] = Guild(guild, client)

    print("Client is done initializing!")


def is_playlist(url):
    if "/playlist?list" in url:
        return True
    elif "&list=" in url:
        return True
    return False


def is_search(url):
    if "youtube" in url:
        return False
    elif "spotify" in url:
        return False
    else:
        return True


@client.command()
async def play(context, *, url=None):
    if is_search(url):
        await guilds[context.guild.id].add_media("search", url, context.author, context.channel)
    elif is_playlist(url):
        await guilds[context.guild.id].add_media("playlist", url, context.author, context.channel)
    else:
        await guilds[context.guild.id].add_media("single", url, context.author, context.channel)


@client.command()
async def pause(context):
    guilds[context.guild.id].pause()


@client.command()
async def resume(context):
    guilds[context.guild.id].resume()


@client.command()
async def skip(context):
    guilds[context.guild.id].skip()


@client.command()
async def queue(context):
    await guilds[context.guild.id].queue(context.channel)


@client.command()
async def get_info(context, *, url=None):
    if is_playlist(url):
        await guilds[context.guild.id].get_playlist_info(context.channel, url)
    else:
        await guilds[context.guild.id].get_info(context.channel, url)


client.run(bot_token)
