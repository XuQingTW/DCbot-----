#導入Discord.py
import discord
from discord import channel
from discord.ext import commands
from discord.flags import Intents
from discord.voice_client import VoiceClient
import random,os
from threading import Thread
from discord import FFmpegPCMAudio
import os
import json
import asyncio
import yt_dlp
import urllib.request
import ssl
#from . import pycld3
#client是我們與Discord連結的橋樑

#氣象APICWB-07D30AE2-5882-4240-9A5A-372F3F3EA24B
json_url = 'https://opendata.cwa.gov.tw/api/v1/rest/datastore/E-A0015-001?Authorization=CWB-07D30AE2-5882-4240-9A5A-372F3F3EA24B&limit=1&offset=0&format=JSON'
context = ssl._create_unverified_context()

#music 0=本地 1=網址


#open file music.json
with open('music.json','r') as file:
    data = json.load(file)
#open file music.json
with open('orange.json','r') as file:
    data_orange = json.load(file)
with open('data.json','r') as file:
    data_num = json.load(file)
#open
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!',intents = intents)
voice_clients = {}
directory_to_scan = r"D:\家龢用\音樂"
directory_orange = r"D:\家龢用\音樂\100"

ytdl_format_options = {
    'format': 'bestaudio/best',
    'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '256',
        }],
    'noplaylist': True,  # 不下載播放列表
    'quiet': True,  # 靜默模式，不打印下載信息
    'no_warnings': True,  # 不打印警告信息
}

ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }
#####################################################################################################################################

async def warning():
    send = 1224902159200686110
    channel = bot.get_channel(send)
    id = data_num["id"]
    print("start search")
    while True:
        with urllib.request.urlopen(json_url, context=context) as jsondata:
            #將JSON進行UTF-8的BOM解碼，並把解碼後的資料載入JSON陣列中
            data = json.loads(jsondata.read().decode('utf-8-sig'))
        data = data['records']['Earthquake'][0]
        if data['EarthquakeNo'] != id:
            print(data['EarthquakeNo'])
            embed = discord.Embed()
            embed.set_image(url=data['ReportImageURI'])
            if data["EarthquakeInfo"]["EarthquakeMagnitude"]["MagnitudeValue"] > 7:
                await channel.send(f"<@everyone>\n地震編號：{data['EarthquakeNo']}\n報告內容：{data['ReportContent']}\n",embed=embed)
            else:
                await channel.send(f"地震編號：{data['EarthquakeNo']}\n報告內容：{data['ReportContent']}\n",embed=embed)
            id = data['EarthquakeNo']
            with open('data.json','w') as f:
                data_num["id"] = data['EarthquakeNo']
                json.dump(data_num,f)
        await asyncio.sleep(30)



#####################################################################################################################################
#play command

async def set_random(ctx,vc,set):
    if set == "off":
            voice_clients[ctx.guild.id]["random"] = False
            await ctx.send("已關閉隨機播放")
    elif set == "on":
        voice_clients[ctx.guild.id]["random"] = True
        if vc.is_playing():#如果正在播放
            a = voice_clients[ctx.guild.id]["list"]
            number = voice_clients[ctx.guild.id]["song"]
            a = a[number:]
            random.shuffle(a)
            for i in range(len(voice_clients[ctx.guild.id]["list"])):#將下一首開始的順序換成隨機
                if i < number:
                    pass
                else:
                    voice_clients[ctx.guild.id]["list"][i] = a[i-number]
        await ctx.send("已開啟隨機播放，將播放隨機順序")
    elif set == None:
        if voice_clients[ctx.guild.id]["random"]:
            await ctx.send("隨機撥放中")
        else:
            await ctx.send("隨機撥放關閉中")
    else:
        await ctx.send("輸入錯誤(on or off)")
                
async def loop(ctx,vc,set):
    if set == "off":
        voice_clients[ctx.guild.id]["loop"] = False
        await ctx.send("已關閉重複播放")
    elif set == "on":
        voice_clients[ctx.guild.id]["loop"] = True
        await ctx.send("已開啟重複播放")
    elif set == None:
        if voice_clients[ctx.guild.id]["loop"]:
            await ctx.send("重複撥放中")
        else:
            await ctx.send("重複撥放已關閉")
    else:
        await ctx.send("輸入錯誤(on or off)")

async def youtube(ctx,vc,url):
    if "youtube.com/watch?v=" in url:
        voice_clients[ctx.guild.id]["list"].append([1,url])

    #如果url是youtube的直播，直接播放
