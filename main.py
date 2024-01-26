import discord
import os, shutil
from discord.ext import commands
from discord import Option
import asyncio
from dotenv import load_dotenv
from network import FTPps, FTPError, SocketPS, SocketError
from google_drive import GDapi, GDapiError
from aiogoogle import HTTPError
import aiosqlite
from utils.constants import (
    bot, IP, PORT, PORTSOCKET, MOUNT_LOCATION, PS_UPLOADDIR, RANDOMSTRING_LENGTH, DATABASENAME, 
    FILE_LIMIT_DISCORD, SCE_SYS_CONTENTS, GTAV_TITLEID, BL3_TITLEID, RDR2_TITLEID, XENO2_TITLEID,
    NPSSO, MAX_FILES, UPLOAD_TIMEOUT, PS_ID_DESC, BOT_DISCORD_UPLOAD_LIMIT, emb12, emb14, emb17, emb20, emb21, emb22, embgdt, embEncrypted1, embDecrypt1,
    emb6, embhttp, embpng, embpng1, embpng2, emb8, embvalidpsn, embnv, embnv1, embnt, embUtimeout, embinit, embTitleChange)
from utils.workspace import startup, initWorkspace, makeWorkspace, cleanup, cleanupSimple, enumerateFiles, listStoredSaves, WorkspaceError
from utils.orbis import obtainCUSA, checkid, checkSaves, handle_accid, OrbisError, obtainID, handleTitles
from utils.extras import generate_random_string, zipfiles, pngprocess
from utils.exceptions import FileError, PSNIDError
from data import Converter, ConverterError, CustomCrypto, CryptoError
import aiofiles
import aiohttp
import re
import json
if NPSSO is not None:
    from psnawp_api import PSNAWP
    from psnawp_api.core.psnawp_exceptions import PSNAWPNotFound
    NPPSO = str(os.getenv("NPSSO"))
    psnawp = PSNAWP(NPPSO)
    print("psnawp initialized")

load_dotenv()

C1socket = SocketPS(IP, PORTSOCKET)

async def errorHandling(ctx, error: str, workspaceFolders: list, uploaded_file_paths: list, mountPaths: list, C1ftp: FTPps) -> None:
    embe = discord.Embed(title="Error",
                            description=error,
                    colour=0x854bf7)
    embe.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
    embe.set_footer(text="Made with expertise by HTOP")
    await ctx.edit(embed=embe)
    if C1ftp is not None:
        await cleanup(C1ftp, workspaceFolders, uploaded_file_paths, mountPaths)
    else:
        cleanupSimple(workspaceFolders)

async def upload2(ctx, saveLocation: str, max_files: int, sys_files: bool, ps_save_pair_upload: bool) -> list | None:

    def check(message, ctx) -> discord.Attachment | str:
        if message.author == ctx.author and message.channel == ctx.channel:
            return len(message.attachments) >= 1 or (message.content and GDapi.is_google_drive_link(message.content))

    try:
        message = await bot.wait_for("message", check=lambda message: check(message, ctx), timeout=UPLOAD_TIMEOUT)  # Wait for 300 seconds for a response with one attachments
    except asyncio.TimeoutError:
        await ctx.edit(embed=embUtimeout)
        raise TimeoutError("TIMED OUT!")

    if len(message.attachments) >= 1 and len(message.attachments) <= max_files:
        attachments = message.attachments
        uploaded_file_paths = []
        await message.delete()
        valid_attachments = await checkSaves(ctx, attachments, ps_save_pair_upload, sys_files)

        for attachment in valid_attachments:
            file_path = os.path.join(saveLocation, attachment.filename)
            await attachment.save(file_path)
            
            emb1 = discord.Embed(title="Upload alert: Successful", description=f"File '{attachment.filename}' has been successfully uploaded and saved.",colour=0x854bf7)
            emb1.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
            emb1.set_footer(text="Made with expertise by HTOP")
            
            await ctx.edit(embed=emb1)
            print(f"Uploaded {attachment.filename}")
            uploaded_file_paths.append(file_path)
    
    elif message.content != None:
        try:
            print(f"message retrieved: {message.content}")
            google_drive_link = message.content
            await message.delete()
            folder_id = await GDapi.grabfolderid(google_drive_link, ctx)
            if not folder_id: raise GDapiError("Could not find the folder id!")
            uploaded_file_paths, *_ = await GDapi.downloadsaves_gd(ctx, folder_id, saveLocation, max_files, [SCE_SYS_CONTENTS] if sys_files else None, ps_save_pair_upload)
            print("made it out of google drive download function")
           
        except asyncio.TimeoutError:
            await ctx.edit(embed=embgdt)
            raise TimeoutError("TIMED OUT!")
    
    else:
        await ctx.send("Reply to the message with files that does not reach the limit, or a public google drive link (no subfolders and dont reach the file limit)!", ephemeral=True)
        
    return uploaded_file_paths

async def upload1(ctx, saveLocation: str) -> str | None:

    def check(message, ctx) -> discord.Attachment | str:
        if message.author == ctx.author and message.channel == ctx.channel:
            return len(message.attachments) == 1 or (message.content and GDapi.is_google_drive_link(message.content))
        
    try:
        message = await bot.wait_for("message", check=lambda message: check(message, ctx), timeout=UPLOAD_TIMEOUT)  # Wait for 120 seconds for a response with an attachment
    except asyncio.TimeoutError:
        await ctx.edit(embed=embUtimeout)
        raise TimeoutError("TIMED OUT!")

    if len(message.attachments) == 1:
        attachment = message.attachments[0]

        if attachment.size > FILE_LIMIT_DISCORD:
            emb15 = discord.Embed(title="Upload alert: Error",
                      description=f"Sorry, the file size of '{attachment.filename}' exceeds the limit of {int(FILE_LIMIT_DISCORD / 1024 / 1024)} MB.",
                      colour=0x854bf7)
    
            emb15.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")

            emb15.set_footer(text="Made with expertise by HTOP")
            await ctx.edit(embed=emb15)
            await message.delete()
            raise FileError("DISCORD UPLOAD ERROR: File size too large!")
        
        else:
            save_path = saveLocation
            file_path = os.path.join(save_path, attachment.filename)
            await attachment.save(file_path)
            print(f"Saved {file_path}")
            emb16 = discord.Embed(title="Upload alert: Successful", description=f"File '{attachment.filename}' has been successfully uploaded and saved.", colour=0x854bf7)
            emb16.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
            emb16.set_footer(text="Made with expertise by HTOP")
            await message.delete()
            await ctx.edit(embed=emb16)
            print(f"Uploaded {attachment.filename}")

            name_of_file = attachment.filename

    elif message.content != None:
        try:
            print(f"message retrieved: {message.content}")
            google_drive_link = message.content
            await message.delete()
            folder_id = await GDapi.grabfolderid(google_drive_link, ctx)
            if not folder_id: raise GDapiError("Could not find the folder id!")
            *_ , name_of_file = await GDapi.downloadsaves_gd(ctx, folder_id, saveLocation, max_files=1, sys_files=False, ps_save_pair_upload=False)

        except asyncio.TimeoutError:
            await ctx.edit(embed=embgdt)
            raise TimeoutError("TIMED OUT!")
    
    else:
        await ctx.send("Reply to the message with either 1 file, or a public google drive folder link (no subfolders and dont reach the file limit)!", ephemeral=True)

    return name_of_file

