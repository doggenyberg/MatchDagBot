import discord
import http.client
import urllib.parse
import json
import os
import logging
import settings
from discord.ext import commands
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Set up basic logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  # Create a logger object for this module

discord_api = settings.DISCORD_API_SECRET  # API secret for Discord bot
football_api = settings.FOOTBALL_API_SECRET  # API secret for football data API
CHANNELS_FILE = "channels.json"  # File to store channel data
global_rounds = []  # List to store game round data globally


# Customized help command
class CustomHelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        # Create an embed object to format the help message in a more readable way.
        embed = discord.Embed(title="Hjälp", color=discord.Color.teal())

        # Add a blank field to the embed.
        embed.add_field(name="", value="", inline=False)

        # Add a field for the `!mdb set_channel` command description.
        embed.add_field(
            name="`!mdb set_channel`",
            value="Ställer in aktuell kanal för automatiska notifieringar.\n\u200b",
            inline=False,
        )

        # Add a field for the `!mdb remove_channel` command description.
        embed.add_field(
            name="`!mdb remove_channel`",
            value="Stoppar aktuell kanal för automatiska notifieringar.\n\u200b",
            inline=False,
        )

        # Add a field for the `!mdb next_game` command description.
        embed.add_field(
            name="`!mdb next_game` följt av `AIK` eller `Hammarby`",
            value="Visar information om nästkommande match för önskat lag.\n\u200b",
            inline=False,
        )

        # Add a field explaining when notifications are sent.
        embed.add_field(
            name="När skickas notifieringarna?",
            value="Notifieringarna skickas ut automatiskt för AIK och Hammarby en dag innan matchdagen för respektive lag.",
            inline=False,
        )

        # Add a field explaining which teams are currently setup for the bot
        embed.add_field(
            name="Vilka lag kan man hämta matchinfo för?"
            value="Just nu kan man bara hämta matchinfo för AIK och Hammarby IF",
            inline=False,
        )


        # Send the formatted help message to the context channel.
        await self.context.send(embed=embed)


# Create an instance of Discord's default intents, which are used to specify what events the bot should receive
intents = discord.Intents.default()

# Enable the intent to receive message content, which allows the bot to read the content of messages
intents.message_content = True

# Create an instance of the commands.Bot class, which represents the bot
# Set the command prefix to "!mdb " (commands must start with this prefix)
# Use the custom help command class CustomHelpCommand for handling help command responses
bot = commands.Bot(
    command_prefix="!mdb ",  # Command prefix used to invoke bot commands
    intents=intents,  # Intents used to specify which events the bot will listen to
    help_command=CustomHelpCommand(),  # Use the custom help command class for help command functionality
)

# Create an instance of AsyncIOScheduler for scheduling tasks to run asynchronously
scheduler = AsyncIOScheduler()


# Loads all the saved channels from json file
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


# Saves the channel to json file
def save_channels(data):
    with open(CHANNELS_FILE, "w") as file:
        json.dump(data, file, indent=1)


# Loads the saved round data from json file
def load_global_rounds():
    if os.path.exists("global_rounds.json"):
        with open("global_rounds.json", "r") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return []
    else:
        return []


# Saves the round data to json file
def save_global_rounds():
    with open("global_rounds.json", "w") as file:
        json.dump(global_rounds, file, indent=4)


# Loads all discord channels that have been setup
server_channels = load_channels()


# Fetch API to retrieve game data
def fetch_rounds():
    # Establish a connection to the football API
    conn = http.client.HTTPSConnection("v3.football.api-sports.io")

    # List of team IDs to fetch fixtures for
    team_ids = [377, 363]
    all_rounds = []  # Initialize a list to store all rounds' data

    # Iterate over each team ID
    for team_id in team_ids:
        # Set up the request headers with the API key
        headers = {"x-rapidapi-key": football_api}

        # Prepare query parameters for the API request
        params = urllib.parse.urlencode(
            {
                "team": team_id,  # Specify the team ID
                "next": "1",  # Fetch only the next fixture
                "timezone": "Europe/Stockholm",  # Set the timezone
            }
        )

        try:
            # Send the request to the API
            conn.request("GET", f"/fixtures?{params}", headers=headers)
            # Get the response from the API
            res = conn.getresponse()
            # Read the response data
            data = res.read()
            # Decode the response data from bytes to a string and parse it as JSON
            json_data = json.loads(data.decode("utf-8"))

            # Check if the response contains errors
            if json_data.get("errors"):
                raise Exception(
                    f"Error fetching data from team ID {team_id}: {json_data['errors']}"
                )
            else:
                # Append the fetched rounds to the all_rounds list
                all_rounds.extend(json_data.get("response", []))

        except Exception as e:
            # Log an error if data retrieval fails and re-raise the exception
            logging.error(f"Could not retrieve data for team ID {team_id}: {e}")
            raise

    # Return the list of all fetched rounds
    return all_rounds


