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
import subprocess
import psutil
import os
from colorama import Fore, Style
import websockets

async def connect_to_wss(socks5_proxy, user_id, auto_proxy_list):
    user_agent = UserAgent(os=['windows', 'macos', 'linux'], browsers='chrome')
    random_user_agent = user_agent.random
    device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, socks5_proxy))
    logger.info(device_id)
    while True:
        try:
            await asyncio.sleep(random.randint(1, 10) / 10)
            custom_headers = {
                "User-Agent": random_user_agent,
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
                logger.info(Fore.GREEN + f"Proxy {socks5_proxy} tersambung ke WSS" + Style.RESET_ALL)
                async def send_ping():
                    while True:
                        try:
                            send_message = json.dumps(
                                {"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}})
                            await websocket.send(send_message)
                            await asyncio.sleep(5)
                        except websockets.exceptions.ConnectionClosedError as e:
                            logger.error(Fore.RED + f"Kesalahan koneksi saat mengirim PING" + Style.RESET_ALL)
                            break  # Keluar dari loop dan coba ulangi koneksi
                        except Exception as e:
                            logger.error(Fore.RED + f"Kesalahan saat mengirim PING" + Style.RESET_ALL)
                            break  # Keluar dari loop dan coba ulangi koneksi

                await asyncio.sleep(1)
                asyncio.create_task(send_ping())

                while True:
                    try:
                        response = await websocket.recv()
                        message = json.loads(response)
                        logger.info(message)
                        if message.get("action") == "AUTH":
                            auth_response = {
                                "id": message["id"],
                                "origin_action": "AUTH",
                                "result": {
                                    "browser_id": device_id,
                                    "user_id": user_id,
                                    "user_agent": custom_headers['User-Agent'],
                                    "timestamp": int(time.time()),
                                    "device_type": "desktop",
                                    "version": "4.29.0",
                                }
                            }
                            await websocket.send(json.dumps(auth_response))

                        elif message.get("action") == "PONG":
                            pong_response = {"id": message["id"], "origin_action": "PONG"}
                            logger.debug(pong_response)
                            await websocket.send(json.dumps(pong_response))
                    except websockets.exceptions.ConnectionClosedError as e:
                        logger.error(Fore.RED + f"Proxy {socks5_proxy} mengalami kesalahan koneksi" + Style.RESET_ALL)
                        await asyncio.sleep(5)  # Tunggu sebelum mencoba lagi
                    except ConnectionResetError as e:
                        logger.error(Fore.RED + f"Koneksi ditutup paksa oleh host jarak jauh" + Style.RESET_ALL)
                        await asyncio.sleep(5)  # Tunggu sebelum mencoba lagi
                    except Exception as e:
                        logger.error(Fore.RED + f"Kesalahan saat menerima pesan" + Style.RESET_ALL)
                        break  # Keluar dari loop dalam dan coba ulangi koneksi
        except Exception as e:
            logger.error(Fore.RED + f"Kesalahan saat mencoba terhubung" + Style.RESET_ALL)
            await asyncio.sleep(5)  # Tunggu sebelum mencoba lagi

def run_script():
    script_path = os.path.abspath(__file__)  # Mendapatkan path absolut dari file yang sedang dieksekusi
    
    # Coba untuk menghentikan instansi yang sudah berjalan dari script
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if 'python' in proc.info['name'] and script_path in proc.info['cmdline']:
            proc.terminate()  # Menghentikan proses

    # Jalankan script
    subprocess.Popen(["python", script_path])

async def main():
    # Baca user_id dari file userid.txt
    with open('userid.txt', 'r') as file:
        user_ids = file.read().splitlines()

    # Ambil proxy dari API
    r = requests.get("https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=text", stream=True)
    if r.status_code == 200:
        with open('auto_proxies.txt', 'wb') as f:
            for chunk in r:
                f.write(chunk)
        with open('auto_proxies.txt', 'r') as file:
            auto_proxy_list = file.read().splitlines()
            auto_proxy_list = auto_proxy_list[:50]  # Batasi hanya 50 proxy

    # Buat tugas untuk setiap kombinasi user_id dan proxy
    tasks = []
    for user_id in user_ids:
        for proxy in auto_proxy_list:
            tasks.append(asyncio.ensure_future(connect_to_wss(proxy, user_id, auto_proxy_list)))

    await asyncio.gather(*tasks)
    while True:
        run_script()
        time.sleep(300)  # Tidur selama 5 menit (300 detik)

if __name__ == '__main__':
    #letsgo
    asyncio.run(main())
