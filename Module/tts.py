from __future__ import annotations

import logging
import os
import re
import aiosqlite
import traceback

import disnake
from disnake import FFmpegPCMAudio
from disnake.ext import commands
from gtts import gTTS
from asgiref.sync import sync_to_async as s2a

from utils.ClientUser import ClientUser as Client

LANGUAGE_LIST = ["English", "Tiếng Việt", "日本語", "русский", "中国人"]


def check_voice():

    async def predicate(inter):


        guild = inter.guild

        try:
            if not inter.author.voice:
                await inter.send("Nya Nya nyan, pliz join a voice channel")
                return
        except AttributeError:
            pass

        if not guild.me.voice:

            perms = inter.author.voice.channel.permissions_for(guild.me)

            if not perms.connect:
                await inter.send("Nya! 💢, I dont have perm to connect to your channel")
                return

        try:
            if inter.author.id not in guild.me.voice.channel.voice_states:
                return
        except AttributeError:
            pass

        return True

    return commands.check(predicate)


async def save_lang_tts(guildID, language):
    async with aiosqlite.connect("langDB.sql") as comm:
        cur = await comm.cursor()
        await cur.execute("""INSERT INTO guildLang (guildID, language) VALUES (?, ?)""", (guildID, language))
        await comm.commit()

async def get_tts_lang(guildID):
    async with aiosqlite.connect("langDB.sql") as comm:
            mouse = await comm.cursor()
            await mouse.execute("SELECT language FROM guildLang WHERE guildID = ?", (guildID,))
            data = await mouse.fetchone()
            if not data:
                return "Tiếng Việt"

            return data[0]


async def setup_table() -> None:
    async with aiosqlite.connect("langDB.sql") as comm:
        mouse = await comm.cursor()
        await mouse.execute("""CREATE TABLE IF NOT EXISTS guildLang(
                                                    guildID INTEGER,
                                                    language TEXT DEFAULT 'Tiếng Việt')""")
        await comm.commit()


async def check_lang(lang):
    pattern = r"^[a-z]{2}$"
    return bool(re.match(pattern, lang))


async def convert_language(lang):
    langlist = {"English": "en",
                "Tiếng Việt": "vi",
                "日本語": "ja",
                "русский": "ru",
                "中国人": "zh"
                }
    return langlist.get(lang)


def process_tts(text, guild_id, channel_id, lang):
    tts = gTTS(text, lang=lang)
    if not os.path.exists(f'./data_tts/{guild_id}'):
        os.makedirs(f'./data_tts/{guild_id}')
    tts.save(f'./data_tts/{guild_id}/{channel_id}_tts.mp3')


class TTS(commands.Cog):
    emoji = "🔊"
    name = "TTS"
    desc_prefix = f"[{emoji} {name}] | "

    def __init__(self, bot: Client):
        self.bot = bot

    @commands.Cog.listener("on_ready")
    async def initalize(self):
        try:
            await setup_table()
        except Exception as e:
            self.bot.log.error(e)

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(description=f"{desc_prefix}Tạo âm thanh từ văn bản", aliases=["s", "speak"])
    async def say(self, ctx: disnake.AppCommandInteraction, *, content = None):

        if content is None:
            return

        if not ctx.author.voice:
            await ctx.send("u forgot something, didnt u?")
            return

        if not ctx.guild.me.voice:

            perms = ctx.author.voice.channel.permissions_for(ctx.guild.me)

            if not perms.connect:
                await ctx.send("No permission ill bro 😭🙏🙏")
                return


        lang = await get_tts_lang(ctx.author.guild.id)
        convlang = await convert_language(lang)

        # Task

        channel = ctx.author.voice.channel

        try:
            vc: disnake.VoiceClient = await channel.connect()
        except Exception as e:
            if "Already connected to a voice channel" in str(e):
                vc = ctx.author.guild.voice_client
            else:
                traceback.print_exc()
                await ctx.channel.send(f"Error!")
                return

        channel_id = ctx.guild.me.voice.channel.id
        guild_id = ctx.guild.id

        if vc.is_playing():
            await ctx.send("Still playing, please wait...", delete_after=10); return

        await s2a(process_tts)(content, guild_id, channel_id, convlang)

        try:
            vc.play(FFmpegPCMAudio(f"./data_tts/{guild_id}/{channel_id}_tts.mp3", executable=self.bot.ffmpeg))
        except disnake.errors.ClientException as e:
            if "ffmpeg.exe was not found." or "ffmpeg was not found." in str(e):
                await ctx.send(f"FFmpeg not found, plis contact developer for fix idk")
                self.bot.log.error("Không có ffmpeg hoặc hệ thống không hỗ trợ ffmpeg, vui lòng kiểm tra lại")
            return await self.bot.close()
        except Exception: traceback.print_exc(); await ctx.channel.send(f"Cant play TS")

    @commands.command(description=f"{desc_prefix}Disconnect", aliases=["stoptts"])
    async def tts_stop(self, ctx: disnake.ApplicationCommandInteraction):

        vc = ctx.author.guild.voice_client
        if vc:
            if ctx.author.id not in ctx.guild.me.voice.channel.voice_states:
                await ctx.send("What do u want.")
                return
            try:
                os.remove(f"./data_tts/{ctx.guild.id}/{ctx.guild.me.voice.channel.id}_tts.mp3")
            except FileNotFoundError:
                pass
            except Exception as e:
                await ctx.channel.send(f"Err.")
                logging.error(f"Error {e}")

            await vc.disconnect()
            await ctx.send("Disconnected.", delete_after=3)
        else:
            await ctx.channel.send("No client connected.")

    @commands.cooldown(1, 15, commands.BucketType.guild)
    @commands.has_guild_permissions(manage_channels=True)
    @commands.slash_command(name = "tts_language", description=f"{desc_prefix} Change language for tts module", options=[disnake.Option('language', description='Language', required=True)])
    async def tts_language(self, ctx: disnake.ApplicationCommandInteraction, language: str = None):
        await ctx.response.defer(ephemeral=True)
        await save_lang_tts(ctx.author.guild.id, language)
        await ctx.edit_original_response(f"Language changed to: {language}")

    @tts_language.autocomplete('language')
    async def get_lang(self, inter: disnake.Interaction, lang: str):
        lang = lang.lower()
        if not lang:
            return [lang for lang in LANGUAGE_LIST]

        return [lang for lang in LANGUAGE_LIST if lang.lower() == lang.lower()]


def setup(bot: Client):
    bot.add_cog(TTS(bot))
