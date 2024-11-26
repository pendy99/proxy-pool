# -*- coding: utf-8 -*-

import re
import aiohttp
import asyncio
import random

# 请求头信息列表，用于模拟浏览器请求
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
]

# 匹配代理IP的正则表达式
IP_REGEX = re.compile(r"(.*:.*@)?\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}")


class ProxyValidator:
    # 预验证和HTTP验证的列表
    pre_validators = []
    http_validators = []

    @classmethod
    def add_pre_validator(cls, func):
        """添加预验证函数"""
        cls.pre_validators.append(func)
        return func

    @classmethod
    def add_http_validator(cls, func):
        """添加HTTP验证函数"""
        cls.http_validators.append(func)
        return func


@ProxyValidator.add_pre_validator
def validate_format(proxy):
    """检查代理格式是否正确"""
    return True if IP_REGEX.fullmatch(proxy) else False


@ProxyValidator.add_http_validator
async def validate_http_proxy(session, proxy):
    """验证HTTP代理是否有效"""
    proxies = {
        "http": f"http://{proxy}",
        "https": f"https://{proxy}"
    }
    headers = {
        'User-Agent': random.choice(USER_AGENTS)
    }

    try:
        async with session.get("http://www.google.com", headers=headers, proxy=proxies['http'], timeout=5) as response:
            return response.status == 200
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return False


async def main():
    """主函数，串联各个验证步骤"""
    # 读取 proxy.md 文件中的代理列表
    try:
        with open('proxy.md', 'r') as file:
            proxies = [line.strip() for line in file.readlines() if line.strip()]
    except FileNotFoundError:
        print("错误: proxy.md 文件未找到")
        return

    async with aiohttp.ClientSession() as session:
        tasks = []
        for proxy in proxies:
            print(f"\n开始验证代理: {proxy}")

            # 进行预验证
            print("\u251c── 进行预验证...")
            pre_validation_passed = True
            for validator in ProxyValidator.pre_validators:
                if not validator(proxy):
                    print(f"\u251c── 预验证失败: {validator.__name__}")
                    pre_validation_passed = False
                    break

            if not pre_validation_passed:
                continue
            print("\u251c── 预验证通过")

            # 进行HTTP验证
            print("\u251c── 进行HTTP验证...")
            task = validate_http_proxy(session, proxy)
            tasks.append((proxy, task))

        # 执行所有的HTTP验证任务
        results = await asyncio.gather(*(task for _, task in tasks))

        for (proxy, task), result in zip(tasks, results):
            if result:
                print(f"\u2514── HTTP验证通过，代理可用！")
                # 将验证通过的代理追加到 ok.md 文件末尾
                try:
                    with open('ok.md', 'a+') as ok_file:
                        ok_file.write(proxy + '\n')
                    print("\u2514── 已将代理追加到 ok.md 文件末尾")
                except IOError:
                    print("\u2514── 错误: 无法写入 ok.md 文件")
            else:
                print(f"\u2514── HTTP验证失败: {proxy}")


if __name__ == "__main__":
    asyncio.run(main())