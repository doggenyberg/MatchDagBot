import discord
import http.client
import urllib.parse
import json
import os
import settings
from discord.ext import commands
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

discord_api = settings.DISCORD_API_SECRET
football_api = settings.FOOTBALL_API_SECRET
football_base_url = "v3.football.api-sports.io"
CHANNELS_FILE = "channels.json"
global_rounds = []


class CustomHelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        embed = discord.Embed(
            title="Hjälp",
            color=discord.Color.teal()
        )

        embed.add_field(
            name="`!mdb set_channel`",
            value="Ställer in aktuell kanal för automatiska notifieringar.\n\u200b",
            inline=False
        )

        embed.add_field(
            name="`!mdb remove_channel`",
            value="Stoppar aktuell kanal för automatiska notifieringar.\n\u200b",
            inline=False
        )

        embed.add_field(
            name="`!mdb next_game` följt utav `AIK` eller `Hammarby`",
            value="Visar information om nästkommande match för önskat lag.\n\u200b",
            inline=False
        )

        embed.add_field(
            name="När skickas notifieringarna?",
            value="Notifieringarna skickas ut automatiskt för AIK och Hammarby en dag innan matchdagen för respektive lag",
            inline=False
)

        await self.context.send(embed=embed)


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!mdb ", intents=intents, help_command=CustomHelpCommand())
scheduler = AsyncIOScheduler()


def load_channels():
    if os.path.exists(CHANNELS_FILE):
        with open(CHANNELS_FILE, "r") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return {}
    else:
        with open(CHANNELS_FILE, "w") as file:
            json.dump({}, file, indent=4)
        return {}


def save_channels(data):
    with open(CHANNELS_FILE, "w") as file:
        json.dump(data, file, indent=1)


server_channels = load_channels()


# Get game info for AIK and Hammarby
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

        try:
            conn.request("GET", f"/fixtures?{params}", headers=headers)
            res = conn.getresponse()
            data = res.read()
            json_data = json.loads(data.decode("utf-8"))

            if json_data.get("errors"):
                raise Exception(
                    f"Error fetching data from team ID {team_id}: {json_data['errors']}"
                )
            else:
                all_rounds.extend(json_data.get("response", []))

        except Exception as e:
            print(f"Could not retrieve data: {e}")
            raise

    return all_rounds


def game_info(team_id):
    try:
        next_game = None
        for round in global_rounds:
            data_ht = round["teams"]["home"]
            data_at = round["teams"]["away"]
            if data_ht["id"] == team_id or data_at["id"] == team_id:
                next_game = round
                break

        if not next_game:
            print(f"No game found for team")
            return None

        return next_game
    except Exception as e:
        print(f"Could not retrieve data: {e}")
        return None


def days_until_game(date_str):
    try:
        date_obj = datetime.fromisoformat(date_str)
        today = datetime.now(date_obj.tzinfo)
        delta = date_obj - today
        days_left = delta.total_seconds() / (24 * 3600)
        return round(days_left)

    except ValueError as e:
        print(f"ValueError calculating days until match: {e}")
        return "Okänt antal"

    except Exception as e:
        print(f"Error calculating days until match: {e}")
        return "Okänt antal"


# Returns team ID from string
def get_team_id(team_name):
    team_ids = {"AIK": 377, "Hammarby": 363}
    return team_ids.get(team_name)


