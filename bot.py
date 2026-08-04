import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import urllib.request
import time

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is online!')

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

def self_ping():
    time.sleep(10)
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if render_url:
        while True:
            try:
                urllib.request.urlopen(render_url)
            except Exception:
                pass
            time.sleep(240)

threading.Thread(target=self_ping, daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# YouTube Bot Block Bypass Configuration (Lara bot er moto kaj korar jonno)
ytdl_format_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

@bot.event
async def on_ready():
    print(f'Bot active: {bot.user.name}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

@bot.tree.command(name="play", description="Play song from YouTube name or URL")
async def play(interaction: discord.Interaction, query: str):
    await interaction.response.defer()
    
    if not interaction.user.voice:
        await interaction.followup.send("❌ Prothome Voice Channel-e join korun!")
        return

    channel = interaction.user.voice.channel
    bot_vc = interaction.guild.voice_client

    try:
        if bot_vc is None:
            bot_vc = await channel.connect()
        elif bot_vc.channel != channel:
            await bot_vc.move_to(channel)

        loop = asyncio.get_event_loop()
        
        search_query = query if query.startswith("http://") or query.startswith("https://") else f"ytsearch:{query}"
        
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search_query, download=False))
        
        if 'entries' in data and len(data['entries']) > 0:
            data = data['entries'][0]

        filename = data.get('url')
        title = data.get('title', 'YouTube Audio')

        if not filename:
            await interaction.followup.send("❌ YouTube theke audio khuje pawa jayni!")
            return

        if bot_vc.is_playing() or bot_vc.is_paused():
            bot_vc.stop()

        source = discord.FFmpegPCMAudio(filename, **ffmpeg_options)
        
        def after_playing(error):
            if error:
                print(f'Player error: {error}')

        bot_vc.play(source, after=after_playing)

        await interaction.followup.send(f"🎵 **Playing from YouTube:** {title}")
    except Exception as e:
        await interaction.followup.send(f"❌ YouTube gan bajate somossha hocche! Error: {e}")

@bot.tree.command(name="stop", description="Stop music")
async def stop(interaction: discord.Interaction):
    bot_vc = interaction.guild.voice_client

    if bot_vc and (bot_vc.is_playing() or bot_vc.is_paused()):
        bot_vc.stop()
        await interaction.response.send_message("⏹️ Gan bondho kora holo!")
    elif bot_vc:
        await interaction.response.send_message("Kono gan cholche na!")
    else:
        await interaction.response.send_message("❌ Ami kono VC-te nei!", ephemeral=True)

@bot.tree.command(name="leave", description="Make bot leave VC")
async def leave(interaction: discord.Interaction):
    bot_vc = interaction.guild.voice_client

    if bot_vc:
        await bot_vc.disconnect()
        await interaction.response.send_message("👋 VC theke leave nilam!")
    else:
        await interaction.response.send_message("❌ Ami kono VC-te nei!", ephemeral=True)

TOKEN = os.getenv('DISCORD_TOKEN')
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ DISCORD_TOKEN paoa jayni!")
