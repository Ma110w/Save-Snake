from dotenv import load_dotenv
load_dotenv()

import discord
from utils.constants import bot, TOKEN
from utils.workspace import startup, check_version
from utils.helpers import threadButton
import asyncio

bot_owner_name = None

async def fetch_bot_owner():
    global bot_owner_name
    app_info = await bot.application_info()
    bot_owner_name = f"🐍 **Bot Owner:** **{app_info.owner.name}**"

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

    if message.content.lower() == "hello":
        await message.channel.send("yeah? whatcha need?")

    if bot.user.mention in message.content.lower():
        if "hi" in message.content.lower() or "hello" in message.content.lower():
            await message.channel.send("?")
        elif "whats up" in message.content.lower() or "whatup" in message.content.lower():
            await message.channel.send("Hey! What's up?")
        elif "what's up?" in message.content.lower() or "what ya doing?" in message.content.lower():
            await message.channel.send("Nothing much, Although {app_info.owner.name} has not turned Me off in 3 weeks, My Work is Torture.")
        elif "guten morgen" in message.content.lower():
            await message.channel.send("Bonjour! Je vous souhaite une excellente journée!")
        elif "gute nacht" in message.content.lower():
            await message.channel.send("Bonne nuit! Fais de beaux rêves")
        elif "wie geht's" in message.content.lower():
            await message.channel.send("Je vais très bien, merci de demander!")
        elif "was geht" in message.content.lower():
            await message.channel.send("Pas grand-chose, mais je suis là pour aider!")
        elif "hallo" in message.content.lower():
            await message.channel.send("Salut! Comment puis-je vous aider?")
        elif "hi bot" in message.content.lower():
            await message.channel.send("Hi! How can I assist you today?")
        elif "servus" in message.content.lower():
            await message.channel.send("Salut! Comment puis-je vous être utile?")
        elif "hey" in message.content.lower():
            await message.channel.send("Hey! what ya want?")
        elif "moin" in message.content.lower():
            await message.channel.send("Salut! En quoi puis-je vous aider?")
        elif "hey there" in message.content.lower():
            await message.channel.send("Hey there!")
        elif "what's up bot" in message.content.lower():
            await message.channel.send("Not much, I dont think you really want the answer though")
        elif "hallo bot" in message.content.lower():
            await message.channel.send("Salut! Comment puis-je t'aider?")
        elif "how's it going" in message.content.lower():
            await message.channel.send("It's going great! Thanks for asking!")
        elif "whats the news" in message.content.lower():
            await message.channel.send("No news yet, but I'm ready to help!")
        elif "wie läufts" in message.content.lower():
            await message.channel.send("Tout va bien! Merci de demander!")
        elif "yo bot" in message.content.lower():
            await message.channel.send("Yo! How can I help today?")
        elif "hello bot" in message.content.lower():
            await message.channel.send("Hello! What can I do for you today?")
        elif "guten tag" in message.content.lower():
            await message.channel.send("Bonjour! Comment puis-je vous aider?")
        elif "alles klar" in message.content.lower():
            await message.channel.send("Tout va bien! Comment puis-je t'aider?")
        elif "how's everything going" in message.content.lower():
            await message.channel.send("Everything's going well! How can I assist you?")
        elif "everything okay" in message.content.lower():
            await message.channel.send("Everything's great! How can I help you today?")
        elif "is everything good" in message.content.lower():
            await message.channel.send("Yes, everything's fine! How can I assist you today?")
        elif "hey bot" in message.content.lower():
            await message.channel.send("Hey! Ready to help, as always!")
        elif "hiya" in message.content.lower():
            await message.channel.send("おはようございます!")


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
            f"If you encounter any issues or need further help, please let me know. **{bot_owner_name}**\n"
            "**Conditions**\n\n"
            f"Please ask before attempting to use my bot for financial gain. I'm happy to give permission; just ping me first. **{bot_owner_name}**"

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