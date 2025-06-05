import discord
from discord.ext import commands
from dotenv import load_dotenv
import logging
import os
import requests
import random
import sqlite3
from thefuzz import fuzz

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="rat.", intents=intents)

conn = sqlite3.connect("userdata.db")
cur = conn.cursor()

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
        question = await ctx.reply(img)
        
        def check(m):
                return fuzz.ratio(m.content.lower(), random_player['displayName'].lower()) >= 80 and m.channel == ctx.message.channel and ctx.message.author == m.author
        
        try:
                answer = await bot.wait_for("message", check=check, timeout=10)
        except:
                await question.reply(f"<@{ctx.message.author.id}> YOU LOST! The correct answer was: {random_player['displayName']}")
                cur.executescript(f"""
                            BEGIN;
                            INSERT OR IGNORE INTO users VALUES (\'{ctx.message.author.name}\', 8, 0);
                            UPDATE users SET plays = plays + 1 WHERE name=\'{ctx.message.author.name}\';
                            COMMIT;
                            """)
        else:
                await answer.reply("YOU WON!")
                cur.executescript(f"""
                            BEGIN;
                            INSERT OR IGNORE INTO users VALUES (\'{ctx.message.author.name}\', 8, 0);
                            UPDATE users SET plays = plays + 1, correct = correct + 1 WHERE name=\'{ctx.message.author.name}\';
                            COMMIT;
                            """)
        
@bot.command()
async def stats(ctx):
        embed=discord.Embed(title="Rat Leaderboard", color=discord.Color.green())
        if cur.execute("SELECT * FROM users ORDER BY plays / correct, plays LIMIT 10").fetchone():    
                query = cur.execute("SELECT * FROM users ORDER BY plays / correct, plays")
                player, plays, correct = zip(*query)
                accuracy = [f"{a}/{b - 8}" for a, b in zip(correct, plays)]
                score = [str(round(a/b, 2)) for a, b in zip(correct, plays)]
                embed.add_field(name = 'Player', value= "\n".join(player), inline = True)
                embed.add_field(name = 'Accuracy', value = "\n".join(accuracy), inline = True)
                embed.add_field(name = 'Score', value = "\n".join(score), inline = True)
        await ctx.send(embed=embed)        
        
bot.run(token, log_handler=handler, log_level=logging.DEBUG) 