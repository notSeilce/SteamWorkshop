# Steam Workshop Downloader

![Python](https://img.shields.io/badge/Python-3.7+-blue.svg?style=flat-square&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)

**Download mods and collections from the Steam Workshop without owning the game!**

This tool allows you to download content from the Steam Workshop for various games, even if you haven't purchased them on Steam.  Simply provide a link to the game's Steam store page and the link to the mod or collection you want to download. Mods are conveniently organized in the `/games/[Game Name]/mods/` directory.

## Features

*   **Download Mods by URL:** Install individual mods by providing their Steam Workshop link.
*   **Download Collections by URL:** Install entire Steam Workshop collections with a single link.
*   **Game Selection:** Easily set up and switch between different games for mod installation.
*   **Parallel Downloads:** Supports downloading multiple mods concurrently to speed up the process (configurable).
*   **Automatic SteamCMD Installation:** Handles the download and setup of SteamCMD if it's not already present.
*   **Mod Existence Check:** Prevents re-downloading mods that are already installed.
*   **Handles Invalid Characters in Mod Names:** Cleans up mod folder names to ensure compatibility with your operating system.
*   **Configurable Language:** Supports English and Russian languages (more languages can be easily added).
*   **Logging:** Detailed logging to a `workshop_downloader.log` file for troubleshooting.

## Tested Games

This downloader has been performance tested and confirmed to work well with:

*   **Counter-Strike 2**
*   **RimWorld**
*   **Project Zomboid** (Optimized for Project Zomboid)

It may work with other games as well, but these are the ones that have been specifically tested.

## Configuration

The program's behavior can be adjusted through the `config.json` file located in the `main` directory after the first run.

*   **`MAX_CONCURRENT_DOWNLOADS`**:  This setting controls the number of mods downloaded simultaneously.
    *   **For users with slower internet connections:**  It's recommended to lower this value (e.g., `MAX_CONCURRENT_DOWNLOADS: 2`) to prevent overloading your network and improve download stability.
    *   **Default Value:** `5` (This might be too high for slow connections, consider lowering it initially).

```json
{
    "GAME_NAME": "\"[Your Game Name]\"",
    "GAME_ID": [Your Game ID],
    "GAME_FOLDER": "[Cleaned Game Folder Name]",
    "MAX_CONCURRENT_DOWNLOADS": [Value],
    "LANGUAGE": "[en/ru]"
}
```

## Mod Structure Support

This downloader is designed to handle common Steam Workshop mod structures. However, some games or mods might use unique or unconventional folder layouts.

If you encounter issues installing mods with unusual structures, or if you would like to request enhanced support for mods with specific folder layouts (especially for games other than Project Zomboid, Counter-Strike 2, and RimWorld), please reach out on Discord: **seilce**.
