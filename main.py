import discord
import http.client
import urllib.parse
import json
import settings
from discord.ext import commands
from datetime import datetime
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
    # conn = http.client.HTTPSConnection("v3.football.api-sports.io")
    # team_ids = [377, 363]
    # all_rounds = []

    # for team_id in team_ids:
    #     headers = {"x-rapidapi-key": football_api}
    #     params = urllib.parse.urlencode(
    #         {
    #             "team": team_id,
    #             "next": "1",
    #             "timezone": "Europe/Stockholm",
    #         }
    #     )

    #     try:
    #         conn.request("GET", f"/fixtures?{params}", headers=headers)
    #         res = conn.getresponse()
    #         data = res.read()
    #         json_data = json.loads(data.decode("utf-8"))

    #         if json_data.get("errors"):
    #             raise Exception(
    #                 f"Error fetching data from team ID {team_id}: {json_data['errors']}"
    #             )
    #         else:
    #             all_rounds.extend(json_data.get("response", []))

    #     except Exception as e:
    #         print(f"Could not retrieve data: {e}")
    #         raise

    all_rounds = [
        {
            "fixture": {
                "id": 1164216,
                "referee": None,
                "timezone": "Europe/Stockholm",
                "date": "2024-08-11T16:00:00+02:00",
                "timestamp": 1723384800,
                "periods": {"first": None, "second": None},
                "venue": {
                    "id": 1501,
                    "name": "Strawberry Arena",
                    "city": "Solna",
                },
                "status": {
                    "long": "Not Started",
                    "short": "NS",
                    "elapsed": None,
                },
            },
            "league": {
                "id": 113,
                "name": "Allsvenskan",
                "country": "Sweden",
                "logo": "https://media.api-sports.io/football/leagues/113.png",
                "flag": "https://media.api-sports.io/flags/se.svg",
                "season": 2024,
                "round": "Regular Season - 18",
            },
            "teams": {
                "home": {
                    "id": 377,
                    "name": "AIK stockholm",
                    "logo": "https://media.api-sports.io/football/teams/377.png",
                    "winner": None,
                },
                "away": {
                    "id": 2240,
                    "name": "Mjallby AIF",
                    "logo": "https://media.api-sports.io/football/teams/2240.png",
                    "winner": None,
                },
            },
            "goals": {"home": None, "away": None},
            "score": {
                "halftime": {"home": None, "away": None},
                "fulltime": {"home": None, "away": None},
                "extratime": {"home": None, "away": None},
                "penalty": {"home": None, "away": None},
            },
        },
        {
            "fixture": {
                "id": 1164216,
                "referee": None,
                "timezone": "Europe/Stockholm",
                "date": "2024-08-11T16:00:00+02:00",
                "timestamp": 1723384800,
                "periods": {"first": None, "second": None},
                "venue": {
                    "id": 1501,
                    "name": "Strawberry Arena",
                    "city": "Solna",
                },
                "status": {
                    "long": "Not Started",
                    "short": "NS",
                    "elapsed": None,
                },
            },
            "league": {
                "id": 113,
                "name": "Allsvenskan",
                "country": "Sweden",
                "logo": "https://media.api-sports.io/football/leagues/113.png",
                "flag": "https://media.api-sports.io/flags/se.svg",
                "season": 2024,
                "round": "Regular Season - 18",
            },
            "teams": {
                "home": {
                    "id": 123,
                    "name": "AIK stockholm",
                    "logo": "https://media.api-sports.io/football/teams/377.png",
                    "winner": None,
                },
                "away": {
                    "id": 2240,
                    "name": "Mjallby AIF",
                    "logo": "https://media.api-sports.io/football/teams/2240.png",
                    "winner": None,
                },
            },
            "goals": {"home": None, "away": None},
            "score": {
                "halftime": {"home": None, "away": None},
                "fulltime": {"home": None, "away": None},
                "extratime": {"home": None, "away": None},
                "penalty": {"home": None, "away": None},
            },
        },
    ]

    return all_rounds


def game_info(team_id):
    try:
        rounds = fetch_rounds()
        next_game = None

        for round in rounds:
            data_ht = round["teams"]["home"]
            data_at = round["teams"]["away"]

            if data_ht["id"] == team_id or data_at["id"] == team_id:
                next_game = round
                break

        if not next_game:
            return None

        return next_game
    except Exception:
        return None


# Returns team ID from string
def get_team_id(team_name):
    team_ids = {"AIK": 377, "Hammarby": 363}
    return team_ids.get(team_name)


# Formats and returns embed for the bot to send
def embed_message(game, team_id):
    def get_color(team_id):
        if team_id == 377:
            return discord.Colour(int("002D56", 16))
        elif team_id == 363:
            return discord.Colour(int("00AB4F", 16))
        return discord.Colour.default()

    def home_or_away():
        if game["teams"]["home"]["id"] == team_id:
            return f"**{home_team_name}** spelar nästa match mot {away_team_name}"
        else:
            return f"**{away_team_name}** spelar nästa match mot {home_team_name}"

    def days_until_match(date_str):
        try:
            date_obj = datetime.fromisoformat(date_str)
            today = datetime.now(date_obj.tzinfo)
            delta = date_obj - today
            return delta.days

        except ValueError as e:
            print(f"ValueError calculating days until match: {e}")
            return "Okänt antal"

        except Exception as e:
            print(f"Error calculating days until match: {e}")
            return "Okänt antal"

    home_team_name = game["teams"]["home"]["name"]
    home_team_logo = game["teams"]["home"]["logo"]
    away_team_name = game["teams"]["away"]["name"]

    date_str = game["fixture"]["date"]
    formatted_date = datetime.fromisoformat(date_str).strftime("%Y-%m-%d %H:%M")
    days_left = days_until_match(date_str)

    arena = game["fixture"]["venue"]["name"]
    city = game["fixture"]["venue"]["city"]

    embed = discord.Embed(
        title=f"**Nästa match**",
        description=f"{home_or_away()} - **{days_left}** dagar kvar!",
        color=get_color(team_id),
    )

    embed.set_thumbnail(url=home_team_logo)
    embed.add_field(name="Arena", value=arena, inline=True)
    embed.add_field(name="Datum", value=formatted_date, inline=True)

    return embed


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.command()
async def set_channel(ctx):
    server_id = ctx.guild.id
    channel_id = ctx.channel.id
    server_channels[server_id] = channel_id
    await ctx.send(f'Jag kommer att skicka match-notifieringar i "{ctx.channel.name}"')


@bot.command()
async def nextgame(ctx, team_name: str):
    team_id = get_team_id(team_name)

    if not team_id:
        await ctx.send(
            "Kunde inte hitta laget. Skriv `AIK` eller `Hammarby` efter `!mdb nextgame`"
        )
        return

    try:
        next_game = game_info(team_id)
        embedded_message = embed_message(next_game, team_id)

        if embedded_message:
            await ctx.send(embed=embedded_message)
        else:
            await ctx.send(f"Kunde inte hitta nästa match.")

    except Exception:
        await ctx.send(f"Jag behöver vila en stund! Prova igen imorgon.")


bot.run(discord_api)
