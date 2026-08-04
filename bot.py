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

ytdl_format_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'scsearch',
    'source_address': '0.0.0.0',
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

@bot.tree.command(name="play", description="Search and play audio safely")
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
        
        if query.startswith("http://") or query.startswith("https://"):
            filename = query
            title = "Direct Stream URL"
        else:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=False))
            if 'entries' in data and len(data['entries']) > 0:
                data = data['entries'][0]
            filename = data.get('url')
            title = data.get('title', 'Requested Audio')

        if not filename:
            await interaction.followup.send("❌ Audio stream khuje pawa jayni!")
            return

        if bot_vc.is_playing() or bot_vc.is_paused():
            bot_vc.stop()

        source = discord.FFmpegPCMAudio(filename, **ffmpeg_options)
        bot_vc.play(source)

        await interaction.followup.send(f"🎵 **Playing:** {title}")
    except Exception as e:
        await interaction.followup.send(f"❌ Gan bajate somossha hocche! Error: {e}")

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