#    if "youtube.com/watch?v=" in url:
#        loop = asyncio.get_event_loop()
#        vc.play(discord.FFmpegPCMAudio(url), after=lambda e:loop.create_task(next_song(ctx, vc)))
#        return

    #如果url是youtube的1ist，將list所有音樂加入list
    if "youtube.com/playlist?list=" in url:
        await ctx.send("本功能會導致bot炸掉，請先不要使用<3愛你呦")
        return
        with yt_dlp.YoutubeDL(ytdl_format_options) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                for i in info['entries']:
                    voice_clients[ctx.guild.id]["list"].append([1,i['url']])
                await ctx.send("已加入播放清單")
            except:
                pass

    if vc.is_playing():
        await ctx.send("已加入播放清單，等待播放")
    else:
        await playing_music(ctx,vc)
    

async def next(ctx,vc,set):#
    if len(voice_clients[ctx.guild.id]["list"]) == 0:
        await ctx.send("播放清單為空")
        return
    await ctx.send("接下來的歌為")
    song = voice_clients[ctx.guild.id]["list"][voice_clients[ctx.guild.id]["song"]]
    if song[0] == 0:
        song_name = os.path.basename(song[1])
        await ctx.send(song_name)
    elif song[0] == 1:
        song_name = song[1]
        await ctx.send(song_name)
async def defult(ctx,vc,set):
    for i in data:
        voice_clients[ctx.guild.id]["list"].append(i)
    await ctx.send("已加入播放清單")


play_command = {
    "random":set_random,
    "loop":loop,
    "youtube":youtube,
    "next":next,
    "defult":defult,
    "d":defult
    
}
#####################################################################################################################################
#function
def scan_music_files(directory):
    music_extensions = ['.m4a', '.mp3', '.wav', '.flac', '.aac', '.ogg']

    music_files = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in music_extensions):
                music_files.append([0,os.path.join(root, file)])
    return music_files

def save_json(data,a=True):
    if a:
        with open('music.json','w') as f:
            json.dump(data,f)
    else:
        with open('orange.json','w') as f:
            json.dump(data,f)


async def is_download_complete(song_file):
    # 檢查文件是否存在並且大於0字節
    try:
        file_stat = os.stat(song_file)
        if file_stat.st_size > 0:
            return True
    except FileNotFoundError:
        pass
    return False

async def playing_music(ctx, vc):
    slist = voice_clients[ctx.guild.id]["list"]
    
    if voice_clients[ctx.guild.id]["song"] == len(slist):#如果播完
        if voice_clients[ctx.guild.id]["loop"]:
            if voice_clients[ctx.guild.id]["random"]:
                random.shuffle(slist)
            voice_clients[ctx.guild.id]["song"] = 0
        else:
            voice_clients[ctx.guild.id]["list"] = []
            voice_clients[ctx.guild.id]["song"] = 0
            await ctx.send('No more songs in queue.')
            return

    loop = asyncio.get_event_loop()
    song = slist[voice_clients[ctx.guild.id]["song"]]##要改這裡
    voice_clients[ctx.guild.id]["song"] += 1
    if song[0] == 0:
        song = song[1]
        song_name = os.path.basename(song)
        vc.play(discord.FFmpegPCMAudio(song), after=lambda e:loop.create_task(next_song(ctx, vc)))
    elif song[0] == 1:
        with yt_dlp.YoutubeDL(ytdl_format_options) as ydl:
            try:
                info = ydl.extract_info(song[1], download=False)
                song_name = info['title']
                song = info['url']
                del info
                vc.play(discord.FFmpegPCMAudio(song, **ffmpeg_options), after=lambda e:loop.create_task(next_song(ctx, vc)))
            except:
                await ctx.send("無法一首該歌曲")
                await next_song(ctx,vc)
                return
    
    await ctx.send(f'Now playing: {song_name}')


async def next_song(ctx, vc, c = False):
    if ctx.guild.id not in voice_clients:
        return
    if voice_clients[ctx.guild.id]["stop"]:
        voice_clients[ctx.guild.id]["stop"] = False
        return
    if c:
        voice_clients[ctx.guild.id]["stop"] = True
    vc.stop()
    await playing_music(ctx,vc)
    
    


