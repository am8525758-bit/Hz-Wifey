import discord
from discord.ext import commands
import yt_dlp
import asyncio

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
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

# /play
@bot.tree.command(name="play", description="Play audio from YouTube")
async def play(interaction: discord.Interaction, search: str):
    await interaction.response.defer()
    
    if not interaction.user.voice:
        await interaction.followup.send("Ami apnar sathe voice channel-e nei! Prothome voice-e join korun.")
        return

    channel = interaction.user.voice.channel
    bot_vc = interaction.guild.voice_client

    if bot_vc is None:
        bot_vc = await channel.connect()
    elif bot_vc.channel != channel:
        await bot_vc.move_to(channel)

    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search, download=False))

    if 'entries' in data:
        data = data['entries'][0]

    filename = data['url']
    title = data.get('title', 'Audio')

    if bot_vc.is_playing() or bot_vc.is_paused():
        bot_vc.stop()

    source = discord.FFmpegPCMAudio(filename, **ffmpeg_options)
    bot_vc.play(source)

    await interaction.followup.send(f"🎵 **Playing:** {title}")

# /stop
@bot.tree.command(name="stop", description="Stop audio")
async def stop(interaction: discord.Interaction):
    bot_vc = interaction.guild.voice_client

    if bot_vc and (bot_vc.is_playing() or bot_vc.is_paused()):
        bot_vc.stop()
        await interaction.response.send_message("⏹️ Gan bondho kora holo!")
    elif bot_vc:
        await interaction.response.send_message("Kono gan cholche na!")
    else:
        await interaction.response.send_message("Ami kono VC-te nei!", ephemeral=True)

# /leave
@bot.tree.command(name="leave", description="Bot leaves VC")
async def leave(interaction: discord.Interaction):
    bot_vc = interaction.guild.voice_client

    if bot_vc:
        await bot_vc.disconnect()
        await interaction.response.send_message("👋 VC theke leave nilam!")
    else:
        await interaction.response.send_message("Ami kono VC-te nei!", ephemeral=True)

# ⚠️ Ekhane tomar Discord Bot Token boshao
bot.run('MTUwMzUxNTczODAwNTE4MDQ4Nw.GogUwE.9OqIrs4Phf1gRSvc6Q9RNxaixuBovtpFS7avEg')
