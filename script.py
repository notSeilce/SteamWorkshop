import os
import sys
import shutil
import subprocess
import re
import asyncio
import aiohttp
from pathlib import Path
import json
import zipfile
import requests
from selectolax.parser import HTMLParser
import logging

logging.basicConfig(level=logging.DEBUG,
format='%(asctime)s - %(levelname)s - %(message)s',
filename='workshop_downloader.log',
filemode='w')

TEXTS = {
"ru": {
"main_menu_title": "Установщик для мастерской Steam",
"main_menu_current_game": "Текущая игра: {game_name} [ID: {game_id}]",
"main_menu_no_game_selected": "Игра не выбрана!",
"main_menu_items_with_game": ["1. Установить моды по ссылкам", "2. Установить моды из коллекции", "3. Сменить игру", "4. Выход"],
"main_menu_items_no_game": ["1. Выбрать игру", "2. Выход"],
"main_menu_prompt": "Выберите действие: ",
"setup_game_title": "Настройка игры",
"setup_game_instruction_link": "Укажите ссылку на игру в Steam\nНапример: https://store.steampowered.com/app/108600/Project_Zomboid/",
"setup_game_link_prompt": "Ссылка: ",
"setup_game_invalid_link": "\nНеверная ссылка. Попробуйте ещё раз.\n",
"setup_game_game_set": "Игра установлена.",
"install_mods_urls_title": "Установка модов по ссылкам",
"install_mods_urls_instructions": "Вставьте ссылки на моды Steam Workshop\nПример: https://steamcommunity.com/sharedfiles/filedetails/?id=2392709985\n\nДля завершения нажмите Enter дважды ",
"install_mods_urls_exit_option": "(Введите 'x' в любой момент для выхода в главное меню)",
"install_mods_urls_invalid_url": "\nНеверная ссылка. Попробуйте ещё раз.\n",
"install_mods_urls_downloaded_message": "\nЗагружено. Нажмите Enter для продолжения...",
"install_mods_collection_title": "Установка модов из коллекции",
"install_mods_collection_instruction_link": "Введите ссылку на коллекцию Steam Workshop\nНапример: https://steamcommunity.com/sharedfiles/filedetails/?id=2392709985\n",
"install_mods_collection_exit_option": "(Введите 'x' для выхода в главное меню)",
"install_mods_collection_invalid_link": "\nНеверная ссылка. Попробуйте ещё раз.\n",
"install_mods_collection_no_mods_in_collection": "\nВ коллекции не найдено модов. Попробуйте другую ссылку.",
"install_mods_collection_mods_found": "\nНайдено модов: {count}",
"install_mods_collection_confirm_install": "\nНачать установку? (y/n): ",
"install_mods_collection_downloaded_message": "\nЗагружено. Нажмите Enter для продолжения...",
"install_mods_collection_error_fetching_mods": "\nПроизошла ошибка при получении модов: {error}",
"install_mods_collection_try_again": "\nПопробовать снова? (y/n): ",
"steamclient_not_found": "Файл steamclient.dll не найден.\nЗапущена загрузка SteamCMD...",
"steamclient_install_failed": "Не удалось установить steamclient.dll. Проверьте настройки SteamCMD.",
"steamcmd_update_error": "Ошибка при обновлении SteamCMD: {error}",
"steamcmd_download_error": "Ошибка при загрузке SteamCMD: {error}",
"steamcmd_extract_error": "Ошибка при извлечении SteamCMD: {error}",
"steamcmd_not_found_error": "SteamCMD не найден. Загрузка и установка...",
"unexpected_error": "Непредвиденная ошибка: {error}",
"steamclient_exit_prompt": "Нажмите Enter для выхода...",
"install_mod_process_installing_mod": "Установка мода [{mod_title}]...",
"install_mod_process_download_completed": "Загрузка мода {mod_title} завершена.",
"install_mod_process_mod_installed": "Мод {mod_title} установлен.",
"install_mod_process_download_error": "Ошибка при загрузке мода {mod_id}: {error}",
"general_separator": "─" * 47,
"general_cls": 'cls' if os.name == 'nt' else 'clear',
"steamcmd_install_success": "SteamCMD успешно установлен.",
"steamcmd_downloading_from": "Загрузка SteamCMD с: {STEAMCMD_DOWNLOAD_URL}",
"steamcmd_extracting_from": "Извлечение SteamCMD из: {zip_path}",
"retrying_download_mod": "Повторная попытка загрузки мода {mod_title} (попытка {retry_count}/{MAX_RETRIES})...",
"max_retries_exceeded_mod": "Превышено количество попыток загрузки мода {mod_title}.",
"error_mod_folder_not_found": "Ошибка: папка мода {mod_id} не найдена после загрузки SteamCMD в {mod_src}",
"copying_mod_from_to": "Копирование мода из {mod_src} в {mod_dest}",
"error_copying_mod": "Ошибка при копировании мода {mod_title}: {error}",
"steamcmd_stdout_steamclient_install": "SteamCMD stdout (steamclient install):\n{process_stdout}",
"steamcmd_stderr_steamclient_install": "SteamCMD stderr (steamclient install):\n{process_stderr}",
"steamcmd_stdout_mod_download": "SteamCMD stdout для мода {mod_id}:\n{stdout_str}",
"steamcmd_stderr_mod_download": "SteamCMD stderr для мода {mod_id}:\n{stderr_str}",
"retrying_download_mod_attempt": "Повторная попытка загрузки мода {mod_title} (попытка {retry_count} из {MAX_RETRIES})...",
"install_mod_process_mod_already_exists": "Мод [{mod_title}] уже установлен.",
"install_mod_process_renaming_mod_to_id": "Переименование мода [{mod_title}] в [{mod_id}] из-за ошибки в названии папки.",
"install_mod_process_mod_installed_as_id": "Мод {mod_id} установлен (название папки изменено).",
},
"en": {
"main_menu_title": "Steam Workshop Downloader",
"main_menu_current_game": "Current Game: {game_name} [ID: {game_id}]",
"main_menu_no_game_selected": "No game selected!",
"main_menu_items_with_game": ["1. Download mods from URLs", "2. Download mods from collection", "3. Change Game", "4. Exit"],
"main_menu_items_no_game": ["1. Select Game", "2. Exit"],
"main_menu_prompt": "Choose an action: ",
"setup_game_title": "Game Setup",
"setup_game_instruction_link": "Enter the Steam game link\nExample: https://store.steampowered.com/app/108600/Project_Zomboid/",
"setup_game_link_prompt": "Link: ",
"setup_game_invalid_link": "\nInvalid link. Please try again.\n",
"setup_game_game_set": "Game set.",
"install_mods_urls_title": "Download Mods by URLs",
"install_mods_urls_instructions": "Paste Steam Workshop mod links\nExample: https://steamcommunity.com/sharedfiles/filedetails/?id=2392709985\n\nPress Enter twice to finish ",
"install_mods_urls_exit_option": "(Enter 'x' at any time to return to the main menu)",
"install_mods_urls_invalid_url": "\nInvalid link. Please try again.\n",
"install_mods_urls_downloaded_message": "\nDownloaded. Press Enter to continue...",
"install_mods_collection_title": "Download Mods from Collection",
"install_mods_collection_instruction_link": "Enter the Steam Workshop Collection link\nExample: https://steamcommunity.com/sharedfiles/filedetails/?id=2392709985\n",
"install_mods_collection_exit_option": "(Enter 'x' to return to the main menu)",
"install_mods_collection_invalid_link": "\nInvalid link. Please try again.\n",
"install_mods_collection_no_mods_in_collection": "\nNo mods found in the collection. Please try another link.",
"install_mods_collection_mods_found": "\nMods found: {count}",
"install_mods_collection_confirm_install": "\nStart downloading? (y/n): ",
"install_mods_collection_downloaded_message": "\nDownloaded. Press Enter to continue...",
"install_mods_collection_error_fetching_mods": "\nAn error occurred while fetching mods: {error}",
"install_mods_collection_try_again": "\nTry again? (y/n): ",
"steamclient_not_found": "steamclient.dll file not found.\nDownloading SteamCMD...",
"steamclient_install_failed": "Failed to install steamclient.dll. Check SteamCMD settings.",
"steamcmd_update_error": "Error updating SteamCMD: {error}",
"steamcmd_download_error": "Error downloading SteamCMD: {error}",
"steamcmd_extract_error": "Error extracting SteamCMD: {error}",
"steamcmd_not_found_error": "SteamCMD not found. Downloading and installing...",
"unexpected_error": "Unexpected error: {error}",
"steamclient_exit_prompt": "Press Enter to exit...",
"install_mod_process_installing_mod": "Downloading mod [{mod_title}]...",
"install_mod_process_download_completed": "Mod {mod_title} download completed.",
"install_mod_process_mod_installed": "Mod {mod_title} installed.",
"install_mod_process_download_error": "Error downloading mod {mod_id}: {error}",
"general_separator": "─" * 47,
"general_cls": 'cls' if os.name == 'nt' else 'clear',
"steamcmd_install_success": "SteamCMD installed successfully.",
"steamcmd_downloading_from": "Downloading SteamCMD from: {STEAMCMD_DOWNLOAD_URL}",
"steamcmd_extracting_from": "Extracting SteamCMD from: {zip_path}",
"retrying_download_mod": "Retrying download for mod {mod_title} (attempt {retry_count}/{MAX_RETRIES})...",
"max_retries_exceeded_mod": "Max retries exceeded for mod {mod_title}.",
"error_mod_folder_not_found": "Error: Mod folder {mod_id} not found after SteamCMD download in {mod_src}",
"copying_mod_from_to": "Copying mod from {mod_src} to {mod_dest}",
"error_copying_mod": "Error copying mod {mod_title}: {error}",
"steamcmd_stdout_steamclient_install": "SteamCMD stdout (steamclient install):\n{process_stdout}",
"steamcmd_stderr_steamclient_install": "SteamCMD stderr (steamclient install):\n{process_stderr}",
"steamcmd_stdout_mod_download": "SteamCMD stdout for mod {mod_id}:\n{stdout_str}",
"steamcmd_stderr_mod_download": "SteamCMD stderr for mod {mod_id}:\n{stderr_str}",
"retrying_download_mod_attempt": "Retrying download for mod {mod_title} (attempt {retry_count} of {MAX_RETRIES})...",
"install_mod_process_mod_already_exists": "Mod [{mod_title}] is already installed.",
"install_mod_process_renaming_mod_to_id": "Renaming mod [{mod_title}] to [{mod_id}] due to folder name error.",
"install_mod_process_mod_installed_as_id": "Mod {mod_id} installed (folder name changed).",
}
}