# Formats and returns embed for the bot to send
def embed_message(game, team_id):
    def aik_name_check(name):
        if name == "AIK stockholm":
            return "AIK"
        return name

    def get_color(team_id):
        if team_id == 377:
            return discord.Colour(int("002D56", 16))
        elif team_id == 363:
            return discord.Colour(int("00AB4F", 16))
        return discord.Colour.default()

    def home_or_away():
        if game["teams"]["home"]["id"] == team_id:
            return f"{home_team_name} spelar nästa match mot {away_team_name}"
        return f"{away_team_name} spelar nästa match mot {home_team_name}"

    home_team_name = game["teams"]["home"]["name"]
    home_team_logo = game["teams"]["home"]["logo"]
    away_team_name = game["teams"]["away"]["name"]
    away_team_logo = game["teams"]["away"]["logo"]
    arena = game["fixture"]["venue"]["name"]

    if game["teams"]["home"]["id"] == team_id:
        team_logo = home_team_logo
    else:
        team_logo = away_team_logo

    home_team_name = aik_name_check(home_team_name)
    away_team_name = aik_name_check(away_team_name)

    date_str = game["fixture"]["date"]
    formatted_date = datetime.fromisoformat(date_str).strftime("%Y-%m-%d %H:%M")
    days_left = days_until_game(date_str)

    embed = discord.Embed(
        title=game["league"]["name"],
        description=f"{home_or_away()} om **{days_left} dagar**!",
        color=get_color(team_id),
    )

    embed.set_thumbnail(url=team_logo)
    embed.add_field(name="", value="", inline=False)
    embed.add_field(name="Datum", value=formatted_date, inline=True)
    embed.add_field(name="Arena", value=arena, inline=True)

    return embed


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    scheduler.start()
    print(f"Scheduler is now started")


@bot.command()
async def set_channel(ctx):
    server_id = str(ctx.guild.id)
    channel_id = ctx.channel.id
    server_channels[server_id] = channel_id
    save_channels(server_channels)
    await ctx.send(f'Jag kommer att skicka match-notifieringar i "{ctx.channel.name}".')


@bot.command()
async def remove_channel(ctx):
    server_id = str(ctx.guild.id)
    current_channel_id = ctx.channel.id

    if server_id in server_channels:
        if server_channels[server_id] == current_channel_id:
            del server_channels[server_id]
            save_channels(server_channels)
            await ctx.send(
                f"Kanalen för match-notifieringar har tagits bort från denna server."
            )
        else:
            await ctx.send(
                "Detta kommando måste köras i samma kanal där `!mdb set_channel` sattes."
            )
    else:
        await ctx.send("Det finns ingen inställd kanal för denna server.")


@bot.command()
async def next_game(ctx, team_name: str = None):
    if not team_name:
        await ctx.send(
            "Du måste ange ett lagnamn efter kommandot `!mdb next_game`. Skriv `AIK` eller `Hammarby`."
        )
        return

    team_id = get_team_id(team_name)

    if not team_id:
        await ctx.send(
            "Kunde inte hitta laget. Skriv `AIK` eller `Hammarby` efter kommandot `!mdb next_game`"
        )
        return

    try:
        next_game = game_info(team_id)
        embedded_message = embed_message(next_game, team_id)

        if embedded_message:
            await ctx.send(embed=embedded_message)
        else:
            await ctx.send(f"Kunde inte hitta nästa match.")

    except Exception as e:
        print(f"Couldn't send message for !mdb next_game: {e}")
        await ctx.send(f"Jag behöver vila en stund! Prova igen imorgon.")

async def send_game_updates():
    global server_channels
    global global_rounds

    server_channels = load_channels()
    if not server_channels:
        print("No channels saved. No updates will be sent.")
        return
    
    print(f"Loaded server_channels: {server_channels}")

    try:
        global_rounds = fetch_rounds()

        for server_id, channel_id in server_channels.items():
            channel = bot.get_channel(int(channel_id))
            if channel:
                print(f"Found channel: {channel.name}")
                for team_name in ["AIK", "Hammarby"]:
                    team_id = get_team_id(team_name)
                    next_game = game_info(team_id)
                    if next_game and days_until_game(next_game["fixture"]["date"]) == 1:
                        embedded_message = embed_message(next_game, team_id)
                        await channel.send(embed=embedded_message)
                        print("Game update was sent successfully to all channels")
                        break
    except Exception as e:
        print(f"Couldn't send game update: {e}")


scheduler.add_job(send_game_updates, "interval", days=1)

bot.run(discord_api)
