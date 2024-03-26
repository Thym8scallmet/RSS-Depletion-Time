import datetime
import os
import platform
import time
from threading import Thread

import discord
from colorama import Back, Fore, Style
from discord import File
from discord.ext import commands
from flask import Flask

#for hosting to to discord
app = Flask('')


@app.route('/')
def home():
  return "Rss Time is up and running live!"


def run():
  app.run(host='0.0.0.0', port=8080)


def keep_alive():
  t = Thread(target=run)
  t.start()


# Start of bot code
client = commands.Bot(command_prefix='.', intents=discord.Intents.all())


async def setup_hook():
  current_cog = None  # Introduce variable to keep track of the current cog
  try:
    for cog in [
        "cogs.TileRS", "cogs.PurgeBot", "cogs.RssDepletion", "cogs.SSTimer",
        "cogs.Translate"
    ]:
      current_cog = cog  # Update current_cog before attempting to load
      await client.load_extension(cog)
  except Exception as e:
    if current_cog:  # Check if current_cog has been set
      print(f"Failed to load extension {current_cog}:", e)
    else:
      print("Failed to load a cog due to an error before loading:", e)


client.setup_hook = setup_hook


@client.event  # This will run each time you restart the bot.
async def on_ready():
  prfx = (Back.BLACK + Fore.GREEN +
          time.strftime("%H:%M:%S UTC", time.gmtime()) + Back.RESET +
          Fore.WHITE + Style.BRIGHT)
  # this formats the output to the counsole
  if client is not None and client.user is not None:
    print(prfx + " Logged in as " + Fore.YELLOW + client.user.name)
    print(prfx + " Bot ID " + Fore.YELLOW + str(client.user.id))
    print(prfx + " Discord Version " + Fore.YELLOW + discord.__version__)
    print(prfx + " Python Version " + Fore.YELLOW +
          str(platform.python_version()))
    #this is needed for the slash commands to work
    synced = await client.tree.sync()
    print(prfx + " Slash CMDs Synced " + Fore.YELLOW + str(len(synced)) +
          " Commands")
    #print(prfx + " Slash CMDs Synced " + Fore.YELLOW + str(len(synced)) + " Commands")
    print(prfx + " Bot is Logged in and ready")


@client.command()
async def rsshelp(ctx):
  embed = discord.Embed(  # Here we assign the discord.Embed object to embed
      title="Rss Depletion Info instructions",
      description=
      ("To use this bot, you must use the command prefix .rss\n\n"
       "It will ask you to provide 2 values. "
       "To obtain these values, \n"
       "Take a screenshot of your alliance's Resource mill's View Details page.\n"
       "After one minute, take another screenshot of the same page.\n\n"
       "Then run the command **.rss** and press enter.\n\n"
       "Enter the Remaining resources from the First SS and press enter.\n"
       "Enter the Remaining resources from the Second SS and press enter.\n\n"
       "You will then get a display of how long until depletion of the mill."),
  )
  await ctx.send(embed=embed)  # Using the correctly defined embed here


@client.command(aliases=['rsstime', 'rsst', 'rssremaining'])
async def rss(ctx):
  await ctx.send("Enter the starting amount (not larger than 400 million "
                 "and without decimals or commas):")
  # Wait for a response from the same user who initiated the command
  msg = await client.wait_for('message',
                              check=lambda message: message.author == ctx.
                              author and message.content.isdigit())

  # Ensure the input for num1 is a valid whole number and not larger than 400 million
  num1 = int(msg.content)
  if num1 > 400000000:
    await ctx.send(
        "The starting amount must not be larger than 400 million. "
        "Please enter number without decimals or commas within the limit.")
    return

  await ctx.send("Enter the amount after 1 minute"
                 " (not larger than 400 million without decimals or commas):")
  # Wait for another response from the same user
  msg = await client.wait_for('message',
                              check=lambda message: message.author == ctx.
                              author and message.content.isdigit())

  # Ensure the input for num2 is a valid whole number and not larger than 400 million
  num2 = int(msg.content)
  if num2 > 400000000:
    await ctx.send(
        "The second amount must not be larger than 400 million."
        "Please enter number without decimals or commas within the limit.")
    return

  rate = num1 - num2
  if rate > 0:
    minutes = num2 / rate
    hours = minutes / 60
    days = hours / 24
  else:
    await ctx.send("Error: Rate of resource gathering cannot be zero.")
    return

  # Calculate the time when the resources will run out by adding
  #'minutes' to the current UTC time
  depletion_time_utc = datetime.datetime.utcnow() + datetime.timedelta(
      minutes=minutes)

  if rate > 0:
    file_path = 'files/GasfieldSnip.PNG'
    file = File(file_path, filename="GasfieldSnip.PNG")
    embed = discord.Embed(
        title="Rss Depletion Info",
        description=(
            f"The starting resource amount is {num1:.0f}\n"
            f"The amount after 1 minute is {num2:.0f}\n\n"
            f"Resources are being gathered at **{rate:.0f}** per minute"),
        colour=discord.Colour.blue(),
        timestamp=ctx.message.created_at)
    msg = await ctx.send(file=file)
    embed.set_thumbnail(url=msg.attachments[0].url)
    embed.add_field(
        name="At the current gathering rate, the mill will be depleted in:",
        value=f"{minutes:.0f} minutes\n{hours:.1f} hours\n{days:.1f} days",
        inline=False)
    embed.add_field(
        name="The mill will be depleted by:",
        value=f"{depletion_time_utc.strftime('%a, %B %#d, %Y, %I:%M %p UTC')}",
        inline=False)
    embed.add_field(name="Local Time for mill depletion:",
                    value=f"<t:{int(depletion_time_utc.timestamp())}:F>",
                    inline=False)
    embed.set_footer(
        text=f"\nThis command was run by {ctx.author.display_name}")

    await ctx.send(embed=embed)
    await msg.delete()
  else:
    await ctx.send(
        "Invalid input. The first amount must be greater than the second.")
    return


token = os.getenv("TOKEN")
# Just before starting your bot
if __name__ == "__main__":
  keep_alive()  # Start the Flask web server
  if token is not None:
    client.run(token)
  else:
    print("Token not loaded properly. Check your environment variables.")