DEFAULT_LANG = "en"
DEFAULT_MAX_CONCURRENT_DOWNLOADS = 5
CURRENT_LANG = DEFAULT_LANG
TEXT = TEXTS[CURRENT_LANG]
STEAMCMD_DOWNLOAD_URL = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip"
MAX_RETRIES = 3

class SteamWorkshopDownloader:
    def __init__(self):
        self.script_dir = Path(os.path.dirname(sys.executable)) if getattr(sys, 'frozen', False) else Path(__file__).parent.absolute()
        self.steamcmd_dir = self.script_dir / "main" / "SteamCMD"
        self.steamcmd_path = self.steamcmd_dir / "steamcmd.exe"
        self.steamclient_path = self.steamcmd_dir / "steamclient.dll"
        self.base_mods_path = self.script_dir / "games"
        self.game_name = None
        self.game_id = None
        self.game_folder = None
        self.mods_path = None
        self.max_concurrent_downloads = None
        self.config_path = self.script_dir / "main" / "config.json"
        self.installed_mods_path = self.script_dir / "main" / "installed_mods.json"
        self.installed_mods = self.load_installed_mods()

        self.check_and_install_steamcmd()
        self.check_and_install_steamclient()
        self.load_config()
        global TEXT
        TEXT = TEXTS[CURRENT_LANG]

    def check_and_install_steamcmd(self):
        if not self.steamcmd_path.exists():
            print(TEXT["steamcmd_not_found_error"])
            logging.info(TEXT["steamcmd_not_found_error"])
            self.steamcmd_dir.mkdir(parents=True, exist_ok=True)
            try:
                self._download_steamcmd()
                self._extract_steamcmd()
                print(TEXT["steamcmd_install_success"])
                logging.info(TEXT["steamcmd_install_success"])
            except Exception as e:
                error_message = TEXT["steamcmd_download_error"].format(error=e) if isinstance(e, requests.exceptions.RequestException) else TEXT["steamcmd_extract_error"].format(error=e)
                logging.error(f"SteamCMD installation error: {error_message}")
                self._exit_with_error(error_message)

    def _download_steamcmd(self):
        print(TEXT["steamcmd_downloading_from"].format(STEAMCMD_DOWNLOAD_URL=STEAMCMD_DOWNLOAD_URL))
        logging.info(TEXT["steamcmd_downloading_from"].format(STEAMCMD_DOWNLOAD_URL=STEAMCMD_DOWNLOAD_URL))
        response = requests.get(STEAMCMD_DOWNLOAD_URL, stream=True)
        response.raise_for_status()
        zip_path = self.steamcmd_dir / "steamcmd.zip"
        with open(zip_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        return zip_path

    def _extract_steamcmd(self, zip_path=None):
        if zip_path is None:
            zip_path = self.steamcmd_dir / "steamcmd.zip"
        print(TEXT["steamcmd_extracting_from"].format(zip_path=zip_path))
        logging.info(TEXT["steamcmd_extracting_from"].format(zip_path=zip_path))
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(self.steamcmd_dir)
        os.remove(zip_path)

    def check_and_install_steamclient(self):
        if not self.steamclient_path.exists():
            print(TEXT["steamclient_not_found"])
            logging.info(TEXT["steamclient_not_found"])
            try:
                process = subprocess.run([str(self.steamcmd_path), '+quit'], check=True, capture_output=True)
                logging.debug(TEXT["steamcmd_stdout_steamclient_install"].format(process_stdout=process.stdout.decode()))
                logging.debug(TEXT["steamcmd_stderr_steamclient_install"].format(process_stderr=process.stderr.decode()))
                if not self.steamclient_path.exists():
                    error_message = TEXT["steamclient_install_failed"]
                    logging.error(f"steamclient.dll install failed: {error_message}")
                    self._exit_with_error(error_message)
            except subprocess.CalledProcessError as e:
                error_message = TEXT["steamcmd_update_error"].format(error=e)
                logging.error(f"SteamCMD update error: {error_message}\nStdout: {e.stdout.decode()}\nStderr: {e.stderr.decode()}")
                self._exit_with_error(error_message)
            except Exception as e:
                error_message = TEXT["unexpected_error"].format(error=e)
                logging.exception(f"Unexpected error during steamclient install: {error_message}")
                self._exit_with_error(error_message)

    def _exit_with_error(self, message):
        print(message)
        input(TEXT["steamclient_exit_prompt"])
        sys.exit(1)

    def load_config(self):
        if not self.config_path.exists():
            self.max_concurrent_downloads = DEFAULT_MAX_CONCURRENT_DOWNLOADS
            self.save_config()
            return
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            self.game_name = config.get('GAME_NAME', '').strip('"')
            self.game_id = config.get('GAME_ID')
            self.game_folder = config.get('GAME_FOLDER')
            self.max_concurrent_downloads = config.get('MAX_CONCURRENT_DOWNLOADS', DEFAULT_MAX_CONCURRENT_DOWNLOADS)
            loaded_lang = config.get('LANGUAGE')
            if loaded_lang in TEXTS:
                global CURRENT_LANG, TEXT
                CURRENT_LANG = loaded_lang
                TEXT = TEXTS[CURRENT_LANG]
            if self.game_folder:
                self.mods_path = self.base_mods_path / self.game_folder / "mods"
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error loading config: {e}")
            logging.error(f"Error loading config file: {e}")
            self.max_concurrent_downloads = DEFAULT_MAX_CONCURRENT_DOWNLOADS
            CURRENT_LANG = DEFAULT_LANG
            TEXT = TEXTS[CURRENT_LANG]

    def save_config(self):
        config = {
            'GAME_NAME': f'"{self.game_name}"',
            'GAME_ID': self.game_id,
            'GAME_FOLDER': self.game_folder,
            'MAX_CONCURRENT_DOWNLOADS': self.max_concurrent_downloads,
            'LANGUAGE': CURRENT_LANG
        }
        config_dir = self.script_dir / "main"
        config_dir.mkdir(parents=True, exist_ok=True)
        with open(config_dir / "config.json", 'w') as configfile:
            json.dump(config, configfile, indent=4)

    def clean_folder_name(self, name):
        invalid_chars = r'[\/:*?"<>|]'
        cleaned_name = re.sub(invalid_chars, '', name)
        cleaned_name = cleaned_name.strip()
        cleaned_name = cleaned_name.replace(" ", "")
        return cleaned_name[:30]

    def setup_game(self):
        os.system(TEXT["general_cls"])
        print(f"\n{TEXT['general_separator']}\n {TEXT['setup_game_title']}\n{TEXT['general_separator']}\n{TEXT['setup_game_instruction_link']}\n")
        while True:
            game_url = input(TEXT["setup_game_link_prompt"]).strip()
            if match_id := re.search(r'/app/(\d+)/', game_url):
                if match_name := re.search(r'/app/\d+/([^/]+)/?$', game_url):
                    self.game_id, self.game_name = match_id.group(1), match_name.group(1)
                    break
            os.system(TEXT["general_cls"])
            print(f"\n{TEXT['setup_game_invalid_link']}\n{TEXT['setup_game_instruction_link']}\n")
        self.game_folder = self.clean_folder_name(self.game_name)
        self.mods_path = self.base_mods_path / self.game_folder / "mods"
        os.makedirs(self.mods_path, exist_ok=True)
        self.save_config()

    def load_installed_mods(self):
        if self.installed_mods_path.exists():
            try:
                with open(self.installed_mods_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, ValueError):
                logging.error("Error loading installed_mods.json, resetting list.")
                return []
        return []

    def save_installed_mods(self):
        installed_mods_dir = self.script_dir / "main"
        installed_mods_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.installed_mods_path, 'w') as f:
                json.dump(self.installed_mods, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Error saving installed_mods.json: {e}")

    def check_mod_exists(self, mod_title, mod_id):
        cleaned_mod_title = self.clean_folder_name(mod_title)
        mod_path_cleaned = self.mods_path / cleaned_mod_title
        mod_path_id = self.mods_path / mod_id
        exists_cleaned = mod_path_cleaned.exists() and mod_path_cleaned.is_dir()
        exists_id = mod_path_id.exists() and mod_path_id.is_dir()
        mod_exists = exists_cleaned or exists_id

        logging.debug(f"check_mod_exists: mod_title='{mod_title}', mod_id='{mod_id}'")
        logging.debug(f"check_mod_exists: Checking cleaned path: {mod_path_cleaned}, exists={exists_cleaned}")
        logging.debug(f"check_mod_exists: Checking ID path: {mod_path_id}, exists={exists_id}")
        logging.debug(f"check_mod_exists: Mod exists result: {mod_exists}")

        return mod_exists

    async def fetch_mod_title(self, mod_id):
        url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={mod_id}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return HTMLParser(await response.text()).css_first('div.workshopItemTitle').text(strip=True)
                    else:
                        logging.warning(f"Failed to fetch mod title for mod_id {mod_id}, status code: {response.status}")
                        return mod_id
        except Exception as e:
            logging.exception(f"Error fetching mod title for mod_id {mod_id}: {e}")
            return mod_id

    async def install_mod(self, mod_id, semaphore, retry_count=0):
        mod_title = await self.fetch_mod_title(mod_id)

        logging.debug(f"install_mod: Before check_mod_exists - mod_title='{mod_title}', mod_id='{mod_id}'")

        if self.check_mod_exists(mod_title, mod_id):
            print(TEXT["install_mod_process_mod_already_exists"].format(mod_title=mod_title))
            logging.info(TEXT["install_mod_process_mod_already_exists"].format(mod_title=mod_title))
            return

        async with semaphore:
            print(TEXT["install_mod_process_installing_mod"].format(mod_title=mod_title))
            logging.info(TEXT["install_mod_process_installing_mod"].format(mod_title=mod_title))
            temp_path = self.script_dir / "temp" / mod_id
            os.makedirs(temp_path, exist_ok=True)
            cmd = [str(self.steamcmd_path), "+force_install_dir", str(temp_path), "+login", "anonymous", "+workshop_download_item", self.game_id, mod_id, "+quit"]
            logging.debug(TEXT["steamcmd_stdout_mod_download"].format(mod_id=mod_id, stdout_str=' '.join(cmd)))
            process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await process.communicate()

            stdout_str = stdout.decode()
            stderr_str = stderr.decode()

            logging.debug(TEXT["steamcmd_stdout_mod_download"].format(mod_id=mod_id, stdout_str=stdout_str))
            logging.debug(TEXT["steamcmd_stderr_mod_download"].format(mod_id=mod_id, stderr_str=stderr_str))

            if process.returncode != 0:
                error_message = TEXT["install_mod_process_download_error"].format(mod_id=mod_id, error=stderr_str)
                print(error_message)
                logging.error(error_message)
                if retry_count < MAX_RETRIES:
                    print(TEXT["retrying_download_mod_attempt"].format(mod_title=mod_title, retry_count=retry_count + 1, MAX_RETRIES=MAX_RETRIES))
                    logging.info(TEXT["retrying_download_mod_attempt"].format(mod_title=mod_title, retry_count=retry_count + 1, MAX_RETRIES=MAX_RETRIES))
                    await asyncio.to_thread(shutil.rmtree, temp_path, ignore_errors=True)
                    await asyncio.sleep(5)
                    return await self.install_mod(mod_id, semaphore, retry_count + 1)
                else:
                    print(TEXT["max_retries_exceeded_mod"].format(mod_title=mod_title))
                    logging.error(TEXT["max_retries_exceeded_mod"].format(mod_title=mod_title))
            else:
                print(TEXT["install_mod_process_download_completed"].format(mod_title=mod_title))
                logging.info(TEXT["install_mod_process_download_completed"].format(mod_title=mod_title))

                mod_src = temp_path / "steamapps" / "workshop" / "content" / self.game_id / mod_id
                if not mod_src.exists():
                    error_message = TEXT["error_mod_folder_not_found"].format(mod_id=mod_id, mod_src=mod_src)
                    print(error_message)
                    logging.error(error_message)
                else:
                    mod_dest = self.mods_path
                    cleaned_mod_title = self.clean_folder_name(mod_title)
                    mod_final_dest_path = mod_dest / cleaned_mod_title

                    if self.game_id == "108600":
                        mod_source_for_copy = mod_src / "mods" / next(iter(mod_src.glob("mods/*")), ".") if (mod_src / "mods").exists() else mod_src
                    else:
                        mod_source_for_copy = mod_src / "mods" if (mod_src / "mods").exists() else mod_src


                    try:
                        print(TEXT["copying_mod_from_to"].format(mod_src=mod_source_for_copy, mod_dest=mod_dest))
                        logging.info(TEXT["copying_mod_from_to"].format(mod_src=mod_source_for_copy, mod_dest=mod_dest))
                        await asyncio.to_thread(shutil.copytree, mod_source_for_copy, mod_final_dest_path, dirs_exist_ok=True)
                        print(TEXT["install_mod_process_mod_installed"].format(mod_title=mod_title))
                        logging.info(TEXT["install_mod_process_mod_installed"].format(mod_title=mod_title))

                        self.installed_mods.append(cleaned_mod_title)
                        self.save_installed_mods()

                    except OSError as e:
                        if e.winerror == 267:
                            print(TEXT["install_mod_process_renaming_mod_to_id"].format(mod_title=mod_title, mod_id=mod_id))
                            logging.warning(TEXT["install_mod_process_renaming_mod_to_id"].format(mod_title=mod_title, mod_id=mod_id))
                            mod_final_dest_path = mod_dest / mod_id
                            await asyncio.to_thread(shutil.copytree, mod_source_for_copy, mod_final_dest_path, dirs_exist_ok=True)
                            print(TEXT["install_mod_process_mod_installed_as_id"].format(mod_id=mod_id))
                            logging.info(TEXT["install_mod_process_mod_installed_as_id"].format(mod_id=mod_id))

                            self.installed_mods.append(mod_id)
                            self.save_installed_mods()
                        else:
                            error_message = TEXT["error_copying_mod"].format(mod_title=mod_title, error=e)
                            print(error_message)
                            logging.exception(error_message)
                    except Exception as e:
                        error_message = TEXT["error_copying_mod"].format(mod_title=mod_title, error=e)
                        print(error_message)
                        logging.exception(error_message)


            await asyncio.to_thread(shutil.rmtree, temp_path, ignore_errors=True)

    async def install_mods(self, mod_ids):
        semaphore = asyncio.Semaphore(self.max_concurrent_downloads)
        await asyncio.gather(*[self.install_mod(mod_id, semaphore) for mod_id in mod_ids])

    async def fetch_collection_mods(self, collection_url):
        async with aiohttp.ClientSession() as session:
            async with session.get(collection_url) as response:
                if response.status != 200: return []
                html = await response.text()
                parser = HTMLParser(html)
                return list(set(match.group(1) for link in parser.css('a') if (href := link.attributes.get('href')) and '/sharedfiles/filedetails/?id=' in href and (match := re.search(r'[?&]id=(\d+)', href))))

    def install_from_urls(self):
        os.system(TEXT["general_cls"])
        print(f"{TEXT['install_mods_urls_title']}\n{TEXT['install_mods_urls_instructions']}{TEXT['install_mods_urls_exit_option']}\n")
        urls, mod_ids = [], []
        while True:
            url = input().strip()
            if url.lower() == 'x': return
            if not url:
                if urls: break
                else: continue
            if not re.search(r'steamcommunity\.com/sharedfiles/filedetails/\?id=\d+', url):
                os.system(TEXT["general_cls"])
                print(f"{TEXT['install_mods_urls_invalid_url']}\n{TEXT['install_mods_urls_instructions']}{TEXT['install_mods_urls_exit_option']}\n")
                continue
            urls.append(url)
        mod_ids = [match.group(1) for url in urls if (match := re.search(r'[?&]id=(\d+)', url))]
        if mod_ids: asyncio.run(self.install_mods(mod_ids))
        input(TEXT["install_mods_urls_downloaded_message"])

    def install_from_collection(self):
        os.system(TEXT["general_cls"])
        print(f"{TEXT['install_mods_collection_title']}\n{TEXT['install_mods_collection_instruction_link']}{TEXT['install_mods_collection_exit_option']}\n")
        while True:
            collection_url = input().strip()
            if collection_url.lower() == 'x': return
            if match := re.search(r'steamcommunity\.com/sharedfiles/filedetails/\?id=(\d+)', collection_url):
                collection_id = match.group(1)
                try:
                    mod_ids = asyncio.run(self.fetch_collection_mods(collection_url))
                    if not mod_ids:
                        os.system(TEXT["general_cls"])
                        print(f"{TEXT['install_mods_collection_no_mods_in_collection']}\n{TEXT['install_mods_collection_instruction_link']}{TEXT['install_mods_collection_exit_option']}\n")
                        continue
                    print(TEXT["install_mods_collection_mods_found"].format(count=len(mod_ids)))
                    if input(TEXT["install_mods_collection_confirm_install"]).lower() != 'y': continue
                    asyncio.run(self.install_mods(mod_ids))
                    input(TEXT["install_mods_collection_downloaded_message"])
                    break
                except Exception as e:
                    os.system(TEXT["general_cls"])
                    print(f"{TEXT['install_mods_collection_error_fetching_mods'].format(error=e)}\n{TEXT['install_mods_collection_try_again']}\n")
                    if input().lower() != 'y': break
            else:
                os.system(TEXT["general_cls"])
                print(f"{TEXT['install_mods_collection_invalid_link']}\n{TEXT['install_mods_collection_instruction_link']}{TEXT['install_mods_collection_exit_option']}\n")

    def main_menu(self):
        while True:
            os.system(TEXT["general_cls"])
            menu_text = f"{TEXT['main_menu_title']}\n"
            if self.game_name:
                menu_text += f"{TEXT['main_menu_current_game'].format(game_name=self.game_name, game_id=self.game_id)}\n{TEXT['general_separator']}\n"
                menu_text += "\n".join(TEXT["main_menu_items_with_game"]) + "\n"
            else:
                menu_text += f"{TEXT['main_menu_no_game_selected']}\n"
                menu_text += "\n".join(TEXT["main_menu_items_no_game"]) + "\n"
            menu_text += f"\n{TEXT['general_separator']}\n{TEXT['main_menu_prompt']}"
            print(menu_text)
            choice = input().strip()
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