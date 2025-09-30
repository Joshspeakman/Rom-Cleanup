# ROM Cleanup Tool

A powerful Python-based ROM collection organizer with intelligent duplicate detection, region-based sorting, and automated cleanup operations.

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 Table of Contents

- [Features](#-features)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Usage Guide](#-usage-guide)
  - [Recommended Cleanup](#recommended-cleanup)
  - [Advanced Options](#advanced-options)
- [Region Detection](#-region-detection)
- [Special Version Detection](#-special-version-detection)
- [Format Preference](#-format-preference)
- [Folder-Based Games](#-folder-based-games)
- [Supported Systems](#-supported-systems)
- [Command Line Options](#-command-line-options)
- [FAQ](#-faq)
- [Contributing](#-contributing)
- [License](#-license)

## 🌟 Features

### Core Functionality

- **🎯 Smart Duplicate Detection**: Identifies duplicate ROMs across different regions, versions, and formats
- **🌍 Region-Based Organization**: Automatically sorts ROMs by region (USA, Europe, Japan, World, etc.)
- **📊 Priority-Based Sorting**: Multi-region ROMs are sorted by configurable priority (default: USA > World > Europe > Japan)
- **💾 Format Intelligence**: Keeps best format based on compression, save file presence, and format quality
- **🎮 Special Version Handling**: Detects and manages Beta, Proto, Alpha, Demo, Hack, and Translation versions
- **📁 Folder Game Support**: Handles multi-disc CD games and arcade games (CHD, CUE/BIN sets) as complete units
- **🔍 Comprehensive Analysis**: Detailed statistics on your ROM collection before any operations

### Advanced Features

- **📈 Version Detection**: Identifies and manages different versions of the same ROM
- **🎰 Content Filtering**: Automatically detects and organizes casino and adult content games
- **💬 Translation Detection**: Identifies fan translations and unofficial English patches
- **🎨 Visual Interface**: Colorful, easy-to-read terminal UI with box-drawing characters
- **⚙️ Configurable Settings**: Extensive customization via `config.ini`
- **🔒 Safe Operations**: Non-destructive moves to review folders before permanent deletion
- **📝 Detailed Logging**: Complete operation logs for audit trails

## 📦 Installation

### Prerequisites

- Python 3.7 or higher
- Windows, macOS, or Linux

### Setup

1. **Download the script**:
   ```bash
   git clone https://github.com/joshspeakman/rom-cleanup.git
   cd rom-cleanup
   ```

2. **No dependencies required!** The script uses only Python standard library modules.

3. **Optional: Create configuration file**:
   ```bash
   # The script will create config.ini on first run with default settings
   python rom_cleanup.py
   ```

## 🚀 Quick Start

1. **Place the script in your ROM directory**:
   ```
   /YourROMs/
   ├── rom_cleanup.py
   ├── Super Mario Bros (USA).nes
   ├── Super Mario Bros (Europe).nes
   ├── Sonic (Japan).md
   └── ...
   ```

2. **Run the script**:
   ```bash
   python rom_cleanup.py
   ```

3. **Choose "Recommended Cleanup"** for automated organization based on best practices.

4. **Review organized files** in region-specific folders (Europe/, Japan/, etc.)

## ⚙️ Configuration

The script creates a `config.ini` file with customizable settings:

### config.ini Structure

```ini
[VERSION_HANDLING]
# Detect version numbers in ROM filenames
detect_versions = true

# Action for older versions: delete, review, or keep
older_version_action = review

[REGION_PRIORITY]
# Priority order for multi-region ROMs (highest to lowest)
priority_order = USA, World, Europe, Japan

[SCANNING]
# Scan subdirectories (false = parent folder only, safer)
scan_subfolders = false

# Folders to exclude from scanning (comma-separated)
excluded_folders = ROM_DELETE, ROM_REVIEW, Adult, Casino, Beta-Proto, Europe, Japan, World, Asia, Australia, Brazil, Canada, China, France, Germany, Italy, Korea, Netherlands, Spain, Sweden, Taiwan, UK

[OUTPUT]
# Log file location
log_file = rom_cleanup_log.txt
```

### Key Settings Explained

| Setting | Description | Default |
|---------|-------------|---------|
| `detect_versions` | Enable version detection (v1.0, Rev A, etc.) | `true` |
| `older_version_action` | What to do with older versions | `review` |
| `priority_order` | Region priority for multi-region ROMs | `USA, World, Europe, Japan` |
| `scan_subfolders` | Recursively scan subdirectories | `false` |
| `excluded_folders` | Folders to skip during scanning | See config.ini |

## 📖 Usage Guide

### Recommended Cleanup

The **Recommended Cleanup** option performs a comprehensive, automated organization:

#### What It Does:

1. **Moves adult content games** → `Adult/` folder
2. **Moves casino/gambling games** → `Casino/` folder
3. **Moves beta/prototype games** → `Beta-Proto/` folder
4. **Organizes non-USA ROMs** → Region folders (`Europe/`, `Japan/`, etc.)
5. **Organizes folder-based games** → Region folders (multi-disc CD games, arcade games)
6. **Removes duplicate ROMs** → `ROM_DELETE/` folder (keeps highest priority region)

#### Example:

**Before:**
```
/ROMs/
├── Baseball (USA).nes
├── Baseball (Europe).nes
├── Soccer (Japan).nes
├── Casino Kid (USA).nes
└── Final Fantasy (Beta).nes
```

**After:**
```
/ROMs/
├── Baseball (USA).nes           # USA version kept in main folder
├── Europe/
│   └── Baseball (Europe).nes    # Non-USA version moved to region folder
├── Japan/
│   └── Soccer (Japan).nes       # Non-USA version moved to region folder
├── Casino/
│   └── Casino Kid (USA).nes     # Casino game moved to Casino folder
└── Beta-Proto/
    └── Final Fantasy (Beta).nes  # Beta version moved to Beta-Proto folder
```

### Advanced Options

The **Advanced Options** menu provides granular control:

#### Bulk Operations

- **Organize non-USA ROMs by region**: Sort Europe, Japan, Asia, etc. into folders
- **Organize folder-based games by region**: Handle multi-disc/arcade games as complete units
- **Move casino/gambling games**: Poker, slots, blackjack, roulette, pachinko games
- **Move adult/mature content**: Games with adult content ratings
- **Keep only main regions**: Remove uncommon regions (Asia, Brazil, Korea, etc.)
- **Move all special versions**: Beta, Proto, Alpha, Demo, Hack, Translation versions
- **Keep only best format**: Remove inferior formats (keeps uncompressed or format with save file)
- **Keep only newest version**: Remove older ROM versions (v1.0 vs v2.0)

#### Individual Operations

- **Move specific region**: Select individual regions to move (Europe, Japan, etc.)
- **Move specific special version**: Select individual special types (Beta, Proto, etc.)
- **Move unknown regions**: ROMs without detectable region tags

#### Management Operations

- **Review ROM_DELETE folder**: See what will be deleted before confirming
- **Review ROM_REVIEW folder**: Check items flagged for manual review
- **Empty cleanup folders**: Remove all files from ROM_DELETE and ROM_REVIEW
- **Remove cleanup folders**: Delete the cleanup folders entirely
- **Remove this script**: Clean exit - removes script file
- **Toggle scanning mode**: Switch between parent folder only / recursive subfolder scanning

## 🌍 Region Detection

### Supported Regions

| Region | Detection Patterns | Priority |
|--------|-------------------|----------|
| USA | (USA), (US), (U), (NA) | 1 (Highest) |
| World | (World), (W) | 2 |
| Europe | (Europe), (EU), (E), (PAL) | 3 |
| Japan | (Japan), (JP), (J), (NTSC-J) | 4 |
| Asia | (Asia), (As) | 5 |
| Australia | (Australia), (AU), (AUS) | 6 |
| Brazil | (Brazil), (BR) | 7 |
| Canada | (Canada), (CA) | 8 |
| China | (China), (CN) | 9 |
| France | (France), (FR) | 10 |
| Germany | (Germany), (DE) | 11 |
| Italy | (Italy), (IT) | 12 |
| Korea | (Korea), (KR) | 13 |
| Netherlands | (Netherlands), (NL) | 14 |
| Spain | (Spain), (ES) | 15 |
| Sweden | (Sweden), (SE) | 16 |
| Taiwan | (Taiwan), (TW) | 17 |
| UK | (UK), (United Kingdom) | 18 |

### Multi-Region ROM Handling

ROMs with multiple regions (e.g., `Baseball Heroes (USA, Europe).zip`) are processed using **priority-based selection**:

- The **primary region** is determined by the configured priority order
- Default priority: `USA > World > Europe > Japan`
- The ROM is sorted to the **highest priority region only**
- Statistics count each ROM only once (prevents inflated counts)

**Example:**
```
Filename: Tournament Cyberball (USA, Europe).zip
Primary Region: USA (highest priority)
Action: Stays in main folder (USA ROMs not moved)

Filename: Soccer Challenge (Europe, Japan).zip
Primary Region: Europe (highest priority between the two)
Action: Moved to Europe/ folder
```

## 🎮 Special Version Detection

### Detected Special Versions

| Type | Detection Patterns | Description |
|------|-------------------|-------------|
| **Proto** | (Proto), (Prototype), [proto] | Prototype/pre-release versions |
| **Beta** | (Beta), [beta], [b] | Beta test versions |
| **Alpha** | (Alpha), [alpha], [a] | Alpha test versions |
| **Demo** | (Demo), [demo], [d] | Demo/trial versions |
| **Sample** | (Sample), [sample] | Sample/kiosk versions |
| **Homebrew** | (Homebrew), [homebrew], [h] | Fan-made games |
| **Hack** | (Hack), [hack], [h#] | ROM hacks/modifications |
| **Translation** | (Translation), [T+], [T-] | Fan translations |
| **Trainer** | [t#], (Trainer) | Games with cheat trainers |
| **Overdump** | [o#], (Overdump) | Incorrectly dumped ROMs |
| **Bad Dump** | [b#], (Bad), [!p] | Corrupted/bad dumps |
| **Good Dump** | [!], (Good) | Verified good dumps |
| **Cracked** | [cr], (Cracked) | Cracked protection |
| **Fixed** | [f#], (Fixed) | Bug-fixed versions |
| **Pirate** | [p#], (Pirate) | Pirate/bootleg versions |

### Translation Detection

The script intelligently detects **fan translations** and **English patches**:

```
Patterns detected:
- [T+Eng], [T+English]
- [T-Eng], [T-English]
- (Translation), (Translated)
- (English), [English]
- Fan Translation, English Translation
```

**Note**: The script distinguishes between language codes and regions to avoid false positives.

## 💾 Format Preference

### Format Ranking System

When multiple formats of the same ROM exist, the script keeps the **best format** based on:

1. **Save file presence** (highest priority - format with .srm/.sav file is kept)
2. **Format quality** (uncompressed > compressed)
3. **Native format preference** (system-specific formats preferred)

### Format Hierarchy Examples

#### Nintendo Systems
```
Preference (High → Low):
.nes (10) > .fds (9) > .unif (8) > .zip (1)
.sfc (10) > .smc (9) > .zip (1)
.gb (10) > .gbc (10) > .zip (1)
.n64 (10) > .z64 (10) > .v64 (9) > .zip (1)
```

#### Sega Systems
```
Preference (High → Low):
.md (10) > .gen (10) > .smd (9) > .bin (8) > .zip (1)
.gg (10) > .zip (1)
.32x (10) > .zip (1)
```

#### Sony Systems
```
Preference (High → Low):
.cue (10) > .chd (9) > .bin (8) > .iso (7) > .zip (1)
.cue + .bin set > single .bin file
```

#### Arcade/MAME
```
Preference (High → Low):
.chd (9) > .zip (5) > .7z (1)
Note: CHD + ZIP combinations detected as arcade games
```

### Format Comparison Example

**Before cleanup:**
```
Super Mario Bros.nes          (Priority: 10)
Super Mario Bros.zip          (Priority: 1)
Super Mario Bros.srm          (Save file detected!)
```

**After cleanup:**
```
✓ Keep: Super Mario Bros.nes  (has associated save file)
✗ Move to ROM_DELETE: Super Mario Bros.zip
✓ Keep: Super Mario Bros.srm
```

## 📁 Folder-Based Games

### What Are Folder-Based Games?

Multi-disc CD games and arcade games that require multiple files to function are treated as **complete units**:

#### Detection Criteria

1. **Multi-disc CD games**: Folders containing 2+ CHD files
2. **CUE/BIN sets**: Folders with 1+ CUE files + 1+ BIN files
3. **Arcade games**: Folders with CHD + ZIP file combinations
4. **M3U playlists**: Folders with .m3u files (multi-disc indicators)

### How They're Organized

Folder-based games are **moved as complete folders** to region-specific locations:

**Before:**
```
/ROMs/
├── Final Fantasy VII (USA)/
│   ├── Disc1.chd
│   ├── Disc2.chd
│   └── Disc3.chd
└── Metal Gear Solid (Europe)/
    ├── Disc1.chd
    └── Disc2.chd
```

**After:**
```
/ROMs/
├── Final Fantasy VII (USA)/     # USA game stays in main folder
│   ├── Disc1.chd
│   ├── Disc2.chd
│   └── Disc3.chd
└── Europe/
    └── Metal Gear Solid (Europe)/  # Entire folder moved
        ├── Disc1.chd
        └── Disc2.chd
```

### Conditional Display

Folder game options **only appear** if folder-based games are detected in your collection. This keeps the interface clean when not needed.

## 🎯 Supported Systems

The tool supports **100+ gaming platforms**:

### Consoles

<details>
<summary><b>Nintendo Systems</b> (click to expand)</summary>

- NES/Famicom (.nes, .fds, .unif, .nsf)
- SNES/Super Famicom (.sfc, .smc, .bs, .spc)
- Nintendo 64 (.n64, .z64, .v64, .rom64)
- GameCube (.gcm, .iso, .tgc, .gcz, .wbfs)
- Wii (.iso, .wbfs, .wia, .rvz, .wad)
- Wii U (.wux, .rpx, .wud)
- Switch (.xci, .nsp, .nro)

</details>

<details>
<summary><b>Nintendo Handhelds</b> (click to expand)</summary>

- Game Boy (.gb, .gbc, .sgb, .dmg)
- Game Boy Advance (.gba, .agb, .mb)
- Nintendo DS (.nds, .dsi, .ids)
- Nintendo 3DS (.3ds, .cia, .3dsx)
- Virtual Boy (.vb, .vboy)
- Pokemon Mini (.min, .pokemini)

</details>

<details>
<summary><b>Sega Systems</b> (click to expand)</summary>

- Master System (.sms, .gg)
- Genesis/Mega Drive (.md, .gen, .smd, .bin)
- Sega CD/Mega-CD (.cue, .chd, .bin, .iso)
- 32X (.32x)
- Saturn (.cue, .chd, .bin, .mds, .ccd)
- Dreamcast (.cdi, .gdi, .chd)
- Game Gear (.gg)
- Pico (.bin)

</details>

<details>
<summary><b>Sony Systems</b> (click to expand)</summary>

- PlayStation (.cue, .chd, .bin, .pbp, .img)
- PlayStation 2 (.iso, .bin, .img)
- PlayStation 3 (.iso, .pkg)
- PlayStation 4 (.pkg)
- PSP (.iso, .cso, .pbp, .dax)
- PS Vita (.vpk)

</details>

<details>
<summary><b>Microsoft Systems</b> (click to expand)</summary>

- Xbox (.xbe, .iso, .xiso)
- Xbox 360 (.xex, .iso, .god, .xbla)
- Xbox One (.xbx1)

</details>

<details>
<summary><b>Other Consoles</b> (click to expand)</summary>

- Atari 2600 (.a26, .bin)
- Atari 5200 (.a52, .bin)
- Atari 7800 (.a78)
- Atari Lynx (.lnx)
- Atari Jaguar (.j64, .jag)
- Neo Geo (.neo, .zip, .ngp, .ngc)
- TurboGrafx-16/PC Engine (.pce, .sgx)
- 3DO (.iso, .chd, .cue)
- ColecoVision (.col)
- Intellivision (.int, .bin)
- Odyssey 2 (.o2)
- WonderSwan (.ws, .wsc)
- N-Gage (.ngage, .n-gage)

</details>

### Computers

<details>
<summary><b>Classic Computers</b> (click to expand)</summary>

- Commodore 64 (.d64, .t64, .prg, .g64)
- Amiga (.adf, .dms, .ipf, .hdf)
- Atari ST (.st, .msa, .dim, .stx)
- ZX Spectrum (.tap, .tzx, .z80, .sna)
- Amstrad CPC (.cpc, .dsk, .cdt)
- MSX (.msx, .dsk, .rom)
- Apple II (.do, .po, .nib, .woz)
- TI-99/4A (.ti99, .tifiles)
- Dragon (.dragon, .vdk)
- Color Computer (.coco, .cas)

</details>

### Arcade

- MAME (.zip, .chd, .7z)
- Neo Geo (.neo, .zip)
- CPS1/CPS2 (.zip)

### File Formats

**Supported extensions**: Over 200 file formats including .nes, .sfc, .md, .gb, .gba, .n64, .nds, .3ds, .iso, .chd, .cue, .bin, .zip, .7z, and many more.

## 💻 Command Line Options

### Basic Usage

```bash
# Interactive mode (default)
python rom_cleanup.py

# Analyze directory and show statistics only
python rom_cleanup.py --analyze

# Run specific cleanup operation
python rom_cleanup.py --cleanup recommended

# Enable recursive subfolder scanning
python rom_cleanup.py --scan-subfolders

# Specify different directory
python rom_cleanup.py --directory /path/to/roms
```

### Advanced Usage

```bash
# Batch operations (non-interactive)
python rom_cleanup.py --batch --cleanup recommended

# Export analysis to JSON
python rom_cleanup.py --analyze --export analysis.json

# Dry run (show what would happen without making changes)
python rom_cleanup.py --dry-run --cleanup recommended

# Verbose logging
python rom_cleanup.py --verbose
```

## ❓ FAQ

### General Questions

**Q: Will this delete my ROMs?**
A: No! The script moves files to `ROM_DELETE/` and `ROM_REVIEW/` folders. You must manually empty these folders to permanently delete files.

**Q: What if I make a mistake?**
A: All moved files are in organized folders. Simply move them back to the main directory and re-run the script.

**Q: Does this work on Windows/Mac/Linux?**
A: Yes! The script is cross-platform and uses Python's standard library.

**Q: Can I customize which regions to keep?**
A: Yes! Edit `config.ini` and change the `priority_order` setting.

**Q: Will this corrupt my ROMs?**
A: No! The script only moves files, it never modifies ROM data.

### Technical Questions

**Q: Why aren't my ROMs being detected?**
A: Check that:
- File extensions are recognized (see Supported Systems)
- If files are in subfolders, enable `scan_subfolders = true` in config.ini
- Files aren't in excluded folders (check `excluded_folders` setting)

**Q: Why did it keep the .zip instead of the .nes file?**
A: The .zip file likely has an associated save file (.srm). The script prioritizes formats with save data to prevent save game loss.

**Q: How do I change region priority?**
A: Edit `config.ini`:
```ini
[REGION_PRIORITY]
priority_order = Europe, USA, Japan, World
```

**Q: Can I run this on my entire ROM collection at once?**
A: Yes, but we recommend:
1. Test on a small subfolder first
2. Back up your collection
3. Review the analysis statistics before proceeding
4. Check `ROM_DELETE/` and `ROM_REVIEW/` before emptying them

**Q: What's the difference between "delete" and "review" for older versions?**
A:
- `delete`: Older versions go to `ROM_DELETE/` (presumed unwanted)
- `review`: Older versions go to `ROM_REVIEW/` (manual decision needed)

**Q: Does this work with No-Intro/TOSEC/Redump sets?**
A: Yes! The script is designed to work with standard ROM naming conventions including No-Intro, TOSEC, Redump, and GoodTools naming schemes.

### Save File Questions

**Q: Will my save files be deleted?**
A: No! Save files (.srm, .sav, .st0, etc.) are preserved. If a ROM has a save file, that ROM format is kept even if another format would normally be preferred.

**Q: What happens to save files when ROMs are moved?**
A: Save files are automatically moved with their associated ROMs to maintain the pairing.

**Q: Are save states different from save files?**
A: Yes:
- **Save files** (.srm, .sav): In-game saves, preserved with ROM
- **Save states** (.st0-.st9): Emulator snapshots, also preserved

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

### Reporting Issues

1. Check if the issue already exists
2. Provide detailed information:
   - ROM filename examples
   - Expected behavior
   - Actual behavior
   - Error messages (if any)

### Suggesting Features

1. Open an issue with the `enhancement` label
2. Describe the feature and use case
3. Provide examples if applicable

### Code Contributions

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Make your changes
4. Add tests if applicable
5. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
6. Push to the branch (`git push origin feature/AmazingFeature`)
7. Open a Pull Request

### Development Setup

```bash
# Clone the repository
git clone https://github.com/joshspeakman/rom-cleanup.git
cd rom-cleanup

# Run tests
python test_rom_cleanup.py

# Run with test data
python rom_cleanup.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 ROM Cleanup Tool Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🙏 Acknowledgments

- Thanks to the No-Intro, TOSEC, and Redump communities for ROM naming standards
- Inspired by ROM organization needs of retro gaming enthusiasts
- Built with ❤️ for the emulation community

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/joshspeakman/rom-cleanup/issues)
- **Discussions**: [GitHub Discussions](https://github.com/joshspeakman/rom-cleanup/discussions)
- **Wiki**: [GitHub Wiki](https://github.com/joshspeakman/rom-cleanup/wiki)

---

**⭐ If you find this tool useful, please consider giving it a star on GitHub!**

*Last updated: 2025-09-30*