# Returns data of next game's info
def game_info(team_id):
    try:
        # Initialize the variable to store the next game information
        next_game = None

        # Loop through all rounds to find the next game for the given team ID
        for round in global_rounds:
            data_ht = round["teams"]["home"]  # Home team data
            data_at = round["teams"]["away"]  # Away team data

            # Check if the current round's home or away team matches the given team ID
            if data_ht["id"] == team_id or data_at["id"] == team_id:
                next_game = round  # Set the found game as the next game
                break  # Exit the loop once the game is found

        # Log a warning and return None if no game was found
        if not next_game:
            logging.warning(
                f"No game found for team. Array global_rounds: {global_rounds}"
            )
            return None

        # Return the next game information
        return next_game
    except Exception as e:
        # Log an error if an exception occurs and return None
        logging.warning(f"Could not retrieve data: {e}")
        return None


# Calculates how many days until next game
def days_until_game(date_str):
    try:
        # Parse the date string into a datetime object
        date_obj = datetime.fromisoformat(date_str)

        # Get the current date and time with the same timezone as date_obj
        today = datetime.now(date_obj.tzinfo)

        # Calculate the time difference between the game date and the current date
        delta = date_obj - today

        # Convert the time difference from seconds to days and round it
        days_left = delta.total_seconds() / (24 * 3600)
        return round(days_left)

    except ValueError as e:
        # Log an error if the date string is invalid and return a default message
        logging.error(f"ValueError calculating days until match: {e}")
        return "Unknown number of days"

    except Exception as e:
        # Log any other errors and return a default message
        logging.error(f"Error calculating days until match: {e}")
        return "Unknown number of days"


# Returns team ID from string
def get_team_id(team_name):
    # Dictionary mapping team names to their corresponding IDs
    team_ids = {"AIK": 377, "Hammarby": 363}

    # Return the ID corresponding to the given team name, or None if not found
    return team_ids.get(team_name)


# Formats and returns embed for the bot to send
def embed_message(game, team_id):
    # Helper function to return the correct word for "days" based on the number of days left
    def word_day_days(days_left):
        word = None
        if days_left > 1:
            word = "dagar"  # Plural form
        elif days_left == 1:
            word = "dag"  # Singular form
        elif days_left == 0:
            word = "dagar (idag)"  # Special case for today
        return word

    # Helper function to correct the name "AIK stockholm" to "AIK"
    def aik_name_check(name):
        if name == "AIK stockholm":
            return "AIK"
        return name

    # Helper function to get the color associated with the team
    def get_color(team_id):
        if team_id == 377:
            return discord.Colour(int("002D56", 16))  # Color for AIK
        elif team_id == 363:
            return discord.Colour(int("00AB4F", 16))  # Color for Hammarby
        return discord.Colour.default()

    # Helper function to determine if the team is playing at home or away
    def home_or_away():
        if game["teams"]["home"]["id"] == team_id:
            return (
                f"{home_team_name} spelar nästa match mot {away_team_name}"  # Home game
            )
        return f"{away_team_name} spelar nästa match mot {home_team_name}"  # Away game

    # Extracting relevant information from the game data
    home_team_name = game["teams"]["home"]["name"]
    home_team_logo = game["teams"]["home"]["logo"]
    away_team_name = game["teams"]["away"]["name"]
    away_team_logo = game["teams"]["away"]["logo"]
    arena = game["fixture"]["venue"]["name"]

    # Determine which team's logo to display
    if game["teams"]["home"]["id"] == team_id:
        team_logo = home_team_logo
    else:
        team_logo = away_team_logo

    # Correct team names if necessary
    home_team_name = aik_name_check(home_team_name)
    away_team_name = aik_name_check(away_team_name)

    # Format the game date and calculate days until the game
    date_str = game["fixture"]["date"]
    formatted_date = datetime.fromisoformat(date_str).strftime("%Y-%m-%d %H:%M")
    days_left = days_until_game(date_str)
    word_day = word_day_days(days_left)

    # Create an embed object to send to Discord
    embed = discord.Embed(
        title=game["league"]["name"],
        description=f"{home_or_away()} om **{days_left} {word_day}**!",  # Embed description
        color=get_color(team_id),  # Embed color based on team
    )

    # Set the team logo as the thumbnail
    embed.set_thumbnail(url=team_logo)
    embed.add_field(name="", value="", inline=False)  # Placeholder for extra spacing
    embed.add_field(name="Datum", value=formatted_date, inline=True)  # Game date
    embed.add_field(name="Arena", value=arena, inline=True)  # Game venue

    return embed  # Return the embed object


# Discord start event
@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user}")
    scheduler.start()
    logging.info(f"Scheduler is started")

    # Load global rounds at startup
    global_rounds = load_global_rounds()

    # Call send_game_updates to run immediately upon startup
    await send_game_updates()