#調用event函式庫
@bot.event
#當機器人完成啟動時
async def on_ready():
    print('目前登入身份：',bot.user)
    game = discord.Game('成為白癡打工仔吧')
    #discord.Status.<狀態>，可以是online,offline,idle,dnd,invisible
    await bot.change_presence(status=discord.Status.online, activity=game)
    await bot.wait_until_ready()
    await warning()




#######################################################################################################
@bot.command()
async def join(ctx):
    voice_channel = ctx.author.voice.channel
    if voice_channel:
        if ctx.guild.id not in voice_clients:
            voice_clients[ctx.guild.id] = {"vc":await voice_channel.connect(),
                                           "list":[],
                                           "random":False,
                                           "loop":False,
                                           "song":0,
                                           "stop":False}
            await ctx.send(f'Joined {voice_channel.name}')
        else:
            await ctx.send('Already in a voice channel.')
    else:
        await ctx.send('You are not connected to a voice channel.')

@bot.command()
async def leave(ctx):
    if ctx.guild.id in voice_clients:
        vc = voice_clients[ctx.guild.id]["vc"]
        if vc.is_playing():
            voice_clients[ctx.guild.id]["stop"] = True
            vc.stop()  
        await voice_clients[ctx.guild.id]["vc"].disconnect()
        del voice_clients[ctx.guild.id]
        await ctx.send('Left the voice channel.')
    else:
        await ctx.send('Not in a voice channel.')

@bot.command()
async def play(ctx,mod=None,set=None):
    if ctx.guild.id not in voice_clients:
        await join(ctx)
    vc = voice_clients[ctx.guild.id]["vc"]
    if mod==None:
        if voice_clients[ctx.guild.id]["random"]:
            random.shuffle(voice_clients[ctx.guild.id]["list"])
        await playing_music(ctx,vc)
    elif mod in play_command:
        await play_command[mod](ctx,vc,set)
    else:
        await ctx.send("輸入錯誤")



@bot.command()
async def pause(ctx):
    if ctx.guild.id in voice_clients:
        vc = voice_clients[ctx.guild.id]["vc"]
        if vc.is_playing():
            vc.pause()

@bot.command()
async def resume(ctx):
    if ctx.guild.id in voice_clients:
        vc = voice_clients[ctx.guild.id]["vc"]
        if vc.is_paused():
            vc.resume()


@bot.command()
async def scan(ctx):
    music = scan_music_files(directory_to_scan)
    save_json(music)
    await ctx.send(f"在目標資料夾尋找到{len(music)}首歌曲")

@bot.command()
async def orange_scan(ctx):
    music = scan_music_files(directory_orange)
    save_json(music,False)
    await ctx.send(f"在目標資料夾尋找到{len(music)}首歌曲")

@bot.command()
async def next(ctx):
    if ctx.guild.id in voice_clients:
        vc = voice_clients[ctx.guild.id]["vc"]
        await next_song(ctx,vc,True)
@bot.command()
async def stop(ctx):
    if ctx.guild.id in voice_clients:
        vc = voice_clients[ctx.guild.id]["vc"]
        voice_clients[ctx.guild.id]["list"] = []
        voice_clients[ctx.guild.id]["song"] = 0
        voice_clients[ctx.guild.id]["stop"] = True
        vc.stop()
@bot.command()
async def special(ctx):
    song = r"D:\SteamLibrary\steamapps\music\100% Orange Juice - Character Song Pack Ultimate Weapon Girl\Ultimate Weapon Girl - Character Song Pack OST\Track 5 - Ultimate Weapon Girl (Bonus Track).mp3"
    if ctx.guild.id in voice_clients:
        vc = voice_clients[ctx.guild.id]["vc"]
        vc.play(discord.FFmpegPCMAudio(song))
        song_name = os.path.basename(song)
        await ctx.send(f'Now playing: ??????????????????????????????????????????')
    else:
        await ctx.send('Not in a voice channel.')

@bot.command()
async def CNM(ctx):
    song = r"C:\Users\ASUS\Downloads\【戰地風雲4】戰地4中文神配音 - 友軍之圍  笑死了！我中彈了....wav"
    if ctx.guild.id in voice_clients:
        vc = voice_clients[ctx.guild.id]["vc"]
        vc.play(discord.FFmpegPCMAudio(song))
        song_name = os.path.basename(song)
        await ctx.send(f'Now playing: ??????????????????????????????????????????')
    else:
        await ctx.send('Not in a voice channel.')
