import asyncio
import random
import ssl
import json
import time
import uuid
from loguru import logger
from websockets_proxy import Proxy, proxy_connect
from fake_useragent import UserAgent

user_agent = UserAgent()
random_user_agent = user_agent.random

async def connect_to_wss(proxy_url, user_id):
    device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, proxy_url))
    logger.info(f"Device ID: {device_id}")
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
            uri = "wss://proxy.wynd.network:4650"
            server_hostname = "proxy.wynd.network"
            proxy = Proxy.from_url(proxy_url)
            logger.info(f"Connecting to {uri} using proxy {proxy_url}")
            async with proxy_connect(uri, proxy=proxy, ssl=ssl_context, server_hostname=server_hostname,
                                     extra_headers=custom_headers) as websocket:
                async def send_ping():
                    while True:
                        send_message = json.dumps(
                            {"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}})
                        logger.debug(f"Sending PING: {send_message}")
                        await websocket.send(send_message)
                        await asyncio.sleep(5)

                await asyncio.sleep(1)
                asyncio.create_task(send_ping())

                while True:
                    response = await websocket.recv()
                    message = json.loads(response)
                    logger.info(f"Received message: {message}")
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
                                "version": "4.20.2",
                                "extension_id": "lkbnfiajjmbhnfledhphioinpickokdi"
                            }
                        }
                        logger.debug(f"Sending AUTH response: {auth_response}")
                        await websocket.send(json.dumps(auth_response))

                    elif message.get("action") == "PONG":
                        pong_response = {"id": message["id"], "origin_action": "PONG"}
                        logger.debug(f"Sending PONG response: {pong_response}")
                        await websocket.send(json.dumps(pong_response))
        except Exception as e:
            logger.error(f"Error: {e}")
            logger.error(f"Proxy: {proxy_url}")

async def main():
    with open('data.txt', 'r') as file:
        lines = file.read().splitlines()
    
    user_proxies = {}
    current_user_id = None
    for line in lines:
        if not line.startswith(('http', 'socks4', 'socks5')):
            current_user_id = line
            user_proxies[current_user_id] = []
        else:
            user_proxies[current_user_id].append(line)

    logger.info(f"User proxies: {user_proxies}")

    tasks = []
    for user_id, proxies in user_proxies.items():
        for proxy in proxies:
            logger.info(f"Scheduling task for user {user_id} with proxy {proxy}")
            tasks.append(asyncio.ensure_future(connect_to_wss(proxy, user_id)))
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())
