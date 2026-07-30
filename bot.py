from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout,
    BasicAuth
)
from aiohttp_socks import ProxyConnector
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_utils import to_hex
from datetime import datetime, timedelta, timezone
from colorama import *
import asyncio, random, time, sys, re, os

class SimpleChain:
    def __init__(self) -> None:
        self.BASE_API = "https://task.simplechain.com"
        self.REF_CODE = "9v5l4qp3563" # U can change it with yours.

        self.USE_PROXY = False
        self.ROTATE_PROXY = False

        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.accounts = {}
        
        self.USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 OPR/117.0.0.0"
        ]

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().strftime('%x %X')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        print(
            f"""
        {Fore.GREEN + Style.BRIGHT}SimpleChain {Fore.BLUE + Style.BRIGHT}Auto BOT
            """
            f"""
        {Fore.GREEN + Style.BRIGHT}Rey? {Fore.YELLOW + Style.BRIGHT}<INI WATERMARK>
            """
        )

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    def load_accounts(self):
        env_accounts = os.getenv("ACCOUNTS")
        if env_accounts:
            accounts = [line.strip() for line in re.split(r'[,\n;]+', env_accounts) if line.strip()]
            if accounts:
                return accounts

        filename = "accounts.txt"
        try:
            with open(filename, 'r') as file:
                accounts = [line.strip() for line in file if line.strip()]
            return accounts
        except Exception as e:
            print(f"{Fore.RED + Style.BRIGHT}Failed To Load Accounts: {e}{Style.RESET_ALL}")
            return None

    def load_proxies(self):
        filename = "proxy.txt"
        try:
            if not os.path.exists(filename):
                self.log(f"{Fore.RED + Style.BRIGHT}File {filename} Not Found.{Style.RESET_ALL}")
                return
            with open(filename, 'r') as f:
                self.proxies = [line.strip() for line in f.read().splitlines() if line.strip()]
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No Proxies Found.{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Proxies Total  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed To Load Proxies: {e}{Style.RESET_ALL}")
            self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"
    
    def get_next_proxy_for_account(self, account):
        if account not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[account] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[account]

    def rotate_proxy_for_account(self, account):
        if not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[account] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy
    
    def build_proxy_config(self, proxy=None):
        if not proxy:
            return None, None, None

        if proxy.startswith("socks"):
            connector = ProxyConnector.from_url(proxy)
            return connector, None, None

        elif proxy.startswith("http"):
            match = re.match(r"http://(.*?):(.*?)@(.*)", proxy)
            if match:
                username, password, host_port = match.groups()
                clean_url = f"http://{host_port}"
                auth = BasicAuth(username, password)
                return None, clean_url, auth
            else:
                return None, proxy, None

        raise Exception("Unsupported Proxy Type.")
    
    def display_proxy(self, proxy_url=None):
        if not proxy_url: return "No Proxy"

        proxy_url = re.sub(r"^(http|https|socks4|socks5)://", "", proxy_url)

        if "@" in proxy_url:
            proxy_url = proxy_url.split("@", 1)[1]

        return proxy_url
    
    def get_next_run_time(self, anchor_minute=1):
        now = datetime.now(timezone.utc)
        today_target = now.replace(hour=0, minute=anchor_minute, second=0, microsecond=0)

        if today_target > now:
            return today_target
        else:
            return today_target + timedelta(days=1)
    
    def initialize_headers(self, address: str):
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Host": "task.simplechain.com",
            "Origin": "https://task.simplechain.com",
            "Pragma": "no-cache",
            "Referer": "https://task.simplechain.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": self.accounts[address]["user_agent"]
        }

        return headers.copy()
        
    def generate_address(self, private_key: str):
        try:
            account = Account.from_key(private_key)
            address = account.address
            return address
        except Exception as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Generate Address Failed {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None
        
    def generate_payload(self, private_key: str, address: str, message: str):
        try:
            encoded_message = encode_defunct(text=message)
            signed_message = Account.sign_message(encoded_message, private_key=private_key)
            signature = to_hex(signed_message.signature)

            payload = {
                "signature": signature,
                "message": message,
                "address": address,
                "inviteCode": self.REF_CODE
            }

            return payload
        except Exception as e:
            raise Exception(f"Generate Req Payload Failed: {str(e)}")

    def mask_account(self, account):
        try:
            mask_account = account[:6] + '*' * 6 + account[-6:]
            return mask_account
        except Exception as e:
            return None

    def print_question(self):
        print(f"{Fore.GREEN + Style.BRIGHT}Running without proxy...{Style.RESET_ALL}")
        self.USE_PROXY = False
    
    async def ensure_ok(self, response):
        if response.status >= 400:
            error_text = await response.text()
            raise Exception(f"HTTP {response.status}: {error_text}")
    
    async def check_connection(self, proxy_url=None):
        url = "https://api.ipify.org?format=json"

        connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
        try:
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=30)) as session:
                async with session.get(url=url, proxy=proxy, proxy_auth=proxy_auth) as response:
                    await self.ensure_ok(response)
                    return True
        except (Exception, ClientResponseError) as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Connection Not 200 OK {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
        
        return None
    
    async def get_nonce(self, address: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/api/v1/get/nonce"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                headers = self.initialize_headers(address)
                headers["Content-Type"] = "application/json"
                payload = {
                    "address": address
                }
                
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(
                        url=url, headers=headers, json=payload, proxy=proxy, proxy_auth=proxy_auth
                    ) as response:
                        await self.ensure_ok(response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Status  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed to Fetch Nonce {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def wallet_login(self, private_key: str, address: str, message: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/api/v1/login"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                headers = self.initialize_headers(address)
                headers["Content-Type"] = "application/json"
                payload = self.generate_payload(private_key, address, message)
                
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(
                        url=url, headers=headers, json=payload, proxy=proxy, proxy_auth=proxy_auth
                    ) as response:
                        await self.ensure_ok(response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Status  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Login Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def user_info(self, address: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/api/v1/user/get/info"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                headers = self.initialize_headers(address)
                headers["Authorization"] = f"Bearer {self.accounts[address]['token']}"
                
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(
                        url=url, headers=headers, proxy=proxy, proxy_auth=proxy_auth
                    ) as response:
                        await self.ensure_ok(response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Points  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed to Fetch Info {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def checkin_status(self, address: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/api/v1/campaign/checkin/status"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                headers = self.initialize_headers(address)
                headers["Authorization"] = f"Bearer {self.accounts[address]['token']}"
                
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(
                        url=url, headers=headers, proxy=proxy, proxy_auth=proxy_auth
                    ) as response:
                        await self.ensure_ok(response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Check-In:{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed to Fetch Status {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def complete_checkin(self, address: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/api/v1/campaign/checkin"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                headers = self.initialize_headers(address)
                headers["Authorization"] = f"Bearer {self.accounts[address]['token']}"
                headers["Content-Type"] = "application/json"
                
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(
                        url=url, headers=headers, json={}, proxy=proxy, proxy_auth=proxy_auth
                    ) as response:
                        await self.ensure_ok(response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Check-In:{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def task_lists(self, address: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/api/v1/task/list"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                headers = self.initialize_headers(address)
                headers["Authorization"] = f"Bearer {self.accounts[address]['token']}"
                
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(
                        url=url, headers=headers, proxy=proxy, proxy_auth=proxy_auth
                    ) as response:
                        await self.ensure_ok(response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Tasks   :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed to Fetch Task Lists {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def complete_task(self, address: str, task_id: str, title: str, proxy_url=None, retries=5):
        url = f"{self.BASE_API}/api/v1/task/complete"
        
        for attempt in range(retries):
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                headers = self.initialize_headers(address)
                headers["Authorization"] = f"Bearer {self.accounts[address]['token']}"
                headers["Content-Type"] = "application/json"

                payload = {
                    "taskId": task_id
                }
                
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(
                        url=url, headers=headers, json=payload, proxy=proxy, proxy_auth=proxy_auth
                    ) as response:
                        await self.ensure_ok(response)
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.BLUE+Style.BRIGHT} ● {Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT}{title}{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Not Completed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def process_check_connection(self, address: str, proxy_url=None):
        while True:
            if self.USE_PROXY:
                proxy_url = self.get_next_proxy_for_account(address)

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Proxy   :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {self.display_proxy(proxy_url)} {Style.RESET_ALL}"
            )

            is_valid = await self.check_connection(proxy_url)
            if is_valid: return True

            if self.ROTATE_PROXY:
                proxy_url = self.rotate_proxy_for_account(address)
                await asyncio.sleep(1)
                continue

            return False
    
    async def process_wallet_login(self, private_key: str, address: str, proxy_url=None):
        is_valid = await self.process_check_connection(address, proxy_url)
        if not is_valid: return False

        if self.USE_PROXY:
            proxy_url = self.get_next_proxy_for_account(address)

        if int(time.time()) > self.accounts[address]["expires"]:

            nonce = await self.get_nonce(address, proxy_url)
            if not nonce: return False

            if nonce.get("code") != 0:
                err_msg = nonce.get("message")
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Status  :{Style.RESET_ALL}"
                    f"{Fore.RED + Style.BRIGHT} {err_msg} {Style.RESET_ALL}"
                )
                return False

            message = nonce.get("data", {}).get("message")

            login = await self.wallet_login(private_key, address, message, proxy_url)
            if not login: return False

            if login.get("code") != 0:
                err_msg = login.get("message")
                self.log(
                    f"{Fore.CYAN + Style.BRIGHT}Status  :{Style.RESET_ALL}"
                    f"{Fore.RED + Style.BRIGHT} {err_msg} {Style.RESET_ALL}"
                )
                return False
            
            self.accounts[address]["token"] = login.get("data", {}).get("token")
            self.accounts[address]["expires"] = int(login.get("data", {}).get("expiresAt", 0))

            self.log(
                f"{Fore.CYAN + Style.BRIGHT}Status  :{Style.RESET_ALL}"
                f"{Fore.GREEN + Style.BRIGHT} Login Success {Style.RESET_ALL}"
            )

        return True

    async def process_accounts(self, private_key: str, address: str, proxy_url=None):
        logined = await self.process_wallet_login(private_key, address, proxy_url)
        if not logined: return False

        if self.USE_PROXY:
            proxy_url = self.get_next_proxy_for_account(address)

        user = await self.user_info(address, proxy_url)
        if user:
            
            if user.get("code") == 0:
                points = user.get("data", {}).get("availablePoints", 0)

                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Points  :{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {points} {Style.RESET_ALL}"
                )
            else:
                err_msg = user.get("message")
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Points  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} {err_msg} {Style.RESET_ALL}"
                )

        checkin = await self.checkin_status(address, proxy_url)
        if checkin:

            if checkin.get("code") == 0:
                has_checkin = checkin.get("data", {}).get("todayChecked", False)

                if not has_checkin:
                    complete = await self.complete_checkin(address, proxy_url)
                    if complete:

                        if complete.get("code") == 0:
                            reward = complete.get("data", {}).get("totalReward", False)

                            self.log(
                                f"{Fore.CYAN+Style.BRIGHT}Check-In:{Style.RESET_ALL}"
                                f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}"
                                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                                f"{Fore.CYAN+Style.BRIGHT} Reward: {Style.RESET_ALL}"
                                f"{Fore.WHITE+Style.BRIGHT}{reward} Points{Style.RESET_ALL}"
                            )
                        else:
                            err_msg = complete.get("message")
                            self.log(
                                f"{Fore.CYAN+Style.BRIGHT}Check-In:{Style.RESET_ALL}"
                                f"{Fore.RED+Style.BRIGHT} {err_msg} {Style.RESET_ALL}"
                            )
                else:
                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}Check-In:{Style.RESET_ALL}"
                        f"{Fore.YELLOW+Style.BRIGHT} Already Completed {Style.RESET_ALL}"
                    )
            else:
                err_msg = checkin.get("message")
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Check-In:{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} {err_msg} {Style.RESET_ALL}"
                )

        task_lists = await self.task_lists(address, proxy_url)
        if task_lists:

            if task_lists.get("code") == 0:
                tasks = task_lists.get("data", {}).get("tasks", [])
                
                self.log(f"{Fore.CYAN+Style.BRIGHT}Tasks   :{Style.RESET_ALL}")

                for task in tasks:
                    task_id = task.get("taskId")
                    title = task.get("taskName")
                    status = task.get("completionStatus")
                    reward = task.get("rewardPoints")

                    if "COMPLETED" in status:
                        self.log(
                            f"{Fore.BLUE+Style.BRIGHT} ● {Style.RESET_ALL}"
                            f"{Fore.WHITE+Style.BRIGHT}{title}{Style.RESET_ALL}"
                            f"{Fore.YELLOW+Style.BRIGHT} Already Completed {Style.RESET_ALL}"
                        )
                        continue

                    complete = await self.complete_task(address, task_id, title, proxy_url)
                    if not complete: continue

                    if complete.get("code") != 0:
                        err_msg = complete.get("message")
                        self.log(
                            f"{Fore.BLUE+Style.BRIGHT} ● {Style.RESET_ALL}"
                            f"{Fore.WHITE+Style.BRIGHT}{title}{Style.RESET_ALL}"
                            f"{Fore.RED+Style.BRIGHT} {err_msg} {Style.RESET_ALL}"
                        )
                        continue

                    self.log(
                        f"{Fore.BLUE+Style.BRIGHT} ● {Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT}{title}{Style.RESET_ALL}"
                        f"{Fore.GREEN+Style.BRIGHT} Completed {Style.RESET_ALL}"
                        f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                        f"{Fore.CYAN+Style.BRIGHT} Reward: {Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT}{reward} Points{Style.RESET_ALL}"
                    )

            else:
                err_msg = task_lists.get("message")
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Tasks   :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} {err_msg} {Style.RESET_ALL}"
                )

    async def main(self):
        try:
            accounts = self.load_accounts()
            if not accounts:
                print(f"{Fore.RED+Style.BRIGHT}No Accounts Loaded.{Style.RESET_ALL}") 
                return

            self.print_question()

            while True:
                self.clear_terminal()
                self.welcome()
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}Account's Total: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
                )

                if self.USE_PROXY: self.load_proxies()

                separator = "=" * 25
                for idx, private_key in enumerate(accounts, start=1):
                    self.log(
                        f"{Fore.CYAN + Style.BRIGHT}{separator}[{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} {idx} {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}-{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} {len(accounts)} {Style.RESET_ALL}"
                        f"{Fore.CYAN + Style.BRIGHT}]{separator}{Style.RESET_ALL}"
                    )

                    address = self.generate_address(private_key)
                    if not address: continue

                    if address not in self.accounts:
                        self.accounts[address] = {
                            "user_agent": random.choice(self.USER_AGENTS),
                            "expires": 0
                        }

                    self.log(
                        f"{Fore.CYAN+Style.BRIGHT}Address :{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {self.mask_account(address)} {Style.RESET_ALL}"
                    )
                        
                    await self.process_accounts(private_key, address)
                    await asyncio.sleep(random.uniform(2.0, 3.0))

                self.log(f"{Fore.CYAN + Style.BRIGHT}={Style.RESET_ALL}"*72)
                
                next_run = self.get_next_run_time(anchor_minute=1)

                while True:
                    now = datetime.now(timezone.utc)
                    remaining = (next_run - now).total_seconds()

                    if remaining <= 0:
                        break

                    formatted_time = self.format_seconds(remaining)

                    print(
                        f"{Fore.CYAN+Style.BRIGHT}[ Wait for{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {formatted_time} {Style.RESET_ALL}"
                        f"{Fore.CYAN+Style.BRIGHT}]{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE+Style.BRIGHT}All Accounts Have Been Processed...{Style.RESET_ALL}",
                        end="\r",
                        flush=True
                    )
                    await asyncio.sleep(1)

        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Error: {e}{Style.RESET_ALL}")
            raise e

if __name__ == "__main__":
    try:
        bot = SimpleChain()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().strftime('%x %X')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ EXIT ] SimpleChain - BOT{Style.RESET_ALL}                                       "                              
        )
        sys.exit(0)