async def extra_decrypt(ctx, title_id: str, destination_directory: str) -> None:
    TIMEOUT = 60 # seconds
    ENCRYPTION_EMOJI = "<:catishochilling:1141168937208397944>"
    DECRYPTION_EMOJI = "<:ratisho:1141168619842191410>"
    done = False

    embedTimeout = discord.Embed(title="Timeout Error:", description="You took too long, sending the file with the format: Encrypted", color=0x854bf7)
    embedTimeout.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
        
    embedFormat = discord.Embed(title="Format", description="Choose what format you want the file to be sent in", color=0x854bf7)
    embedFormat.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
    embedFormat.set_footer(text="If you want to use the file in a save editor, choose decrypted")

    async def handle_timeout() -> None:
        nonlocal done
            
        if not done:
            await ctx.edit(embed=embedTimeout, view=None)
            print("timeout")
            await asyncio.sleep(2)
            done = True

    async def awaitDone() -> None:
        nonlocal done

        try:
            while not done:  # Continue waiting until done is True
                await asyncio.sleep(1)  # Sleep for 1 second to avoid busy-waiting
        except asyncio.CancelledError:
            pass  # Handle cancellation if needed

    class CryptoButton(discord.ui.View):
        def __init__(self, game: str, start_offset: int) -> None:
            self.game = game
            self.offset = start_offset
            super().__init__(timeout=TIMEOUT)
                
        async def on_timeout(self) -> None:
            self.disable_all_items()
            await handle_timeout()
            
        @discord.ui.button(label="Decrypted", style=discord.ButtonStyle.blurple, emoji=DECRYPTION_EMOJI, custom_id="decrypt")
        async def decryption_callback(self, _, interaction) -> None:
            nonlocal done
                
            await interaction.response.edit_message(view=None)
            try:
                if self.game == "GTAV" or self.game == "RDR2": await CustomCrypto.Rstar.decryptFile(destination_directory, self.offset)
                elif self.game == "XENO2": await CustomCrypto.Xeno2.decryptFile(destination_directory)
                elif self.game == "BL3": await CustomCrypto.BL3.decryptFile(destination_directory)
            except CryptoError as e:
                raise CryptoError(e)
            except Exception:
                raise CryptoError("Invalid save!")
            print("Decrypted final")
            done = True
            
        @discord.ui.button(label="Encrypted", style=discord.ButtonStyle.blurple, emoji=ENCRYPTION_EMOJI, custom_id="encrypt")
        async def encryption_callback(self, _, interaction):
            nonlocal done

            await interaction.response.edit_message(view=None)
            print("Encrypted final")
            done = True

    if title_id in GTAV_TITLEID:
        print("GTA 5 SAVE RECOGNIZED")

        await ctx.edit(embed=embedFormat, view=CryptoButton("GTAV", start_offset=0x114))

        await awaitDone()

    elif title_id in RDR2_TITLEID:
        print("RDR 2 SAVE RECOGNIZED")

        await ctx.edit(embed=embedFormat, view=CryptoButton("RDR2", start_offset=0x120))

        await awaitDone()

    elif title_id in XENO2_TITLEID:
        print("XENOVERSE 2 SAVE RECOGNIZED")

        await ctx.edit(embed=embedFormat, view=CryptoButton("XENO2", start_offset=None))

        await awaitDone()

    elif title_id in BL3_TITLEID:
        print("BL3 SAVE RECOGNIZED")

        await ctx.edit(embed=embedFormat, view=CryptoButton("BL3", start_offset=None))

        await awaitDone()

async def extra_import(title_id: str, file_name: str) -> None:
    if title_id in GTAV_TITLEID:
        print("GTA 5 SAVE RECOGNIZED")
        offset_to_check_gta5 = 0x114
        check_for = b"PSIN"

        async with aiofiles.open(file_name, "rb") as file:
            await file.seek(offset_to_check_gta5)
            header = await file.read(4)

        if header == check_for:
            print(f"{check_for.decode('utf-8')} header at {offset_to_check_gta5} found")
            try: await CustomCrypto.Rstar.encryptFile(file_name, offset_to_check_gta5)
            except Exception: raise CryptoError("Invalid save!")
            print("Encrypted")

        else:
            print(f"{check_for.decode('utf-8')} header at {offset_to_check_gta5} not found")

    elif title_id in RDR2_TITLEID:
        print("RDR 2 SAVE RECOGNIZED")
        offset_to_check_rdr2 = 0x120
        check_for = b"RSAV"

        async with aiofiles.open(file_name, "rb") as file:
            await file.seek(offset_to_check_rdr2)
            header = await file.read(4)

        if header == check_for:
            print(f"{check_for.decode('utf-8')} header at {offset_to_check_rdr2} found")
            try: await CustomCrypto.Rstar.encryptFile(file_name, offset_to_check_rdr2)
            except Exception: raise CryptoError("Invalid save!")
            print("Encrypted")
        else:
            print(f"{check_for.decode('utf-8')} header at {offset_to_check_rdr2} not found")

    elif title_id in XENO2_TITLEID:
        print("XENOVERSE 2 SAVE RECOGNIZED")
        check_for = b"#SAV"

        async with aiofiles.open(file_name, "rb") as file:
            first_bytes = await file.read(4)

        if first_bytes == check_for:
            print(f"{check_for.decode('utf-8')} header found at start")
            try: await CustomCrypto.Xeno2.encryptFile(file_name)
            except CryptoError as e: raise CryptoError(e)
            except Exception: raise CryptoError("Invalid save!")
            print("encrypted")
        else:
           print(f"{check_for.decode('utf-8')} header not found at start")

    elif title_id in BL3_TITLEID:
        print("BL3 SAVE RECOGNIZED")
        check_for = b"Player"

        async with aiofiles.open(file_name, "rb") as file:
            data = await file.read()

        if CustomCrypto.BL3.searchData(data, check_for):
            print(f"{check_for.decode('utf-8')} string found in save")
            try: await CustomCrypto.BL3.encryptFile(file_name)
            except CryptoError as e: raise CryptoError(e)
            except Exception: raise CryptoError("Invalid save!")
            print("encrypted")
        else:
           print(f"{check_for.decode('utf-8')} string not found in save")

async def psusername(ctx, username: str) -> str | None:
    await ctx.defer()

    def check1(message, ctx):
        if message.author == ctx.author and message.channel == ctx.channel:
            return message.content

    limit = 0
    usernamePattern = r"^[a-zA-Z0-9_-]+$"
    print(f"{username}\t{len(username)}")

    if len(username) < 3 or len(username) > 16:
        await ctx.edit(embed=embnv1)
        raise PSNIDError("Invalid PS username!")
    elif not bool(re.match(usernamePattern, username)):
        await ctx.edit(embed=embnv1)
        raise PSNIDError("Invalid PS username!")

    if NPPSO is not None:
        try:
            userSearch = psnawp.user(online_id=username)
            user_id = userSearch.account_id
            user_id = handle_accid(user_id)
            delmsg = False
            print(f"Obtained {username}:\t{user_id}")

        except PSNAWPNotFound:
            print("failed to get ID from username. ask the user for their ID")
            await ctx.respond(embed=emb8)
            delmsg = True

            try:
                response = await bot.wait_for('message', check=lambda message: check1(message, ctx), timeout=60)
                print(f"message retrieved: {response.content}")
                if checkid(response.content):
                    print("ID passed check")
                    user_id = response.content
                    await response.delete()
                else:
                    await ctx.edit(embed=embnv)
                    await response.delete()
                    raise PSNIDError("ACCOUNT ID DID NOT PASS CHECK!")
            except asyncio.TimeoutError:
                await ctx.edit(embed=embnt)
                raise TimeoutError("TIMED OUT!")

    else:
        while True:

            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://psn.flipscreen.games/search.php?username={username}") as response:
                    response.text = await response.text()

            if response.status == 200 and limit != 20:
                data = json.loads(response.text)
                obtainedUsername = data["online_id"]
                print(f"Obtained: {obtainedUsername}\t{len(obtainedUsername)}")
                if obtainedUsername.lower() == username.lower():
                    user_id = data["user_id"]
                    user_id = handle_accid(user_id)
                    print(f"got id: {user_id}")
                    delmsg = False
                    break
                else:
                    limit += 1
            else:
                print("failed to get ID from username. ask the user for their ID")
                await ctx.respond(embed=emb8)
                delmsg = True

                try:
                    response = await bot.wait_for('message', check=lambda message: check1(message, ctx), timeout=60)
                    print(f"message retrieved: {response.content}")
                    if checkid(response.content):
                        print("ID passed check")
                        user_id = response.content
                        await response.delete()
                        break
                    else:
                        await ctx.edit(embed=embnv)
                        await response.delete()
                        raise PSNIDError("ACCOUNT ID DID NOT PASS CHECK!")
                except asyncio.TimeoutError:
                    await ctx.edit(embed=embnt)
                    raise TimeoutError("TIMED OUT!")
            
    if delmsg:
        await asyncio.sleep(0.5)
        await ctx.edit(embed=embvalidpsn)
    else:
        await ctx.respond(embed=embvalidpsn)

    await asyncio.sleep(0.5)
    return user_id.lower()

