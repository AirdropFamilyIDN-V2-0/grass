import asyncio
import random
import ssl
import json
import time
import uuid
import requests
import sys
from loguru import logger
from websockets_proxy import Proxy, proxy_connect
from fake_useragent import UserAgent
from colorama import init, Fore

init(autoreset=True)

# Function to display banner
def tampilkan_banner():
    banner = f"""
{Fore.GREEN}╔═══════════════════════════════════════════════════════════════════════════╗
{Fore.GREEN}║                                                                           ║
{Fore.GREEN}║   ██████╗ ██████╗  █████╗ ███████╗███████╗    ██████╗  ██████╗ ████████╗  ║
{Fore.GREEN}║  ██╔════╝ ██╔══██╗██╔══██╗██╔════╝██╔════╝    ██╔══██╗██╔═══██╗╚══██╔══╝  ║
{Fore.GREEN}║  ██║  ███╗██████╔╝███████║███████╗███████╗    ██████╔╝██║   ██║   ██║     ║
{Fore.GREEN}║  ██║   ██║██╔══██╗██╔══██║╚════██║╚════██║    ██╔══██╗██║   ██║   ██║     ║
{Fore.GREEN}║  ╚██████╔╝██║  ██║██║  ██║███████║███████║    ██████╔╝╚██████╔╝   ██║     ║
{Fore.GREEN}║   ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝    ╚═════╝  ╚═════╝    ╚═╝     ║
{Fore.GREEN}║                                                                           ║
{Fore.GREEN}║        Multi Akun For Free Proxy - Created by: @AirdropFamilyIDN          ║
{Fore.GREEN}╚═══════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

tampilkan_banner()

# Input manual untuk waktu tunggu dalam menit
try:
    waktu_tunggu_menit = int(input("Rotasi Proxy Dalam menit : "))
except ValueError:
    logger.error(f"{Fore.RED}Input tidak valid. Menggunakan waktu tunggu default 120 menit.")
    waktu_tunggu_menit = 120

# Set up logging format
logger.remove()
logger.add(sys.stderr, format="{time:YYYY-MM-DD} {time:HH:mm:ss} | ngarit | {message}")

# Function to handle WebSocket connection and proxy management
async def connect_to_wss(socks5_proxy, user_id):
    user_agent = UserAgent(os=['windows', 'macos', 'linux'], browsers='chrome')
    random_user_agent = user_agent.random
    device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, socks5_proxy))
    logger.info(f"{Fore.GREEN}Koneksi device terhubung")

    while True:
        try:
            await asyncio.sleep(random.randint(1, 10) / 10)
            custom_headers = {
                "User-Agent": random_user_agent,
                "Origin": "chrome-extension://lkbnfiajjmbhnfledhphioinpickokdi"
            }
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            urilist = ["wss://proxy.wynd.network:4444/", "wss://proxy.wynd.network:4650/"]
            uri = random.choice(urilist)
            server_hostname = "proxy.wynd.network"
            proxy = Proxy.from_url(socks5_proxy)
            async with proxy_connect(uri, proxy=proxy, ssl=ssl_context, server_hostname=server_hostname,
                                     extra_headers=custom_headers) as websocket:
                # Handle sending periodic pings to keep the connection alive
                async def send_ping():
                    while True:
                        send_message = json.dumps({"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}})
                        logger.info(f"{Fore.GREEN}PING dikirim")
                        await websocket.send(send_message)
                        await asyncio.sleep(5)

                await asyncio.sleep(1)
                asyncio.create_task(send_ping())

                while True:
                    response = await websocket.recv()
                    message = json.loads(response)
                    logger.info(f"{Fore.GREEN}Tersambung ke server")
                    if message.get("action") == "AUTH":
                        auth_response = {
                            "id": message["id"],
                            "origin_action": "AUTH",
                            "result": {
                                "browser_id": device_id,
                                "user_id": user_id,
                                "user_agent": custom_headers['User-Agent'],
                                "timestamp": int(time.time()),
                                "device_type": "extension",
                                "version": "4.26.2",
                                "extension_id": "lkbnfiajjmbhnfledhphioinpickokdi"
                            }
                        }
                        logger.info(f"{Fore.GREEN}Tersambung ke server")
                        await websocket.send(json.dumps(auth_response))

                    elif message.get("action") == "PONG":
                        pong_response = {"id": message["id"], "origin_action": "PONG"}
                        logger.info(f"{Fore.GREEN}Tersambung ke server")
                        await websocket.send(json.dumps(pong_response))
        except Exception as e:
           # logger.error(f"{Fore.RED}Terjadi error: {str(e)}")
            remove_proxy_from_file(socks5_proxy, user_id)

# Remove proxy from file if it's used or invalid
def remove_proxy_from_file(proxy_to_remove, user_id):
    user_proxy_file = f"{user_id}_proxies.txt"
    with open(user_proxy_file, 'r') as file:
        lines = file.readlines()

    updated_lines = [line for line in lines if line.strip() != proxy_to_remove]
    with open(user_proxy_file, 'w') as file:
        file.writelines(updated_lines)

   # logger.info(f"{Fore.RED}Proxy '{proxy_to_remove}' telah dihapus")

# Main execution loop
async def main():
    with open('user_id.txt', 'r') as user_file:
        user_ids = user_file.read().splitlines()

    # Fetch proxy list once
    r = requests.get("https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=text", stream=True)
    if r.status_code == 200:
        with open('auto_proxies.txt', 'wb') as f:
            for chunk in r:
                f.write(chunk)
        with open('auto_proxies.txt', 'r') as file:
            auto_proxy_list = file.read().splitlines()

    # Remove the max_connections_per_user limit
    # max_connections_per_user = 40

    # Create a list to hold all tasks
    all_tasks = []

    # Assign proxies for each user and create tasks
    for user_id in user_ids:
        # Remove the check for available proxies
        # if len(auto_proxy_list) < max_connections_per_user:
        #     logger.info(f"{Fore.YELLOW}Tidak ada cukup proxy yang tersisa untuk digunakan.")
        #     break

        # Assign all available proxies for this user
        proxies_for_user = auto_proxy_list  # Use all available proxies

        # Gabungkan proxy baru dengan proxy yang sudah ada
        user_proxy_file = f"{user_id}_proxies.txt"
        try:
            with open(user_proxy_file, 'r') as file:
                existing_proxies = file.read().splitlines()
        except FileNotFoundError:
            existing_proxies = []

        # Gabungkan proxy baru dengan yang sudah ada
        combined_proxies = list(set(existing_proxies + proxies_for_user))

        # Tulis proxy gabungan ke file
        with open(user_proxy_file, 'w') as file:
            for proxy in combined_proxies:
                file.write(f"{proxy}\n")

        # Create tasks for each proxy for this user
        tasks = [asyncio.ensure_future(connect_to_wss(proxy, user_id)) for proxy in proxies_for_user]
        all_tasks.extend(tasks)

        # Remove the proxies used for this user from the global list
        # auto_proxy_list = [proxy for proxy in auto_proxy_list if proxy not in proxies_for_user]
       # logger.info(f"{Fore.GREEN}Berpindah ke akun berikutnya setelah mencoba semua proxy untuk user_id: {user_id}")

    # Run all tasks concurrently
    await asyncio.gather(*all_tasks)

    #logger.info(f"{Fore.BLUE}Menunggu {waktu_tunggu_menit} menit sebelum mengambil proxy baru...")
    await asyncio.sleep(waktu_tunggu_menit * 60)

if __name__ == '__main__':
    asyncio.run(main())
