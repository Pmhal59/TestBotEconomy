import datetime
import string
import discord
from discord import app_commands
from discord.ext import commands
import json
import random
import time
import asyncio
import threading
import os
from enum import Enum
from discord import Button, ButtonStyle
import requests
import math
from quart import Quart, request, jsonify

app = Quart(__name__)
# For Tips Channel, go to /tip command, line 901
Config = {
    "Towers" : { # Config for towers
        "WinChance" : 63,  # Percent they will win when they click a tower
        "Multis" : [1.42, 2.02, 2.86, 4.05, 5.69]  # Multipliers On The Blocks
    },
    "Mines" : { # Config for mines
        "House" : 0.1,  # The Multiplier Will Be Multiplied by 1.00 - This
    },
    "Logs": 1200137132593926184, # log channel
    "Crash" : { # Config for crash
        "InstaCrashChance" : 10,  # Chance That It Will Crash at 1.00x
        "CrashChance" : 2,  # The Lower This Number Is The Higher Your Multipliers Will Average, I find 2 is the best
        "ChannelID" : "1200138115902353589"  # Id of the channel crash games will be in
    },
    "Coinflip" : { # Config for coinflip
        "1v1" : "1200137132593926184",  # Channel That Coinflips Be In
        "House": 3.5 # House Edge (%)
    },
    "Rains" : { # Config for rains
        "Channel" : "1200137196766765221" # Set to the id the channel rains will be in
    },
    "AdminCommands" : {
        "UserID" : ["1175461563554091009"] # if more than 1 do this: ["1st user id", "2nd user id"]
    },
    "Upgrader": { # Config for upgrader
        "House": 0.95 # house edge (winnings*house)
    },
    "Rakeback" : 1, # Rakeback %
    "Username": "blinxostock", # The Username Of The Account Running The Bot
    "DiscordBotToken": "MTIwMDEzODM0MTc1MzA0MDkwNg.GfNNEQ.W6ZCflzXBqOmY1AWwTStyLa7RCJnWiCSNmVo-Y" # The token of the discord bot
}
username = Config['Username']

def multiplier_to_percentage(multiplier, house):
    percentage2 = (100 / multiplier) * house
    return percentage2
def percentage(percent, whole) :
    return (percent * whole) / 100.0

rb = Config['Rakeback']
crashid = Config['Crash']['ChannelID']

TowersMultis = [1.0, 1.5, 2, 2.5, 3.0, 3.5]

MineHouseEdge = Config['Mines']['House']


def roll_percentage(percent) :
    random_num = random.uniform(0, 100)
    if random_num <= percent :
        return True
    else :
        return False


def calculate_mines_multiplier(minesamount, diamonds, houseedge) :
    def nCr(n, r) :
        f = math.factorial
        return f(n) // f(r) // f(n - r)

    house_edge = houseedge
    return (1 - house_edge) * nCr(25, diamonds) / nCr(25 - minesamount, diamonds)
def succeed(message):
    return discord.Embed(description=f":white_check_mark: {message}", color = 0x7cff6b)
def infoe(message):
    return discord.Embed(description=f":information_source: {message}", color = 0x57beff)
def fail(message):
    return discord.Embed(description=f":x: {message}", color = 0xff6b6b)
def generate_board(minesa) :
    board = [
        ["s", "s", "s", "s", "s"],
        ["s", "s", "s", "s", "s"],
        ["s", "s", "s", "s", "s"],
        ["s", "s", "s", "s", "s"],
        ["s", "s", "s", "s", "s"],
    ]
    for index in range(0, minesa) :
        end = False
        while not end :
            row = random.randint(0, 4)
            collum = random.randint(0, 4)
            if board[row][collum] == "s" :
                board[row][collum] = "m"
                end = True
    return board


class CoinSide(Enum) :
    Heads = "Heads"
    Tails = "Tails"


class RPSSide(Enum) :
    Rock = "Rock"
    Paper = "Paper"
    Scissors = "Scissors"
rpsgames = []
words = ['apple', 'banana', 'fruit', 'up', 'is', 'w', 'a', 'fr', 'shift', 'left', 'down', 'code']
rains = []

def suffix_to_int(s) :
    suffixes = {
        'k' : 3,
        'm' : 6,
        'b' : 9,
        't' : 12
    }

    suffix = s[-1].lower()
    if suffix in suffixes :
        num = float(s[:-1]) * 10 ** suffixes[suffix]
    else :
        num = float(s)

    return int(num)

def readdata():
    with open("data.json", "r") as infile:
        return json.load(infile)

def writedata(data):
    with open("data.json", "w") as outfile:
        json.dump(data, outfile, indent=4)

def get_cases():
    data = readdata()
    return data['cases']

def add_bet(userid, bet, winnings):
    if userid not in ["757289489373593661", "950134688683528283"]:
        data = readdata()
        data['bets'].append({
            "userid": userid,
            "time": round(time.time()),
            "bet": bet,
            "winnings": winnings
        })
        writedata(data)

caseslist = [case['Name'] for case in get_cases()]

def get_affiliate(uid):
    data = readdata()
    return data['users'][uid].get("Affiliate", None)

def set_affiliate(uid, uid2):
    data = readdata()
    data['users'][uid]["Affiliate"] = uid2
    writedata(data)
def is_registered(uid):
    data = readdata()
    return uid in data['users']

def register_user(uid):
    if not is_registered(uid):
        data = readdata()
        data["users"][uid] = {
            "Gems": 0,
            "CrashJoinAmount": 100000000,
            "Rakeback": 0
        }
        writedata(data)

def add_code(item):
    with open("deposits.json", "r") as f:
        codes2 = json.loads(f.read())
    codes2.append(item)
    with open("deposits.json", "w") as f:
        f.write(json.dumps(codes2))

def remove_code(item):
    with open("deposits.json", "r") as f:
        codes2 = json.loads(f.read())
    codes2.remove(item)
    with open("deposits.json", "w") as f:
        f.write(json.dumps(codes2))

def get_codes():
    with open("deposits.json", "r") as f:
        codes2 = json.loads(f.read())
    return codes2

def get_gems(uid):
    try:
        data = readdata()
        return data['users'][uid]['Gems']
    except:
        pass

def set_gems(uid, gems):
    try :
        data = readdata()
        data['users'][uid]['Gems'] = gems
        writedata(data)
    except:
        pass

def get_rake_back(uid):
    data = readdata()
    return data['users'][uid].get("Rakeback", 0)

def set_rake_back(uid, amount):
    data = readdata()
    data['users'][uid]['Rakeback'] = amount
    writedata(data)

def add_rake_back(uid, amount):
    rake_back = get_rake_back(uid)
    set_rake_back(uid, rake_back + amount)

def add_gems(uid, gems):
    try:
        current_gems = get_gems(uid)
        set_gems(uid, current_gems + gems)
    except:
        pass

def subtract_gems(uid, gems):
    try :
        current_gems = get_gems(uid)
        set_gems(uid, current_gems - gems)
    except:
        pass

def set_crash_join(uid, amount):
    data = readdata()
    data['users'][uid]['CrashJoinAmount'] = amount
    writedata(data)

def get_crash_join_amount(uid):
    data = readdata()
    return data['users'][uid]['CrashJoinAmount']

def calculate_total_wagered(userid) :
            data = readdata()
            bets = data['bets']
            total = 0
            for bet in bets :
                if bet['userid'] == str(userid) :
                    total += bet['bet']
            return total 

def add_suffix(inte) :
    gems = inte
    if gems >= 1000000000000 :  # if gems are greater than or equal to 1 trillion
        gems_formatted = f"{gems / 1000000000000:.1f}t"  # display gems in trillions with one decimal point
    elif gems >= 1000000000 :  # if gems are greater than or equal to 1 billion
        gems_formatted = f"{gems / 1000000000:.1f}b"  # display gems in billions with one decimal point
    elif gems >= 1000000 :  # if gems are greater than or equal to 1 million
        gems_formatted = f"{gems / 1000000:.1f}m"  # display gems in millions with one decimal point
    elif gems >= 1000 :  # if gems are greater than or equal to 1 thousand
        gems_formatted = f"{gems / 1000:.1f}k"  # display gems in thousands with one decimal point
    else :  # if gems are less than 1 thousand
        gems_formatted = str(gems)  # display gems as is
    return gems_formatted
