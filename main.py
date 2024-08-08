import settings
import discord
from discord.ext import commands
import datetime


intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!mdb ", intents=intents)

server_channels = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command()
async def set_channel(ctx):
    server_id = ctx.guild.id
    channel_id = ctx.channel.id
    server_channels[server_id] = channel_id
    await ctx.send(f"Notifications are now set to {ctx.channel.name}")

@bot.command()
async def notify(ctx, message: str):
    server_id = ctx.guild.id
    channel_id = server_channels.get(server_id)
    
    if channel_id:
        channel = bot.get_channel(channel_id)
        await channel.send(message)
    else:
        await ctx.send("Ingen kanal har ställts in. Använd !mdb set_channel för att ställa in kanal.")

bot.run(settings.DISCORD_API_SECRET)