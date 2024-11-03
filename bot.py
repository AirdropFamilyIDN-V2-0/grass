import asyncio
import random
import ssl
import json
import time
import uuid
from loguru import logger
from websockets_proxy import Proxy, proxy_connect
from fake_useragent import UserAgent

# Generate a random user-agent
user_agent = UserAgent(os='windows', platforms='pc', browsers='chrome')
random_user_agent = user_agent.random

async def connect_to_wss(socks5_proxy, user_id, semaphore):
    async with semaphore:  # Limit concurrency using semaphore
        device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, socks5_proxy))
        logger.info(f"Connecting with Device ID: {device_id}")

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

                # List of possible WebSocket URIs
                urilist = ["wss://proxy.wynd.network:4444/", "wss://proxy.wynd.network:4650/"]
                uri = random.choice(urilist)
                server_hostname = "proxy.wynd.network"

                # Create Proxy object from proxy string
                proxy = Proxy.from_url(socks5_proxy)

                # Establish WebSocket connection using proxy
                async with proxy_connect(uri, proxy=proxy, ssl=ssl_context, server_hostname=server_hostname,
                                         extra_headers=custom_headers) as websocket:
                    
                    async def send_ping():
                        while True:
                            send_message = json.dumps(
                                {"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}})
                            logger.debug(f"Sending PING: {send_message}")
                            await websocket.send(send_message)
                            await asyncio.sleep(5)  # Ping every 5 seconds

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
                                    "version": "4.26.2",
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
                logger.error(f"Error with proxy {socks5_proxy}: {e}")
                await asyncio.sleep(5)  # Add a delay before retrying

async def main():
    _user_id = input('Please Enter your user ID: ')
    semaphore = asyncio.Semaphore(10)  # Limit to 10 concurrent connections

    # Read local proxies and add 'socks5://' prefix with proper authentication
    with open('local_proxies.txt', 'r') as file:
        local_proxies = []
        for line in file:
            parts = line.strip().split(':')  # Split proxy components
            if len(parts) == 4:  # Ensure it has 4 parts: host, port, username, password
                host = parts[0]
                port = parts[1]
                username = parts[2]
                password = parts[3]
                # Construct the socks5 proxy URL
                proxy_url = f'socks5://{username}:{password}@{host}:{port}'
                local_proxies.append(proxy_url)
            else:
                logger.error(f"Invalid proxy format: {line.strip()}")

    tasks = [asyncio.ensure_future(connect_to_wss(proxy, _user_id, semaphore)) for proxy in local_proxies]
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())
