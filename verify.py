# -*- coding: utf-8 -*-
import re
import aiohttp
import asyncio
import random
import os
from datetime import datetime

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
]

IP_REGEX = re.compile(r"(.*:.*@)?\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}")

class ProxyValidator:
    pre_validators = []
    http_validators = []

    @classmethod
    def add_pre_validator(cls, func):
        cls.pre_validators.append(func)
        return func

    @classmethod
    def add_http_validator(cls, func):
        cls.http_validators.append(func)
        return func

@ProxyValidator.add_pre_validator
def validate_format(proxy):
    return True if IP_REGEX.fullmatch(proxy) else False

async def validate_http_proxy(session, semaphore, proxy):
    async with semaphore:
        headers = {
            'User-Agent': random.choice(USER_AGENTS)
        }
        proxy_url = f"http://{proxy}"
        try:
            async with session.get("http://www.ip3366.net/", headers=headers, proxy=proxy_url, timeout=3) as response:
                return response.status == 200
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return False

async def main():
    try:
        with open('proxy.txt', 'r', encoding='utf-8') as file:
            raw_proxies = set(line.strip() for line in file if line.strip())
    except FileNotFoundError:
        print("错误: proxy.txt 文件未找到")
        return

    valid_proxies = [p for p in raw_proxies if all(v(p) for v in ProxyValidator.pre_validators)]
    print(f"共读取到 {len(raw_proxies)} 个代理，格式有效的有 {len(valid_proxies)} 个")

    current_date = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(current_date, exist_ok=True)
    readme_path = os.path.join(current_date, 'README.md')
    if not os.path.exists(readme_path):
        with open(readme_path, 'w', encoding='utf-8') as readme_file:
            readme_file.write("# 验证通过的代理列表\n\n")

    semaphore = asyncio.Semaphore(100)
    connector = aiohttp.TCPConnector(limit=100)

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [(proxy, asyncio.create_task(validate_http_proxy(session, semaphore, proxy)))
                 for proxy in valid_proxies]

        results = await asyncio.gather(*(t for _, t in tasks))
        success_proxies = [proxy for (proxy, _), result in zip(tasks, results) if result]

    if success_proxies:
        with open(readme_path, 'a', encoding='utf-8') as readme_file:
            for proxy in success_proxies:
                readme_file.write(f" - {proxy}\n")

    print(f"验证完成：{len(success_proxies)} 个代理可用。")

if __name__ == "__main__":
    asyncio.run(main())
