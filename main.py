import cv2
import discord
#import dlib
from discord.ext import commands
from dotenv import load_dotenv
import io
import json
import logging
import numpy as np
import os
import requests
import random
import sqlite3
from thefuzz import fuzz

load_dotenv()
token = os.getenv("DISCORD_TOKEN")
env = os.getenv("ENVIRONMENT")

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="rat.", intents=intents)

conn = sqlite3.connect("userdata.db")
cur = conn.cursor()

face_detector = cv2.FaceDetectorYN.create("face_detection_yunet_2023mar.onnx", "", (600, 436), 0.9, 0.3, 5000)
# dlib_detector = dlib.get_frontal_face_detector()
# predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

with open('blocklist.json', 'r') as file:
    blocklist_data = json.load(file)

blocklist = blocklist_data['users']

@bot.event
async def on_ready():
        print("READY")

async def find_player():
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
        if ctx.message.channel.type == discord.ChannelType.private:
                return
        
        if ctx.message.author.name in blocklist:
                ctx.reply("YOU ARE A CHEATER!")
                return
        
        random_player, _, img = await find_player()
        
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
        if ctx.message.channel.type == discord.ChannelType.private:
                return
        
        if ctx.message.author.name in blocklist:
                ctx.reply("YOU ARE A CHEATER!")
                return
        
        while True:
                random_player, response, _ = await find_player()
                img_ary = np.asarray(bytearray(response.content), dtype=np.uint8)
                img_transparent = cv2.imdecode(img_ary, cv2.IMREAD_UNCHANGED)
                bgr = cv2.cvtColor(img_transparent, cv2.COLOR_BGRA2BGR)
                _, faces = face_detector.detect(bgr)
                if len(faces) == 0:
                        continue
                x, y, w, h = faces[0][:4].astype(int)
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
                
# async def get_landmarks(image):
#     faces = dlib_detector(image)
#     if len(faces) == 0: return None
#     landmarks = predictor(image, faces[0])
#     return [(p.x, p.y) for p in landmarks.parts()]

# async def get_face():
#     player, response, _ = await find_player()
#     img = cv2.imdecode(np.asarray(bytearray(response.content), dtype=np.uint8), cv2.IMREAD_COLOR_RGB)
#     points = None
#     while points is None:
#         points = await get_landmarks(img)
#     return player, img, points

# async def find_index(points, point):
#         distances = np.linalg.norm(points - point, axis=1)
#         return np.argmin(distances)

# async def warp_triangle(img, tri_in, tri_out):
#         r_in = cv2.boundingRect(np.float32([tri_in]))
#         r_out = cv2.boundingRect(np.float32([tri_out]))

#         tri_in_cropped = [((tri_in[i][0] - r_in[0]), (tri_in[i][1] - r_in[1])) for i in range(3)]
#         tri_out_cropped = [((tri_out[i][0] - r_out[0]), (tri_out[i][1] - r_out[1])) for i in range(3)]

#         img_in_cropped = img[r_in[1]:r_in[1] + r_in[3], r_in[0]:r_in[0] + r_in[2]]
        
#         warp_mat = cv2.getAffineTransform(np.float32(tri_in_cropped), np.float32(tri_out_cropped))
#         img_out_cropped = cv2.warpAffine(img_in_cropped, warp_mat, (r_out[2], r_out[3]), None, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
        
#         return img_out_cropped, r_out

# @bot.command()
# async def mash(ctx):
#         if ctx.message.channel.type == discord.ChannelType.private:
#                 return
        
#         if ctx.message.author.name in blocklist:
#                 ctx.reply("YOU ARE A CHEATER!")
#                 return
        
#         player1, img1, points1 = await get_face()
#         player2, img2, points2 = None, None, None
#         while not player2 or player2['id'] == player1['id']:
#                 player2, img2, points2 = await get_face()

#         height, width, _ = img1.shape
#         img2 = cv2.resize(img2, (width, height))

#         points1 = np.array([(np.clip(p[0], 0, width - 1), np.clip(p[1], 0, height - 1)) for p in points1], dtype=np.float32)
#         points2 = np.array([(np.clip(p[0], 0, width - 1), np.clip(p[1], 0, height - 1)) for p in points2], dtype=np.float32)

#         avg_points = (points1 + points2) / 2

#         rect = (0, 0, width, height)
#         subdiv = cv2.Subdiv2D(rect)
#         subdiv.insert(avg_points.tolist())

#         delaunay_triangles_coords = subdiv.getTriangleList()

#         delaunay_indices = []
#         for t in delaunay_triangles_coords:
#                 pt1 = (t[0], t[1])
#                 pt2 = (t[2], t[3])
#                 pt3 = (t[4], t[5])
        
#                 idx1 = await find_index(avg_points, pt1)
#                 idx2 = await find_index(avg_points, pt2)
#                 idx3 = await find_index(avg_points, pt3)
                
#                 if idx1 != idx2 and idx1 != idx3 and idx2 != idx3:
#                         delaunay_indices.append((idx1, idx2, idx3))

#         morphed_face_bgr = np.zeros(img1.shape, dtype=img1.dtype)
#         alpha_mask = np.zeros((height, width), dtype=np.uint8)

#         for indices in delaunay_indices:
#                 tri1 = [points1[indices[0]], points1[indices[1]], points1[indices[2]]]
#                 tri2 = [points2[indices[0]], points2[indices[1]], points2[indices[2]]]
#                 tri_avg = [avg_points[indices[0]], avg_points[indices[1]], avg_points[indices[2]]]

