import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import json, os
from dotenv import load_dotenv
from scraper import check_stock

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
ROLE_ID = int(os.getenv("ROLE_ID"))
WATCHLIST_FILE = "watchlist.json"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE) as f:
            return json.load(f)
    return []

def save_watchlist(data):
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(data, f, indent=2)

@bot.command()
async def watch(ctx, site: str, product_id: str, *, name: str):
    """Usage: !watch target 12345678 Pokemon Cards"""
    watchlist = load_watchlist()

    # Check for duplicates
    for item in watchlist:
        if item["site"] == site.lower() and item["product_id"] == product_id:
            await ctx.send(f"⚠️ **{item['name']}** is already on the watchlist!")
            return

    entry = {
        "site": site.lower(),
        "product_id": product_id,
        "name": name,
        "in_stock": False
    }
    watchlist.append(entry)
    save_watchlist(watchlist)
    await ctx.send(f"✅ Now watching **{name}** on **{site}** (ID: `{product_id}`)")

@bot.command()
async def watchlist(ctx):
    """Show everything being watched"""
    wl = load_watchlist()
    if not wl:
        await ctx.send("Watchlist is empty. Use `!watch <site> <product_id> <name>`")
        return
    
    # Build lines
    lines = [f"`{i}` — {item['name']} ({item['site']}, ID: {item['product_id']})" 
             for i, item in enumerate(wl)]
    
    # Split into chunks under 2000 characters
    chunks = []
    current = "**Current Watchlist:**\n"
    for line in lines:
        if len(current) + len(line) + 1 > 1900:
            chunks.append(current)
            current = "**Continued:**\n"
        current += line + "\n"
    chunks.append(current)

    # Send each chunk as a separate message
    for chunk in chunks:
        await ctx.send(chunk)

@bot.command()
async def remove(ctx, index: int):
    """Remove an item by index: !remove 0"""
    wl = load_watchlist()
    if 0 <= index < len(wl):
        removed = wl.pop(index)
        save_watchlist(wl)
        await ctx.send(f"🗑️ Removed **{removed['name']}**")
    else:
        await ctx.send("Invalid index.")

async def check_all_stock():
    channel = bot.get_channel(CHANNEL_ID)
    wl = load_watchlist()
    changed = False

    for item in wl:
        result, price = check_stock(item)
        if result is True and not item["in_stock"]:
            item["in_stock"] = True
            changed = True
            role = discord.utils.get(channel.guild.roles, id=ROLE_ID)

            if item["site"] == "target":
                link = f"https://www.target.com/p/-/A-{item['product_id']}"
            elif item["site"] == "walmart":
                link = f"https://www.walmart.com/ip/{item['product_id']}"
            elif item["site"] == "pokemoncenter":
                link = f"https://www.pokemoncenter.com/product/{item['product_id']}"

            price_str = f"💰 **${price:.2f}**\n" if price else ""

            await channel.send(
                f"{role.mention} 🚨 **IN STOCK: {item['name']}**\n"
                f"Site: {item['site']} | ID: `{item['product_id']}`\n"
                f"{price_str}"
                f"🔗 {link}"
            )
        elif result is False and item["in_stock"]:
            item["in_stock"] = False
            changed = True

    if changed:
        save_watchlist(wl)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_all_stock, "interval", minutes=2)
    scheduler.start()

bot.run(TOKEN)