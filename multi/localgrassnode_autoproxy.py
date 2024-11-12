import asyncio
import random
import ssl
import json
import time
import uuid
import requests
import shutil
from loguru import logger
from websockets_proxy import Proxy, proxy_connect
from fake_useragent import UserAgent
from colorama import init, Fore, Back, Style
import sys

init(autoreset=True)

def tampilkan_banner():
    banner = f"""
{Fore.GREEN}╔═══════════════════════════════════════════════════════════════════════════╗
{Fore.GREEN}║                                                                           ║
{Fore.GREEN}║   ██████╗ ██████╗  █████╗ ███████╗███████╗    ██████╗  ██████╗ ████████╗  ║
{Fore.GREEN}║  ██╔════╝ ██╔══██╗██╔══██╗██╔════╝██╔════╝    ██╔══██╗██╔═══██╗╚══██╔══╝  ║
{Fore.GREEN}║  ██║  ███╗██████╔╝███████║███████╗███████╗    ██████╔╝██║   ██║   ██║     ║
{Fore.GREEN}║  ██║   ██║██╔══██╗██╔══██║╚════██║╚════██║    ██╔══██╗██║   ██║   ██║     ║
{Fore.GREEN}║  ╚██████╔╝██║  ██║██║  ██║███████║███████║    ██████╔╝╚██████╔╝   ██║     ║
{Fore.GREEN}║   ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝    ╚═════╝  ╚═════╝    ╚═╝     ║
{Fore.GREEN}║                                                                           ║
{Fore.GREEN}║        Auto Remove Proxies - Created by: @AirdropFamilyIDN                ║
{Fore.GREEN}╚═══════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

tampilkan_banner()

logger.remove()
logger.add(sys.stderr, format="Tanggal {time:YYYY-MM-DD} Jam {time:HH:mm:ss} | {level} | {message}")

async def connect_to_wss(socks5_proxy, user_id):
    user_agent = UserAgent(os=['windows', 'macos', 'linux'], browsers='chrome')
    random_user_agent = user_agent.random
    device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, socks5_proxy))
    logger.info(f"{Fore.GREEN}Koneksi device terhubung...")
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
            urilist = ["wss://proxy2.wynd.network:4444/","wss://proxy2.wynd.network:4650/"]
            uri = random.choice(urilist)
            server_hostname = "proxy2.wynd.network"
            proxy = Proxy.from_url(socks5_proxy)
            async with proxy_connect(uri, proxy=proxy, ssl=ssl_context, server_hostname=server_hostname,
                                     extra_headers=custom_headers) as websocket:
                async def send_ping():
                    while True:
                        send_message = json.dumps(
                            {"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}})
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
            proxy_to_remove = socks5_proxy

            with open('auto_proxies.txt', 'r') as file:
                lines = file.readlines()

            updated_lines = [line for line in lines if line.strip() != proxy_to_remove]

            with open('auto_proxies.txt', 'w') as file:
                file.writelines(updated_lines)

            logger.info(f"{Fore.RED}Proxy '{proxy_to_remove}' has been removed from the file.")

async def main():
    with open('user_id.txt', 'r') as user_file:
        user_ids = user_file.read().splitlines()

    r = requests.get("https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=text", stream=True)
    if r.status_code == 200:
        with open('auto_proxies.txt', 'wb') as f:
            for chunk in r:
                f.write(chunk)
        with open('auto_proxies.txt', 'r') as file:
            auto_proxy_list = file.read().splitlines()

    max_connections_per_user = 40

    for user_id in user_ids:
        proxies_for_user = auto_proxy_list[:max_connections_per_user]
        tasks = [asyncio.ensure_future(connect_to_wss(proxy, user_id)) for proxy in proxies_for_user]
        await asyncio.gather(*tasks)

        auto_proxy_list = auto_proxy_list[max_connections_per_user:]
        if not auto_proxy_list:
            logger.info(f"{Fore.YELLOW}Tidak ada proxy yang tersisa untuk digunakan.")
            break

if __name__ == '__main__':
    asyncio.run(main())
