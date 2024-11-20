from dotenv import load_dotenv
load_dotenv()

import discord
from utils.constants import bot, TOKEN
from utils.workspace import startup, check_version
from utils.helpers import threadButton
bis = ":bust_in_silhouette:"
arw = "<:resignarrow:1308822404214030397>"
@bot.event
async def on_ready() -> None:
    from google_drive import checkGDrive
    startup()
    await check_version()
    bot.add_view(threadButton()) # make view persistent
    checkGDrive.start() # start gd daemon
    print(
        f"Bot is ready, invite link: https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot"
    )

@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author.bot:
        return

    if message.content == "hello":
        await message.channel.send("hi")

    await bot.process_commands(message)
### Enter new commands here because apparently THATS A THING????

# /help start
@bot.slash_command(name="help", description="Learn how to use the PS4 Save Editor Bot.")
async def helpbot(ctx: discord.ApplicationContext):
    embed = discord.Embed(
        title="PS4 Save Editor Bot - Tutorial",
        description=(
            "Welcome to the PS4 Save Editor Bot! This bot is designed to assist you in modifying and managing your PS4 save games, ",
            "whether you're looking to resign, decrypt, or customize your saves.\n\n",
            "### **How to Use**\n",
            "Use the following commands to interact with your PS4 save files. For best results, ensure your saves are compatible.\n\n",
            "**Core Commands:**\n",
            {bis}, {arw}, {bis}, "**/resign** - Resign your PS4 save file to a new PlayStation account.\n",
            "🌍 **/reregion** - Change the region of a save to match your game version.\n",
            "🔓 **/decrypt** - Decrypt your save file for editing.\n",
            "🔒 **/encrypt** - Re-encrypt your save file after making changes.\n",
            "🖼️ **/change picture** - Customize the icon/picture associated with your save.\n",
            "📝 **/change title** - Modify the title of your save file for better organization.\n\n",
            "**Quick and Advanced Tools:**\n",
            "⚡ **/quick cheats** - Add pre-made cheat codes to your save for specific games.\n",
            "🎮 **/quick codes** - Apply quick save modifications with preloaded codes.\n",
            "📁 **/quick resign** - Quickly resign pre-stored save files.\n",
            "🔑 **/sealed_key decrypt** - Decrypt sealed keys in `.bin` files.\n",
            "🧩 **/convert** - Convert PS4 save files to PC or other supported platforms.\n",
            "📜 **/sfo read** - Extract information from a `param.sfo` file.\n",
            "🖋️ **/sfo write** - Edit and rewrite parameters in a `param.sfo` file.\n\n",
            "**Important Notes:**\n",
            "- Ensure that your saves are properly backed up before making modifications.\n",
            "- Resigning and re-encryption are required for saves to function on new accounts or consoles.\n\n",
            "**Learn More**\n",
            "Watch our detailed video tutorial for step-by-step instructions: **[YouTube Tutorial](https://www.youtube.com/watch?v=cGeVhia0KjA)**\n\n",
            "If you encounter any issues or need further help, please let me know. **Saviel** 🔥",
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