@bot.command()
async def orange(ctx):
    if ctx.guild.id in voice_clients:
        vc = voice_clients[ctx.guild.id]["vc"]
        voice_clients[ctx.guild.id]["list"] = data_orange
        if voice_clients[ctx.guild.id]["random"]:
            random.shuffle(voice_clients[ctx.guild.id]["list"])
        await playing_music(ctx,vc)
    else:
        await join(ctx)
        await orange(ctx)
@bot.command()
async def c(ctx):
    await ctx.send(voice_clients)

    
@bot.command()
async def chelp(ctx):
    await ctx.send("""可憐打工仔的指令:
    !join - 加入語音頻道
    !leave - 離開語音頻道
    !play - 播放
           random (on/off/空氣)- 隨機播放
           loop (on/off/空氣) - 重複播放
           youtube (URL) - 播放youtube歌曲(雖然這樣說但twitch也可以撥放~~抖音好想也可以~~)
           next - 顯示下一首歌曲
           defoult/d - 播放預設歌曲(我電腦的所有歌)
    !pause - 暫停
    !resume - 繼續
    !stop - 停止
    !next - 跳到下一首
    !scan - 更新音樂資料夾
    !chelp - 顯示指令説明
    !orange - orange juice
    !special - ???
    !CNM - 戰地風雲4中文神配音
    !c - 開發者debug用工具""")
#########################################################################################################




@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author == bot.user:
        return
    if message.channel.id == 1216603222215491594:
        image = []
        try:
            for i in message.attachments:
                 image.append(i.url)
        except:
            pass
        send = 1216430186917003428
        channel = bot.get_channel(send)
        if len(image) == 0:
            await channel.send(message.content)
        else:
            for i in image:
                await channel.send(i)
        return
    elif message.channel.id == 1216602901695430676:
        image = []
        try:
            for i in message.attachments:
                image.append(i.url)
        except:
            pass
        send = 1216430327585833041
        channel = bot.get_channel(send)
        if len(image) == 0:
            await channel.send(message.content)
        else:
            for i in image:
                await channel.send(i)


                
@bot.event
async def on_message_edit(before, after):

    if before.content != after.content:
        if before.channel.id == 1216603222215491594:
            send = 1216430186917003428
            channel = bot.get_channel(send)
            await channel.send(after.content)
        elif before.channel.id == 1216602901695430676:
            send = 1216430327585833041
            channel = bot.get_channel(send)
            await channel.send("編輯後:"+after.content)
        

@bot.event
async def on_raw_reaction_add(payload):
    print (payload.emoji)
    guild = bot.get_guild(payload.guild_id)
    if payload.message_id == 1216564236487229562:#分群身分組一般人跟怪人
        if str(payload.emoji) == '<:miku:1216434199675015188>':
            role = 1216560881719050260
            role = guild.get_role(role)
            await payload.member.add_roles(role)
        elif str(payload.emoji) == '<:emoji_2:1216564009692692491>':
            role = 1216560795261861939
            role = guild.get_role(role)
            await payload.member.add_roles(role)
    elif payload.message_id == 1216688099036495902:#主群身分組一般人跟怪人
        if str(payload.emoji) == '<:blue_archive:1197924218160025660>':
            role = 1216400867356573706
            role = guild.get_role(role)
            await payload.member.add_roles(role)
        elif str(payload.emoji) == '<:more18:1162345474586591263>':
            role = 1216400764033957888
            role = guild.get_role(role)
            await payload.member.add_roles(role)
@bot.event
async def on_raw_reaction_remove(payload):
    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    if payload.message_id == 1216564236487229562:#分群身分組一般人跟怪人
        if str(payload.emoji) == '<:miku:1216434199675015188>':
            role = 1216560881719050260
            role = guild.get_role(role)
            await member.remove_roles(role)
        elif str(payload.emoji) == '<:emoji_2:1216564009692692491>':
            role = 1216560795261861939
            role = guild.get_role(role)
            await member.remove_roles(role)
    elif payload.message_id == 1216688099036495902:#主群身分組一般人跟怪人
        if str(payload.emoji) == '<:blue_archive:1197924218160025660>':
            role = 1216400867356573706
            role = guild.get_role(role)
            await member.remove_roles(role)
        elif str(payload.emoji) == '<:more18:1162345474586591263>':
            role = 1216400764033957888
            role = guild.get_role(role)
            await member.remove_roles(role)

bot.run('') 
