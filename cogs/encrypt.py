import discord
import asyncio
import os
import aiofiles.os
import shutil
from discord.ext import commands
from discord import Option
from aiogoogle import HTTPError
from network import FTPps, SocketPS, FTPError, SocketError
from google_drive import GDapiError
from data.crypto import CryptoError
from utils.constants import (
    IP, PORT, PS_UPLOADDIR, PORTSOCKET, MAX_FILES, BASE_ERROR_MSG, RANDOMSTRING_LENGTH, MOUNT_LOCATION, SCE_SYS_CONTENTS, PS_ID_DESC,
    logger, Color,
    embhttp, emb6, emb14
)
from utils.workspace import initWorkspace, makeWorkspace, WorkspaceError, cleanup, cleanupSimple, enumerateFiles
from utils.extras import generate_random_string, obtain_savenames
from utils.helpers import psusername, upload2, errorHandling, send_final
from utils.orbis import obtainCUSA, OrbisError
from utils.exceptions import PSNIDError, FileError
from utils.helpers import replaceDecrypted

class Encrypt(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @discord.slash_command(description="Swap the decrypted savefile from the encrypted ones you upload.")
    async def encrypt(
              self, 
              ctx: discord.ApplicationContext, 
              upload_individually: Option(bool, description="Choose if you want to upload the decrypted files one by one, or the ones you want at once."), # type: ignore
              include_sce_sys: Option(bool, description="Choose if you want to upload the contents of the 'sce_sys' folder."), # type: ignore
              playstation_id: Option(str, description=PS_ID_DESC, default="") # type: ignore
            ) -> None:
        
        newUPLOAD_ENCRYPTED, newUPLOAD_DECRYPTED, newDOWNLOAD_ENCRYPTED, newPNG_PATH, newPARAM_PATH, newDOWNLOAD_DECRYPTED, newKEYSTONE_PATH = initWorkspace()
        workspaceFolders = [newUPLOAD_ENCRYPTED, newUPLOAD_DECRYPTED, newDOWNLOAD_ENCRYPTED, 
                            newPNG_PATH, newPARAM_PATH, newDOWNLOAD_DECRYPTED, newKEYSTONE_PATH]
        try: await makeWorkspace(ctx, workspaceFolders, ctx.channel_id)
        except WorkspaceError: return
        C1ftp = FTPps(IP, PORT, PS_UPLOADDIR, newDOWNLOAD_DECRYPTED, newUPLOAD_DECRYPTED, newUPLOAD_ENCRYPTED,
                    newDOWNLOAD_ENCRYPTED, newPARAM_PATH, newKEYSTONE_PATH, newPNG_PATH)
        C1socket = SocketPS(IP, PORTSOCKET)
        mountPaths = []

        try:
            user_id = await psusername(ctx, playstation_id)
            await asyncio.sleep(0.5)
            await ctx.edit(embed=emb14)
            uploaded_file_paths = await upload2(ctx, newUPLOAD_ENCRYPTED, max_files=MAX_FILES, sys_files=False, ps_save_pair_upload=True)
        except HTTPError as e:
            await ctx.edit(embed=embhttp)
            cleanupSimple(workspaceFolders)
            logger.exception(f"{e} - {ctx.user.name} - (expected)")
            return
        except (PSNIDError, TimeoutError, GDapiError) as e:
            await errorHandling(ctx, e, workspaceFolders, None, None, None)
            logger.exception(f"{e} - {ctx.user.name} - (expected)")
            return
        except Exception as e:
            await errorHandling(ctx, BASE_ERROR_MSG, workspaceFolders, None, None, None)
            logger.exception(f"{e} - {ctx.user.name} - (unexpected)")
            return

        savenames = await obtain_savenames(newUPLOAD_ENCRYPTED)
        full_completed = []

        if len(uploaded_file_paths) >= 2:
            random_string = generate_random_string(RANDOMSTRING_LENGTH)
            uploaded_file_paths = enumerateFiles(uploaded_file_paths, random_string)
            for save in savenames:
                realSave = f"{save}_{random_string}"
                random_string_mount = generate_random_string(RANDOMSTRING_LENGTH)
                try:
                    await aiofiles.os.rename(os.path.join(newUPLOAD_ENCRYPTED, save), os.path.join(newUPLOAD_ENCRYPTED, realSave))
                    await aiofiles.os.rename(os.path.join(newUPLOAD_ENCRYPTED, save + ".bin"), os.path.join(newUPLOAD_ENCRYPTED, realSave + ".bin"))

                    embmo = discord.Embed(title="Encryption & Resigning process: Initializing",
                        description=f"Mounting {save}.",
                        colour=Color.DEFAULT.value)
                    embmo.set_footer(text="Made by hzh.")
                    await ctx.edit(embed=embmo)

                    await C1ftp.uploadencrypted_bulk(realSave)
                    mount_location_new = MOUNT_LOCATION + "/" + random_string_mount
                    await C1ftp.make1(mount_location_new)
                    mountPaths.append(mount_location_new)
                    await C1socket.socket_dump(mount_location_new, realSave)
                
                    files = await C1ftp.ftpListContents(mount_location_new)

                    if len(files) == 0: raise FileError("Could not list any decrypted saves!")
                    location_to_scesys = mount_location_new + "/sce_sys"
                    await C1ftp.dlparamonly_grab(location_to_scesys)
                    title_id = await obtainCUSA(newPARAM_PATH)
 
                    completed = await replaceDecrypted(ctx, C1ftp, files, title_id, mount_location_new, upload_individually, newUPLOAD_DECRYPTED, save)

                    if include_sce_sys:
                        if len(await aiofiles.os.listdir(newUPLOAD_DECRYPTED)) > 0:
                            shutil.rmtree(newUPLOAD_DECRYPTED)
                            await aiofiles.os.mkdir(newUPLOAD_DECRYPTED)
                            
                        embSceSys = discord.Embed(title=f"Upload: sce_sys contents\n{save}",
                            description="Please attach the sce_sys files you want to upload.",
                            colour=Color.DEFAULT.value)
                        embSceSys.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
                        embSceSys.set_footer(text="Made by hzh.")

                        await ctx.edit(embed=embSceSys)
                        uploaded_file_paths_sys = await upload2(ctx, newUPLOAD_DECRYPTED, max_files=len(SCE_SYS_CONTENTS), sys_files=True, ps_save_pair_upload=False)

                        if len(uploaded_file_paths_sys) <= len(SCE_SYS_CONTENTS) and len(uploaded_file_paths) >= 1:
                            filesToUpload = await aiofiles.os.listdir(newUPLOAD_DECRYPTED)
                            await C1ftp.upload_scesysContents(ctx, filesToUpload, location_to_scesys)
                        
                    location_to_scesys = mount_location_new + "/sce_sys"
                    await C1ftp.dlparam(location_to_scesys, user_id)
                    await C1socket.socket_update(mount_location_new, realSave)
                    await C1ftp.dlencrypted_bulk(False, user_id, realSave)

                    if len(completed) == 1: completed = "".join(completed)
                    else: completed = ", ".join(completed)
                    full_completed.append(completed)

                    embmidComplete = discord.Embed(title="Encrypting & Resigning Process: Successful",
                                description=f"Resigned **{completed}** with title id **{title_id}** to **{playstation_id or user_id}**.",
                                colour=Color.DEFAULT.value)
                    embmidComplete.set_footer(text="Made by hzh.")

                    await ctx.edit(embed=embmidComplete)
                except HTTPError as e:
                    await ctx.edit(embed=embhttp)
                    cleanup(C1ftp, workspaceFolders, uploaded_file_paths, mountPaths)
                    logger.exception(f"{e} - {ctx.user.name} - (expected)")
                    return
                except (SocketError, FTPError, OrbisError, FileError, CryptoError, OSError) as e:
                    if isinstance(e, OSError) and hasattr(e, "winerror") and e.winerror == 121: 
                        e = "PS4 not connected!"
                    await errorHandling(ctx, e, workspaceFolders, uploaded_file_paths, mountPaths, C1ftp)
                    logger.exception(f"{e} - {ctx.user.name} - (expected)")
                    return
                except Exception as e:
                    await errorHandling(ctx, BASE_ERROR_MSG, workspaceFolders, uploaded_file_paths, mountPaths, C1ftp)
                    logger.exception(f"{e} - {ctx.user.name} - (unexpected)")
                    return
                
            if len(full_completed) == 1: full_completed = "".join(full_completed)
            else: full_completed = ", ".join(full_completed)

            embComplete = discord.Embed(title="Encrypting & Resigning Process: Successful: Successful",
                            description=f"Resigned **{full_completed}** to **{playstation_id or user_id}**.",
                            colour=Color.DEFAULT.value)
            embComplete.set_footer(text="Made by hzh.")

            await ctx.edit(embed=embComplete)

            try: 
                await send_final(ctx, "PS4.zip", newDOWNLOAD_ENCRYPTED)
            except HTTPError as e:
                errmsg = "HTTPError while uploading file to Google Drive, if problem reoccurs storage may be full."
                await errorHandling(ctx, errmsg, workspaceFolders, uploaded_file_paths, mountPaths, C1ftp)
                logger.exception(f"{e} - {ctx.user.name} - (expected)")
                return

            await asyncio.sleep(1)
            await cleanup(C1ftp, workspaceFolders, uploaded_file_paths, mountPaths)
        else:
            await ctx.edit(embed=emb6)
            cleanupSimple(workspaceFolders)

def setup(bot: commands.Bot) -> None:
    bot.add_cog(Encrypt(bot))