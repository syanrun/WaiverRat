import discord
from discord.ext import commands
from dotenv import load_dotenv
import logging
import os
import requests
import random
from thefuzz import fuzz

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="rat.", intents=intents)

@bot.event
async def on_ready():
        print("READY")
        
@bot.command()
async def quiz(ctx):
        response = requests.get("https://partners.api.espn.com/v2/sports/football/nfl/athletes?limit=7000")
        positions = ["QB", "WR", "RB", "TE"]
        active_players = [athlete for athlete in response.json()['athletes'] if athlete['position']['abbreviation'] in positions and athlete['status']['type'] == 'active']
        img = None
        while True:
                random_player = random.choice(active_players)
                img = f"https://a.espncdn.com/i/headshots/nfl/players/full/{random_player['id']}.png"
                response = requests.get(img)
                if response.status_code != 404:
                        break
        await ctx.send(img)
        
        def check(m):
                return fuzz.ratio(m.content.lower(), random_player['displayName'].lower()) >= 80 and m.channel == ctx.message.channel and ctx.message.author == m.author
        
        try:
                await bot.wait_for("message", check=check, timeout=10)
        except:
                await ctx.send(f"YOU LOST! The correct answer was: {random_player['displayName']}")
        else:
                await ctx.send("YOU WON!")
        
        
        
bot.run(token, log_handler=handler, log_level=logging.DEBUG) 