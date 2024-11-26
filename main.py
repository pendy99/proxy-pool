# -*- coding: utf-8 -*-

import re
from time import sleep
import requests
from lxml import html

## 2024.11.26 : 已经修复了，从代理网站获取候选验证的代理...

class ProxyFetcher:
    """
    Proxy getter
    """

    @staticmethod
    def get_headers():
        """Generate headers to make requests look like a browser"""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Connection": "keep-alive"
        }

    @staticmethod
    def write_proxy_to_file(proxy):
        """Append the proxy to proxy.txt file"""
        with open("proxy.txt", "a+") as file:
            file.write(proxy + "\n")

    @staticmethod
    def free_proxy_03():
        """开心代理"""
        target_urls = [
            "http://www.kxdaili.com/dailiip.html",
            "http://www.kxdaili.com/dailiip/2/1.html"
        ]
        headers = ProxyFetcher.get_headers()
        for url in target_urls:
            response = requests.get(url, headers=headers, verify=False)
            tree = html.fromstring(response.content)
            for tr in tree.xpath("//table[@class='active']//tr")[1:]:
                ip = "".join(tr.xpath('./td[1]/text()')).strip()
                port = "".join(tr.xpath('./td[2]/text()')).strip()
                proxy = f"{ip}:{port}"
                ProxyFetcher.write_proxy_to_file(proxy)
                yield proxy

    @staticmethod
    def free_proxy_05(page_count=1):
        """
        快代理 https://www.kuaidaili.com
        """
        base_urls = [
            'https://www.kuaidaili.com/free/inha/{}/',
            'https://www.kuaidaili.com/free/intr/{}/'
        ]
        headers = ProxyFetcher.get_headers()

        # 构造所有需要爬取的 URL
        urls_to_scrape = []
        for page_index in range(1, page_count + 1):
            for base_url in base_urls:
                urls_to_scrape.append(base_url.format(page_index))

        # 爬取每个 URL 并提取代理信息
        for url in urls_to_scrape:
            response = requests.get(url, headers=headers, verify=False)
            tree = html.fromstring(response.content)
            rows = tree.xpath('.//table//tr')[1:]  # 跳过表头
            sleep(1)  # 必须 sleep，防止频率过高被封禁

            for row in rows:
                ip = row.xpath('./td[1]/text()')[0].strip()
                port = row.xpath('./td[2]/text()')[0].strip()
                proxy = f"{ip}:{port}"
                ProxyFetcher.write_proxy_to_file(proxy)
                yield proxy

    @staticmethod
    def free_proxy_07():
        """云代理"""
        urls = ['http://www.ip3366.net/free/?stype=1', "http://www.ip3366.net/free/?stype=2"]
        headers = ProxyFetcher.get_headers()
        for url in urls:
            response = requests.get(url, headers=headers, timeout=10, verify=False)
            proxies = re.findall(r'<td>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</td>[\s\S]*?<td>(\d+)</td>', response.text)
            for proxy in proxies:
                proxy_str = ":".join(proxy)
                ProxyFetcher.write_proxy_to_file(proxy_str)
                yield proxy_str

    @staticmethod
    def free_proxy_10():
        """ 89免费代理 """
        headers = ProxyFetcher.get_headers()
        response = requests.get("https://www.89ip.cn/index_1.html", headers=headers, verify=False, timeout=10)
        proxies = re.findall(
            r'<td.*?>[\s\S]*?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})[\s\S]*?</td>[\s\S]*?<td.*?>[\s\S]*?(\d+)[\s\S]*?</td>',
            response.text)
        for proxy in proxies:
            proxy_str = ':'.join(proxy)
            ProxyFetcher.write_proxy_to_file(proxy_str)
            yield proxy_str

    @staticmethod
    def free_proxy_11():
        """ 稻壳代理 https://www.docip.net/ """
        headers = ProxyFetcher.get_headers()
        response = requests.get("https://www.docip.net/data/free.json", headers=headers, verify=False, timeout=10)
        try:
            data = response.json().get('data', [])
            for each in data:
                proxy = each['ip']
                ProxyFetcher.write_proxy_to_file(proxy)
                yield proxy
        except Exception as e:
            print(e)

def main():
    proxy_fetcher = ProxyFetcher()
    for proxy_source in [proxy_fetcher.free_proxy_03, proxy_fetcher.free_proxy_05,
                         proxy_fetcher.free_proxy_07, proxy_fetcher.free_proxy_10, proxy_fetcher.free_proxy_11]:
        print(f"Fetching proxies from: {proxy_source.__name__}")
        for proxy in proxy_source():
            print(proxy)


if __name__ == '__main__':
    main()