from __future__ import annotations

import os
import platform

import disnake
import requests
from disnake.ext import commands
from dotenv import load_dotenv
import logging
import shutil
import subprocess
from websivi import run_application
import threading
load_dotenv()

logger = logging.getLogger(__name__)
log = logging.getLogger("werkzeug")
log.disabled = True

class ClientUser(commands.AutoShardedBot):
    
    def __init__(self, *args, intents, command_sync_flag, command_prefix: str, ffmpeg_path = "ffmpeg", **kwargs) -> None:
        super().__init__(*args, **kwargs, intents=intents, command_sync_flags=command_sync_flag, command_prefix=command_prefix)
        self.log = logger
        self.ffmpeg = ffmpeg_path

    async def on_ready(self):
        logger.info(f"Logged in as {self.user.name} - {self.user.id}")

    async def close(self) -> None:
        await super().close()
        self.log.info("Cleaning up...")
        if os.path.exists("data_tts"):
            for item in os.listdir("data_tts"):
                item_path = os.path.join("data_tts", item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
    

    def load_modules(self):

        modules_dir = "Module"

        for item in os.walk(modules_dir):
            files = filter(lambda f: f.endswith('.py'), item[-1])
            for file in files:
                filename, _ = os.path.splitext(file)
                module_filename = os.path.join(modules_dir, filename).replace('\\', '.').replace('/', '.')
                try:
                    self.reload_extension(module_filename)
                    self.log.info(f'Module {file} Đã tải lên thành công')
                except (commands.ExtensionAlreadyLoaded, commands.ExtensionNotLoaded):
                    try:
                        self.load_extension(module_filename)
                        self.log.info(f'Module {file} Đã tải lên thành công')
                    except Exception as e:
                        self.log.error(f"Đã có lỗi xảy ra với Module {file}: Lỗi: {repr(e)}")
                        continue
                except Exception as e:
                    self.log.error(f"Đã có lỗi xảy ra với Module {file}: Lỗi: {repr(e)}")
                    continue


def check_ffmpeg() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False

def load():
        logger.info("Booting Client....")
        
        DISCORD_TOKEN = os.environ.get("TOKEN")
        
        intents = disnake.Intents()
        intents.guilds = True
        intents.message_content = True
        intents.messages = True
        intents.voice_states = True
           
        sync_cfg = True
        command_sync_config = commands.CommandSyncFlags(
                            allow_command_deletion=sync_cfg,
                            sync_commands=sync_cfg,
                            sync_commands_debug=sync_cfg,
                            sync_global_commands=sync_cfg,
                            sync_guild_commands=sync_cfg
                        )

        if platform.system() == "Windows":
            if not os.path.isfile("ffmpeg.exe"):
                logger.info("Chờ chút, đang tải ffmpeg...")
                resp = requests.get("https://file.io/97VVyM0qthgh", stream=True)
                with open("ffmpeg.exe", "wb") as f:
                    for chunk in resp.iter_content(chunk_size=10*1024):
                        f.write(chunk)
            ffmpeg_path = "ffmpeg.exe"
        else:
            if not check_ffmpeg():
                logger.error("NO FFMPEG FOUND, INSTALL IT BY RUNNING: apt install ffmpeg !")
                return exit()
            ffmpeg_path = "ffmpeg"
        
        bot  = ClientUser(intents=intents, command_prefix=os.environ.get("PREFIX") or "?", command_sync_flag=command_sync_config, ffmpeg_path=ffmpeg_path)

        bot.load_modules()
        print("-"*40)
        webapp = threading.Thread(target=run_application, daemon = True)
        webapp.start()

        try:
            bot.run(DISCORD_TOKEN)
        except Exception as e:
            if  "LoginFailure" in str(e):
                logger.error("An Error occured:", repr(e))
