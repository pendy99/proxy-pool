# -*- coding: utf-8 -*-
import asyncio
import aiohttp
from aiohttp import ClientSession
from lxml import html
import re
from pathlib import Path

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

    async def gather_all(self):
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

if __name__ == '__main__':
    fetcher = AsyncProxyFetcher()
    asyncio.run(fetcher.gather_all())