async def replaceDecrypted(ctx, fInstance: FTPps, files: list, titleid: str, mountLocation: str , upload_individually: bool, upload_decrypted: str) -> list | None:
    completed = []
    if upload_individually or len(files) == 1:
        for file in files:
            fullPath = mountLocation + "/" + file
            cwdHere = fullPath.split("/")
            lastN = cwdHere.pop(len(cwdHere) - 1)
            cwdHere = "/".join(cwdHere)

            emb18 = discord.Embed(title="Resigning Process (Decrypted): Upload",
                            description=f"Please attach a decrypted savefile that you want to upload, MUST be equivalent to {file} (can be any name).",
                            colour=0x854bf7)
            emb18.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
            emb18.set_footer(text="Made with expertise by HTOP")

            await ctx.edit(embed=emb18)

            attachmentName = await upload1(ctx, upload_decrypted)
            attachmentPath = os.path.join(upload_decrypted, attachmentName)
            newPath = os.path.join(upload_decrypted, lastN)
            os.rename(attachmentPath, newPath)
            await extra_import(titleid, newPath)

            await fInstance.replacer(cwdHere, lastN)
            completed.append(file)
    
    else:
        SPLITVALUE = "SLASH"
        patterned = '\n'.join(files)
        emb18 = discord.Embed(title="Resigning Process (Decrypted): Upload",
                            description=f"Please attach at least one of these files and make sure its the same name, including path in the name if that is the case. Instead of '/' use '{SPLITVALUE}', here are the contents:\n{patterned}",
                            colour=0x854bf7)
        emb18.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
        emb18.set_footer(text="Made with expertise by HTOP")

        await ctx.edit(embed=emb18)
        uploaded_file_paths = await upload2(ctx, upload_decrypted, max_files=MAX_FILES, sys_files=False, ps_save_pair_upload=False)

        if len(uploaded_file_paths) >= 1:
            for file in os.listdir(upload_decrypted):
                file1 = file.split(SPLITVALUE)
                if file1[0] == "": file1 = file1[1:]
                file1 = "/".join(file1)
                print(f"[FILE]: {file1}")

                if file1 not in patterned:
                    os.remove(os.path.join(upload_decrypted, file))
                    
                else:
                    for saveFile in files:
                        print(f"[TARGETSEARCH]: Seaching for {saveFile}")
                        print(f"[TARGETSEARCH]: {file1}")
                        if file1 == saveFile:
                            print(f"[TARGETSEARCH]: Found!")
                            lastN = os.path.basename(saveFile)
                            cwdHere = saveFile.split("/")
                            cwdHere = cwdHere[:-1]
                            cwdHere = "/".join(cwdHere)
                            cwdHere = mountLocation + "/" + cwdHere

                            filePath = os.path.join(upload_decrypted, file)
                            newRename = os.path.join(upload_decrypted, lastN)
                            os.rename(filePath, newRename)
                            await extra_import(titleid, newRename)

                            await fInstance.replacer(cwdHere, lastN) 
                            completed.append(lastN)     
                    
        else:
            raise FileError("Too many files!")

    if len(completed) == 0:
        raise FileError("Could not replace any files")

    return completed

