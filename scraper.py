import aiohttp
import os

SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY")
print(f"ScraperAPI Key loaded: {SCRAPER_API_KEY[:5] if SCRAPER_API_KEY else 'NOT FOUND'}")

def scraper_url(url):
    return f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}

# --- TARGET ---
async def check_target(tcin, store_id="3991"):
    try:
        url = (
            f"https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1"
            f"?key=9f36aeafbe60771e321a7cc95a78140772ab3e96"
            f"&tcin={tcin}&store_id={store_id}&pricing_store_id={store_id}"
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(scraper_url(url), headers=HEADERS, timeout=aiohttp.ClientTimeout(total=30)) as r:
                print(f"Target status: {r.status} for {tcin}")
                if r.status != 200:
                    return None, None
                data = await r.json(content_type=None)
                product = data["data"]["product"]
                status = product["fulfillment"]["shipping_options"]["availability_status"]
                try:
                    price = product["price"]["current_retail"]
                except:
                    price = None
                print(f"Target {tcin}: {status} | ${price}")
                return status == "IN_STOCK", price
    except Exception as e:
        print(f"Target error ({tcin}): {e}")
        return None, None

# --- WALMART ---
async def check_walmart(item_id):
    try:
        url = f"https://www.walmart.com/terra-firma/item?ids={item_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(scraper_url(url), headers=HEADERS, timeout=aiohttp.ClientTimeout(total=30)) as r:
                print(f"Walmart status: {r.status} for {item_id}")
                if r.status != 200:
                    return None, None
                data = await r.json(content_type=None)
                product = data["payload"]["selected"]["product"]
                available = product["buyBox"]["pickupEligible"]
                try:
                    price = product["priceMap"]["price"]
                except:
                    price = None
                print(f"Walmart {item_id}: {available} | ${price}")
                return available, price
    except Exception as e:
        print(f"Walmart error ({item_id}): {e}")
        return None, None

# --- POKEMON CENTER ---
async def check_pokemoncenter(product_id):
    try:
        url = f"https://www.pokemoncenter.com/api/products/{product_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(scraper_url(url), headers=HEADERS, timeout=aiohttp.ClientTimeout(total=30)) as r:
                print(f"PokeCenter status: {r.status} for {product_id}")
                if r.status != 200:
                    return None, None
                data = await r.json(content_type=None)
                in_stock = data.get("inStock", False)
                try:
                    price = data["price"]
                except:
                    price = None
                print(f"PokeCenter {product_id}: {in_stock} | ${price}")
                return in_stock, price
    except Exception as e:
        print(f"PokeCenter error ({product_id}): {e}")
        return None, None

# --- ROUTER ---
async def check_stock(item):
    site = item["site"]
    pid = item["product_id"]

    if site == "target":
        return await check_target(pid)
    elif site == "walmart":
        return await check_walmart(pid)
    elif site == "pokemoncenter":
        return await check_pokemoncenter(pid)
    return None, None