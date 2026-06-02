from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import discord
from discord.ext import tasks
import os
from dotenv import load_dotenv
import json
from discord import app_commands

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

PST = ZoneInfo("America/Los_Angeles")

# =========================
# YOUR PREDICTOR DATA
# =========================

MONTH_PATTERN = [2, 1, 3, 0, 4, 1, 2, 0, 3, 1, 4, 0]

EVENT_CATEGORY = {
    0: "Black Shard",
    1: "Black Shard",
    2: "Red Shard",
    3: "Red Shard",
    4: "Red Shard",
}

AREA_NAMES = {
    1: "Daylight Prairie",
    2: "Hidden Forest",
    3: "Valley of Triumph",
    4: "Golden Wasteland",
    5: "Vault of Knowledge",
}

NO_EVENT_DAYS = {
    0: [5, 6],
    1: [6, 0],
    2: [0, 1],
    3: [1, 2],
    4: [2, 3],
}

SUBAREAS = {
    1: {
        0: "Butterfly Fields",
        1: "Prairie Village",
        2: "Prairie Caves",
        3: "Bird Nest",
        4: "Sanctuary Islands",
    },
    2: {
        0: "Forest Brook",
        1: "Boneyard",
        2: "Sacred Pond",
        3: "Treehouse",
        4: "Elevated Clearing",
    },
    3: {
        0: "Frozen Lake",
        1: "Frozen Lake",
        2: "Village of Dreams",
        3: "Village of Dreams",
        4: "Hermit Valley",
    },
    4: {
        0: "Broken Temple",
        1: "Battlefield",
        2: "Graveyard",
        3: "Crab Fields",
        4: "Forgotten Ark",
    },
    5: {
        0: "Starlight Desert",
        1: "Starlight Desert",
        2: "Jellyfish Cove",
        3: "Jellyfish Cove",
        4: "Jellyfish Cove",
    },
}

REWARDS = {
    1: {
        0: "4 Cakes",
        1: "4 Cakes",
        2: "2 Ascended Candles",
        3: "2.5 Ascended Candles",
        4: "3.5 Ascended Candles",
    },
    2: {
        0: "4 Cakes",
        1: "4 Cakes",
        2: "2.5 Ascended Candles",
        3: "3.5 Ascended Candles",
        4: "3.5 Ascended Candles",
    },
    3: {
        0: "4 Cakes",
        1: "4 Cakes",
        2: "2.5 Ascended Candles",
        3: "2.5 Ascended Candles",
        4: "3.5 Ascended Candles",
    },
    4: {
        0: "4 Cakes",
        1: "4 Cakes",
        2: "2 Ascended Candles",
        3: "2.5 Ascended Candles",
        4: "3.5 Ascended Candles",
    },
    5: {
        0: "4 Cakes",
        1: "4 Cakes",
        2: "3.5 Ascended Candles",
        3: "3.5 Ascended Candles",
        4: "3.5 Ascended Candles",
    },
}

OCCURRENCES = {
    0: [
        (1, 58, 40),
        (9, 58, 40),
        (17, 58, 40),
    ],
    1: [
        (2, 18, 40),
        (10, 18, 40),
        (18, 18, 40),
    ],
    2: [
        (7, 48, 40),
        (13, 48, 40),
        (19, 48, 40),
    ],
    3: [
        (2, 28, 40),
        (8, 28, 40),
        (14, 28, 40),
    ],
    4: [
        (3, 38, 40),
        (9, 38, 40),
        (15, 38, 40),
    ],
}

def get_area(target_date):
    return ((target_date.day - 1) % 5) + 1

def get_event_group(target_date):
    day_index = target_date.day - 1
    return MONTH_PATTERN[day_index % len(MONTH_PATTERN)]

def has_event(target_date, event_group):
    weekday = target_date.weekday()
    return weekday not in NO_EVENT_DAYS[event_group]

def ordinal(n):
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {
            1: "st",
            2: "nd",
            3: "rd",
        }.get(n % 10, "th")

    return f"{n}{suffix}"

def print_event_info(target_date):
    area = get_area(target_date)
    event_group = get_event_group(target_date)

    formatted_date = (
        f"{target_date.strftime('%A')}, "
        f"{ordinal(target_date.day)} "
        f"{target_date.strftime('%B %Y')}"
    )

    print(f"{formatted_date}:")

    if not has_event(target_date, event_group):
        print("No event today.")
        return

    category = EVENT_CATEGORY[event_group]
    subarea = SUBAREAS[area][event_group]
    reward = REWARDS[area][event_group]

    area_name = AREA_NAMES[area]

    print(f"{category} in {subarea} ({area_name})")
    print(f"Rewards: {reward}.")

    occurrences = OCCURRENCES[event_group]

    for i, occurrence in enumerate(occurrences, start=1):
        print(f"{i}st occurrence: {occurrence}" if i == 1 else
              f"{i}nd occurrence: {occurrence}" if i == 2 else
              f"{i}rd occurrence: {occurrence}")

# =========================
# MESSAGE GENERATOR
# =========================

sent_occurrences = set()
finished_occurrences = set()

