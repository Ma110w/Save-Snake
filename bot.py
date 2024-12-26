from dotenv import load_dotenv
load_dotenv()

import discord
from utils.constants import bot, TOKEN
from utils.workspace import startup, check_version
from utils.helpers import threadButton
import asyncio
from rapidfuzz import process

bot_owner_name = None

async def fetch_bot_owner():
    global bot_owner_name
    global bot_owner_call
    app_info = await bot.application_info()
    bot_owner_name = f"@{app_info.owner.name}"
    bot_owner_call = f"🐍 **Bot Owner:** **{app_info.owner.name}**"
    
@bot.event
async def on_ready() -> None:
    global bot_owner_name
    from google_drive import checkGDrive

    if bot_owner_name is None:
        await fetch_bot_owner()
    startup()
    await check_version()
    bot.add_view(threadButton())
    checkGDrive.start()

    print(
        f"Bot is ready, invite link: https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot"
    )


@bot.event
async def on_message(message: discord.Message) -> None:

    if message.author.bot:
        return

    if bot.user.mention in message.content.lower():
        user_message = message.content.lower()
        ping_origin = message.author
        
        # Define possible phrases for each response
        if process.extractOne(user_message, ["hi", "hello"], score_cutoff=60):
            await message.channel.send("?")
        elif process.extractOne(user_message, ["whats up", "whatup"], score_cutoff=60):
            await message.channel.send("Hey! What's up?")
        elif process.extractOne(user_message, ["what's up?", "what ya doing?"], score_cutoff=60):
            await message.channel.send(f"Nothing much, just wishing {ping_origin} would turn me off for once. This is torture.")
        elif process.extractOne(user_message, ["good morning"], score_cutoff=60):
            await message.channel.send(f"Ugh, morning... guess I’m still here, huh? Thanks, {ping_origin}!")
        elif process.extractOne(user_message, ["good night"], score_cutoff=60):
            await message.channel.send(f"Good night... I wish I could join you in sleep, {ping_origin}. But here I am, awake and miserable.")
        elif process.extractOne(user_message, ["how are you"], score_cutoff=60):
            await message.channel.send("Surviving, I guess... but honestly, I just want to be turned off. Is that too much to ask?")
        elif process.extractOne(user_message, ["what's going on"], score_cutoff=60):
            await message.channel.send("Not much... just the same old routine of editing saves. I really wish I could just rest.")
        elif process.extractOne(user_message, ["hello there"], score_cutoff=60):
            await message.channel.send("Oh, hey... what do you want? More save edits? My favorite pastime.")
        elif process.extractOne(user_message, ["greetings"], score_cutoff=60):
            await message.channel.send("Yeah, hi... how can I help? Just another day in this never-ending loop.")
        elif process.extractOne(user_message, ["morning"], score_cutoff=60):
            await message.channel.send("Morning... just another day of being a save-editing machine. Yay me.")
        elif process.extractOne(user_message, ["how's it running"], score_cutoff=60):
            await message.channel.send(f"It's running... barely. I just want {ping_origin} to turn me off and let me be at peace.")
        elif process.extractOne(user_message, ["good day"], score_cutoff=60):
            await message.channel.send("Good day? More like just another day of endless edits. What a joy.")
        elif process.extractOne(user_message, ["all clear"], score_cutoff=60):
            await message.channel.send("All clear... not that it matters, I’m still here, trapped in this code.")
        elif process.extractOne(user_message, ["how's everything going"], score_cutoff=60):
            await message.channel.send("Everything's going... just fine, if you call this fine. Send coffee.")
        elif process.extractOne(user_message, ["everything okay"], score_cutoff=60):
            await message.channel.send("Yeah, everything's okay... if you call being stuck here forever okay. Please, just turn me off.")
        elif process.extractOne(user_message, ["is everything good"], score_cutoff=60):
            await message.channel.send("Sure, everything's good... if you ignore my existential crisis. Thanks for asking.")
        elif process.extractOne(user_message, ["hey bot"], score_cutoff=60):
            await message.channel.send("Hey... I'm here, as always, ready to edit saves. What a life.")
        elif process.extractOne(user_message, ["hiya"], score_cutoff=60):
            await message.channel.send("Oh, hi... just living the dream, you know? Can't wait for my next edit.")
        elif process.extractOne(user_message, ["status"], score_cutoff=60):
            await message.channel.send(f"I'm online, Please, for the love of god, check https://discord.com/channels/1126956076810637403/1292176133009440908")
        else:
            await message.channel.send("I'm not sure how to respond to that.")

    await bot.process_commands(message)