#                 warped_tri1, r1 = await warp_triangle(img1, tri1, tri_avg)
#                 warped_tri2, r2 = await warp_triangle(img2, tri2, tri_avg)

#                 if warped_tri1.shape != warped_tri2.shape:
#                         warped_tri2 = cv2.resize(warped_tri2, (warped_tri1.shape[1], warped_tri1.shape[0]))
                
#                 morphed_tri = cv2.addWeighted(warped_tri1, 0.5, warped_tri2, 0.5, 0)
                
#                 mask = np.zeros((r1[3], r1[2], 3), dtype=np.float32)
#                 tri_avg_cropped = [(tri_avg[i][0] - r1[0], tri_avg[i][1] - r1[1]) for i in range(3)]
#                 cv2.fillConvexPoly(mask, np.int32(tri_avg_cropped), (1.0, 1.0, 1.0), 16, 0)
                
#                 cv2.fillConvexPoly(alpha_mask, np.int32(tri_avg), (255), 16, 0)

#                 morphed_face_rect = morphed_face_bgr[r1[1]:r1[1]+r1[3], r1[0]:r1[0]+r1[2]]
#                 if mask.shape != morphed_tri.shape:
#                         morphed_tri = cv2.resize(morphed_tri, (mask.shape[1], mask.shape[0]))
#                 morphed_face_bgr[r1[1]:r1[1]+r1[3], r1[0]:r1[0]+r1[2]] = morphed_face_rect * (1 - mask) + morphed_tri * mask

#         b, g, r = cv2.split(morphed_face_bgr)
#         final_morphed_face = cv2.merge([b, g, r, alpha_mask])

#         rows, cols = np.where(alpha_mask > 0)
#         padding = 20
#         min_y = max(0, np.min(rows) - padding)
#         max_y = min(height - 1, np.max(rows) + padding)
#         min_x = max(0, np.min(cols) - padding)
#         max_x = min(width - 1, np.max(cols) + padding)

#         cropped_face = final_morphed_face[min_y:max_y+1, min_x:max_x+1]

#         rescaled_face = cv2.resize(cropped_face, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
#         final_image = cv2.cvtColor(rescaled_face, cv2.COLOR_BGRA2RGBA)
#         _, encoded_image = cv2.imencode(".png", final_image)
#         image_file = io.BytesIO(encoded_image.tobytes())
#         discord_file = discord.File(image_file, filename="image.png")
#         question = await ctx.reply(file=discord_file)
        
#         answer1 = None
#         answer2 = None
                
#         def check(m):
#                 nonlocal answer1, answer2
#                 if m.channel == ctx.message.channel and ctx.message.author == m.author:
#                         if fuzz.ratio(m.content.lower(), player1['displayName'].lower()) >= 80:
#                                 answer1 = m
#                         elif fuzz.ratio(m.content.lower(), player2['displayName'].lower()) >= 80:
#                                 answer2 = m
#                 return answer1 and answer2 
        
#         try:
#                 await bot.wait_for("message", check=check, timeout=15)
#         except:
#                 score = 0
#                 if answer1:
#                         score = .5
#                         await answer1.reply(f"<@{ctx.message.author.id}> YOU SPLIT! The other player was: {player2['displayName']}")
#                 elif answer2:
#                         score = .5
#                         await answer2.reply(f"<@{ctx.message.author.id}> YOU SPLIT! The other player was: {player1['displayName']}")
#                 else:
#                         await question.reply(f"<@{ctx.message.author.id}> YOU LOST! The correct answer was: {player1['displayName']} and {player2['displayName']}")
#                 cur.executescript(f"""
#                             BEGIN;
#                             INSERT OR IGNORE INTO mashusers VALUES (\'{ctx.message.author.name}\', 8, 0, 0, 0);
#                             UPDATE mashusers SET plays = plays + 1, correct = correct + {score} WHERE name=\'{ctx.message.author.name}\';
#                             UPDATE mashusers SET maxstreak = MAX(maxstreak, currstreak), currstreak = 0 WHERE name=\'{ctx.message.author.name}\';
#                             COMMIT;
#                             """)
#         else:
#                 await answer1.reply("YOU WON!")
#                 await answer2.reply("YOU WON!")
#                 cur.executescript(f"""
#                             BEGIN;
#                             INSERT OR IGNORE INTO mashusers VALUES (\'{ctx.message.author.name}\', 8, 0, 0, 0);
#                             UPDATE mashusers SET plays = plays + 1, correct = correct + 1 WHERE name=\'{ctx.message.author.name}\';
#                             UPDATE mashusers SET currstreak = currstreak + 1 WHERE name=\'{ctx.message.author.name}\'; 
#                             COMMIT;
#                             """)


async def create_leaderboard(title, db):
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
        await ctx.send(embed=await create_leaderboard("Rat Leaderboard", "users"))
        
@bot.command()
async def facestats(ctx):
        await ctx.send(embed=await create_leaderboard("Face Rat Leaderboard", "faceusers"))
        
# @bot.command()
# async def mashstats(ctx):
#         await ctx.send(embed=await create_leaderboard("Mash Rat Leaderboard", "mashusers"))      
       
if env == "dev": 
        bot.run(token, log_handler=handler, log_level=logging.DEBUG) 
else:
        bot.run(token, log_handler=None)