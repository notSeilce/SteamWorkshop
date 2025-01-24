import os
import sys
import shutil
import subprocess
import re
import requests
import asyncio
import aiohttp
from pathlib import Path
from typing import Optional, List, Set
from bs4 import BeautifulSoup
import json
from concurrent.futures import ThreadPoolExecutor
from selectolax.parser import HTMLParser
import time

class SteamWorkshopDownloader:
    def __init__(self):
        if getattr(sys, 'frozen', False):
            self.script_dir = Path(os.path.dirname(sys.executable))
        else:
            self.script_dir = Path(__file__).parent.absolute()
        
        self.steamcmd_dir = self.script_dir / "main" / "SteamCMD"
        self.steamcmd_path = self.steamcmd_dir / "steamcmd.exe"
        self.steamclient_path = self.steamcmd_dir / "steamclient.dll"
        
        self.base_mods_path = self.script_dir / "games"
        self.game_name: Optional[str] = None
        self.game_id: Optional[str] = None
        self.game_folder: Optional[str] = None
        self.mods_path: Optional[Path] = None
        self.max_concurrent_downloads: Optional[int] = None
        
        self.check_and_install_steamclient()
        
        self.load_config()
    
    def check_and_install_steamclient(self):
        if not self.steamclient_path.exists():
            print("Файл steamclient.dll не найден.\nЗапущена загрузка...")
            
            self.steamcmd_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                subprocess.run(
                    [str(self.steamcmd_path), '+quit'], 
                    check=True, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE
                )
                
                if not self.steamclient_path.exists():
                    print("Не удалось установить steamclient.dll. Проверьте настройки SteamCMD.")
                    input("Нажмите Enter для выхода...")
                    sys.exit(1)
            except subprocess.CalledProcessError as e:
                print(f"Ошибка при обновлении SteamCMD: {e}")
                input("Нажмите Enter для выхода...")
                sys.exit(1)
            except Exception as e:
                print(f"Непредвиденная ошибка: {e}")
                input("Нажмите Enter для выхода...")
                sys.exit(1)
 
    def load_config(self) -> None:
        config_path = self.script_dir / "main" / "config.json"
        if not config_path.exists(): 
            return
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            self.game_name = config.get('GAME_NAME', '').strip('"')
            self.game_id = config.get('GAME_ID')
            self.game_folder = config.get('GAME_FOLDER')
            
            max_downloads = config.get('MAX_CONCURRENT_DOWNLOADS')
            self.max_concurrent_downloads = int(max_downloads) if max_downloads is not None else None
            
            if self.game_folder:
                self.mods_path = self.base_mods_path / self.game_folder / "mods"
        
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error loading config: {e}")

    def save_config(self) -> None:
        config = {
            'GAME_NAME': f'"{self.game_name}"', 
            'GAME_ID': self.game_id, 
            'GAME_FOLDER': self.game_folder, 
            'MAX_CONCURRENT_DOWNLOADS': self.max_concurrent_downloads
        }
        
        with open(self.script_dir / "main" / "config.json", 'w') as configfile:
            json.dump(config, configfile, indent=4)

    def clean_folder_name(self, name: str) -> str:
        return "".join(c for c in name if c.isalnum())

    def setup_game(self) -> None:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n" + "═" * 47 + "\n Настройка игры\n" + "═" * 47 + "\n")
        
        while True:
            print("Укажите ссылку на игру в Steam\nНапример: https://store.steampowered.com/app/108600/Project_Zomboid/\n")
            game_url = input("Ссылка: ").strip()
            
            match_id = re.search(r'/app/(\d+)/', game_url)
            match_name = re.search(r'/app/\d+/([^/]+)/?$', game_url)
            
            if match_id and match_name:
                self.game_id = match_id.group(1)
                self.game_name = match_name.group(1)
                break
            else:
                os.system('cls' if os.name == 'nt' else 'clear')
                print("\nНеверная ссылка. Попробуйте ещё раз.\n")
        
        self.game_folder = self.clean_folder_name(self.game_name)
        self.mods_path = self.base_mods_path / self.game_folder / "mods"
        os.makedirs(self.mods_path, exist_ok=True)
        self.save_config()
        
    async def fetch_mod_title(self, mod_id: str) -> str:
        collection_url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={mod_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(collection_url) as response:
                if response.status != 200:
                    return mod_id
                
                html = await response.text()
                parser = HTMLParser(html)
                
                title_element = parser.css_first('div.workshopItemTitle')
                if title_element:
                    return title_element.text(strip=True)
                
                return mod_id

    async def install_mod(self, mod_id: str, semaphore: asyncio.Semaphore) -> None:
        mod_title = await self.fetch_mod_title(mod_id)
        
        async with semaphore:
            print(f"Установка мода [{mod_title}]...")
            temp_download_path = self.script_dir / "temp" / mod_id
            os.makedirs(temp_download_path, exist_ok=True)

            cmd = [
                str(self.steamcmd_path), "+force_install_dir", str(temp_download_path),
                "+login", "anonymous", "+workshop_download_item", self.game_id, mod_id, "+quit"
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                print(f"Ошибка при загрузке мода {mod_id}: {stderr.decode()}")
            else:
                print(f"Загрузка мода {mod_title} завершена.")

            mod_source = temp_download_path / "steamapps" / "workshop" / "content" / self.game_id / mod_id
            if mod_source.exists():
                if (mod_source / "mods").exists():
                    await asyncio.to_thread(shutil.copytree, mod_source / "mods", self.mods_path, dirs_exist_ok=True)
                else:
                    await asyncio.to_thread(shutil.copytree, mod_source, self.mods_path / mod_title, dirs_exist_ok=True)

                print(f"Мод {mod_title} установлен.")
            await asyncio.to_thread(shutil.rmtree, temp_download_path, ignore_errors=True)

    async def install_mods(self, mod_ids: List[str]) -> None:
        semaphore = asyncio.Semaphore(self.max_concurrent_downloads)
        tasks = [self.install_mod(mod_id, semaphore) for mod_id in mod_ids]
        await asyncio.gather(*tasks)

    async def fetch_collection_mods(self, collection_url: str) -> List[str]:
        async with aiohttp.ClientSession() as session:
            async with session.get(collection_url) as response:
                if response.status != 200:
                    return []
                html = await response.text()
                parser = HTMLParser(html)
                
                mod_ids = []
                for link in parser.css('a'):
                    if not link.attributes.get('href'):
                        continue
                    
                    href = link.attributes['href']
                    
                    if '/sharedfiles/filedetails/?id=' in href:
                        match = re.search(r'[?&]id=(\d+)', href)
                        if match:
                            mod_ids.append(match.group(1))
                
                return list(set(mod_ids))

    def install_from_urls(self) -> None:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("Установка модов по ссылкам\n")
        print("Вставьте ссылки на моды Steam Workshop\nПример: https://steamcommunity.com/sharedfiles/filedetails/?id=2392709985"
            "\n\nДля завершения нажмите Enter дважды ")
        print("(Введите 'x' в любой момент для выхода в главное меню)")
        
        urls = []
        while True:
            url = input().strip()
            
            if url.lower() == 'x':
                return
            
            if not url:
                if urls:
                    break
                else:
                    continue
            
            if not re.search(r'steamcommunity\.com/sharedfiles/filedetails/\?id=\d+', url):
                os.system('cls' if os.name == 'nt' else 'clear')
                print("Неверная ссылка. Попробуйте ещё раз.\n")
                print("Вставьте ссылки на моды Steam Workshop\nПример: https://steamcommunity.com/sharedfiles/filedetails/?id=2392709985"
            "\n\nДля завершения нажмите Enter дважды ")
                print("(Введите 'x' в любой момент для выхода в главное меню)")
                continue
            
            urls.append(url)
        
        mod_ids = []
        for url in urls:
            if match := re.search(r'[?&]id=(\d+)', url):
                mod_ids.append(match.group(1))
        
        if mod_ids:
            asyncio.run(self.install_mods(mod_ids))
        
        input("\nЗагружено. Нажмите Enter для продолжения...")
        
    def install_from_collection(self) -> None:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("Установка модов из коллекции\n")
        
        while True:
            print("Введите ссылку на коллекцию Steam Workshop\nНапример: https://steamcommunity.com/sharedfiles/filedetails/?id=2392709985\n")
            print("(Введите 'x' для выхода в главное меню)")
            collection_url = input()
            
            if collection_url.lower() == 'x':
                return
            
            match = re.search(r'steamcommunity\.com/sharedfiles/filedetails/\?id=(\d+)', collection_url)
            if not match:
                os.system('cls' if os.name == 'nt' else 'clear')
                print("\nНеверная ссылка. Попробуйте ещё раз.\n")
                continue
            
            collection_id = match.group(1)
            
            try:
                mod_ids = asyncio.run(self.fetch_collection_mods(collection_url))
                
                if not mod_ids:
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print("\nВ коллекции не найдено модов. Попробуйте другую ссылку.")
                    continue
                
                print(f"\nНайдено модов: {len(mod_ids)}")
                if input("\nНачать установку? (y/n): ").lower() != 'y':
                    continue
                
                asyncio.run(self.install_mods(mod_ids))
                input("\nЗагружено. Нажмите Enter для продолжения...")
                break
            
            except Exception as e:
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f"\nПроизошла ошибка при получении модов: {e}")
                if input("\nПопробовать снова? (y/n): ").lower() != 'y':
                    break

    def main_menu(self) -> None:
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("Установщик для мастерской стим\n")
            if self.game_name:
                print(f"Текущая игра: {self.game_name} [ID: {self.game_id}]\n" + "─" * 47)
                print(" 1. Установить моды по ссылкам\n 2. Установить моды из коллекции\n 3. Сменить игру\n 4. Выход")
            else:
                print("Игра не выбрана!\n 1. Выбрать игру\n 2. Выход")
            print("\n" + "─" * 47)
            choice = input("\nВыберите действие: ").strip()
            if self.game_name:
                if choice == "1": self.install_from_urls()
                elif choice == "2": self.install_from_collection()
                elif choice == "3": self.setup_game()
                elif choice == "4": sys.exit(0)
            else:
                if choice == "1": self.setup_game()
                elif choice == "2": sys.exit(0)

if __name__ == "__main__":
    downloader = SteamWorkshopDownloader()
    downloader.main_menu()