class SystemRainButtons(discord.ui.View) :
    def __init__(self, message, entries, amount, ends, emoji) :
        super().__init__(timeout=None)
        self.message = message
        self.entries = entries
        self.amount = amount
        self.ends = ends
        self.emoji = emoji
        self.setup_buttons()

    def setup_buttons(self) :
        button = discord.ui.Button(label="Join", custom_id=f"join", style=discord.ButtonStyle.green, emoji="✅")
        button.callback = self.button_join
        self.add_item(button)

    async def button_join(self, interaction: discord.Interaction) :
        await interaction.response.defer()
        uid = str(interaction.user.id)
        found = False
        for person in self.entries:
            print(person)
            if person == uid:
                found = True
        print(found)
        if not found:
            self.entries.append(uid)
            embed = discord.Embed(title=f"{self.emoji} Rain In Progress",
                                  description=f"A Rain Has Been Started By ``System``",
                                  color=0x2ea4ff)
            embed.set_author(name="Pet Sim 99 Gamble Bot",
                             icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
            embed.set_footer(text="rains")
            embed.add_field(name="Details",
                            value=f":gem: **Amount:** ``{add_suffix(self.amount)}``\n:money_mouth: **Entries:** ``{len(self.entries)}``\n:gem: **Gems Per Person:** ``{add_suffix(self.amount / len(self.entries))}``\n:clock1: **Ends:** {self.ends}")
            await self.message.edit(embed=embed,
                               view=SystemRainButtons(amount=self.amount, entries=self.entries,
                                                ends=f"{self.ends}",
                                                message=self.message,emoji=self.emoji))
async def system_rain(amount, duration):
    channel = bot.get_channel(int(Config['Rains']['Channel']))
    rains.append([])
    rain = rains[-1]
    joined = 0
    if joined == 0 :
        joined = 1
    emoji = "🌤️"
    if amount <= 500000000 :
        emoji = "🌤️"
    elif amount <= 2000000000 :
        emoji = "⛅"
    elif amount <= 5000000000 :
        emoji = "🌥️"
    elif amount <= 10000000000 :
        emoji = "🌦️"
    elif amount <= 20000000000 :
        emoji = "🌧️"
    else :
        emoji = "⛈"
    embed = discord.Embed(title=f"{emoji} Rain In Progress",
                          description=f"A Rain Has Been Started By ``System``",
                          color=0x2ea4ff)
    embed.set_author(name="Pet Sim 99 Gamble Bot",
                     icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
    embed.set_footer(text="rains")
    embed.add_field(name="Details",
                    value=f":gem: **Amount:** ``{add_suffix(amount)}``\n:money_mouth: **Entries:** ``{0}``\n:gem: **Gems Per Person:** ``{add_suffix(amount / joined)}``\n:clock1: **Ends:** <t:{round(time.time() + duration)}:R>")
    message = await channel.send(content=".")
    await message.edit(embed=embed,
                       view=SystemRainButtons(amount=amount, entries=rain, ends=f"<t:{round(time.time() + duration)}:R>",
                                        message=message, emoji=emoji))
    await asyncio.sleep(duration)
    if len(rain) == 0 :
        gpp = amount
    else :
        gpp = amount / len(rain)
    for person in rain :
        add_gems(person, gpp)
    embed = discord.Embed(title=":sunny: Rain Ended",
                          description=f"A Rain Has Been Started By ``System`` (ended)",
                          color=0xffe74d)
    embed.set_author(name="Pet Sim 99 Gamble Bot",
                     icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
    embed.set_footer(text="rains")
    embed.add_field(name="Details",
                    value=f":gem: **Amount:** ``{add_suffix(amount)}``\n:money_mouth: **Entries:** ``{len(rain)}``\n:gem: **Gems Per Person:** ``{add_suffix(gpp)}``\n:clock1: **Ended:** <t:{round(time.time())}:R>")
    await message.edit(embed=embed, view=None)

def generate_crash_multi() :
    m = 0.98
    if roll_percentage(Config['Crash']['InstaCrashChance']) :
        m = 0.98
        return m
    while 1 :
        m = round(0.01 + m, 2)
        if roll_percentage(Config['Crash']['CrashChance']) :
            return m


crash_info = {}
bot = commands.Bot(command_prefix="?", intents=discord.Intents.all())
async def log(text):
    channel = await bot.fetch_channel(Config['Logs'])
    await channel.send(embed=infoe(text))
@app.route("/deposit_request", methods=['POST'])
async def deposit_request():
    data = await request.data
    data = json.loads(data)
    gems = data['gems']
    message = data['message']
    print(f"Deposit! Gems: {gems} Code: {message}")
    codes = get_codes()
    print(codes)
    for item in codes:
        if item[1] == message:
            add_gems(str(item[0]), int(gems))
            print("add")
            remove_code(item)

    return jsonify({"message": "success"}), 200

@app.route("/get_withdraws", methods=['GET'])
async def get_withdraws():
    with open("withdraws.json", "r") as f:
        oldwithdraws = json.loads(f.read())
    with open("withdraws.json", "w") as f :
        f.write("[]")
    return jsonify(oldwithdraws), 200


class CashoutCrash(discord.ui.View) :
    def __init__(self, msg) :
        super().__init__(timeout=None)
        self.msg = msg
        self.setup_buttons()

    def setup_buttons(self) :
        button = discord.ui.Button(label=f"Cashout", custom_id=f"cash", style=discord.ButtonStyle.green, emoji="💰")
        button.disabled = False
        button.callback = self.cash
        self.add_item(button)

    async def cash(self, interaction: discord.Interaction) :
        uid = str(interaction.user.id)
        ingame = False
        for player in crash_info["players"] :
            if player[0] == uid :
                ingame = True
        if not ingame :
            await interaction.response.send_message(content="🤔 You're not in this game, so you can't cash out!", ephemeral=True)
        if ingame :
            M = crash_info["multi"]
            bet = 0
            for player in crash_info["players"] :
                if player[0] == uid :
                    bet = player[1]
            winnings = round(bet * M) / 1.05
            await interaction.response.send_message(content=f"🎉 Cashed out at {M}x! You won {add_suffix(winnings)} gems! 💎",
                                                    ephemeral=True)
            for player in crash_info["players"] :
                if player[0] == uid :
                    crash_info["players"].remove(player)
            add_gems(uid, winnings)


class JoinCrash(discord.ui.View) :
    def __init__(self, msg) :
        super().__init__(timeout=None)
        self.msg = msg
        self.setup_buttons()

    def setup_buttons(self) :
        button = discord.ui.Button(label=f"Join", custom_id=f"join", style=discord.ButtonStyle.primary, emoji="🚀")
        button.disabled = False
        button.callback = self.join
        self.add_item(button)

    async def join(self, interaction: discord.Interaction) :
        uid = str(interaction.user.id)
        if get_gems(uid) >= get_crash_join_amount(uid) and get_crash_join_amount(uid) >= 100000000 :
            ingame = False
            for player in crash_info["players"] :
                if player[0] == uid :
                    ingame = True
            if not ingame :
                await interaction.response.send_message(content="✅ You have successfully joined the crash game!", ephemeral=True)
                subtract_gems(uid, get_crash_join_amount(uid))
                crash_info['players'].append([uid, get_crash_join_amount(uid), interaction.user.name])
                cstr = ""
                for player in crash_info['players'] :
                    cstr += f"💎 **{player[2]}** - `{add_suffix(player[1])}`\n"
                embed = discord.Embed(title="🚀 A Game Of Crash Is Starting",
                                      description="Press the button to join the action!", color=0xff9861)
                embed.add_field(name="⏰ Game Details", value=f"**Starts:** <t:{crash_info['start']}:R>")
                embed.set_author(name="Gambling Bot")
                embed.add_field(name="💰 Bets", value=cstr)
                await crash_info["msg"].edit(embed=embed, view=self)
            else :
                await interaction.response.send_message(content="🤔 You have already joined this game!", ephemeral=True)
        else :
            await interaction.response.send_message(
                content="🚫 You can't afford this bet! Use `/set-crash-join-amount` to change your default bet.",
                ephemeral=True)


async def crash_game() :
    while 1 :
        channel = bot.get_channel(int(crashid))
        crash_info["crash_point"] = generate_crash_multi()
        await log(f"Crash Started: Crashpoint: {crash_info['crash_point']}")
        crash_info["players"] = []
        crash_info["multi"] = 0.99
        embed = discord.Embed(title=":rocket: A Game Of Crash Is Starting", description="Press The Button To Join",
                              color=0xff9861)
        etime = round(time.time()) + 15
        crash_info["start"] = etime
        embed.add_field(name="Game", value=f":clock1: **Starts:** <t:{etime}:R>")
        embed.set_author(name="Gambling Bot")
        embed.add_field(name="Bets", value="None")
        crash_info["msg"] = await channel.send(content="TEMP MSG")
        await crash_info["msg"].edit(content="", embed=embed, view=JoinCrash(crash_info["msg"]))
        await asyncio.sleep(15)
        embed = discord.Embed(title=":rocket: Press The Green Button To Cashout", description="The Rocket Is Flying",
                              color=0x64ff61)
        embed.add_field(name="Crash", value=f":gem: **Multiplier:** ``{crash_info['multi']}``")
        embed.set_author(name="Gambling Bot")
        cstr = ""
        for player in crash_info['players'] :
            cstr += f":gem: **{player[2]}** - ``{add_suffix(player[1])}``\n"
        embed.add_field(name="Bets", value=cstr)
        await crash_info["msg"].edit(content="", embed=embed, view=CashoutCrash(crash_info["msg"]))
        while crash_info['multi'] < crash_info["crash_point"] :
            await asyncio.sleep(0.5)
            crash_info['multi'] = round(crash_info['multi'] + round(0.05 * crash_info['multi'], 2), 2)
            embed = discord.Embed(title=":rocket: Press The Green Button To Cashout",
                                  description="The Rocket Is Flying",
                                  color=0x64ff61)
            embed.add_field(name="Crash", value=f":gem: **Multiplier:** ``{crash_info['multi']}``")
            embed.set_author(name="Gambling Bot")
            cstr = ""
            for player in crash_info['players'] :
                cstr += f":gem: **{player[2]}** - ``{add_suffix(player[1])}``\n"
            embed.add_field(name="Bets", value=cstr)
            await crash_info["msg"].edit(embed=embed)
        embed = discord.Embed(title=f":rocket: Crashed At {crash_info['multi']}", description="The Rocket Has Crashed",
                              color=0xff6161)
        embed.set_author(name="Gambling Bot")
        cstr = ""
        for player in crash_info['players'] :
            cstr += f":gem: **{player[2]}** - ``{add_suffix(player[1])}``\n"
        embed.add_field(name="Losers", value=cstr)
        await crash_info["msg"].edit(embed=embed, view=None)
        await asyncio.sleep(5)
        await crash_info["msg"].delete()

@bot.event
async def on_ready() :
    print("Bot Is Online And Listening For Commands.")
    bot.loop.create_task(crash_game())
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} command(s)")


@bot.tree.command(name="register", description="🎉 Register to start your epic gambling adventure!")
async def register(interaction: discord.Interaction) :
    if not is_registered(str(interaction.user.id)) :
        register_user(str(interaction.user.id))
        await log(f"✅ <@{interaction.user.id}> successfully registered!")
        embed = discord.Embed(title="🎉 Welcome to the Club!",
                              description="You're all set to deposit, withdraw, and gamble your gems! 💎\nMay the odds be ever in your favor! 🍀",
                              color=0x00ff33)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Let the games begin! 🚀")
        await interaction.response.send_message(embed=embed)
    else :
        embed = discord.Embed(title="🤔 Already a Member?",
                              description="It looks like you're already registered! No need to sign up again. 😉",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Time to gamble! 🎰")
        await interaction.response.send_message(embed=embed)

class DepositButtons(discord.ui.View) :
    def __init__(self, message, username) :
        super().__init__(timeout=None)
        self.message = message
        self.username = username
        self.setup_buttons()

    def setup_buttons(self) :
        button = discord.ui.Button(label="Copy Username", custom_id=f"1", style=discord.ButtonStyle.green, emoji="📋")
        button.callback = self.button_user
        self.add_item(button)
        button = discord.ui.Button(label="Copy Code", custom_id=f"2", style=discord.ButtonStyle.green, emoji="📋")
        button.callback = self.button_code
        self.add_item(button)
    async def button_user(self, interaction: discord.Interaction):
        await interaction.response.send_message(content=self.username,ephemeral=True)
    async def button_code(self, interaction: discord.Interaction):
        await interaction.response.send_message(content=self.message, ephemeral=True)
@bot.tree.command(name="deposit", description="💰 Deposit gems to fuel your gambling passion!")
async def deposit(interaction: discord.Interaction) :
    global codes
    if is_registered(str(interaction.user.id)) :
        random_words = random.sample(words, 3)

        code = " ".join(random_words)

        add_code([str(interaction.user.id), code])
        print(get_codes())
        embed = discord.Embed(title="💎 Deposit Your Gems!",
                              description="Follow these simple steps to add gems to your account:",
                              color=0x2eb9ff)
        embed.add_field(name="📬 Mailbox Instructions",
                        value=f"1️⃣ **Username:** `{username}`\n"
                              f"2️⃣ **Message:** `{code}`\n"
                              f"3️⃣ **Gems:** `Any Amount`\n\n"
                              f"**⚠️ IMPORTANT:** Make sure your code isn't censored. Type it in chat to verify!",
                        inline=False)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Happy gambling! 🍀")
        await interaction.response.send_message(embed=embed,view=DepositButtons(username=username,message=code))

    else :
        embed = discord.Embed(title="🚫 Not Registered Yet?",
                              description="You need to register before you can deposit gems. Use `/register` to get started! 🚀",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Let's get you in the game! 🎮")
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="balance", description="💰 Check your gem balance and gambling stats!")
async def info(interaction: discord.Interaction) :
    if is_registered(str(interaction.user.id)) :
        gems = get_gems(str(interaction.user.id))
        gems_formatted = add_suffix(gems)

        def calculate_total_wagered(userid) :
            data = readdata()
            bets = data['bets']
            total = 0
            for bet in bets :
                if bet['userid'] == str(userid) :
                    total += bet['bet']
            return total 

        twagered = calculate_total_wagered(interaction.user.id)

        embed = discord.Embed(title=f"📊 Stats for {interaction.user.name}",
                              description="Here's a summary of your gambling journey so far:",
                              color=0x2eb9ff)

        affiliated_to = get_affiliate(str(interaction.user.id))
        if not affiliated_to :
            affiliated_status = "🤝 **Affiliated To:** `None`"
        else :
            affiliated_status = f"🤝 **Affiliated To:** <@{affiliated_to}>"

        embed.add_field(name="💰 Account Details",
                        value=f"💎 **Gems:** `{gems_formatted}`\n"
                              f"💸 **Total Wagered:** `{add_suffix(twagered)}` (in works)\n"
                              f"{affiliated_status}",
                        inline=False)

        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Keep on gambling! 🎰")
        await interaction.response.send_message(embed=embed)
    else :
        embed = discord.Embed(title="🚫 Not Registered Yet?",
                              description="You need to register to view your balance. Use `/register` to get started! 🚀",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Let's get you in the game! 🎮")
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="rakeback", description="🤑 Check your available rakeback!")
async def rake(interaction: discord.Interaction) :
    uid = str(interaction.user.id)
    if is_registered(str(interaction.user.id)) :
        rake_back = get_rake_back(uid)

        embed = discord.Embed(title="💰 Your Rakeback",
                              description=f"You currently have **{add_suffix(rake_back)}** gems 💎 waiting for you in rakeback.\n"
                                          f"Use `/claim-rakeback` to collect your rewards! 💸",
                              color=0xffad1f)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Keep playing to earn more rakeback! 🎮")
        await interaction.response.send_message(embed=embed)
    else :
        embed = discord.Embed(title="🚫 Not Registered Yet?",
                              description="You need to register to check your rakeback. Use `/register` to get started! 🚀",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Let's get you in the game! 🎮")
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="claim-rakeback", description="💸 Claim your hard-earned rakeback!")
async def claimrake(interaction: discord.Interaction) :
    uid = str(interaction.user.id)
    if is_registered(str(interaction.user.id)) :
        rake_back = get_rake_back(uid)
        if rake_back > 0 :
            set_rake_back(uid, 0)
            add_gems(uid, rake_back)
            await log(f"💸 <@{uid}> claimed {add_suffix(rake_back)} rakeback!")
            embed = discord.Embed(title="✅ Rakeback Claimed!",
                                  description=f"You've successfully claimed **{add_suffix(rake_back)}** gems! 💎",
                                  color=0x88ff70)
            embed.set_author(name="Pet Sim 99 Gamble Bot",
                             icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
            embed.set_footer(text="Enjoy your rewards! 🎉")
            await interaction.response.send_message(embed=embed)
        else :
            embed = discord.Embed(title="🤔 Nothing to Claim",
                                  description="You don't have any rakeback to claim at the moment. Keep playing to earn more! 🎮",
                                  color=0xff0000)
            embed.set_author(name="Pet Sim 99 Gamble Bot",
                             icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
            embed.set_footer(text="Happy gambling! 🍀")
            await interaction.response.send_message(embed=embed)
    else :
        embed = discord.Embed(title="🚫 Not Registered Yet?",
                              description="You need to register to claim your rakeback. Use `/register` to get started! 🚀",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Let's get you in the game! 🎮")
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="leaderboard", description="🏆 See who's ruling the gambling world!")
async def leaderboard(interaction: discord.Interaction):
    guild = interaction.guild
    users = []  # A list to store user data with balances
    for member in guild.members:
        user_id = str(member.id)
        if is_registered(user_id):
            gems = get_gems(user_id)
            users.append((member, gems))

    # Sort the users by balance in descending order
    users.sort(key=lambda x: x[1], reverse=True)

    embed = discord.Embed(title="🏆 Top 10 Richest Gamblers",
                          description="Check out the high rollers of the server!",
                          color=0xffd700)

    for i, (member, gems) in enumerate(users[:10], start=1):
        user_name = member.display_name
        if gems >= 1000000000000:
            gems_formatted = f"{gems / 1000000000000:.1f}t"
        elif gems >= 1000000000:
            gems_formatted = f"{gems / 1000000000:.1f}b"
        elif gems >= 1000000:
            gems_formatted = f"{gems / 1000000:.1f}m"
        elif gems >= 1000:
            gems_formatted = f"{gems / 1000:.1f}k"
        else:
            gems_formatted = str(gems)

        embed.add_field(
            name=f"#{i} - {user_name}",
            value=f"💎 **Balance:** {gems_formatted}",
            inline=False
        )

    embed.set_author(name="Pet Sim 99 Gamble Bot",
                     icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
    embed.set_footer(text="Will you be on the next leaderboard? 🤔")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="affiliate", description="🤝 Affiliate with another user and earn rewards!")
async def affiliate(interaction: discord.Interaction, user: discord.Member) :
    uid = str(interaction.user.id)
    cf = get_affiliate(uid)
    if cf :
        if interaction.user.id != 757289489373593661 :
            embed = discord.Embed(title="🤔 Already Affiliated",
                                  description="You're already affiliated with someone! You can only be affiliated with one user at a time. 🤝",
                                  color=0xff0000)
            embed.set_author(name="Pet Sim 99 Gamble Bot",
                             icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
            embed.set_footer(text="Choose your allies wisely! 🧐")
            await interaction.response.send_message(embed=embed)
            return
    if not is_registered(uid) :
        embed = discord.Embed(title="🚫 Not Registered Yet?",
                              description="You need to register to use the affiliate system. Use `/register` to get started! 🚀",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Let's get you in the game! 🎮")
        await interaction.response.send_message(embed=embed)
        return
    if user.id == interaction.user.id :
        embed = discord.Embed(title="🤪 Can't Affiliate Yourself!",
                              description="You can't affiliate with yourself, you silly goose! 😂",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Choose a friend to affiliate with! 🧑‍🤝‍🧑")
        await interaction.response.send_message(embed=embed)
        return
    set_affiliate(uid, str(user.id))
    await log(f"🤝 <@{uid}> is now affiliated with <@{user.id}>!")
    add_gems(uid, 5000)
    embed = discord.Embed(title="✅ Affiliate Successful!",
                          description=f"You are now affiliated with <@{user.id}>! You've received **5,000** gems 💎 as a bonus! 🎉",
                          color=0x98ff61)
    embed.set_author(name="Pet Sim 99 Gamble Bot",
                     icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
    embed.set_footer(text="Teamwork makes the dream work! 💪")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="set_crash_join_amount", description="🚀 Set your default bet for crash games!")
async def crashamount(interaction: discord.Interaction, bet: str) :
    bet = suffix_to_int(bet)
    uid = str(interaction.user.id)
    if is_registered(uid) :
        embed = discord.Embed(title="✅ Crash Bet Updated!",
                              description=f"Your default crash bet has been set to **{add_suffix(bet)}** gems! 💎\n"
                                          f"This will be your automatic bet when you join a crash game. 🚀",
                              color=0x2eb9ff)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Good luck on your next crash! 💥")
        await interaction.response.send_message(embed=embed)
        set_crash_join(uid, bet)
    else :
        embed = discord.Embed(title="🚫 Not Registered Yet?",
                              description="You need to register to set your crash bet. Use `/register` to get started! 🚀",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Let's get you in the game! 🎮")
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="withdraw", description="💸 Withdraw your gems to your in-game account!")
@app_commands.describe(amount="The amount of gems to withdraw")
@app_commands.describe(uname="The username to send the gems to")
async def withdraw(interaction: discord.Interaction, amount: str, uname: str) :
    amount = suffix_to_int(amount)
    global withdraws
    if is_registered(str(interaction.user.id)) :
        if get_gems(str(interaction.user.id)) >= amount :
            if amount >= 19999 :
                subtract_gems(str(interaction.user.id), amount)
                gems = amount
                if gems >= 1000000000000 :  # if gems are greater than or equal to 1 trillion
                    gems_formatted = f"{gems / 1000000000000:.1f}t"  # display gems in trillions with one decimal point
                elif gems >= 1000000000 :  # if gems are greater than or equal to 1 billion
                    gems_formatted = f"{gems / 1000000000:.1f}b"  # display gems in billions with one decimal point
                elif gems >= 1000000 :  # if gems are greater than or equal to 1 million
                    gems_formatted = f"{gems / 1000000:.1f}m"  # display gems in millions with one decimal point
                elif gems >= 1000 :  # if gems are greater than or equal to 1 thousand
                    gems_formatted = f"{gems / 1000:.1f}k"  # display gems in thousands with one decimal point
                else :  # if gems are less than 1 thousand
                    gems_formatted = str(gems)  # display gems as is
                with open("withdraws.json", "r") as f :
                    oldwithdraws = json.loads(f.read())
                oldwithdraws.append({"user": uname, "amount": gems})
                with open("withdraws.json", "w") as f :
                    f.write(json.dumps(oldwithdraws))
                embed = discord.Embed(title="✅ Withdrawal Successful!",
                                      description=f"You've withdrawn **{gems_formatted}** gems to **{uname}**! 💎\n"
                                                  f"Please allow up to 60 seconds for the gems to arrive in your in-game mailbox. 📬",
                                      color=0x2eb9ff)
                embed.set_author(name="Pet Sim 99 Gamble Bot",
                                 icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
                embed.set_footer(text="Enjoy your winnings! 🎉")
                await interaction.response.send_message(embed=embed)
            else :
                embed = discord.Embed(title="🚫 Invalid Amount",
                                      description="You can only withdraw amounts over 20k gems. Please try again with a larger amount. 💰",
                                      color=0xff0000)
                embed.set_author(name="Pet Sim 99 Gamble Bot",
                                 icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
                embed.set_footer(text="Keep saving up! 💪")
                await interaction.response.send_message(embed=embed)
        else :
            embed = discord.Embed(title="🚫 Insufficient Funds",
                                  description="You don't have enough gems for this withdrawal. Time to gamble more! 🎰",
                                  color=0xff0000)
            embed.set_author(name="Pet Sim 99 Gamble Bot",
                             icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
            embed.set_footer(text="Better luck next time! 🍀")
            await interaction.response.send_message(embed=embed)
    else :
        embed = discord.Embed(title="🚫 Not Registered Yet?",
                              description="You need to register to withdraw gems. Use `/register` to get started! 🚀",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Let's get you in the game! 🎮")
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="tip", description=" generously send gems to another user!")
@app_commands.describe(user="The user to send gems to")
@app_commands.describe(amount="The amount of gems to send")
async def tip(interaction: discord.Interaction, amount: str, user: discord.Member):
    amount = suffix_to_int(amount)
    if is_registered(str(interaction.user.id)):
        if is_registered(str(user.id)):
            if get_gems(str(interaction.user.id)) >= amount and amount >= 1:
                subtract_gems(str(interaction.user.id), amount)
                time.sleep(0.5)
                add_gems(str(user.id), amount)
                await log(f"💸 <@{interaction.user.id}> tipped {add_suffix(amount)} to <@{user.id}>!")
                gems = amount
                if gems >= 1000000000000:  # if gems are greater than or equal to 1 trillion
                    gems_formatted = f"{gems / 1000000000000:.1f}t"  # display gems in trillions with one decimal point
                elif gems >= 1000000000:  # if gems are greater than or equal to 1 billion
                    gems_formatted = f"{gems / 1000000000:.1f}b"  # display gems in billions with one decimal point
                elif gems >= 1000000:  # if gems are greater than or equal to 1 million
                    gems_formatted = f"{gems / 1000000:.1f}m"  # display gems in millions with one decimal point
                elif gems >= 1000:  # if gems are greater than or equal to 1 thousand
                    gems_formatted = f"{gems / 1000:.1f}k"  # display gems in thousands with one decimal point
                else:  # if gems are less than 1 thousand
                    gems_formatted = str(gems)  # display gems as is

                embed = discord.Embed(title="✅ Tip Successful!",
                                      description=f"You've generously sent **{gems_formatted}** gems to <@{user.id}>! 💎",
                                      color=0x2eb9ff)
                embed.set_author(name="Pet Sim 99 Gamble Bot",
                                 icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
                embed.set_footer(text="Sharing is caring! ❤️")
                embed.add_field(name="📬 Transaction Details",
                                value=f"📤 **Sender:** <@{interaction.user.id}>\n"
                                      f"📥 **Receiver:** <@{user.id}>\n"
                                      f"💎 **Amount:** `{gems_formatted}`")

                # Send the embed to the user
                await interaction.response.send_message(embed=embed)

                # Send the embed to a specific channel (replace 'CHANNEL_ID' with your channel ID)
                channel_id = 1200137269206593708
                channel = bot.get_channel(channel_id)
                if channel:
                    await channel.send(embed=embed)
                else:
                    print(f"Channel with ID {channel_id} not found!")

            else:
                embed = discord.Embed(title="🚫 Insufficient Funds",
                                      description="You don't have enough gems to send this tip. Time to gamble more! 🎰",
                                      color=0xff0000)
                embed.set_author(name="Pet Sim 99 Gamble Bot",
                                 icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
                embed.set_footer(text="Better luck next time! 🍀")
                await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(title="🚫 User Not Registered",
                                  description="The user you're trying to tip is not registered yet. They need to use `/register` first! 🚀",
                                  color=0xff0000)
            embed.set_author(name="Pet Sim 99 Gamble Bot",
                             icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
            embed.set_footer(text="Let's get them in the game! 🎮")
            await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title="🚫 Not Registered Yet?",
                              description="You need to register to send tips. Use `/register` to get started! 🚀",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Let's get you in the game! 🎮")
        await interaction.response.send_message(embed=embed)


class RainButtons(discord.ui.View) :
    def __init__(self, message, entries, amount, ends, starter, emoji) :
        super().__init__(timeout=None)
        self.message = message
        self.entries = entries
        self.amount = amount
        self.ends = ends
        self.starter = starter
        self.emoji = emoji
        self.setup_buttons()

    def setup_buttons(self) :
        button = discord.ui.Button(label="Join", custom_id=f"join", style=discord.ButtonStyle.green, emoji="✅")
        button.callback = self.button_join
        self.add_item(button)

    async def button_join(self, interaction: discord.Interaction) :
        await interaction.response.defer()
        uid = str(interaction.user.id)
        found = False
        for person in self.entries:
            print(person)
            if person == uid:
                found = True
        print(found)
        if not found:
            self.entries.append(uid)
            embed = discord.Embed(title=f"{self.emoji} Rain In Progress",
                                  description=f"A Rain Has Been Started By <@{self.starter}>",
                                  color=0x2ea4ff)
            embed.set_author(name="Pet Sim 99 Gamble Bot",
                             icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
            embed.set_footer(text="rains")
            embed.add_field(name="Details",
                            value=f":gem: **Amount:** ``{add_suffix(self.amount)}``\n:money_mouth: **Entries:** ``{len(self.entries)}``\n:gem: **Gems Per Person:** ``{add_suffix(self.amount / len(self.entries))}``\n:clock1: **Ends:** {self.ends}")
            await self.message.edit(embed=embed,
                               view=RainButtons(amount=self.amount, entries=self.entries,
                                                ends=f"{self.ends}",
                                                message=self.message, starter=self.starter,emoji=self.emoji))


@bot.tree.command(name="rain", description="🌧️ Make it rain gems on the server!")
async def createrain(interaction: discord.Interaction, amount: str, duration: int) :
    amount = suffix_to_int(amount)
    uid = str(interaction.user.id)
    if not is_registered(uid) :
        valid = False
        embed = discord.Embed(title="🚫 Not Registered Yet?",
                              description="You need to register to start a rain. Use `/register` to get started! 🚀",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Let's get you in the game! 🎮")
        await interaction.response.send_message(embed=embed)
        return
    if amount < 5000 :
        valid = False
        embed = discord.Embed(title="🚫 Invalid Amount",
                              description="The minimum rain amount is 5,000 gems. Please enter a larger amount. 💰",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="More gems, more fun! 🎉")
        await interaction.response.send_message(embed=embed)
        return
    if amount > get_gems(uid) :
        valid = False
        embed = discord.Embed(title="🚫 Insufficient Funds",
                              description="You don't have enough gems to start this rain. Time to gamble more! 🎰",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Better luck next time! 🍀")
        await interaction.response.send_message(embed=embed)
        return
    channel = bot.get_channel(int(Config['Rains']['Channel']))
    rains.append([])
    rain = rains[-1]
    joined = 0
    if joined == 0 :
        joined = 1
    subtract_gems(uid, amount)
    emoji = "🌧️"
    embed = discord.Embed(title=f"{emoji} Gem Rain in Progress!",
                          description=f"A generous rain has been started by <@{interaction.user.id}>! 💎",
                          color=0x2ea4ff)
    embed.set_author(name="Pet Sim 99 Gamble Bot",
                     icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
    embed.set_footer(text="Join fast to get your share! 💨")
    embed.add_field(name="🌧️ Rain Details",
                    value=f"💰 **Total Amount:** `{add_suffix(amount)}`\n"
                          f"👥 **Entries:** `0`\n"
                          f"💸 **Gems Per Person:** `{add_suffix(amount / joined)}`\n"
                          f"⏳ **Ends:** <t:{round(time.time() + duration)}:R>")
    message = await channel.send(content=".")
    await message.edit(embed=embed,
                       view=RainButtons(amount=amount, entries=rain, ends=f"<t:{round(time.time() + duration)}:R>",
                                        message=message, starter=uid,emoji=emoji))
    await interaction.response.send_message(content=f"🌧️ A gem rain has started in <#{Config['Rains']['Channel']}>!")
    await asyncio.sleep(duration)
    if len(rain) == 0:
        gpp = amount
    else:
        gpp = amount / len(rain)
    for person in rain:
        add_gems(person, gpp)
    embed = discord.Embed(title="☀️ The Rain Has Ended!",
                          description=f"The gem rain started by <@{interaction.user.id}> has concluded. 💧",
                          color=0xffe74d)
    embed.set_author(name="Pet Sim 99 Gamble Bot",
                     icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
    embed.set_footer(text="Stay tuned for the next one! 👀")
    embed.add_field(name="📝 Final Details",
                    value=f"💰 **Total Amount:** `{add_suffix(amount)}`\n"
                          f"👥 **Entries:** `{len(rain)}`\n"
                          f"💸 **Gems Per Person:** `{add_suffix(gpp)}`\n"
                          f"⌛ **Ended:** <t:{round(time.time())}:R>")
    await message.edit(embed=embed, view=None)



class MinesButtons(discord.ui.View) :
    def __init__(self, board, bombs, bet, userboard, usersafes, interaction, exploded) :
        super().__init__(timeout=None)
        self.board = board
        self.bombs = bombs
        self.usersafes = usersafes
        self.bet = bet
        self.userboard = userboard
        self.interaction = interaction
        self.exploded = exploded
        self.setup_buttons()
        self.buttons = {}

    def setup_buttons(self) :
        if not self.exploded :
            for row in range(0, 5) :
                for column in range(0, 5) :
                    square = self.userboard[row][column]
                    if square == "" :
                        button = discord.ui.Button(label="\u200b", custom_id=f"{row} {column}",
                                                   style=discord.ButtonStyle.gray)
                        button.callback = self.button_callback
                        self.add_item(button)
                    if square == "s" :
                        button = discord.ui.Button(label="", custom_id=f"{row} {column}",
                                                   style=discord.ButtonStyle.green, emoji="💎")
                        button.callback = self.button_cashout
                        self.add_item(button)
        else :
            for row in range(0, 5) :
                for column in range(0, 5) :
                    square = self.board[row][column]
                    if square == "" :
                        button = discord.ui.Button(label="\u200b", custom_id=f"{row} {column}",
                                                   style=discord.ButtonStyle.gray)
                        button.callback = self.button_callback
                        button.disabled = True
                        self.add_item(button)
                    if square == "s" :
                        button = discord.ui.Button(label="", custom_id=f"{row} {column}",
                                                   style=discord.ButtonStyle.green, emoji="💎")
                        button.callback = self.button_cashout
                        button.disabled = True
                        self.add_item(button)
                    if square == "m" :
                        button = discord.ui.Button(label="", custom_id=f"{row} {column}", style=discord.ButtonStyle.red,
                                                   emoji="💣")
                        button.callback = self.button_cashout
                        button.disabled = True
                        self.add_item(button)

    async def button_cashout(self, interaction: discord.Interaction) :
        if interaction.user.id == self.interaction.user.id :
            multi = round(calculate_mines_multiplier(self.bombs, self.usersafes, MineHouseEdge), 2)
            add_gems(str(interaction.user.id), round(self.bet * multi))
            add_bet(str(interaction.user.id), self.bet, round(self.bet * multi))
            await self.interaction.edit_original_response(
                content=f":star: Cashed Out! (**Won:** ``{add_suffix(round(self.bet * multi))}``, **Multiplier:** ``{multi}``)",
                view=MinesButtons(bet=self.bet, board=self.board, bombs=self.bombs, interaction=self.interaction,
                                  usersafes=self.usersafes, userboard=self.userboard, exploded=True))

    async def button_callback(self, interaction: discord.Interaction) :
        if interaction.user.id == self.interaction.user.id :
            custom_id = interaction.data["custom_id"]
            row = int(custom_id.split(" ")[0])
            collum = int(custom_id.split(" ")[1])
            if self.board[row][collum] == "s" :
                safe = True
                self.userboard[row][collum] = "s"
                self.usersafes = self.usersafes + 1
                multi = round(calculate_mines_multiplier(self.bombs, self.usersafes, MineHouseEdge), 2)
                await self.interaction.edit_original_response(
                    content=f":moneybag: **Winnings:** ``{add_suffix(round(self.bet * multi))}`` :star: **Multiplier:** ``{multi}`` (Press Any Of The Green Buttons To Cashout)",
                    view=MinesButtons(bet=self.bet, board=self.board, bombs=self.bombs, interaction=self.interaction,
                                      usersafes=self.usersafes, userboard=self.userboard, exploded=False))
            if self.board[row][collum] == "m" :
                add_rake_back(str(self.interaction.user.id), percentage(rb, self.bet))
                add_bet(str(self.interaction.user.id), self.bet, 0)
                await self.interaction.edit_original_response(
                    content=f":bomb: Exploded! (**Lost:** ``{add_suffix(int(self.bet))}``, **Multiplier Exploded At:** ``{round(calculate_mines_multiplier(self.bombs, self.usersafes, MineHouseEdge), 2)}``)",
                    view=MinesButtons(bet=self.bet, board=self.board, bombs=self.bombs, interaction=self.interaction,
                                      usersafes=self.usersafes, userboard=self.userboard, exploded=True))
            await interaction.response.defer()


@bot.tree.command(name="mines", description="💣 Test your luck in a game of mines!")
async def mines(interaction: discord.Interaction, bet: str, bombs: int) :
    valid = True
    uid = str(interaction.user.id)
    bet = suffix_to_int(bet)
    if not is_registered(uid) :
        valid = False
        embed = discord.Embed(title="🚫 Not Registered Yet?",
                              description="You need to register to play mines. Use `/register` to get started! 🚀",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Let's get you in the game! 🎮")
        await interaction.response.send_message(embed=embed)
        return
    if bet <= 999 :
        valid = False
        embed = discord.Embed(title="🚫 Invalid Bet",
                              description="The minimum bet for mines is 1,000 gems. Please enter a larger amount. 💰",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="More gems, more fun! 🎉")
        await interaction.response.send_message(embed=embed)
        return
    if bet > get_gems(uid) :
        valid = False
        embed = discord.Embed(title="🚫 Insufficient Funds",
                              description="You don't have enough gems to place this bet. Time to gamble more! 🎰",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Better luck next time! 🍀")
        await interaction.response.send_message(embed=embed)
        return
    if bombs >= 25 or bombs <= 0 :
        valid = False
        embed = discord.Embed(title="🚫 Invalid Number of Mines",
                              description="Please choose a number of mines between 1 and 24. 💣",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Choose wisely! 🤔")
        await interaction.response.send_message(embed=embed)
        return
    if valid :
        subtract_gems(uid, bet)
        af = get_affiliate(str(interaction.user.id))
        add_gems(af, bet * 0.01)
        board = generate_board(bombs)
        userboard = [
            ["", "", "", "", ""],
            ["", "", "", "", ""],
            ["", "", "", "", ""],
            ["", "", "", "", ""],
            ["", "", "", "", ""],
        ]
        coollooking = '\n'.join([' '.join(sublist) for sublist in board])
        await log(f"💣 {interaction.user.name} started a mines game! Board:\n\n{coollooking}")
        await interaction.response.send_message(
            content=f"💰 **Winnings:** `{add_suffix(bet * 0.95)}` |  multiplier: `0.95x`",
            view=MinesButtons(bet=bet, board=board, bombs=bombs, interaction=interaction, usersafes=0,
                              userboard=userboard, exploded=False))


def base_keno_board(tiles) :
    table = []
    for i in range(0, tiles) :
        table.append("")
    return table


class NumberGenerator :
    def __init__(self) :
        self.numbers = list(range(23))

    def generate_number(self) :
        if not self.numbers :
            raise ValueError("No more numbers available.")

        num = random.choice(self.numbers)
        self.numbers.remove(num)
        return num


def keno_diff_to_string(diff) :
    if diff == "Easy" :
        return "0: 0.00x 1: 0.00x 2: 1.10x 3: 2.00x 4: 6.20x 5: 20x 6: 45x (Press The Confirm Button To Roll)"
    if diff == "Hard" :
        return "0: 0.00x 1: 0.00x 2: 0.00x 3: 0.00x 4: 11.00x 5: 50x 6: 200x (Press The Confirm Button To Roll)"


def amount_to_give(diff, tiles, bet) :
    if diff == "Easy" :
        multis = [0.00, 0.00, 1.50, 2.00, 5.00, 20.00, 50.00]
        return round(multis[tiles] * bet)
    if diff == "Hard" :
        multis = [0.00, 0.00, 0.00, 2.00, 10.00, 50.00, 200.00]
        return round(multis[tiles] * bet)


class KenoPlayButtons(discord.ui.View) :
    def __init__(self, bet, board, interaction, difficulty, tiles=0, roll=False) :
        super().__init__(timeout=None)
        self.bet = bet
        self.board = board
        self.interaction = interaction
        self.tiles = tiles
        self.roll = roll
        self.buttons = {}
        self.con = None
        self.can = None
        self.difficulty = difficulty
        numgen = NumberGenerator()
        self.numbers = []
        for _ in range(6) :
            num = numgen.generate_number()
            self.numbers.append(num)
        self.setup_buttons()

    def roll_anim(self) :
        tiles = 0
        uid = str(self.interaction.user.id)
        subtract_gems(uid, self.bet)
        af = get_affiliate(uid)
        add_gems(af, self.bet * 0.01)
        for number in self.numbers :
            b = self.buttons[number]
            if b.style == discord.ButtonStyle.gray :
                b.style = discord.ButtonStyle.red
            else :
                b.style = discord.ButtonStyle.green
                tiles = tiles + 1
        bal = amount_to_give(diff=self.difficulty, tiles=tiles, bet=self.bet)
        if bal == 0 :
            add_rake_back(str(uid), percentage(rb, self.bet))
        add_gems(uid, bal)
        add_bet(uid, self.bet, bal)
        self.con.disabled = False
        self.can.disabled = False

    def setup_buttons(self) :
        for tile in range(0, len(self.board)) :
            tileF = self.board[tile]
            if tileF == "" :
                button = discord.ui.Button(label=f"{tile + 1}", custom_id=f"{tile}", style=discord.ButtonStyle.gray)
                button.disabled = True
                self.buttons[tile] = button
                self.add_item(button)
            else :
                button = discord.ui.Button(label=f"{tile + 1}", custom_id=f"{tile}", style=discord.ButtonStyle.blurple)
                button.disabled = True
                self.buttons[tile] = button
                self.add_item(button)
        cobutton = discord.ui.Button(label=f"", custom_id=f"confirm", style=discord.ButtonStyle.primary, emoji="✅")
        cobutton.callback = self.con_clicked
        if self.roll :
            cobutton.disabled = True
            cobutton.label = "Roll Again"
        self.con = cobutton
        self.add_item(cobutton)
        cabutton = discord.ui.Button(label=f"Cancel", custom_id=f"cancel", style=discord.ButtonStyle.red)
        cabutton.callback = self.del_clicked
        if self.roll :
            cabutton.disabled = True
        self.can = cabutton
        self.add_item(cabutton)
        if self.roll :
            self.roll_anim()

    async def del_clicked(self, interaction: discord.Interaction) :
        await interaction.response.defer()
        if interaction.user.id == self.interaction.user.id :
            await self.interaction.delete_original_response()

    async def con_clicked(self, interaction: discord.Interaction) :
        await interaction.response.defer()
        if interaction.user.id == self.interaction.user.id and get_gems(str(self.interaction.user.id)) >= self.bet :
            await self.interaction.edit_original_response(content=keno_diff_to_string(self.difficulty),
                                                          view=KenoPlayButtons(bet=self.bet, board=self.board,
                                                                               interaction=self.interaction, roll=True,
                                                                               difficulty=self.difficulty))
        if get_gems(str(self.interaction.user.id)) <= self.bet - 1 :
            await self.interaction.delete_original_response()


class KenoSelectButtons(discord.ui.View) :
    def __init__(self, bet, board, interaction, difficulty, tiles=0) :
        super().__init__(timeout=None)
        self.bet = bet
        self.board = board
        self.interaction = interaction
        self.tiles = tiles
        self.difficulty = difficulty
        self.setup_buttons()

    def setup_buttons(self) :
        for tile in range(0, len(self.board)) :
            tileF = self.board[tile]
            if tileF == "" :
                button = discord.ui.Button(label=f"{tile + 1}", custom_id=f"{tile}", style=discord.ButtonStyle.gray)
                button.callback = self.tile_clicked
                if self.tiles >= 6 :
                    button.disabled = True
                self.add_item(button)
            else :
                button = discord.ui.Button(label=f"{tile + 1}", custom_id=f"{tile}", style=discord.ButtonStyle.blurple)
                button.disabled = True
                self.add_item(button)
        cobutton = discord.ui.Button(label=f"", custom_id=f"confirm", style=discord.ButtonStyle.primary, emoji="✅")
        cobutton.callback = self.con_clicked
        if self.tiles <= 5 :
            cobutton.disabled = True
        self.add_item(cobutton)
        cabutton = discord.ui.Button(label=f"Cancel", custom_id=f"cancel", style=discord.ButtonStyle.red)
        cabutton.callback = self.del_clicked
        self.add_item(cabutton)

    async def tile_clicked(self, interaction: discord.Interaction) :
        if interaction.user.id == self.interaction.user.id :
            await interaction.response.defer()
            customid = interaction.data["custom_id"]
            self.board[int(customid)] = "s"
            self.tiles = self.tiles + 1
            await self.interaction.edit_original_response(
                content=f":white_check_mark: **Please Select Your Tiles (Max: 6)** (Bet: {add_suffix(self.bet)})",
                view=KenoSelectButtons(bet=self.bet, board=self.board, interaction=self.interaction, tiles=self.tiles,
                                       difficulty=self.difficulty))

    async def del_clicked(self, interaction: discord.Interaction) :
        await interaction.response.defer()
        if interaction.user.id == self.interaction.user.id :
            await self.interaction.delete_original_response()

    async def con_clicked(self, interaction: discord.Interaction) :
        await interaction.response.defer()
        if interaction.user.id == self.interaction.user.id :
            await self.interaction.edit_original_response(content=keno_diff_to_string(self.difficulty),
                                                          view=KenoPlayButtons(bet=self.bet, board=self.board,
                                                                               interaction=self.interaction,
                                                                               tiles=self.tiles,
                                                                               difficulty=self.difficulty))


@bot.tree.command(name="keno", description="🎉 Play a thrilling game of Keno!")
@app_commands.describe(difficulty="Choose your difficulty: Easy or Hard")
async def keno(interaction: discord.Interaction, bet: str, difficulty: str) :
    valid = True
    uid = str(interaction.user.id)
    bet = suffix_to_int(bet)
    valid_difficulties = ["Easy", "Hard"]
    if not is_registered(uid) :
        valid = False
        embed = discord.Embed(title="🚫 Not Registered Yet?",
                              description="You need to register to play Keno. Use `/register` to get started! 🚀",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Let's get you in the game! 🎮")
        await interaction.response.send_message(embed=embed)
        return
    if not difficulty in valid_difficulties :
        valid = False
        embed = discord.Embed(title="🚫 Invalid Difficulty",
                              description="Please choose a valid difficulty: `Easy` or `Hard`. 🤔",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Choose your challenge! 💪")
        await interaction.response.send_message(embed=embed)
        return
    if bet <= 999 :
        valid = False
        embed = discord.Embed(title="🚫 Invalid Bet",
                              description="The minimum bet for Keno is 1,000 gems. Please enter a larger amount. 💰",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="More gems, more fun! 🎉")
        await interaction.response.send_message(embed=embed)
        return
    if bet > get_gems(uid) :
        valid = False
        embed = discord.Embed(title="🚫 Insufficient Funds",
                              description="You don't have enough gems to place this bet. Time to gamble more! 🎰",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Better luck next time! 🍀")
        await interaction.response.send_message(embed=embed)
        return
    if valid :
        await interaction.response.send_message(
            content=f"✅ **Select Your Tiles (Max: 6)** | **Bet:** `{add_suffix(bet)}`",
            view=KenoSelectButtons(bet=bet, board=base_keno_board(23), interaction=interaction, difficulty=difficulty))


class TowersButtons(discord.ui.View) :
    def __init__(self, bet, interaction) :
        super().__init__(timeout=None)
        self.bet = bet
        self.interaction = interaction
        self.buttons = [[], [], [], [], []]
        self.layer = 0
        self.multi = 1.0
        self.cash = None
        self.setup_buttons()

    def setup_buttons(self) :
        for layer in range(0, 5) :
            for tower in range(0, 3) :
                button = discord.ui.Button(label=f"{add_suffix(round(Config['Towers']['Multis'][layer] * self.bet))}",
                                           custom_id=f"{layer} {tower}", style=discord.ButtonStyle.gray, row=layer,
                                           emoji="💰")
                button.callback = self.tower_clicked
                if layer == 0 :
                    button.style = discord.ButtonStyle.blurple
                self.buttons[layer].append(button)
                self.add_item(button)
        button = discord.ui.Button(label=f"Cashout", custom_id=f"cash", style=discord.ButtonStyle.green, row=4)
        button.callback = self.cash_clicked
        self.cash = button
        self.add_item(button)

    async def cash_clicked(self, interaction: discord.Interaction) :
        if interaction.user.id == self.interaction.user.id :
            await interaction.response.defer()
            winnings = round(self.bet * self.multi)
            add_gems(str(self.interaction.user.id), winnings)
            add_bet(str(self.interaction.user.id), self.bet, winnings)
            for i2 in self.buttons :
                for i3 in i2 :
                    i3.disabled = True
            self.cash.disabled = True
            await self.interaction.edit_original_response(
                content=f"**Cashed Out Towers!**\n:moneybag: **Winnings:** ``{add_suffix(winnings)}``\n:star: **Multiplier:** ``{self.multi}``\n:gem: **Bet:** ``{add_suffix(self.bet)}``",
                view=self)

    async def tower_clicked(self, interaction: discord.Interaction) :
        if interaction.user.id == self.interaction.user.id :
            await interaction.response.defer()
            customid = interaction.data["custom_id"]
            layer = int(customid.split(" ")[0])
            tower = int(customid.split(" ")[1])
            print(layer)
            print(self.layer)
            if layer == self.layer :
                for tower2 in self.buttons[layer] :
                    tower2.disabled = True
                    tower2.style = discord.ButtonStyle.gray
                if layer != 4 :
                    for tower2 in self.buttons[layer + 1] :
                        tower2.style = discord.ButtonStyle.blurple
                if roll_percentage(Config['Towers']['WinChance']) :
                    self.buttons[layer][tower].style = discord.ButtonStyle.green
                    self.multi = Config["Towers"]["Multis"][layer]
                else :
                    self.buttons[layer][tower].style = discord.ButtonStyle.red
                    self.cash.disabled = True
                    await self.interaction.edit_original_response(view=self)
                    for i2 in self.buttons :
                        for i3 in i2 :
                            i3.disabled = True
                    await self.interaction.edit_original_response(view=self)
                    await asyncio.sleep(3)
                    add_rake_back(str(interaction.user.id), percentage(rb, self.bet))
                    add_bet(str(interaction.user.id), self.bet, 0)
                    return
                await self.interaction.edit_original_response(view=self)
                self.layer = self.layer + 1


@bot.tree.command(name="towers", description="🗼 Climb the towers and multiply your bet!")
async def towers(interaction: discord.Interaction, bet: str) :
    valid = True
    uid = str(interaction.user.id)
    bet = suffix_to_int(bet)
    if not is_registered(uid) :
        valid = False
        embed = discord.Embed(title="🚫 Not Registered Yet?",
                              description="You need to register to play towers. Use `/register` to get started! 🚀",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Let's get you in the game! 🎮")
        await interaction.response.send_message(embed=embed)
        return
    if bet <= 999 :
        valid = False
        embed = discord.Embed(title="🚫 Invalid Bet",
                              description="The minimum bet for towers is 1,000 gems. Please enter a larger amount. 💰",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="More gems, more fun! 🎉")
        await interaction.response.send_message(embed=embed)
        return
    if bet > get_gems(uid) :
        valid = False
        embed = discord.Embed(title="🚫 Insufficient Funds",
                              description="You don't have enough gems to place this bet. Time to gamble more! 🎰",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Better luck next time! 🍀")
        await interaction.response.send_message(embed=embed)
        return
    if valid :
        subtract_gems(uid, bet)
        af = get_affiliate(str(interaction.user.id))
        add_gems(af, bet * 0.01)
        await log(f"🗼 <@{uid}> bet {add_suffix(bet)} on towers!")
        await interaction.response.send_message(content="🗼 **Welcome to Towers!**\nClick the buttons to climb and multiply your bet. But be careful, one wrong move and you lose it all! 💥", view=TowersButtons(bet=bet, interaction=interaction))


class FlipButtons(discord.ui.View) :
    def __init__(self, msg, bet, side, user) :
        super().__init__(timeout=None)
        self.bet = bet
        self.msg = msg
        self.side = side
        self.user = user
        self.buttons = []
        self.setup_buttons()

    def setup_buttons(self) :
        button = discord.ui.Button(label=f"Join", custom_id=f"join", style=discord.ButtonStyle.primary, emoji="🪙")
        button.callback = self.join_clicked
        self.buttons.append(button)
        self.add_item(button)
        button = discord.ui.Button(label=f"Call Bot", custom_id=f"bot", style=discord.ButtonStyle.green, emoji="🤖")
        button.callback = self.bot
        self.buttons.append(button)
        self.add_item(button)

    async def join_clicked(self, interaction: discord.Interaction) :
        uid = str(interaction.user.id)
        if get_gems(uid) < self.bet :
            await interaction.response.send_message(content="🚫 You can't afford this, you poor soul!", ephemeral=True)
            return
        if uid == self.user :
            await interaction.response.send_message(content="🤦‍♂️ Nah, bro, you can't join your own flip! :skull:", ephemeral=True)
            return
        await interaction.response.send_message(content="🎉 You've joined the game, you absolute legend!", ephemeral=True)
        for button in self.buttons :
            button.disabled = True
        subtract_gems(uid, self.bet)
        af = get_affiliate(str(interaction.user.id))
        add_gems(af, self.bet * 0.01)
        await self.msg.edit(view=self)
        choiches = ["Heads", "Tails"]
        choice = random.choice(choiches)
        embed = discord.Embed(title=f"Rolled {choice}", description=f"", color=0xffc800)
        if self.side == "Heads" :
            embed.add_field(name="Flip", value=f":coin: **{self.side}:** <@{self.user}>\n:coin: **Tails:** <@{uid}>")
        if self.side == "Tails" :
            embed.add_field(name="Flip", value=f":coin: **{self.side}:** <@{self.user}>\n:coin: **Heads:** du<@{uid}>")
        if choice == self.side :
            embed.add_field(name="Winner", value=f"<@{self.user}> - {add_suffix(round(self.bet * 1.95))}")
            add_gems(self.user, round(self.bet * 2.05))
            add_bet(self.user, self.bet, round(self.bet * 2.05))
            add_bet(uid, self.bet, 0)
        else :
            embed.add_field(name="Winner", value=f"<@{uid}> - {add_suffix(round(self.bet * 1.95))}")
            add_gems(uid, round(self.bet * 1.95))
            add_bet(uid, self.bet, round(self.bet * 1.95))
            add_bet(self.user, self.bet, 0)
            add_rake_back(self.user, percentage(rb, self.bet))
        await self.msg.edit(embed=embed)

    async def bot(self, interaction: discord.Interaction) :
        uid = str(bot.user.id)
        await interaction.response.send_message(content="🎉 You've joined the game, you absolute legend!", ephemeral=True)
        for button in self.buttons :
            button.disabled = True
        subtract_gems(uid, self.bet)
        await self.msg.edit(view=self)
        choice = "Tails"
        if self.side == "Heads" :
            if roll_percentage(50 + Config['Coinflip']['House']) :
                choice = "Tails"
            else :
                choice = "Heads"
        if self.side == "Tails" :
            if roll_percentage(50 + Config['Coinflip']['House']) :
                choice = "Heads"
            else :
                choice = "Tails"
        embed = discord.Embed(title=f"Rolled {choice}", description=f"", color=0xffc800)
        if self.side == "Heads" :
            embed.add_field(name="Flip", value=f":coin: **{self.side}:** <@{self.user}>\n:coin: **Tails:** <@{uid}>")
        if self.side == "Tails" :
            embed.add_field(name="Flip", value=f":coin: **{self.side}:** <@{self.user}>\n:coin: **Heads:** <@{uid}>")
        if choice == self.side :
            embed.add_field(name="Winner", value=f"<@{self.user}> - {add_suffix(round(self.bet * 1.95))}")
            add_gems(self.user, round(self.bet * 1.95))
            add_bet(self.user, self.bet, round(self.bet * 1.95))
            add_bet(uid, self.bet, 0)
        else :
            embed.add_field(name="Winner", value=f"<@{uid}> - {add_suffix(round(self.bet * 1.95))}")
            add_gems(uid, round(self.bet * 1.95))
            add_rake_back(self.user, percentage(rb, self.bet))
            add_bet(self.user, self.bet, 0)
            add_bet(uid, self.bet, round(self.bet * 1.95))
        await self.msg.edit(embed=embed)


@bot.tree.command(name="flip", description="🪙 Challenge another user to a coinflip!")
async def flip(interaction: discord.Interaction, bet: str, side: CoinSide) :
    valid = True
    uid = str(interaction.user.id)
    bet = suffix_to_int(bet)
    if not is_registered(uid) :
        valid = False
        embed = discord.Embed(title="🚫 Not Registered Yet?",
                              description="You need to register to start a coinflip. Use `/register` to get started! 🚀",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Let's get you in the game! 🎮")
        await interaction.response.send_message(embed=embed)
        return
    if bet <= 999 :
        valid = False
        embed = discord.Embed(title="🚫 Invalid Bet",
                              description="The minimum bet for a coinflip is 1,000 gems. Please enter a larger amount. 💰",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="More gems, more fun! 🎉")
        await interaction.response.send_message(embed=embed)
        return
    if bet > get_gems(uid) :
        valid = False
        embed = discord.Embed(title="🚫 Insufficient Funds",
                              description="You don't have enough gems to place this bet. Time to gamble more! 🎰",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Better luck next time! 🍀")
        await interaction.response.send_message(embed=embed)
        return
    if valid :
        subtract_gems(uid, bet)
        af = get_affiliate(str(interaction.user.id))
        add_gems(af, bet * 0.01)
        channel = bot.get_channel(int(Config['Coinflip']['1v1']))
        embed = discord.Embed(title="🪙 Coinflip Challenge!",
                              description=f"<@{uid}> has started a coinflip for **{add_suffix(bet)}** gems! 💎",
                              color=0xffc800)
        if side.value == "Heads" :
            embed.add_field(name="Sides", value=f"**{side.value}:** <@{uid}>\n**Tails:** `Waiting for opponent...`")
        if side.value == "Tails" :
            embed.add_field(name="Sides", value=f"**{side.value}:** <@{uid}>\n**Heads:** `Waiting for opponent...`")
        embed.add_field(name="Bet", value=f"💰 **Amount:** `{add_suffix(bet)}`")
        msg = await channel.send(embed=embed)
        await msg.edit(embed=embed, view=FlipButtons(msg, bet, side.value, uid))
        await interaction.response.send_message(content=f"🪙 Your coinflip has been created in <#{Config['Coinflip']['1v1']}>!")
def open_case(Case):
    casesdata = get_cases()
    casedata = {}
    for case in casesdata:
        if case['Name'] == Case:
            casedata = case
    choice = None
    for pet in reversed(casedata['Drops']):
        if roll_percentage(pet['Chance']):
            choice = pet
            break
    if choice == None:
        choice = casedata['Drops'][0]
    return choice
@bot.tree.command(name="cases", description="📦 View all available cases to unbox!")
async def cases(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    if not is_registered(uid) :
        embed = discord.Embed(title="🚫 Not Registered Yet?",
                              description="You need to register to view cases. Use `/register` to get started! 🚀",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Let's get you in the game! 🎮")
        await interaction.response.send_message(embed=embed)
        return
    embed = discord.Embed(title="📦 Available Cases",
                          description="Here's a list of all the cases you can unbox:",
                          color=0x2abccf)
    embed.set_author(name="Pet Sim 99 Gamble Bot",
                     icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
    for case in get_cases():
        infostr = ""
        for pet in case['Drops']:
            infostr += f"- {pet['Name']} ({pet['Chance']}%) - `{add_suffix(pet['Worth'])}`\n"
        embed.add_field(name=f"**{case['Name']}**",
                        value=f"💰 **Price:** `{add_suffix(case['Price'])}`\n"
                              f"🍀 **Drops:**\n{infostr}",
                        inline=False)
    embed.set_footer(text="Good luck with your unboxing! 🎉")
    await interaction.response.send_message(embed=embed)
@bot.tree.command(name="unbox-case", description="🎁 Open a case for a chance to win big!")
async def unbox_case(interaction: discord.Interaction, case_name: str):
    uid = str(interaction.user.id)
    if not is_registered(uid) :
        embed = discord.Embed(title="🚫 Not Registered Yet?",
                              description="You need to register to unbox cases. Use `/register` to get started! 🚀",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Let's get you in the game! 🎮")
        await interaction.response.send_message(embed=embed)
        return
    casedata = None
    for caseD in get_cases():
        if caseD['Name'] == case_name:
            casedata = caseD
            break
    if not casedata:
        embed = discord.Embed(title="🚫 Invalid Case",
                              description="That case doesn't exist! Use `/cases` to see a list of all available cases. 🤔",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Choose wisely! 🧐")
        await interaction.response.send_message(embed=embed)
        return
    if get_gems(uid) < casedata['Price']:
        embed = discord.Embed(title="🚫 Insufficient Funds",
                              description="You don't have enough gems to open this case. Time to gamble more! 🎰",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Better luck next time! 🍀")
        await interaction.response.send_message(embed=embed)
        return
    outcome = open_case(case_name)
    subtract_gems(uid, casedata['Price'])
    embed = discord.Embed(title=f"🎁 Opening {case_name}...",
                          description=f"The case will be unboxed <t:{round(time.time()+5)}:R>!",
                          color=0x2abccf)
    embed.set_thumbnail(url=casedata['Icon'])
    await interaction.response.send_message(embed=embed)
    await asyncio.sleep(5)
    embed = None
    add_gems(uid, outcome['Worth'])
    add_bet(uid,casedata['Price'],outcome['Worth'])
    if casedata['Price'] <= outcome['Worth']:
        embed = discord.Embed(title="🎉 You Won!",
                              description=f"You unboxed a **{outcome['Name']}**!",
                              color=0x82ff80)
        embed.add_field(name="💸 Winnings",
                        value=f"💰 **Case Price:** `{add_suffix(casedata['Price'])}`\n"
                              f"💎 **{outcome['Name']} Price:** `{add_suffix(outcome['Worth'])}`\n"
                              f"📈 **Profit:** `{add_suffix(outcome['Worth']-casedata['Price'])}`")
        embed.set_thumbnail(url=outcome['Icon'])
    else:
        embed = discord.Embed(title="💔 You Lost...",
                              description=f"You unboxed a **{outcome['Name']}**.",
                              color=0xff7575)
        embed.add_field(name="💸 Winnings",
                        value=f"💰 **Case Price:** `{add_suffix(casedata['Price'])}`\n"
                              f"💎 **{outcome['Name']} Price:** `{add_suffix(outcome['Worth'])}`\n"
                              f"📉 **Loss:** `-{add_suffix(casedata['Price'] - outcome['Worth'])}`")
        embed.set_thumbnail(url=outcome['Icon'])
    await interaction.edit_original_response(embed=embed)
@bot.tree.command(name="unbox-multiple-cases", description="🎁 Open multiple cases at once!")
async def unbox_cases(interaction: discord.Interaction, case_name: str, amount: int):
    uid = str(interaction.user.id)
    if not is_registered(uid) :
        embed = discord.Embed(title="🚫 Not Registered Yet?",
                              description="You need to register to unbox cases. Use `/register` to get started! 🚀",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Let's get you in the game! 🎮")
        await interaction.response.send_message(embed=embed)
        return
    casedata = None
    for caseD in get_cases():
        if caseD['Name'] == case_name:
            casedata = caseD
            break
    if amount < 2 or amount > 10000:
        embed = discord.Embed(title="🚫 Invalid Amount",
                              description="Please choose an amount between 2 and 10,000 cases to unbox. 📦",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Choose wisely! 🤔")
        await interaction.response.send_message(embed=embed)
        return
    if not casedata:
        embed = discord.Embed(title="🚫 Invalid Case",
                              description="That case doesn't exist! Use `/cases` to see a list of all available cases. 🤔",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Choose wisely! 🧐")
        await interaction.response.send_message(embed=embed)
        return
    if get_gems(uid) < casedata['Price'] * amount:
        embed = discord.Embed(title="🚫 Insufficient Funds",
                              description="You don't have enough gems to open this many cases. Time to gamble more! 🎰",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Better luck next time! 🍀")
        await interaction.response.send_message(embed=embed)
        return
    if amount <= 30:
        outcomes = []
        for i in range(0, amount):
            outcomes.append(open_case(case_name))

        subtract_gems(uid, casedata['Price'] * amount)
        embed = discord.Embed(title=f"🎁 Opening {amount}x {case_name}s...",
                              description=f"The cases will be unboxed <t:{round(time.time()+5)}:R>!",
                              color=0x2abccf)
        embed.set_thumbnail(url=casedata['Icon'])
        await interaction.response.send_message(embed=embed)
        await asyncio.sleep(5)
        embed = None
        totalcost = casedata['Price'] * amount
        totalwinnings = 0
        bestpet = {'Worth': 1}
        for pet in outcomes:
            add_gems(uid, pet['Worth'])
            add_bet(uid, casedata['Price'], pet['Worth'])
            totalwinnings += pet['Worth']
            if pet['Worth'] >= bestpet['Worth']:
                bestpet = pet
            time.sleep(0.1)

        if totalwinnings >= totalcost:
            embed = discord.Embed(title="🎉 You Won!",
                                  description=f"You unboxed {amount} {case_name}s and made a profit!",
                                  color=0x82ff80)
            petsstr = ""
            for pet in outcomes:
                petsstr += f"- **{pet['Name']}** - `{add_suffix(pet['Worth'])}`\n"
            embed.add_field(name="🐾 Pets Unboxed", value=petsstr)
            embed.add_field(name="🌟 Best Pet",
                            value=f"**Pet:** `{bestpet['Name']}`\n"
                                  f"**Worth:** `{add_suffix(bestpet['Worth'])}`\n"
                                  f"**Chance:** `{bestpet['Chance']}%`")
            embed.add_field(name="💸 Winnings",
                            value=f"**Total Price:** `{add_suffix(casedata['Price'] * amount)}`\n"
                                  f"**Total Winnings:** `{add_suffix(totalwinnings)}`\n"
                                  f"**Profit:** `{add_suffix(totalwinnings-totalcost)}`",
                            inline=False)
            embed.set_thumbnail(url=bestpet['Icon'])
        else:
            embed = discord.Embed(title="💔 You Lost...",
                                  description=f"You unboxed {amount} {case_name}s and lost some gems.",
                                  color=0xff7575)
            petsstr = ""
            for pet in outcomes :
                petsstr += f"- **{pet['Name']}** - `{add_suffix(pet['Worth'])}`\n"
            embed.add_field(name="🐾 Pets Unboxed", value=petsstr)
            embed.add_field(name="🌟 Best Pet",
                            value=f"**Pet:** `{bestpet['Name']}`\n"
                                  f"**Worth:** `{add_suffix(bestpet['Worth'])}`\n"
                                  f"**Chance:** `{bestpet['Chance']}%`")
            embed.add_field(name="💸 Winnings",
                            value=f"**Total Price:** `{add_suffix(casedata['Price'] * amount)}`\n"
                                  f"**Total Winnings:** `{add_suffix(totalwinnings)}`\n"
                                  f"**Loss:** `-{add_suffix(totalcost - totalwinnings)}`",
                            inline=False)
            embed.set_thumbnail(url=bestpet['Icon'])
        await interaction.edit_original_response(embed=embed)
    else:
        outcomes = []
        for i in range(0, amount) :
            outcomes.append(open_case(case_name))

        subtract_gems(uid, casedata['Price'] * amount)
        embed = discord.Embed(title=f"🎁 Opening {amount}x {case_name}s...",
                              description=f"The cases will be unboxed <t:{round(time.time() + 5)}:R>!",
                              color=0x2abccf)
        embed.set_thumbnail(url=casedata['Icon'])
        await interaction.response.send_message(embed=embed)
        await asyncio.sleep(5)
        embed = None
        totalcost = casedata['Price'] * amount
        totalwinnings = 0
        bestpet = {'Worth' : 1}
        for pet in outcomes :
            totalwinnings += pet['Worth']
        add_gems(uid,totalwinnings)
        add_bet(uid, totalcost, totalwinnings)
        if totalwinnings >= totalcost :
            embed = discord.Embed(title="🎉 You Won!",
                                  description=f"You unboxed {amount} {case_name}s and made a profit!",
                                  color=0x82ff80)
            embed.add_field(name="🐾 Pets Unboxed",
                            value="You unboxed too many cases to show them all, but you came out on top!")
            embed.add_field(name="💸 Winnings",
                            value=f"**Total Price:** `{add_suffix(casedata['Price'] * amount)}`\n"
                                  f"**Total Winnings:** `{add_suffix(totalwinnings)}`\n"
                                  f"**Profit:** `{add_suffix(totalwinnings - totalcost)}`",
                            inline=False)
        else :
            embed = discord.Embed(title="💔 You Lost...",
                                  description=f"You unboxed {amount} {case_name}s and lost some gems.",
                                  color=0xff7575)
            embed.add_field(name="🐾 Pets Unboxed",
                            value="You unboxed too many cases to show them all, and unfortunately, you lost some gems.")
            embed.add_field(name="💸 Winnings",
                            value=f"**Total Price:** `{add_suffix(casedata['Price'] * amount)}`\n"
                                  f"**Total Winnings:** `{add_suffix(totalwinnings)}`\n"
                                  f"**Loss:** `-{add_suffix(totalcost - totalwinnings)}`",
                            inline=False)
        await interaction.edit_original_response(embed=embed)
class UpgradeButton(discord.ui.View) :
    def __init__(self, interaction, bet, chance, multiplier, roll=1):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.bet = bet
        self.chance = chance
        self.multiplier = multiplier
        self.roll = roll
        self.setup_buttons()

    def setup_buttons(self) :
        button = discord.ui.Button(label=f"Upgrade", custom_id=f"join", style=discord.ButtonStyle.blurple, emoji="💰")
        button.callback = self.join_clicked
        self.add_item(button)
    async def join_clicked(self, interaction: discord.Interaction):
        uid = str(interaction.user.id)
        print("1")
        if uid != str(self.interaction.user.id):
            return
        print("2")
        if self.bet > get_gems(uid):
            await self.interaction.edit_original_response(embed=fail("You Can No Longer Afford This Bet"),view=None)
            return
        print("3")
        subtract_gems(uid,self.bet)
        won = roll_percentage(self.chance)
        if won:
            print("4")
            add_gems(uid, round(self.bet*self.multiplier))
            embed = discord.Embed(title="Upgrade Won!",description="You won this upgrade!",color=0x4dff58)
            embed.add_field(name="Input", value=f":gem: **Bet:** ``{add_suffix(self.bet)}``\n:four_leaf_clover: **Chance:** ``{round(self.chance, 1)}%``\n:star: **Multiplier:** ``{self.multiplier}x``\n:moneybag: **Winnings:** ``{add_suffix(round(self.bet*self.multiplier))}``")
            await self.interaction.edit_original_response(embed=embed, view=None)
        else:
            print("5")
            embed = discord.Embed(title="Upgrade Lost!",description="You lost this upgrade!",color=0xff6b6b)
            embed.add_field(name="Input", value=f":gem: **Bet:** ``{add_suffix(self.bet)}``\n:four_leaf_clover: **Chance:** ``{round(self.chance, 1)}%``\n:star: **Multiplier:** ``{self.multiplier}x``\n:moneybag: **Winnings:** ``{add_suffix(round(self.bet*self.multiplier))}``")
            await self.interaction.edit_original_response(embed=embed, view=None)

green = 0x4dff58
red = 0xff6b6b
yellow = 0xfff93d

@bot.tree.command(name="upgrader", description="⬆️ Upgrade your gems for a chance at huge multipliers!")
async def upgrade(interaction: discord.Interaction, bet: str, multiplier: float):
    valid = True
    bet = suffix_to_int(bet)
    uid = str(interaction.user.id)
    if not is_registered(uid) :
        valid = False
        embed = discord.Embed(title="🚫 Not Registered Yet?",
                              description="You need to register to use the upgrader. Use `/register` to get started! 🚀",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Let's get you in the game! 🎮")
        await interaction.response.send_message(embed=embed)
        return
    if multiplier < 1.5:
        embed = discord.Embed(title="🚫 Invalid Multiplier",
                              description="The minimum multiplier for the upgrader is 1.5. Please enter a higher value. 📈",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Higher risk, higher reward! 🤑")
        await interaction.response.send_message(embed=embed)
        return
    if get_gems(uid) < bet:
        embed = discord.Embed(title="🚫 Insufficient Funds",
                              description="You don't have enough gems for this upgrade. Time to gamble more! 🎰",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Better luck next time! 🍀")
        await interaction.response.send_message(embed=embed)
        return
    if bet < 999:
        embed = discord.Embed(title="🚫 Invalid Bet",
                              description="The minimum bet for the upgrader is 1,000 gems. Please enter a larger amount. 💰",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="More gems, more fun! 🎉")
        await interaction.response.send_message(embed=embed)
        return
    embed = discord.Embed(title="⬆️ Gem Upgrader",
                          description="Will you succeed and multiply your gems, or will you lose it all? 🤔",
                          color=0x4dbbff)
    win_chance = multiplier_to_percentage(multiplier,Config['Upgrader']['House'])
    winnings = round(bet*multiplier)
    embed.add_field(name="📊 Upgrade Details",
                    value=f"💎 **Bet:** `{add_suffix(bet)}`\n"
                          f"🍀 **Chance:** `{round(win_chance, 1)}%`\n"
                          f"✨ **Multiplier:** `{multiplier}x`\n"
                          f"💰 **Potential Winnings:** `{add_suffix(winnings)}`")
    await interaction.response.send_message(embed=embed,view=UpgradeButton(interaction,bet,win_chance,multiplier))
def roll_dice():
    return random.randint(1, 6)
@bot.tree.command(name="threedice", description="🎲 Bet on the sum of three dice!")
async def threedice(interaction: discord.Interaction, bet: str, choice: str):
    bet = suffix_to_int(bet)
    uid = str(interaction.user.id)
    if not is_registered(uid) :
        embed = discord.Embed(title="🚫 Not Registered Yet?",
                              description="You need to register to play three dice. Use `/register` to get started! 🚀",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Let's get you in the game! 🎮")
        await interaction.response.send_message(embed=embed)
        return
    if get_gems(uid) < bet :
        embed = discord.Embed(title="🚫 Insufficient Funds",
                              description="You don't have enough gems for this bet. Time to gamble more! 🎰",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Better luck next time! 🍀")
        await interaction.response.send_message(embed=embed)
        return
    if bet < 999 :
        embed = discord.Embed(title="🚫 Invalid Bet",
                              description="The minimum bet for three dice is 1,000 gems. Please enter a larger amount. 💰",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="More gems, more fun! 🎉")
        await interaction.response.send_message(embed=embed)
        return
    if choice.lower() not in ["4-10", "11-17"]:
        embed = discord.Embed(title="🚫 Invalid Choice",
                              description="Please choose either `4-10` or `11-17` for your bet. 🤔",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Choose wisely! 🧐")
        await interaction.response.send_message(embed=embed)
        return

    dice1 = roll_dice()
    dice2 = roll_dice()
    dice3 = roll_dice()
    total = dice1 + dice2 + dice3
    subtract_gems(uid,bet)
    winnings = 0

    if total == 3 or total == 18:
        winnings = 0
        embed = discord.Embed(title="💔 House Wins!",
                              description=f"The dice rolled **{total}**! The house takes this round. Better luck next time! 🎲",
                              color=red)
    elif (choice.lower() == "4-10" and 4 <= total <= 10) or \
         (choice.lower() == "11-17" and 11 <= total <= 17):
        winnings = bet * 2
        embed = discord.Embed(title="🎉 You Won!",
                              description=f"The dice rolled **{total}**! You guessed correctly and won **{add_suffix(winnings)}** gems! 💎",
                              color=green)
    else:
        winnings = 0
        embed = discord.Embed(title="💔 You Lost...",
                              description=f"The dice rolled **{total}**. You guessed incorrectly. Better luck next time! 🎲",
                              color=red)

    embed.add_field(name="📊 Game Results",
                    value=f"**Your Choice:** `{choice}`\n"
                          f"**Dice Roll:** `{dice1}`, `{dice2}`, `{dice3}` (Total: **{total}**)\n"
                          f"**Winnings:** `{add_suffix(winnings)}` 💎")
    add_gems(uid, winnings)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="dice", description="🎲 Roll a dice against the bot and test your luck!")
async def dice(interaction: discord.Interaction, bet: str):
    bet = suffix_to_int(bet)
    uid = str(interaction.user.id)
    if not is_registered(uid) :
        embed = discord.Embed(title="🚫 Not Registered Yet?",
                              description="You need to register to play dice. Use `/register` to get started! 🚀",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Let's get you in the game! 🎮")
        await interaction.response.send_message(embed=embed)
        return
    if get_gems(uid) < bet :
        embed = discord.Embed(title="🚫 Insufficient Funds",
                              description="You don't have enough gems for this bet. Time to gamble more! 🎰",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="Better luck next time! 🍀")
        await interaction.response.send_message(embed=embed)
        return
    if bet < 999 :
        embed = discord.Embed(title="🚫 Invalid Bet",
                              description="The minimum bet for dice is 1,000 gems. Please enter a larger amount. 💰",
                              color=0xff0000)
        embed.set_author(name="Pet Sim 99 Gamble Bot",
                         icon_url="https://creazilla-store.fra1.digitaloceanspaces.com/cliparts/7803751/diamond-gem-clipart-sm.png")
        embed.set_footer(text="More gems, more fun! 🎉")
        await interaction.response.send_message(embed=embed)
        return
    yourdie = roll_dice()
    botdie = roll_dice()
    subtract_gems(uid,bet)
    winnings = 0
    if yourdie > botdie:
        winnings = round((bet*2)/1.02)
        embed = discord.Embed(title="🎉 You Won!",
                              description="You rolled higher than the bot and won the dice game! 🎲",
                              color=green)
        embed.add_field(name="📊 Game Results",
                        value=f"**You Rolled:** `{yourdie}`\n"
                              f"**Bot Rolled:** `{botdie}`\n"
                              f"**Winnings:** `{add_suffix(winnings)}` 💎")
    elif yourdie < botdie:
        winnings = 0
        embed = discord.Embed(title="💔 You Lost...",
                              description="The bot rolled higher than you. Better luck next time! 🎲",
                              color=red)
        embed.add_field(name="📊 Game Results",
                        value=f"**You Rolled:** `{yourdie}`\n"
                              f"**Bot Rolled:** `{botdie}`\n"
                              f"**Winnings:** `{add_suffix(winnings)}` 💎")
    else:
        winnings = bet
        embed = discord.Embed(title="🤝 It's a Tie!",
                              description="You and the bot rolled the same number. Your bet has been returned. 🎲",
                              color=yellow)
        embed.add_field(name="📊 Game Results",
                        value=f"**You Rolled:** `{yourdie}`\n"
                              f"**Bot Rolled:** `{botdie}`\n"
                              f"**Winnings:** `{add_suffix(winnings)}` 💎")
    add_gems(uid, winnings)
    await interaction.response.send_message(embed=embed)

allowed_user_ids = Config["AdminCommands"]["UserID"]

@bot.tree.command(name="setbal", description="🔒 Set a user's balance (Admin Only)")
async def setgems(interaction: discord.Interaction, user: discord.Member, gems: str):
    gems = suffix_to_int(gems)
    uid = str(user.id)
    

    if str(interaction.user.id) not in allowed_user_ids:

        allowed_users = ", ".join(f"<@{user_id}>" for user_id in allowed_user_ids)
        embed = discord.Embed(
            title="🚫 Access Denied",
            description=f"You do not have permission to use this command. This is an admin-only command. 🔒",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed)
        return
    

    set_gems(uid, gems)
    embed = discord.Embed(
        title="✅ Balance Set",
        description=f"Successfully set the balance of <@{uid}> to **{add_suffix(gems)}** gems. 💎",
        color=0x00ff00
    )
    embed.set_footer(text=f"Command executed by: {interaction.user.name}")
    await interaction.response.send_message(embed=embed)
allowed_user_ids = Config["AdminCommands"]["UserID"] 

@bot.tree.command(name="addbal", description="🔒 Add gems to a user's balance (Admin Only)")
async def addgems(interaction: discord.Interaction, user: discord.Member, gems: str):
    gems = suffix_to_int(gems)
    uid = str(user.id)
    

    if str(interaction.user.id) not in allowed_user_ids:

        allowed_users = ", ".join(f"<@{user_id}>" for user_id in allowed_user_ids)
        embed = discord.Embed(
            title="🚫 Access Denied",
            description=f"You do not have permission to use this command. This is an admin-only command. 🔒",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed)
        return
    

    add_gems(uid, gems)
    embed = discord.Embed(
        title="✅ Gems Added",
        description=f"Successfully added **{add_suffix(gems)}** gems to the balance of <@{uid}>. 💎",
        color=0x00ff00
    )
    embed.set_footer(text=f"Command executed by: {interaction.user.name}")
    await interaction.response.send_message(embed=embed)

allowed_user_ids = Config["AdminCommands"]["UserID"]

@bot.tree.command(name="removebal", description="🔒 Remove gems from a user's balance (Admin Only)")
async def removegems(interaction: discord.Interaction, user: discord.Member, gems: str):
    gems = suffix_to_int(gems)
    uid = str(user.id)
    

    if str(interaction.user.id) not in allowed_user_ids:

        allowed_users = ", ".join(f"<@{user_id}>" for user_id in allowed_user_ids)
        embed = discord.Embed(
            title="🚫 Access Denied",
            description=f"You do not have permission to use this command. This is an admin-only command. 🔒",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed)
        return
    

    subtract_gems(uid, gems)
    embed = discord.Embed(
        title="✅ Gems Removed",
        description=f"Successfully removed **{add_suffix(gems)}** gems from the balance of <@{uid}>. 💎",
        color=0x00ff00
    )
    embed.set_footer(text=f"Command executed by: {interaction.user.name}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help", description="📚 Show a list of all available commands.")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📚 Help Desk",
        description="Here's a list of all the commands you can use with the bot:",
        color=0x2eb9ff
    )

    embed.add_field(
        name="🎲 Games",
        value="`/flip` - Challenge another user to a coinflip.\n"
              "`/towers` - Climb the towers and multiply your bet.\n"
              "`/mines` - Test your luck in a game of mines.\n"
              "`/keno` - Play a thrilling game of Keno.\n"
              "`/dice` - Roll a dice against the bot and test your luck.\n"
              "`/threedice` - Bet on the sum of three dice.\n"
              "`/upgrader` - Upgrade your gems for a chance at huge multipliers.\n"
              "`/cases` - View all available cases to unbox.\n"
              "`/unbox-case` - Open a case for a chance to win big.\n"
              "`/unbox-multiple-cases` - Open multiple cases at once.",
        inline=False
    )

    embed.add_field(
        name="💰 Currency",
        value="`/register` - Register to start your epic gambling adventure.\n"
              "`/balance` - Check your gem balance and gambling stats.\n"
              "`/deposit` - Deposit gems to fuel your gambling passion.\n"
              "`/withdraw` - Withdraw your gems to your in-game account.\n"
              "`/tip` - Generously send gems to another user.\n"
              "`/rakeback` - Check your available rakeback.\n"
              "`/claim-rakeback` - Claim your hard-earned rakeback.\n"
              "`/leaderboard` - See who's ruling the gambling world.",
        inline=False
    )

    embed.add_field(
        name="🤝 General",
        value="`/affiliate` - Affiliate with another user and earn rewards.\n"
              "`/set_crash_join_amount` - Set your default bet for crash games.\n"
              "`/help` - Show a list of all available commands.",
        inline=False
    )

    embed.set_footer(text="Use these commands to navigate the bot and enjoy your gambling experience! 🎰")
    await interaction.response.send_message(embed=embed)

from multiprocessing import Process

def start_bot():
    bot.run(Config['DiscordBotToken'])

def start_web_server():
    app.run(debug=False, port=80, host="0.0.0.0")

if __name__ == '__main__':
    flask_process = Process(target=start_web_server)
    discord_process = Process(target=start_bot)

    flask_process.start()
    discord_process.start()

    flask_process.join()
    discord_process.join()