# Discord command !mdb set_channel
# activates notifications for the current channel
@bot.command()
async def set_channel(ctx):
    # Get the server (guild) ID as a string
    server_id = str(ctx.guild.id)
    # Get the current channel ID
    channel_id = ctx.channel.id

    # Check if the server is already registered and the channel is already set for notifications
    if server_id in server_channels and server_channels[server_id] == channel_id:
        # Inform the user that the current channel is already set for notifications
        await ctx.send("Den här kanalen är redan inställd för notifikationer!")
        return

    # Set the current channel for notifications in the server
    server_channels[server_id] = channel_id
    # Save the updated channel list to the file
    save_channels(server_channels)
    # Inform the user that the bot will send match notifications in the current channel
    await ctx.send(f'Jag kommer att skicka match-notifieringar i "{ctx.channel.name}".')


# Discord command !mdb remove_channel
# deactivates notifications for the current channel
@bot.command()
async def remove_channel(ctx):
    # Get the server (guild) ID as a string
    server_id = str(ctx.guild.id)
    # Get the current channel ID
    current_channel_id = ctx.channel.id

    # Check if the server ID is in the saved channels
    if server_id in server_channels:
        # Check if the current channel is the one set for notifications
        if server_channels[server_id] == current_channel_id:
            # Remove the channel from the saved channels list
            del server_channels[server_id]
            # Save the updated channels list to the file
            save_channels(server_channels)
            # Inform the user that the notification channel has been removed
            await ctx.send(
                "Notifikationer kommer inte längre skickas till denna kanal."
            )
        else:
            # Inform the user that the command must be run in the same channel where `!mdb set_channel` was used
            await ctx.send(
                "Detta kommando måste köras i samma kanal där `!mdb set_channel` sattes ursprungligen."
            )
    else:
        # Inform the user that no notification channel is set for this server
        await ctx.send("Det finns ingen kanal som är inställd för notifikationer. Använd `!mdb set_channel` för att ställa in kanal.")


# Discord command !mdb next_channel
# sends out a message for next game
@bot.command()
async def next_game(ctx, team_name: str = None):
    # Check if a team name was provided
    if not team_name:
        # Inform the user that they need to provide a team name and return early
        await ctx.send(
            "Du måste ange ett lagnamn efter kommandot `!mdb next_game`. Skriv `AIK` eller `Hammarby`."
        )
        return

    # Get the team ID based on the provided team name
    team_id = get_team_id(team_name)

    # If the team ID is not found, inform the user and return early
    if not team_id:
        await ctx.send(
            "Kunde inte hitta laget. Skriv `AIK` eller `Hammarby` efter kommandot `!mdb next_game`"
        )
        return

    try:
        # Retrieve information about the next game for the specified team
        next_game = game_info(team_id)
        # Create an embedded message with the game information
        embedded_message = embed_message(next_game, team_id)

        # If the embedded message was created successfully, send it in the current context (channel)
        if embedded_message:
            await ctx.send(embed=embedded_message)
        else:
            # If no game was found, inform the user
            await ctx.send(f"Kunde inte hitta nästa match.")

    except Exception as e:
        # Log a warning if an error occurs while sending the next game message
        logging.warning(f"Couldn't send message for !mdb next_game: {e}")
        # Inform the user that the bot is temporarily unable to process the request
        await ctx.send("Jag behöver en paus! Prova gärna igen imorgon.")


# Calls the fetch function and sends
# out notifiations to all saved channels
async def send_game_updates():
    global server_channels
    global global_rounds

    # Load saved channels and rounds from JSON files
    server_channels = load_channels()
    global_rounds = load_global_rounds()

    # Check if there are any channels to send updates to
    if not server_channels:
        logging.info("No channels saved. No updates will be sent.")
        return

    logging.info(f"Loaded server_channels: {server_channels}")

    try:
        # Fetch new match schedules from the API
        fetched_rounds = fetch_rounds()
        global_rounds = (
            fetched_rounds  # Update the global_rounds variable with new data
        )
        save_global_rounds()  # Save the updated rounds to the JSON file

        # Iterate over all saved server channels
        for server_id, channel_id in server_channels.items():
            channel = bot.get_channel(int(channel_id))
            if channel:
                # Check the next game for both AIK and Hammarby
                for team_name in ["AIK", "Hammarby"]:
                    team_id = get_team_id(team_name)
                    next_game = game_info(team_id)

                    # If the next game is scheduled for tomorrow
                    if next_game and days_until_game(next_game["fixture"]["date"]) == 1:
                        # Create an embedded message for the game
                        embedded_message = embed_message(next_game, team_id)
                        # Send the embedded message to the corresponding channel
                        await channel.send(embed=embedded_message)
                        print("Game update was sent successfully to all channels")
                        break
    except Exception as e:
        # Log any errors that occur while sending game updates
        logging.error(f"Couldn't send game update: {e}")


# Schedule the send_game_updates function to run every 24 hours (86400 seconds)
scheduler.add_job(send_game_updates, "interval", seconds=86400)


# Start the bot with the specified Discord API token
bot.run(discord_api)
