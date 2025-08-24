# -*- coding: utf-8 -*-
import asyncio
import aiohttp
from aiohttp import ClientSession
from lxml import html
import re
from pathlib import Path
import random
import os
from datetime import datetime

class AsyncProxyFetcher:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Connection": "keep-alive"
    }

    def __init__(self):
        self.proxy_file = Path("proxy.txt")
        self.proxy_file.write_text("")  # Clear file at start

    async def fetch(self, url: str, session: ClientSession) -> str:
        try:
            async with session.get(url, timeout=10, ssl=False) as response:
                content = await response.read()
                return content.decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            return ""

    async def parse_kxdaili(self, session: ClientSession, url: str):
        html_text = await self.fetch(url, session)
        tree = html.fromstring(html_text)
        proxies = []
        for tr in tree.xpath("//table[@class='active']//tr")[1:]:
            ip = "".join(tr.xpath('./td[1]/text()')).strip()
            port = "".join(tr.xpath('./td[2]/text()')).strip()
            if ip and port:
                proxies.append(f"{ip}:{port}")
        return proxies

    async def parse_kuaidaili(self, session: ClientSession, url: str):
        html_text = await self.fetch(url, session)
        tree = html.fromstring(html_text)
        proxies = []
        for tr in tree.xpath(".//table//tr")[1:]:
            ip = tr.xpath('./td[1]/text()')[0].strip()
            port = tr.xpath('./td[2]/text()')[0].strip()
            proxies.append(f"{ip}:{port}")
        return proxies

    async def parse_ip3366(self, session: ClientSession, url: str):
        html_text = await self.fetch(url, session)
        proxies = re.findall(r'<td>(\d{1,3}(?:\.\d{1,3}){3})</td>[\s\S]*?<td>(\d+)</td>', html_text)
        return [f"{ip}:{port}" for ip, port in proxies]

    async def parse_89ip(self, session: ClientSession, url: str):
        html_text = await self.fetch(url, session)
        proxies = re.findall(r'<td.*?>(\d{1,3}(?:\.\d{1,3}){3})</td>[\s\S]*?<td.*?>(\d+)</td>', html_text)
        return [f"{ip}:{port}" for ip, port in proxies]

    async def parse_docip(self, session: ClientSession, url: str):
        try:
            async with session.get(url, timeout=10, ssl=False) as resp:
                json_data = await resp.json()
                return [item['ip'] for item in json_data.get('data', [])]
        except Exception as e:
            print(f"Failed to fetch JSON from {url}: {e}")
            return []

    async def gather_all_and_verify(self):
        urls = {
            self.parse_kxdaili: [
                f"http://www.kxdaili.com/dailiip/{i}/{j}.html"
                for i in [1, 2] for j in range(1, 11)
            ],
            self.parse_kuaidaili: [
                f"https://www.kuaidaili.com/free/inha/{i}/" for i in range(1, 6)
            ] + [
                f"https://www.kuaidaili.com/free/intr/{i}/" for i in range(1, 6)
            ],
            self.parse_ip3366: [
                f"http://www.ip3366.net/free/?stype={stype}&page={i}"
                for stype in [1, 2] for i in range(1, 6)
            ],
            self.parse_89ip: ["https://www.89ip.cn/index_1.html"],
            self.parse_docip: ["https://www.docip.net/data/free.json"]
        }

        async with aiohttp.ClientSession(headers=self.headers) as session:
            tasks = []
            for parser, url_list in urls.items():
                for url in url_list:
                    tasks.append(parser(session, url))

            results = await asyncio.gather(*tasks)
            all_proxies = [proxy for sublist in results for proxy in sublist if proxy]

            with self.proxy_file.open("a") as f:
                for proxy in all_proxies:
                    f.write(proxy + "\n")

            print(f"Fetched {len(all_proxies)} proxies.")

        ## verify_main
        await verify_main()

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



USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
]

IP_REGEX = re.compile(r"(.*:.*@)?\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}")

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
            # 随便找个外网，进行验证，看是否正常返回200.
            async with session.get("http://www.ip3366.net/", headers=headers, proxy=proxy_url, timeout=3) as response:
                return response.status == 200
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return False

async def verify_main():
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

if __name__ == '__main__':
    fetcher = AsyncProxyFetcher()
    asyncio.run(fetcher.gather_all_and_verify())