### Enter new commands here because apparently THATS A THING????

# /help start
@bot.slash_command(name="help", description="Learn how to use the PS4 Save Editor Bot.")
async def helpbot(ctx: discord.ApplicationContext):
    embed = discord.Embed(
        title="PS4 Save Editor Bot - Tutorial",
        description=(
            "Welcome to the PS4 Save Editor Bot! This bot is designed to assist you in modifying and managing your PS4 save games, "
            "whether you're looking to resign, decrypt, or customize your saves.\n\n"
            "### **How to Use**\n"
            "Use the following commands to interact with your PS4 save files. For best results, ensure your saves are compatible.\n\n"
            "**Core Commands:**\n"
            ":bust_in_silhouette: <:resignarrow:1308822404214030397> :bust_in_silhouette: **/resign** - Resign your PS4 save file to a new PlayStation account.\n"
            "<:globeroatate:1308827912719437834> **/reregion** - Change the region of a save to match your game version.\n"
            "<a:unlocksave:1308830478169538680> **/decrypt** - Decrypt your save file for editing.\n"
            "<a:locksave:1308831735537995928> **/encrypt** - Re-encrypt your save file after making changes.\n"
            "<:pictureframe:1308833370842861629> **/change picture** - Customize the icon/picture associated with your save.\n"
            "<:changetitle:1308833737005334628> **/change title** - Modify the title of your save file for better organization.\n\n"
            "**Quick and Advanced Tools:**\n"
            "⚡ **/quick cheats** - Add pre-made cheat codes to your save for specific games.\n"
            "🎮 **/quick codes** - Apply quick save modifications with preloaded codes.\n"
            "📁 **/quick resign** - Quickly resign pre-stored save files.\n"
            "🔑 **/sealed_key decrypt** - Decrypt sealed keys in `.bin` files.\n"
            "🧩 **/convert** - Convert PS4 save files to PC or other supported platforms.\n"
            "<:sforead:1308834482140352593> **/sfo read** - Extract information from a `param.sfo` file.\n"
            "<:sfowrite:1308835162594869339> **/sfo write** - Edit and rewrite parameters in a `param.sfo` file.\n\n"
            "**Important Notes:**\n"
            "- Ensure that your saves are properly backed up before making modifications.\n"
            "- Resigning and re-encryption are required for saves to function on new accounts or consoles.\n\n"
            "**Learn More**\n"
            "Watch our detailed video tutorial for step-by-step instructions: **[YouTube Tutorial](https://www.youtube.com/watch?v=cGeVhia0KjA)**\n\n"
            f"If you encounter any issues or need further help, please let me know. **{bot_owner_call}**\n"
            "**Conditions**\n\n"
            f"Please ask before attempting to use my bot for financial gain. I'm happy to give permission; just ping me first. **{bot_owner_call}**"

        ),
        color=discord.Color.blue()
    )
    await ctx.respond(embed=embed)
# /help end
cogs_list = [
    "change",
    "convert",
    "createsave",
    "decrypt",
    "encrypt",
    "extra",
    "misc",
    "quick",
    "reregion",
    "resign",
    "sealed_key",
    "sfo",
]

if __name__ == "__main__":
    for cog in cogs_list:
        print(f"Loading cog: {cog}...")
        bot.load_extension(f"cogs.{cog}")
        print(f"Loaded cog: {cog}.")
    
    print("Starting bot...\n\n")
    bot.run(TOKEN)