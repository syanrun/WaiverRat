import cv2
import discord
from discord.ext import commands
from dotenv import load_dotenv
import io
import logging
import numpy as np
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

def find_player():
        response = requests.get("https://partners.api.espn.com/v2/sports/football/nfl/athletes?limit=7000")
        positions = ["QB", "WR", "RB", "TE"]
        active_players = [athlete for athlete in response.json()['athletes'] if athlete['position']['abbreviation'] in positions and athlete['status']['type'] == 'active']
        img = None
        while True:
                random_player = random.choice(active_players)
                img = f"https://a.espncdn.com/i/headshots/nfl/players/full/{random_player['id']}.png"
                response = requests.get(img)
                if response.status_code == 200:
                        break
        return random_player, response, img
        
@bot.command()
async def quiz(ctx):
        random_player, _, img = find_player()
        
        question = await ctx.reply(img)
        
        def check(m):
                return fuzz.ratio(m.content.lower(), random_player['displayName'].lower()) >= 80 and m.channel == ctx.message.channel and ctx.message.author == m.author
        
        try:
                answer = await bot.wait_for("message", check=check, timeout=10)
        except:
                await question.reply(f"<@{ctx.message.author.id}> YOU LOST! The correct answer was: {random_player['displayName']}")
                cur.executescript(f"""
                            BEGIN;
                            INSERT OR IGNORE INTO users VALUES (\'{ctx.message.author.name}\', 8, 0, 0, 0);
                            UPDATE users SET plays = plays + 1 WHERE name=\'{ctx.message.author.name}\';
                            UPDATE users SET maxstreak = MAX(maxstreak, currstreak), currstreak = 0 WHERE name=\'{ctx.message.author.name}\';
                            COMMIT;
                            """)
        else:
                await answer.reply("YOU WON!")
                cur.executescript(f"""
                            BEGIN;
                            INSERT OR IGNORE INTO users VALUES (\'{ctx.message.author.name}\', 8, 0, 0, 0);
                            UPDATE users SET plays = plays + 1, correct = correct + 1 WHERE name=\'{ctx.message.author.name}\';
                            UPDATE users SET currstreak = currstreak + 1 WHERE name=\'{ctx.message.author.name}\'; 
                            COMMIT;
                            """)

@bot.command()
async def face(ctx):
        while True:
                random_player, response, _ = find_player()
                img_ary = np.asarray(bytearray(response.content), dtype=np.uint8)
                img_transparent = cv2.imdecode(img_ary, cv2.IMREAD_UNCHANGED)
                gray = cv2.cvtColor(img_transparent, cv2.COLOR_RGBA2GRAY)
                face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_alt2.xml')
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                if len(faces) == 0:
                        continue
                x, y, w, h = faces[0]
                face = img_transparent[y:y+h, x:x+w]
                rescaled_face = cv2.resize(face, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
                _, encoded_image = cv2.imencode(".png", rescaled_face)
                image_file = io.BytesIO(encoded_image.tobytes())
                discord_file = discord.File(image_file, filename="image.png")
                break
        
        question = await ctx.reply(file=discord_file)
        
        def check(m):
                return fuzz.ratio(m.content.lower(), random_player['displayName'].lower()) >= 80 and m.channel == ctx.message.channel and ctx.message.author == m.author
        
        try:
                answer = await bot.wait_for("message", check=check, timeout=10)
        except:
                await question.reply(f"<@{ctx.message.author.id}> YOU LOST! The correct answer was: {random_player['displayName']}")
                cur.executescript(f"""
                            BEGIN;
                            INSERT OR IGNORE INTO faceusers VALUES (\'{ctx.message.author.name}\', 8, 0, 0, 0);
                            UPDATE faceusers SET plays = plays + 1 WHERE name=\'{ctx.message.author.name}\';
                            UPDATE faceusers SET maxstreak = MAX(maxstreak, currstreak), currstreak = 0 WHERE name=\'{ctx.message.author.name}\';
                            COMMIT;
                            """)
        else:
                await answer.reply("YOU WON!")
                cur.executescript(f"""
                            BEGIN;
                            INSERT OR IGNORE INTO faceusers VALUES (\'{ctx.message.author.name}\', 8, 0, 0, 0);
                            UPDATE faceusers SET plays = plays + 1, correct = correct + 1 WHERE name=\'{ctx.message.author.name}\';
                            UPDATE faceusers SET currstreak = currstreak + 1 WHERE name=\'{ctx.message.author.name}\'; 
                            COMMIT;
                            """)

def create_leaderboard(title, db):
        embed=discord.Embed(title=title, color=discord.Color.green())
        
        if cur.execute(f"SELECT * FROM {db}").fetchone():    
                query = cur.execute(f"SELECT * FROM {db} ORDER BY correct * 1.0 / plays DESC, plays DESC")
                player, plays, correct, currstreak, maxstreak = zip(*query)
                score = [f"{str(round(a/b, 2))} ({a}/{b - 8})"  for a, b in zip(correct, plays)]
                maxstreak = [str(max(a, b)) for a, b in zip(currstreak, maxstreak)]
                embed.add_field(name = 'Player', value= "\n".join(player), inline = True)
                embed.add_field(name = 'Score', value = "\n".join(score), inline = True)
                embed.add_field(name = 'Streak', value = "\n".join(maxstreak), inline = True)
        return embed

@bot.command()
async def stats(ctx):
        await ctx.send(embed=create_leaderboard("Rat Leaderboard", "users"))
        
@bot.command()
async def facestats(ctx):
        await ctx.send(embed=create_leaderboard("Face Rat Leaderboard", "faceusers"))      
        
bot.run(token, log_handler=handler, log_level=logging.DEBUG) 