def generate_message(highlight_occurrence=None,target_date=None):
    if target_date is None:
        target_date = datetime.now(PST).date()

    today = target_date

    area = get_area(today)
    event_group = get_event_group(today)

    formatted_date = (
        f"{today.strftime('%A')}, "
        f"{ordinal(today.day)} "
        f"{today.strftime('%B %Y')}"
    )

    if not has_event(today, event_group):
        return (
            f"{formatted_date}\n"
            f"No shard event today."
        )

    category = EVENT_CATEGORY[event_group]
    subarea = SUBAREAS[area][event_group]
    reward = REWARDS[area][event_group]
    area_name = AREA_NAMES[area]

    message = (
        f"{formatted_date}\n\n"
        f"{category} in {subarea} ({area_name})\n\n"
        f"Rewards: {reward}\n\n"
    )

    occurrences = OCCURRENCES[event_group]

    for i, (hour, minute, second) in enumerate(occurrences, start=1):

        start_dt = datetime(
            today.year,
            today.month,
            today.day,
            hour,
            minute,
            second,
            tzinfo=PST
        )

        end_dt = start_dt + timedelta(
            hours=3,
            minutes=51,
            seconds=20
        )

        start_unix = int(start_dt.timestamp())
        end_unix = int(end_dt.timestamp())

        ordinal_text = (
            "1st" if i == 1 else
            "2nd" if i == 2 else
            "3rd"
        )

        line = (
            f"{ordinal_text} occurrence: "
            f"<t:{start_unix}:D> <t:{start_unix}:T> "
            f"- "
            f"<t:{end_unix}:D> <t:{end_unix}:T> "
            f"(<t:{start_unix}:R>)"
        )

        if highlight_occurrence == i:
            line = f"**{line}**"

        message += line + "\n"

    return message

def validate_date(day, month, year):
    try:
        return datetime(
            year,
            month,
            day
        ).date()
    except ValueError:
        return None

# =========================
# DISCORD BOT
# =========================

intents = discord.Intents.default()

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

CHANNELS_FILE = "channels.json"


def load_channels():
    if not os.path.exists(CHANNELS_FILE):
        return {}

    with open(CHANNELS_FILE, "r") as f:
        return json.load(f)


def save_channels(data):
    with open(CHANNELS_FILE, "w") as f:
        json.dump(data, f, indent=4)


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    try:
        synced = await tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

    daily_reset.start()
    occurrence_tracker.start()


@tree.command(
    name="setchannel",
    description="Set the shard announcement channel"
)
@app_commands.checks.has_permissions(administrator=True)
async def setchannel(
    interaction: discord.Interaction,
    channel: discord.TextChannel
):
    data = load_channels()

    data[str(interaction.guild.id)] = channel.id

    save_channels(data)

    await interaction.response.send_message(
        f"Shard announcements will now be sent in {channel.mention}"
    )

#Shard Today
@tree.command(
    name="shardtoday",
    description="Show today's shard info"
)
async def shardtoday(interaction: discord.Interaction):
    await interaction.response.send_message(generate_message())

# Predict Shard
@tree.command(
    name="predictshard",
    description="Predict shard information for any date"
)
@app_commands.describe(
    day="Day",
    month="Month",
    year="Year"
)
async def predictshard(
    interaction: discord.Interaction,
    day: app_commands.Range[int, 1, 31],
    month: app_commands.Range[int, 1, 12],
    year: app_commands.Range[int, 2020, 2035]
):
    target_date = validate_date(
        day,
        month,
        year
    )

    if target_date is None:
        await interaction.response.send_message(
            "That date does not exist."
        )
        return

    await interaction.response.send_message(
        generate_message(
            target_date=target_date
        )
    )

@tasks.loop(minutes=1)
async def daily_reset():
    now = datetime.now(PST)

    if now.hour == 0 and now.minute == 0:

        data = load_channels()

        for guild_id, channel_id in data.items():

            channel = client.get_channel(channel_id)

            if channel:
                try:
                    await channel.send(generate_message())
                except Exception as e:
                    print(
                        f"Failed sending to {channel_id}: {e}"
                    )

@tasks.loop(seconds=30)
async def occurrence_tracker():

    now = datetime.now(PST)

    today = now.date()

    area = get_area(today)
    event_group = get_event_group(today)

    if not has_event(today, event_group):
        return

    occurrences = OCCURRENCES[event_group]

    data = load_channels()

    for i, (hour, minute, second) in enumerate(occurrences, start=1):

        start_dt = datetime(
            today.year,
            today.month,
            today.day,
            hour,
            minute,
            second,
            tzinfo=PST
        )

        end_dt = start_dt + timedelta(
            hours=3,
            minutes=51,
            seconds=20
        )

        start_key = f"{today}_{i}_start"
        end_key = f"{today}_{i}_end"

        # START MESSAGE
        if (
            start_dt <= now < start_dt + timedelta(seconds=30)
            and start_key not in sent_occurrences
        ):

            sent_occurrences.add(start_key)

            for guild_id, channel_id in data.items():

                channel = client.get_channel(channel_id)

                if channel:
                    try:
                        await channel.send(
                            f"Shard occurrence started.\n\n"
                            f"{generate_message(highlight_occurrence=i)}"
                        )
                    except Exception as e:
                        print(e)

        # END MESSAGE
        if (
            end_dt <= now < end_dt + timedelta(seconds=30)
            and end_key not in finished_occurrences
        ):

            finished_occurrences.add(end_key)

            ordinal_text = (
                "1st" if i == 1 else
                "2nd" if i == 2 else
                "3rd"
            )

            for guild_id, channel_id in data.items():

                channel = client.get_channel(channel_id)

                if channel:
                    try:
                        await channel.send(
                            f"{ordinal_text} occurrence is finished."
                        )
                    except Exception as e:
                        print(e)

client.run(TOKEN)