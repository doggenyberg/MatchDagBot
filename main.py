import discord
import http.client
import urllib.parse
import json
import settings
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler

discord_api = settings.DISCORD_API_SECRET
football_api = settings.FOOTBALL_API_SECRET
football_base_url = "v3.football.api-sports.io"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!mdb ", intents=intents)

server_channels = {}

# Get game info for AIK Stockholm and Hammarby FF
def fetch_rounds():
    conn = http.client.HTTPSConnection("v3.football.api-sports.io")
    team_ids = [377, 363]
    all_rounds = []

    for team_id in team_ids:
        headers = {"x-rapidapi-key": football_api}
        params = urllib.parse.urlencode(
            {
                "team": team_id,
                "next": "1",
                "timezone": "Europe/Stockholm",
            }
        )

        conn.request("GET", f"/fixtures?{params}", headers=headers)

        res = conn.getresponse()
        data = res.read()
        json_data = json.loads(data.decode("utf-8"))

        if json_data.get("errors"):
            print(f"Error fetching data from team ID {team_id}: {json_data['errors']}")
        else:
            all_rounds.extend(json_data.get("response", []))

    return all_rounds

# Returns team ID from string
def get_team_id(team_name):
    team_ids = {
        "AIK": 377,
        "Hammarby": 363
    }
    
    return team_ids.get(team_name)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.command()
async def set_channel(ctx):
    server_id = ctx.guild.id
    channel_id = ctx.channel.id
    server_channels[server_id] = channel_id
    print(f"")
    await ctx.send(f"Notifications are now set to {ctx.channel.name}")


@bot.command()
async def nextmatch(ctx, team_name: str):
    team_id = get_team_id(team_name)
    
    if not team_id:
        await ctx.send("Kunde inte hitta laget. Skriv `AIK` eller `Hammarby` efter `!mdb nextmatch`")
        return 
    
    rounds = fetch_rounds()
    next_match = None
    home_team = {}
    away_team = {}
    home_team_data = {}
    away_team_data = {}
    
    for round in rounds:
        home_team_data = round['teams']['home']
        away_team_data = round['teams']['away']
        
        if home_team_data['id'] == team_id or away_team_data['id'] == team_id:
            next_match = round
            break
    
    if next_match:
        home_team = {
            "name": home_team_data['name'],
            "logo": home_team_data['logo']
        }
        
        away_team = {
            "name": away_team_data['name'],
            "logo": away_team_data['logo']
        }
        
        
        await ctx.send(f'{home_team["name"]} {home_team["logo"]} {away_team["name"]} {away_team["logo"]}')
    else:
        await ctx.send(f'Kunde inte hitta nästa match.')


@bot.command()
async def notify(ctx, message: str):
    server_id = ctx.guild.id
    channel_id = server_channels.get(server_id)

    if channel_id:
        channel = bot.get_channel(channel_id)
        await channel.send(message)
    else:
        await ctx.send(
            "Ingen kanal har ställts in. Använd `!mdb set_channel` för att ställa in kanal."
        )


rounds_data = fetch_rounds()
bot.run(discord_api)
