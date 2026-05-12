import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.target.com/",
}

# --- TARGET ---
def check_target(tcin, store_id="3991"):
    try:
        url = (
            f"https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1"
            f"?key=9f36aeafbe60771e321a7cc95a78140772ab3e96"
            f"&tcin={tcin}&store_id={store_id}&pricing_store_id={store_id}"
        )
        session = requests.Session()
        session.get("https://www.target.com", headers=HEADERS, timeout=10)
        r = session.get(url, headers=HEADERS, timeout=10)
        print(f"Target status: {r.status_code} for {tcin}")
        data = r.json()
        product = data["data"]["product"]
        status = product["fulfillment"]["shipping_options"]["availability_status"]
        
        # Get price
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
def check_walmart(item_id):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": f"https://www.walmart.com/ip/{item_id}",
        }
        url = f"https://www.walmart.com/terra-firma/item?ids={item_id}"
        session = requests.Session()
        session.get(f"https://www.walmart.com/ip/{item_id}", headers=headers, timeout=10)
        r = session.get(url, headers=headers, timeout=10)
        print(f"Walmart status: {r.status_code} for {item_id}")
        data = r.json()
        product = data["payload"]["selected"]["product"]
        available = product["buyBox"]["pickupEligible"]

        # Get price
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
def check_pokemoncenter(product_id):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Referer": "https://www.pokemoncenter.com/",
        }
        url = f"https://www.pokemoncenter.com/api/products/{product_id}"
        r = requests.get(url, headers=headers, timeout=10)
        print(f"PokeCenter status: {r.status_code} for {product_id}")
        data = r.json()
        in_stock = data.get("inStock", False)

        # Get price
        try:
            price = data["price"]
        except:
            price = None

        print(f"PokeCenter {product_id}: {in_stock} | ${price}")
        return in_stock, price
    except Exception as e:
        print(f"PokemonCenter error ({product_id}): {e}")
        return None, None

# --- ROUTER ---
def check_stock(item):
    site = item["site"]
    pid = item["product_id"]

    if site == "target":
        return check_target(pid)
    elif site == "walmart":
        return check_walmart(pid)
    elif site == "pokemoncenter":
        return check_pokemoncenter(pid)
    return None, None