class threadButton(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Create thread", style=discord.ButtonStyle.primary, custom_id="CreateThread")
    async def callback(self, _, interaction) -> None:
        await interaction.response.send_message("Creating thread...", ephemeral=True)
        
        try:
            thread = await interaction.channel.create_thread(name=generate_random_string(RANDOMSTRING_LENGTH), auto_archive_duration=10080)
            await thread.send(interaction.user.mention)
            async with aiosqlite.connect(DATABASENAME) as db:
                cursor = await db.cursor()
                await cursor.execute("INSERT INTO Threads (id) VALUES (?)", (thread.id,))
                await db.commit()
        except Exception as e:
            print(f"Can not create thread: {e}")

@bot.event
async def on_ready() -> None:
    startup()
    bot.add_view(threadButton())
    print(
        f"Bot is ready, invite link: https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot"
    )

@bot.event
async def on_message(message) -> None:
    if message.author.bot:
        return

    if message.content == "hello":
        await message.channel.send("hi")

    await bot.process_commands(message)

@bot.slash_command(description="Resign encrypted savefiles (the usable ones you put in the console).")
async def resign_encrypted_save(ctx, playstation_id: Option(str, description=PS_ID_DESC)) -> None:
    newUPLOAD_ENCRYPTED, newUPLOAD_DECRYPTED, newDOWNLOAD_ENCRYPTED, newPNG_PATH, newPARAM_PATH, newDOWNLOAD_DECRYPTED, newKEYSTONE_PATH = initWorkspace()
    workspaceFolders = [newUPLOAD_ENCRYPTED, newUPLOAD_DECRYPTED, newDOWNLOAD_ENCRYPTED, 
                        newPNG_PATH, newPARAM_PATH, newDOWNLOAD_DECRYPTED, newKEYSTONE_PATH]
    try: await makeWorkspace(ctx, workspaceFolders)
    except WorkspaceError: return
    print("**********************************")
    C1ftp = FTPps(IP, PORT, PS_UPLOADDIR, newDOWNLOAD_DECRYPTED, newUPLOAD_DECRYPTED, newUPLOAD_ENCRYPTED,
                  newDOWNLOAD_ENCRYPTED, newPARAM_PATH, newKEYSTONE_PATH, newPNG_PATH)
    mountPaths = []

    try:
        user_id = await psusername(ctx, playstation_id)
        await asyncio.sleep(0.5)
        await ctx.edit(embed=embEncrypted1)
        uploaded_file_paths = await upload2(ctx, newUPLOAD_ENCRYPTED, max_files=MAX_FILES, sys_files=False, ps_save_pair_upload=True)
    except HTTPError as e:
        print(e)
        await ctx.edit(embed=embhttp)
        cleanupSimple(workspaceFolders)
        return
    except (PSNIDError, TimeoutError, GDapiError):
        await errorHandling(ctx, e, workspaceFolders, None, None, None)
        return

    savename2 = []

    file_name_10 = os.listdir(newUPLOAD_ENCRYPTED)

    for file_name11 in file_name_10:
        if not file_name11.endswith(".bin"):
            savename2.append(file_name11)

    
    print(uploaded_file_paths)
    print(savename2)
    if len(uploaded_file_paths) >= 2:
        random_string = generate_random_string(RANDOMSTRING_LENGTH)
        uploaded_file_paths = enumerateFiles(uploaded_file_paths, random_string)
        for save in savename2:
            realSave = f"{save}_{random_string}"
            print(f"doing {save}")
            try:
                os.rename(os.path.join(newUPLOAD_ENCRYPTED, save), os.path.join(newUPLOAD_ENCRYPTED, realSave))
                os.rename(os.path.join(newUPLOAD_ENCRYPTED, save + ".bin"), os.path.join(newUPLOAD_ENCRYPTED, realSave + ".bin"))
                emb4 = discord.Embed(title="Resigning process: Encrypted",
                            description=f"Your save (**{save}**) is being resigned, please wait...",
                            colour=0x854bf7)

                emb4.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")

                emb4.set_footer(text="Made with expertise by HTOP")

                await ctx.edit(embed=emb4)
                print("starting upload...")
                await C1ftp.uploadencrypted_bulk(realSave)
                print("uploaded")
                mount_location_new = MOUNT_LOCATION + "/" + random_string
                await C1ftp.make1(mount_location_new)
                mountPaths.append(mount_location_new)
                await C1socket.socket_dump(mount_location_new, realSave)
                location_to_scesys = mount_location_new + "/sce_sys"
                await C1ftp.dlparam(location_to_scesys, user_id)
                print("Param processes completed")
                await C1socket.socket_update(mount_location_new, realSave)
                print("Updated mount")
                await C1ftp.dlencrypted_bulk(False, user_id, realSave)
                print("downloaded")

                emb5 = discord.Embed(title="Resigning process (Encrypted): Successful",
                            description=f"**{save}** resigned to **{playstation_id}**",
                            colour=0x854bf7)

                emb5.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")

                emb5.set_footer(text="Made with expertise by HTOP")

                await ctx.edit(embed=emb5)
                print(f"{save} done")
            except (SocketError, FTPError, OrbisError, OSError) as e:
                if isinstance(e, OSError) and hasattr(e, "winerror") and e.winerror == 121: 
                    e = "PS4 not connected!"
                await errorHandling(ctx, e, workspaceFolders, uploaded_file_paths, mountPaths, C1ftp)
                return
        
        if len(savename2) == 1:
            finishedFiles = "".join(savename2)
        else: finishedFiles = ", ".join(savename2)
        
        embRdone = discord.Embed(title="Resigning process (Encrypted): Successful",
                            description=f"**{finishedFiles}** resigned to **{playstation_id}**.",
                            colour=0x854bf7)
        embRdone.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
        embRdone.set_footer(text="Made with expertise by HTOP")
        
        await ctx.edit(embed=embRdone)
        
        zipfiles(newDOWNLOAD_ENCRYPTED, "PS4.zip")
        final_file = os.path.join(newDOWNLOAD_ENCRYPTED, "PS4.zip")
        final_size = os.path.getsize(final_file)
        file_size_mb = final_size / (1024 * 1024)

        if file_size_mb < BOT_DISCORD_UPLOAD_LIMIT:
            await ctx.respond(file=discord.File(final_file))
        else:
            reenc = final_file
            reenc_name = "PS4.zip"
            file_url = await GDapi.uploadzip(reenc, reenc_name)
            embg = discord.Embed(title="Google Drive: Upload complete",
                        description=f"Here is **{finishedFiles}** resigned:\n<{file_url}>.",
                        colour=0x854bf7)
            embg.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
            embg.set_footer(text="Made with expertise by HTOP")
            await ctx.respond(embed=embg)

        await asyncio.sleep(1)
        await cleanup(C1ftp, workspaceFolders, uploaded_file_paths, mountPaths)
        print("done")
            
    else: 
        await ctx.edit(embed=emb6)
        cleanupSimple(workspaceFolders)

@bot.slash_command(description="Decrypt a savefile and download the contents.")
async def decrypt_save(ctx, include_sce_sys: Option(bool, description="Choose if you want to include the 'sce_sys' folder.")) -> None:
    newUPLOAD_ENCRYPTED, newUPLOAD_DECRYPTED, newDOWNLOAD_ENCRYPTED, newPNG_PATH, newPARAM_PATH, newDOWNLOAD_DECRYPTED, newKEYSTONE_PATH = initWorkspace()
    workspaceFolders = [newUPLOAD_ENCRYPTED, newUPLOAD_DECRYPTED, newDOWNLOAD_ENCRYPTED, 
                        newPNG_PATH, newPARAM_PATH, newDOWNLOAD_DECRYPTED, newKEYSTONE_PATH]
    try: await makeWorkspace(ctx, workspaceFolders)
    except WorkspaceError: return
    print("**********************************")
    C1ftp = FTPps(IP, PORT, PS_UPLOADDIR, newDOWNLOAD_DECRYPTED, newUPLOAD_DECRYPTED, newUPLOAD_ENCRYPTED,
                  newDOWNLOAD_ENCRYPTED, newPARAM_PATH, newKEYSTONE_PATH, newPNG_PATH)
    mountPaths = []

    await ctx.respond(embed=embDecrypt1)
    try:
        uploaded_file_paths = await upload2(ctx, newUPLOAD_ENCRYPTED, max_files=MAX_FILES, sys_files=False, ps_save_pair_upload=True)
    except HTTPError as e:
        print(e)
        await ctx.edit(embed=embhttp)
        cleanupSimple(workspaceFolders)
        return
    except (TimeoutError, GDapiError) as e:
        await errorHandling(ctx, e, workspaceFolders, None, None, None)
        return
            
    savename3 = []

    file_name_10 = os.listdir(newUPLOAD_ENCRYPTED)


    for file_name11 in file_name_10:
        if not file_name11.endswith(".bin"):
            savename3.append(file_name11)
    
    print(uploaded_file_paths)
    print(savename3)
    
    if len(uploaded_file_paths) >= 2:
        random_string = generate_random_string(RANDOMSTRING_LENGTH)
        uploaded_file_paths = enumerateFiles(uploaded_file_paths, random_string)
        print(uploaded_file_paths)
        for save in savename3:
            destination_directory = os.path.join(newDOWNLOAD_DECRYPTED, f"dec_{save}")
            realSave = f"{save}_{random_string}"
            print(f"doing {save}")

            emb11 = discord.Embed(title="Decrypt process: Initializing",
                      description=f"Mounting {save}.",
                      colour=0x854bf7)
            emb11.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
            emb11.set_footer(text="Made with expertise by HTOP")
            
            try:
                os.rename(os.path.join(newUPLOAD_ENCRYPTED, save), os.path.join(newUPLOAD_ENCRYPTED, realSave))
                os.rename(os.path.join(newUPLOAD_ENCRYPTED, save + ".bin"), os.path.join(newUPLOAD_ENCRYPTED, realSave + ".bin"))
                os.mkdir(destination_directory)
                await ctx.edit(embed=emb11)
                await C1ftp.uploadencrypted_bulk(realSave)
                mount_location_new = MOUNT_LOCATION + "/" + random_string
                await C1ftp.make1(mount_location_new)
                mountPaths.append(mount_location_new)
                await C1socket.socket_dump(mount_location_new, realSave)
                print("Mounted")
                await ctx.edit(embed=emb12)

                if include_sce_sys:
                    await C1ftp.ftp_download_folder(mount_location_new, destination_directory, False)
                else:
                    await C1ftp.ftp_download_folder(mount_location_new, destination_directory, True)
                
                location_to_scesys = mount_location_new + "/sce_sys"
                await C1ftp.dlparamonly_grab(location_to_scesys)
                title_id_grab = await obtainCUSA(newPARAM_PATH)
                print("FTP done")
                os.rename(destination_directory, destination_directory + f"_{title_id_grab}")
                destination_directory = destination_directory + f"_{title_id_grab}"

                emb13 = discord.Embed(title="Decrypt process: Successful",
                            description=f"Downloaded the decrypted save of **{save}** from **{title_id_grab}**.",
                            colour=0x854bf7)
                emb13.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
                emb13.set_footer(text="Made with expertise by HTOP")

                await extra_decrypt(ctx, title_id_grab, destination_directory)

                await ctx.edit(embed=emb13)
            except (SocketError, FTPError, OrbisError, CryptoError, OSError) as e:
                if isinstance(e, OSError) and hasattr(e, "winerror") and e.winerror == 121: 
                    e = "PS4 not connected!"
                await errorHandling(ctx, e, workspaceFolders, uploaded_file_paths, mountPaths, C1ftp)
                return
        
        if len(os.listdir(newDOWNLOAD_DECRYPTED)) == 1:
            zip_name = os.listdir(newDOWNLOAD_DECRYPTED)
            zip_name = "".join(zip_name)
            zip_name += ".zip"
        else:
            zip_name = "Decrypted-Saves.zip"
        
        zipfiles(newDOWNLOAD_DECRYPTED, zip_name)
        zip_in_THIS_path = os.path.join(newDOWNLOAD_DECRYPTED, zip_name)
        size_check1 = os.path.getsize(zip_in_THIS_path)
        size_in_mb = size_check1 / (1024 * 1024)

        if len(savename3) == 1:
            finishedFiles = "".join(savename3)
        else: finishedFiles = ", ".join(savename3)

        embDdone = discord.Embed(title="Decryption process: Successful",
                            description=f"**{finishedFiles}** has been decrypted.",
                            colour=0x854bf7)
        embDdone.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
        embDdone.set_footer(text="Made with expertise by HTOP")

        await ctx.edit(embed=embDdone)

        if size_in_mb < BOT_DISCORD_UPLOAD_LIMIT:
            await ctx.respond(file=discord.File(zip_in_THIS_path))
        else:
            file_url = await GDapi.uploadzip(zip_in_THIS_path, zip_name)
            embg = discord.Embed(title="Google Drive: Upload complete", description=f"Here is **{finishedFiles}** decrypted:\n<{file_url}>", colour=0x854bf7)
            embg.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
            embg.set_footer(text="Made with expertise by HTOP")
            await ctx.respond(embed=embg)
        print("sent zip")
        
        await asyncio.sleep(1)
        await cleanup(C1ftp, workspaceFolders, uploaded_file_paths, mountPaths)
        print("done")

    else:
        await ctx.edit(embed=emb6)
        cleanupSimple(workspaceFolders)

@bot.slash_command(description="Swap the decrypted savefile from the encrypted ones you upload.")
async def resign_decrypted_save(ctx, playstation_id: Option(str, description=PS_ID_DESC), upload_individually: Option(bool, description="Choose if you want to upload the decrypted files one by one, or the ones you want at once."), include_sce_sys: Option(bool, description="Choose if you want to upload the contents of the 'sce_sys' folder.")) -> None:
    newUPLOAD_ENCRYPTED, newUPLOAD_DECRYPTED, newDOWNLOAD_ENCRYPTED, newPNG_PATH, newPARAM_PATH, newDOWNLOAD_DECRYPTED, newKEYSTONE_PATH = initWorkspace()
    workspaceFolders = [newUPLOAD_ENCRYPTED, newUPLOAD_DECRYPTED, newDOWNLOAD_ENCRYPTED, 
                        newPNG_PATH, newPARAM_PATH, newDOWNLOAD_DECRYPTED, newKEYSTONE_PATH]
    try: await makeWorkspace(ctx, workspaceFolders)
    except WorkspaceError: return
    print("**********************************")
    C1ftp = FTPps(IP, PORT, PS_UPLOADDIR, newDOWNLOAD_DECRYPTED, newUPLOAD_DECRYPTED, newUPLOAD_ENCRYPTED,
                  newDOWNLOAD_ENCRYPTED, newPARAM_PATH, newKEYSTONE_PATH, newPNG_PATH)
    mountPaths = []

    try:
        user_id = await psusername(ctx, playstation_id)
        await asyncio.sleep(0.5)
        await ctx.edit(embed=emb14)
        uploaded_file_paths = await upload2(ctx, newUPLOAD_ENCRYPTED, max_files=2, sys_files=False, ps_save_pair_upload=True)
    except HTTPError as e:
        print(e)
        await ctx.edit(embed=embhttp)
        cleanupSimple(workspaceFolders)
        return
    except (PSNIDError, TimeoutError, GDapiError) as e:
        await errorHandling(ctx, e, workspaceFolders, None, None, None)
        return

    savename6 = []

    file_name_10 = os.listdir(newUPLOAD_ENCRYPTED)

    for file_name11 in file_name_10:
        if not file_name11.endswith(".bin"):
            savename6.append(file_name11)

    savename6 = "".join(savename6)

    print(savename6)

    if len(uploaded_file_paths) == 2:
        random_string = generate_random_string(RANDOMSTRING_LENGTH)
        uploaded_file_paths = enumerateFiles(uploaded_file_paths, random_string)
        savename6 += f"_{random_string}"
        try:
            for file in os.listdir(newUPLOAD_ENCRYPTED):
                if file.endswith(".bin"):
                    os.rename(os.path.join(newUPLOAD_ENCRYPTED, file), os.path.join(newUPLOAD_ENCRYPTED, os.path.splitext(file)[0] + f"_{random_string}" + ".bin"))
                else:
                    os.rename(os.path.join(newUPLOAD_ENCRYPTED, file), os.path.join(newUPLOAD_ENCRYPTED, file + f"_{random_string}"))
            await ctx.edit(embed=emb17)
            await C1ftp.uploadencrypted()
            mount_location_new = MOUNT_LOCATION + "/" + random_string
            await C1ftp.make1(mount_location_new)
            mountPaths.append(mount_location_new)
            await C1socket.socket_dump(mount_location_new, savename6)
           
            files = await C1ftp.ftpListContents(mount_location_new)
            print(f"[LISTED]: {files}")

            if len(files) == 0: raise Exception("Could not list any decrypted saves!")
            location_to_scesys = mount_location_new + "/sce_sys"
            await C1ftp.dlparamonly_grab(location_to_scesys)
            print("grabbed")
            title_id = await obtainCUSA(newPARAM_PATH)

            if upload_individually: completed = await replaceDecrypted(ctx, C1ftp, files, title_id, mount_location_new, True, newUPLOAD_DECRYPTED)
            else: completed = await replaceDecrypted(ctx, C1ftp, files, title_id, mount_location_new, False, newUPLOAD_DECRYPTED)

            if include_sce_sys:
                if len(os.listdir(newUPLOAD_DECRYPTED)) > 0:
                    shutil.rmtree(newUPLOAD_DECRYPTED)
                    os.mkdir(newUPLOAD_DECRYPTED)
                    
                embSceSys = discord.Embed(title="Upload: sce_sys contents",
                      description="Please attach the sce_sys files you want to upload.",
                      colour=0x854bf7)
                embSceSys.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
                embSceSys.set_footer(text="Made with expertise by HTOP")

                await ctx.edit(embed=embSceSys)
                uploaded_file_paths_sys = await upload2(ctx, newUPLOAD_DECRYPTED, max_files=len(SCE_SYS_CONTENTS), sys_files=True, ps_save_pair_upload=False)

                if len(uploaded_file_paths_sys) <= len(SCE_SYS_CONTENTS) and len(uploaded_file_paths) >= 1:
                    filesToUpload = os.listdir(newUPLOAD_DECRYPTED)
                    await C1ftp.upload_scesysContents(ctx, filesToUpload, location_to_scesys)
                
            location_to_scesys = mount_location_new + "/sce_sys"
            await C1ftp.dlparam(location_to_scesys, user_id)
            print("Resigned")
            await C1socket.socket_update(mount_location_new, savename6)
            print("Updated")
            await C1ftp.dlencrypted_new(savename6, user_id)
            print("Written to PS4.zip")
            if len(completed) == 1: completed = "".join(completed)
            else: completed = ", ".join(completed)

            emb19 = discord.Embed(title="Resigning Process (Decrypted): Successful",
                          description=f"Resigned **{completed}** with title id **{title_id}** to **{playstation_id}**.",
                          colour=0x854bf7)
            emb19.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
            emb19.set_footer(text="Made with expertise by HTOP")

            await ctx.edit(embed=emb19)

            final_file = os.path.join(newDOWNLOAD_ENCRYPTED, "PS4.zip")
            final_size = os.path.getsize(final_file)
            file_size_mb = final_size / (1024 * 1024)

            if file_size_mb < BOT_DISCORD_UPLOAD_LIMIT:
                await ctx.respond(file=discord.File(final_file))
            else:
                reenc = final_file
                reenc_name = "PS4.zip"
                file_url = await GDapi.uploadzip(reenc, reenc_name)

                embg = discord.Embed(title="Google Drive: Upload complete",
                          description=f"Here is your save:\n<{file_url}>",
                          colour=0x854bf7)
                embg.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
                embg.set_footer(text="Made with expertise by HTOP")
                await ctx.edit(embed=embg)

            await cleanup(C1ftp, workspaceFolders, uploaded_file_paths, mountPaths)
            print("done")

        except HTTPError as e:
            print(e)
            await ctx.edit(embed=embhttp)
            cleanup(C1ftp, workspaceFolders, uploaded_file_paths, mountPaths)
            return
        except (SocketError, FTPError, OrbisError, FileError, CryptoError, OSError) as e:
            if isinstance(e, OSError) and hasattr(e, "winerror") and e.winerror == 121: 
                e = "PS4 not connected!"
            await errorHandling(ctx, e, workspaceFolders, uploaded_file_paths, mountPaths, C1ftp)
            return

    else:
        await ctx.edit(embed=emb6)
        cleanupSimple(workspaceFolders)

@bot.slash_command(description="Change the region of a save (Must be from the same game).")
async def reregion(ctx, playstation_id: Option(str, description=PS_ID_DESC)) -> None: 
    newUPLOAD_ENCRYPTED, newUPLOAD_DECRYPTED, newDOWNLOAD_ENCRYPTED, newPNG_PATH, newPARAM_PATH, newDOWNLOAD_DECRYPTED, newKEYSTONE_PATH = initWorkspace()
    workspaceFolders = [newUPLOAD_ENCRYPTED, newUPLOAD_DECRYPTED, newDOWNLOAD_ENCRYPTED, 
                        newPNG_PATH, newPARAM_PATH, newDOWNLOAD_DECRYPTED, newKEYSTONE_PATH]
    try: await makeWorkspace(ctx, workspaceFolders)
    except WorkspaceError: return
    print("**********************************")
    C1ftp = FTPps(IP, PORT, PS_UPLOADDIR, newDOWNLOAD_DECRYPTED, newUPLOAD_DECRYPTED, newUPLOAD_ENCRYPTED,
                  newDOWNLOAD_ENCRYPTED, newPARAM_PATH, newKEYSTONE_PATH, newPNG_PATH)
    mountPaths = []

    try:
        user_id = await psusername(ctx, playstation_id)
        await asyncio.sleep(0.5)
        await ctx.edit(embed=emb21)
        uploaded_file_paths = await upload2(ctx, newUPLOAD_ENCRYPTED, max_files=2, sys_files=False, ps_save_pair_upload=True)
    except HTTPError as e:
        print(e)
        await ctx.edit(embed=embhttp)
        cleanupSimple(workspaceFolders)
        return
    except (PSNIDError, TimeoutError, GDapiError) as e:
        await errorHandling(ctx, e, workspaceFolders, None, None, None)
        return
        
    savename__ = []

    file_name_10 = os.listdir(newUPLOAD_ENCRYPTED)

    for file_name11 in file_name_10:
        if not file_name11.endswith(".bin"):
            savename__.append(file_name11)

    savename__ = "".join(savename__)

    print(savename__)

    print(uploaded_file_paths)

    if len(uploaded_file_paths) == 2:
        random_string = generate_random_string(RANDOMSTRING_LENGTH)
        uploaded_file_paths = enumerateFiles(uploaded_file_paths, random_string)
        savename__ += f"_{random_string}"
        try:
            for file in os.listdir(newUPLOAD_ENCRYPTED):
                if file.endswith(".bin"):
                    os.rename(os.path.join(newUPLOAD_ENCRYPTED, file), os.path.join(newUPLOAD_ENCRYPTED, os.path.splitext(file)[0] + f"_{random_string}" + ".bin"))
                else:
                    os.rename(os.path.join(newUPLOAD_ENCRYPTED, file), os.path.join(newUPLOAD_ENCRYPTED, file + f"_{random_string}"))
        
            await ctx.edit(embed=emb22)
            await C1ftp.uploadencrypted()
            mount_location_new = MOUNT_LOCATION + "/" + random_string
            await C1ftp.make1(mount_location_new)
            mountPaths.append(mount_location_new)
            await C1socket.socket_dump(mount_location_new, savename__)
            location_to_scesys = mount_location_new + "/sce_sys"
            print("Mounted")
            await C1ftp.retrievekeystone(location_to_scesys)
            print("Keystone obtained")
            await C1ftp.dlparamonly_grab(location_to_scesys)

            target_titleid = await obtainCUSA(newPARAM_PATH)
            
            emb23 = discord.Embed(title="Obtain process: Keystone",
                          description=f"Keystone from **{target_titleid}** obtained.",
                          colour=0x854bf7)
            emb23.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
            emb23.set_footer(text="Made with expertise by HTOP")

            await ctx.edit(embed=emb23)

            shutil.rmtree(newUPLOAD_ENCRYPTED)
            os.makedirs(newUPLOAD_ENCRYPTED)

            await C1ftp.deleteuploads(savename__)
        except (SocketError, FTPError, OrbisError, OSError) as e:
            if isinstance(e, OSError) and hasattr(e, "winerror") and e.winerror == 121: 
                e = "PS4 not connected!"
            await errorHandling(ctx, e, workspaceFolders, uploaded_file_paths, mountPaths, C1ftp)
            return
       
    else: 
        await ctx.edit(embed=emb6)
        cleanupSimple(workspaceFolders)
        return

    await ctx.edit(embed=emb20)

    try: uploaded_file_paths = await upload2(ctx, newUPLOAD_ENCRYPTED, max_files=MAX_FILES, sys_files=False, ps_save_pair_upload=True)
    except HTTPError as e:
        print(e)
        await ctx.edit(embed=embhttp)
        await cleanup(C1ftp, workspaceFolders, uploaded_file_paths, mountPaths)
        return
    except (TimeoutError, GDapiError) as e:
        await errorHandling(ctx, e, workspaceFolders, uploaded_file_paths, mountPaths, C1ftp)
        return
        
    savename__ = []

    file_name_10 = os.listdir(newUPLOAD_ENCRYPTED)

    for file_name11 in file_name_10:
        if not file_name11.endswith(".bin"):
            savename__.append(file_name11)

    print(uploaded_file_paths)
    print(savename__)
    if len(uploaded_file_paths) >= 2:
        random_string = generate_random_string(RANDOMSTRING_LENGTH)
        uploaded_file_paths = enumerateFiles(uploaded_file_paths, random_string)
        for save in savename__:
            realSave = f"{save}_{random_string}"
            print(f"doing {save}")
            try:
                os.rename(os.path.join(newUPLOAD_ENCRYPTED, save), os.path.join(newUPLOAD_ENCRYPTED, realSave))
                os.rename(os.path.join(newUPLOAD_ENCRYPTED, save + ".bin"), os.path.join(newUPLOAD_ENCRYPTED, realSave + ".bin")) 
                emb4 = discord.Embed(title="Resigning process: Encrypted",
                            description=f"Your save (**{save}**) is being resigned, please wait...",
                            colour=0x854bf7)
                emb4.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
                emb4.set_footer(text="Made with expertise by HTOP")
                await ctx.edit(embed=emb4)
                await C1ftp.uploadencrypted_bulk(realSave)
                mount_location_new = MOUNT_LOCATION + "/" + random_string
                await C1ftp.make1(mount_location_new)
                mountPaths.append(mount_location_new)
                location_to_scesys = mount_location_new + "/sce_sys"
                await C1socket.socket_dump(mount_location_new, realSave)
                await C1ftp.reregioner(location_to_scesys, target_titleid, user_id)
                print("ReRegioned")
                await C1ftp.keystoneswap(location_to_scesys)
                print("Keystone swapped")
                await C1socket.socket_update(mount_location_new, realSave)
                print("Updated")
                await C1ftp.dlencrypted_bulk(True, user_id, realSave)
                print("downloaded")

                emb5 = discord.Embed(title="Re-regioning & Resigning process (Encrypted): Successful",
                            description=f"**{save}** resigned to **{playstation_id}** (**{target_titleid}**).",
                            colour=0x854bf7)

                emb5.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")

                emb5.set_footer(text="Made with expertise by HTOP")

                await ctx.edit(embed=emb5)
                print(f"{save} done")
            except (SocketError, FTPError, OrbisError, OSError) as e:
                if isinstance(e, OSError) and hasattr(e, "winerror") and e.winerror == 121: 
                    e = "PS4 not connected!"
                await errorHandling(ctx, e, workspaceFolders, uploaded_file_paths, mountPaths, C1ftp)
                return
            
        if len(savename__) == 1:
            finishedFiles = "".join(savename__)
        else: finishedFiles = ", ".join(savename__)

        embRgdone = discord.Embed(title="Re-regioning & Resigning process (Encrypted): Successful",
                            description=f"**{finishedFiles}** resigned to **{playstation_id}** (**{target_titleid}**).",
                            colour=0x854bf7)
        embRgdone.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
        embRgdone.set_footer(text="Made with expertise by HTOP")
        
        await ctx.edit(embed=embRgdone)
            
        zipfiles(newDOWNLOAD_ENCRYPTED, "PS4.zip")
        final_file = os.path.join(newDOWNLOAD_ENCRYPTED, "PS4.zip")
        final_size = os.path.getsize(final_file)
        file_size_mb = final_size / (1024 * 1024)

        if file_size_mb < BOT_DISCORD_UPLOAD_LIMIT:
            await ctx.respond(file=discord.File(final_file))
        else:
            reenc = final_file
            reenc_name = "PS4.zip"
            file_url = await GDapi.uploadzip(reenc, reenc_name)

            embg = discord.Embed(title="Google Drive: Upload complete",
                    description=f"Here is **{finishedFiles}** re-regioned and resigned to **{playstation_id}** with title id **{target_titleid}**:\n<{file_url}>",
                    colour=0x854bf7)
            embg.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
            embg.set_footer(text="Made with expertise by HTOP")
            await ctx.respond(embed=embg)

        if target_titleid in XENO2_TITLEID:
            await ctx.respond("Make sure to remove the random string after and including '_' when you are going to copy that file to the console. Only required if you re-regioned more than 1 save at once.", ephemeral=True)

        await asyncio.sleep(1)
        await cleanup(C1ftp, workspaceFolders, uploaded_file_paths, mountPaths)
        print("done")
        
    else: 
        await ctx.edit(embed=emb6)
        cleanupSimple(workspaceFolders)

@bot.slash_command(description="Changes the picture of your save, this is just cosmetic.")
async def changepic(ctx, picture: discord.Attachment) -> None:
    newUPLOAD_ENCRYPTED, newUPLOAD_DECRYPTED, newDOWNLOAD_ENCRYPTED, newPNG_PATH, newPARAM_PATH, newDOWNLOAD_DECRYPTED, newKEYSTONE_PATH = initWorkspace()
    workspaceFolders = [newUPLOAD_ENCRYPTED, newUPLOAD_DECRYPTED, newDOWNLOAD_ENCRYPTED, 
                        newPNG_PATH, newPARAM_PATH, newDOWNLOAD_DECRYPTED, newKEYSTONE_PATH]
    try: await makeWorkspace(ctx, workspaceFolders)
    except WorkspaceError: return
    print("**********************************")
    C1ftp = FTPps(IP, PORT, PS_UPLOADDIR, newDOWNLOAD_DECRYPTED, newUPLOAD_DECRYPTED, newUPLOAD_ENCRYPTED,
                  newDOWNLOAD_ENCRYPTED, newPARAM_PATH, newKEYSTONE_PATH, newPNG_PATH)
    mountPaths = []
    pngfile = os.path.join(newPNG_PATH, "icon0.png")
    size = (228, 128)

    await ctx.respond(embed=embpng)

    try: uploaded_file_paths = await upload2(ctx, newUPLOAD_ENCRYPTED, max_files=MAX_FILES, sys_files=False, ps_save_pair_upload=True)
    except HTTPError as e:
        print(e)
        await ctx.edit(embed=embhttp)
        cleanupSimple(workspaceFolders)
        return
    except (TimeoutError, GDapiError) as e:
        await errorHandling(ctx, e, workspaceFolders, None, None, None)
        return
            
    savenamepng = []

    file_name_png = os.listdir(newUPLOAD_ENCRYPTED)

    for file_namepng1 in file_name_png:
        if not file_namepng1.endswith(".bin"):
            savenamepng.append(file_namepng1)

    print(uploaded_file_paths)
    print(savenamepng)
    if len(uploaded_file_paths) >= 2:
        # png handling
        await picture.save(pngfile)
        pngprocess(pngfile, size)
        print(f"Saved {pngfile}")
        random_string = generate_random_string(RANDOMSTRING_LENGTH)
        uploaded_file_paths = enumerateFiles(uploaded_file_paths, random_string)
        for save in savenamepng:
            realSave = f"{save}_{random_string}"
            print(f"doing {save}")

            try:
                os.rename(os.path.join(newUPLOAD_ENCRYPTED, save), os.path.join(newUPLOAD_ENCRYPTED, realSave))
                os.rename(os.path.join(newUPLOAD_ENCRYPTED, save + ".bin"), os.path.join(newUPLOAD_ENCRYPTED, realSave + ".bin"))
                await ctx.edit(embed=embpng1)
                await C1ftp.uploadencrypted_bulk(realSave)
                mount_location_new = MOUNT_LOCATION + "/" + random_string
                await C1ftp.make1(mount_location_new)
                mountPaths.append(mount_location_new)
                await C1socket.socket_dump(mount_location_new, realSave)
                print("Mounted")
                await ctx.edit(embed=embpng2)
                location_to_scesys = mount_location_new + "/sce_sys"
                await C1ftp.swappng(location_to_scesys)
                await C1ftp.dlparamonly_grab(location_to_scesys)
                print("grabbed param")
                png_accid = await obtainID(newPARAM_PATH)
                await C1socket.socket_update(mount_location_new, realSave)
                print("Updated")
                await C1ftp.dlencrypted_bulk(False, png_accid, realSave)
                print("downloaded")

                embpngs = discord.Embed(title="PNG process: Successful",
                            description=f"Altered the save png of **{save}**.",
                            colour=0x854bf7)
                embpngs.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
                embpngs.set_footer(text="Made with expertise by HTOP")

                await ctx.edit(embed=embpngs)
                print(f"{save} done")

            except (SocketError, FTPError, OrbisError, OSError) as e:
                if isinstance(e, OSError) and hasattr(e, "winerror") and e.winerror == 121: 
                    e = "PS4 not connected!"
                await errorHandling(ctx, e, workspaceFolders, uploaded_file_paths, mountPaths, C1ftp)
                return
        
        if len(savenamepng) == 1:
            finishedFiles = "".join(savenamepng)
        else: finishedFiles = ", ".join(savenamepng)

        embPdone = discord.Embed(title="PNG process: Successful",
                            description=f"Altered the save png of **{finishedFiles}**.",
                            colour=0x854bf7)
        embPdone.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
        embPdone.set_footer(text="Made with expertise by HTOP")

        await ctx.edit(embed=embPdone)
        
        zipfiles(newDOWNLOAD_ENCRYPTED, "PS4.zip")
        final_file = os.path.join(newDOWNLOAD_ENCRYPTED, "PS4.zip")
        final_size = os.path.getsize(final_file)
        file_size_mb = final_size / (1024 * 1024)

        if file_size_mb < BOT_DISCORD_UPLOAD_LIMIT:
            print("less than 25mb")
            await ctx.respond(file=discord.File(final_file))
        else:
            reenc = final_file
            reenc_name = "PS4.zip"
            file_url = await GDapi.uploadzip(reenc, reenc_name)

            embg = discord.Embed(title="Google Drive: Upload complete",
                    description=f"Here is **{finishedFiles}** with altered save png:\n<{file_url}>",
                    colour=0x854bf7)
            embg.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
            embg.set_footer(text="Made with expertise by HTOP")
            await ctx.respond(embed=embg)

        await asyncio.sleep(1)
        await cleanup(C1ftp, workspaceFolders, uploaded_file_paths, mountPaths)
        print("done")

    else:
        await ctx.edit(embed=emb6)
        cleanupSimple(workspaceFolders)

@bot.slash_command(description="Resign pre stored saves.")
async def quickresign(ctx, playstation_id: Option(str, description=PS_ID_DESC)) -> None:
    newUPLOAD_ENCRYPTED, newUPLOAD_DECRYPTED, newDOWNLOAD_ENCRYPTED, newPNG_PATH, newPARAM_PATH, newDOWNLOAD_DECRYPTED, newKEYSTONE_PATH = initWorkspace()
    workspaceFolders = [newUPLOAD_ENCRYPTED, newUPLOAD_DECRYPTED, newDOWNLOAD_ENCRYPTED, 
                        newPNG_PATH, newPARAM_PATH, newDOWNLOAD_DECRYPTED, newKEYSTONE_PATH]
    try: await makeWorkspace(ctx, workspaceFolders)
    except: return
    print("**********************************")
    C1ftp = FTPps(IP, PORT, PS_UPLOADDIR, newDOWNLOAD_DECRYPTED, newUPLOAD_DECRYPTED, newUPLOAD_ENCRYPTED,
                  newDOWNLOAD_ENCRYPTED, newPARAM_PATH, newKEYSTONE_PATH, newPNG_PATH)
    mountPaths = []
    
    try:
        user_id = await psusername(ctx, playstation_id)
        await asyncio.sleep(0.5)
        response = await listStoredSaves(ctx)
    except (PSNIDError, TimeoutError) as e:
        await errorHandling(ctx, e, workspaceFolders, None, None, None)
        return
    
    if response == "EXIT":
        embExit = discord.Embed(title="Exited.", colour=0x854bf7)
        embExit.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
        embExit.set_footer(text="Made with expertise by HTOP")
        await ctx.edit(embed=embExit)
        cleanupSimple(workspaceFolders)
        return
    
    random_string = generate_random_string(RANDOMSTRING_LENGTH)
    saveName = os.path.basename(response)
    files = os.listdir(newUPLOAD_ENCRYPTED)
    realSave = f"{saveName}_{random_string}"

    try:
        shutil.copyfile(response, os.path.join(newUPLOAD_ENCRYPTED, f"{saveName}_{random_string}"))
        shutil.copyfile(response + ".bin", os.path.join(newUPLOAD_ENCRYPTED, f"{saveName}_{random_string}.bin"))

        emb4 = discord.Embed(title="Resigning process: Encrypted",
                    description=f"Your save (**{saveName}**) is being resigned, please wait...",
                    colour=0x854bf7)
        emb4.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
        emb4.set_footer(text="Made with expertise by HTOP")

        await ctx.edit(embed=emb4)
        print("starting upload...")
        await C1ftp.uploadencrypted_bulk(realSave)
        print("uploaded")
        mount_location_new = MOUNT_LOCATION + "/" + random_string
        await C1ftp.make1(mount_location_new)
        mountPaths.append(mount_location_new)
        await C1socket.socket_dump(mount_location_new, realSave)
        location_to_scesys = mount_location_new + "/sce_sys"
        await C1ftp.dlparam(location_to_scesys, user_id)
        print("Param processes completed")
        await C1socket.socket_update(mount_location_new, realSave)
        print("Updated mount")
        await C1ftp.dlencrypted_bulk(False, user_id, realSave)
        print("downloaded")

        emb5 = discord.Embed(title="Resigning process (Encrypted): Successful",
                    description=f"**{saveName}** resigned to **{playstation_id}**",
                    colour=0x854bf7)
        emb5.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
        emb5.set_footer(text="Made with expertise by HTOP")

        await ctx.edit(embed=emb5)

    except (SocketError, FTPError, OrbisError, OSError) as e:
        if isinstance(e, OSError) and hasattr(e, "winerror") and e.winerror == 121: 
            e = "PS4 not connected!"
        elif isinstance(e, OrbisError): 
            print(f"{response} is invalid") # If OrbisError is raised you have stored an invalid save
        await errorHandling(ctx, e, workspaceFolders, files, mountPaths, C1ftp)
        return
    
    embRdone = discord.Embed(title="Resigning process (Encrypted): Successful",
                            description=f"**{saveName}** resigned to **{playstation_id}**",
                            colour=0x854bf7)
    embRdone.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
    embRdone.set_footer(text="Made with expertise by HTOP")
    
    await ctx.edit(embed=embRdone)
    
    zipfiles(newDOWNLOAD_ENCRYPTED, "PS4.zip")
    final_file = os.path.join(newDOWNLOAD_ENCRYPTED, "PS4.zip")
    final_size = os.path.getsize(final_file)
    file_size_mb = final_size / (1024 * 1024)

    if file_size_mb < BOT_DISCORD_UPLOAD_LIMIT:
        await ctx.respond(file=discord.File(final_file))
    else:
        reenc = final_file
        reenc_name = "PS4.zip"
        file_url = await GDapi.uploadzip(reenc, reenc_name)

        embg = discord.Embed(title="Google Drive: Upload complete",
                    description=f"Here is **{saveName}** resigned:\n<{file_url}>.",
                    colour=0x854bf7)
        embg.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
        embg.set_footer(text="Made with expertise by HTOP")
        await ctx.respond(embed=embg)

    # await asyncio.sleep(1)
    await cleanup(C1ftp, workspaceFolders, files, mountPaths)
    print("done")

@bot.slash_command(description="Change the titles of your save.")
async def changetitle(ctx, maintitle: Option(str, description="For example Grand Theft Auto V."), subtitle: Option(str, description="For example Franklin and Lamar (1.6%).")) -> None:
    newUPLOAD_ENCRYPTED, newUPLOAD_DECRYPTED, newDOWNLOAD_ENCRYPTED, newPNG_PATH, newPARAM_PATH, newDOWNLOAD_DECRYPTED, newKEYSTONE_PATH = initWorkspace()
    workspaceFolders = [newUPLOAD_ENCRYPTED, newUPLOAD_DECRYPTED, newDOWNLOAD_ENCRYPTED, 
                        newPNG_PATH, newPARAM_PATH, newDOWNLOAD_DECRYPTED, newKEYSTONE_PATH]
    try: await makeWorkspace(ctx, workspaceFolders)
    except WorkspaceError: return
    print("**********************************")
    C1ftp = FTPps(IP, PORT, PS_UPLOADDIR, newDOWNLOAD_DECRYPTED, newUPLOAD_DECRYPTED, newUPLOAD_ENCRYPTED,
                  newDOWNLOAD_ENCRYPTED, newPARAM_PATH, newKEYSTONE_PATH, newPNG_PATH)
    mountPaths = []

    await ctx.respond(embed=embTitleChange)

    try: uploaded_file_paths = await upload2(ctx, newUPLOAD_ENCRYPTED, max_files=MAX_FILES, sys_files=False, ps_save_pair_upload=True)
    except HTTPError as e:
        print(e)
        await ctx.edit(embed=embhttp)
        cleanupSimple(workspaceFolders)
        return
    except (TimeoutError, GDapiError) as e:
        await errorHandling(ctx, e, workspaceFolders, None, None, None)
        return
            
    savenamepng = []

    file_name_png = os.listdir(newUPLOAD_ENCRYPTED)

    for file_namepng1 in file_name_png:
        if not file_namepng1.endswith(".bin"):
            savenamepng.append(file_namepng1)

    print(uploaded_file_paths)
    print(savenamepng)
    if len(uploaded_file_paths) >= 2:
        random_string = generate_random_string(RANDOMSTRING_LENGTH)
        uploaded_file_paths = enumerateFiles(uploaded_file_paths, random_string)
        for save in savenamepng:
            realSave = f"{save}_{random_string}"
            print(f"doing {save}")

            embTitleChange1 = discord.Embed(title="Change title: Processing",
                                description=f"Processing {save}.",
                                colour=0x854bf7)
            embTitleChange1.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
            embTitleChange1.set_footer(text="Made with expertise by HTOP")

            try:
                os.rename(os.path.join(newUPLOAD_ENCRYPTED, save), os.path.join(newUPLOAD_ENCRYPTED, realSave))
                os.rename(os.path.join(newUPLOAD_ENCRYPTED, save + ".bin"), os.path.join(newUPLOAD_ENCRYPTED, realSave + ".bin"))
                await ctx.edit(embed=embTitleChange1)
                await C1ftp.uploadencrypted_bulk(realSave)
                mount_location_new = MOUNT_LOCATION + "/" + random_string
                await C1ftp.make1(mount_location_new)
                mountPaths.append(mount_location_new)
                await C1socket.socket_dump(mount_location_new, realSave)
                print("Mounted")
                location_to_scesys = mount_location_new + "/sce_sys"
                await C1ftp.dlparamonly_grab(location_to_scesys)
                print("grabbed param")
                accid = await obtainID(newPARAM_PATH)
                await handleTitles(newPARAM_PATH, maintitle, subtitle)
                await C1ftp.upload_sfo(newPARAM_PATH, location_to_scesys)
                await C1socket.socket_update(mount_location_new, realSave)
                print("Updated")
                await C1ftp.dlencrypted_bulk(False, accid, realSave)
                print("downloaded")

                embTitleSuccess = discord.Embed(title="Title altering process: Successful",
                            description=f"Altered the save titles of **{save}**.",
                            colour=0x854bf7)
                embTitleSuccess.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
                embTitleSuccess.set_footer(text="Made with expertise by HTOP")

                await ctx.edit(embed=embTitleSuccess)
                print(f"{save} done")

            except (SocketError, FTPError, OrbisError, OSError) as e:
                if isinstance(e, OSError) and hasattr(e, "winerror") and e.winerror == 121: 
                    e = "PS4 not connected!"
                await errorHandling(ctx, e, workspaceFolders, uploaded_file_paths, mountPaths, C1ftp)
                return
        
        if len(savenamepng) == 1:
            finishedFiles = "".join(savenamepng)
        else: finishedFiles = ", ".join(savenamepng)

        embTdone = discord.Embed(title="Title altering process: Successful",
                            description=f"Altered the save titles of **{finishedFiles}**.",
                            colour=0x854bf7)
        embTdone.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
        embTdone.set_footer(text="Made with expertise by HTOP")

        await ctx.edit(embed=embTdone)
        
        zipfiles(newDOWNLOAD_ENCRYPTED, "PS4.zip")
        final_file = os.path.join(newDOWNLOAD_ENCRYPTED, "PS4.zip")
        final_size = os.path.getsize(final_file)
        file_size_mb = final_size / (1024 * 1024)

        if file_size_mb < BOT_DISCORD_UPLOAD_LIMIT:
            await ctx.respond(file=discord.File(final_file))
        else:
            reenc = final_file
            reenc_name = "PS4.zip"
            file_url = await GDapi.uploadzip(reenc, reenc_name)

            embg = discord.Embed(title="Google Drive: Upload complete",
                    description=f"Here is **{finishedFiles}** with altered save titles:\n<{file_url}>",
                    colour=0x854bf7)
            embg.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
            embg.set_footer(text="Made with expertise by HTOP")
            await ctx.respond(embed=embg)

        await asyncio.sleep(1)
        await cleanup(C1ftp, workspaceFolders, uploaded_file_paths, mountPaths)
        print("done")

    else:
        await ctx.edit(embed=emb6)
        cleanupSimple(workspaceFolders)

@bot.slash_command(description="Convert a ps4 savefile to pc or vice versa on supported games that needs converting.")
async def convert(ctx, game: Option(str, choices=["GTA V", "RDR 2"], description="Choose what game the savefile belongs to."), savefile: discord.Attachment) -> None:
    newUPLOAD_ENCRYPTED, newUPLOAD_DECRYPTED, newDOWNLOAD_ENCRYPTED, newPNG_PATH, newPARAM_PATH, newDOWNLOAD_DECRYPTED, newKEYSTONE_PATH = initWorkspace()
    workspaceFolders = [newUPLOAD_ENCRYPTED, newUPLOAD_DECRYPTED, newDOWNLOAD_ENCRYPTED, 
                        newPNG_PATH, newPARAM_PATH, newDOWNLOAD_DECRYPTED, newKEYSTONE_PATH]
    try: await makeWorkspace(ctx, workspaceFolders)
    except WorkspaceError: return
    print("**********************************")

    embConverting = discord.Embed(title="Converting",
                        description=f"Starting convertion process for {game}...",
                        colour=0x854bf7)
    embConverting.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
    embConverting.set_footer(text="Made with expertise by HTOP")

    await ctx.respond(embed=embConverting)

    if savefile.size / (1024 * 1024) > BOT_DISCORD_UPLOAD_LIMIT:
        e = "File size is too large!" # may change in the future when a game with larger savefile sizes are implemented
        await errorHandling(ctx, e, workspaceFolders, None, None, None)
        return

    savegame = os.path.join(newUPLOAD_DECRYPTED, savefile.filename)
    await savefile.save(savegame)

    try:
        if game == "GTA V":
            result = await Converter.Rstar.convertFile_GTAV(savegame)
        
        elif game == "RDR 2":
            result = await Converter.Rstar.convertFile_RDR2(savegame)
    
    except ConverterError as e:
        await errorHandling(ctx, e, workspaceFolders, None, None, None)
        return
    
    embCDone = discord.Embed(title="Success",
                        description=f"{result}\nPlease report any errors.",
                        colour=0x854bf7)
    embCDone.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
    embCDone.set_footer(text="Made with expertise by HTOP")

    await ctx.edit(embed=embCDone)
    await ctx.respond(file=discord.File(savegame))

    cleanupSimple(workspaceFolders)
    print("done")

@bot.slash_command(description="Checks if the bot is functional.")
async def ping(ctx) -> None:
    print("**********************************")
    await ctx.defer()
    result = 0
    latency = bot.latency * 1000
    C1ftp = FTPps(IP, PORT, None, None, None, None, None, None, None, None)
    try:
        await C1ftp.testConnection()
        result += 1
        print("PING: connected to FTP")
    except OSError as e:
        print(f"PING: FTP could not connect: {e}")

    try:
        await C1socket.testConnection()
        result += 1
        print("PING: connected to SOCKET")
    except (OSError) as e:
        print(f"PING: SOCKET could not connect: {e}")

    if result == 2:
        func = discord.Embed(title=f"Connections: 2/2\nLatency: {latency: .2f}ms", color=0x22EA0D)

        func.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
        await ctx.respond(embed=func)
        print(f"bot is functional: {result}/2")
    else: 
        notfunc = discord.Embed(title=f"Connections: {result}/2\nLatency: {latency: .2f}ms", colour=0xF42B00)

        notfunc.set_thumbnail(url="https://cdn.discordapp.com/avatars/248104046924267531/743790a3f380feaf0b41dd8544255085.png?size=1024")
        await ctx.respond(embed=notfunc)
        print(f"bot is not functional: {result}/2")

@bot.command()
@commands.is_owner()
async def init(ctx) -> None:
    try: 
        await ctx.channel.purge(limit=1)
    except Exception as e:
        print(f"Can not purge message sent: {e}")

    await ctx.send(embed=embinit, view=threadButton())

bot.run(str(os.getenv("TOKEN")))