#!/usr/bin/env python3

import os
import re
import shutil
import datetime
import configparser
import argparse
from collections import defaultdict, Counter
from pathlib import Path

# ANSI Color Codes for terminal output
class Colors:
    """ANSI color codes for enhanced terminal output"""
    # Basic colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'

    # Bright colors
    BRIGHT_RED = '\033[91;1m'
    BRIGHT_GREEN = '\033[92;1m'
    BRIGHT_YELLOW = '\033[93;1m'
    BRIGHT_BLUE = '\033[94;1m'
    BRIGHT_MAGENTA = '\033[95;1m'
    BRIGHT_CYAN = '\033[96;1m'

    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

    # Background colors
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'

    @staticmethod
    def strip_colors(text):
        """Remove ANSI color codes from text"""
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

class ROMAnalyzer:
    def __init__(self):
        self.unknown_regions = set()
        self.unknown_specials = set()
        self.log_file = "rom_cleanup_log.txt"
        self.scan_subfolders = False  # Default to parent folder only (safer, prevents re-counting moved ROMs)

        # Version handling configuration
        self.detect_versions = True
        self.older_version_action = "review"  # Options: delete, review, keep

        # Region priority configuration - default order for keeping ROMs and handling multi-region ROMs
        self.region_priority = ['USA', 'World', 'Europe', 'Japan']

        # Region patterns - common ROM naming conventions
        # Updated to handle both parentheses and standalone text
        # IMPORTANT: Must be defined BEFORE load_config() is called
        self.region_patterns = {
            'USA': [r'\(USA?\)', r'\(US\)', r'\(U\)', r'\(NA\)', r'\bUSA?\b', r'\bUS\b', r'\bNA\b'],
            'Europe': [r'\(Europe?\)', r'\(EU\)', r'\(E\)', r'\(PAL\)', r'\bEurope?\b', r'\bEU\b', r'\bPAL\b'],
            'Japan': [r'\(Japan?\)', r'\(JP\)', r'\(J\)', r'\(NTSC-J\)', r'\bJapan?\b', r'\bJP\b', r'\bJ\b'],
            'World': [r'\(World\)', r'\(W\)', r'\bWorld\b', r'\bW\b'],
            'Asia': [r'\(Asia\)', r'\(As\)', r'\bAsia\b', r'\bAs\b'],
            'Australia': [r'\(Australia\)', r'\(AU\)', r'\(AUS\)', r'\bAustralia\b', r'\bAU\b', r'\bAUS\b'],
            'Brazil': [r'\(Brazil\)', r'\(BR\)', r'\bBrazil\b', r'\bBR\b'],
            'Canada': [r'\(Canada\)', r'\(CA\)', r'\bCanada\b', r'\bCA\b'],
            'China': [r'\(China\)', r'\(CN\)', r'\bChina\b', r'\bCN\b'],
            'France': [r'\(France\)', r'\(FR\)', r'\bFrance\b', r'\bFR\b'],
            'Germany': [r'\(Germany\)', r'\(DE\)', r'\bGermany\b', r'\bDE\b'],
            'Italy': [r'\(Italy\)', r'\(IT\)', r'\bItaly\b', r'\bIT\b'],
            'Korea': [r'\(Korea\)', r'\(KR\)', r'\bKorea\b', r'\bKR\b'],
            'Netherlands': [r'\(Netherlands\)', r'\(NL\)', r'\bNetherlands\b', r'\bNL\b'],
            'Spain': [r'\(Spain\)', r'\(ES\)', r'\bSpain\b', r'\bES\b'],
            'Sweden': [r'\(Sweden\)', r'\(SE\)', r'\bSweden\b', r'\bSE\b'],
            'Taiwan': [r'\(Taiwan\)', r'\(TW\)', r'\bTaiwan\b', r'\bTW\b'],
            'UK': [r'\(UK\)', r'\(United Kingdom\)', r'\bUK\b', r'\bUnited Kingdom\b']
        }

        # Special version patterns
        # Note: Removed 'Unl' (Unlicensed) as these are legitimate commercial releases
        self.special_patterns = {
            'Proto': [r'\(Proto\s*\d*\)', r'\(Prototype\s*\d*\)', r'\[proto\s*\d*\]', r'\[prototype\s*\d*\]'],
            'Beta': [r'\(Beta\s*\d*\)', r'\[beta\s*\d*\]', r'\[b\d*\]'],
            'Alpha': [r'\(Alpha\s*\d*\)', r'\[alpha\s*\d*\]', r'\[a\d*\]'],
            'Demo': [r'\(Demo\s*\d*\)', r'\[demo\s*\d*\]', r'\[d\d*\]'],
            'Sample': [r'\(Sample\s*\d*\)', r'\[sample\s*\d*\]'],
            'Homebrew': [r'\(Homebrew\)', r'\[homebrew\]', r'\[h\]'],
            'Hack': [r'\(Hack\)', r'\[hack\]', r'\[h\d+\]'],
            'Translation': [r'\(Translation\)', r'\[T\+', r'\[T-'],
            'Trainer': [r'\[t\d*\]', r'\(Trainer\)'],
            'Overdump': [r'\[o\d*\]', r'\(Overdump\)'],
            'Bad Dump': [r'\[b\d*\]', r'\(Bad\)', r'\[!p\]'],
            'Good Dump': [r'\[!\]', r'\(Good\)'],
            'Cracked': [r'\[cr\]', r'\(Cracked\)'],
            'Fixed': [r'\[f\d*\]', r'\(Fixed\)'],
            'Pirate': [r'\[p\d*\]', r'\(Pirate\)']
        }

        # Translation patterns - more comprehensive list
        self.translation_patterns = [
            r'\[T\+.*?\]',  # [T+Eng], [T+English], etc.
            r'\[T-.*?\]',   # [T-Eng], [T-English], etc.
            r'\(Translation\)',
            r'\(Translated\)',
            r'\(English\)',
            r'\[English\]',
            r'\(Eng\)',
            r'\[Eng\]',
            r'\[T&.*?\]',   # Translation & other modifications
            r'English Translation',
            r'Fan Translation',
            r'\bTranslated\b',
            r'\bEnglish\b'
        ]

        # Language code patterns - these should NOT be treated as regions
        self.language_code_patterns = [
            r'\b(En|Fr|De|Es|It|Nl|Pt|Sv|No|Da|Fi|Pl|Ru|Ja|Ko|Zh)\b',  # Common 2-letter language codes
            r'\bEng\b', r'\bFre\b', r'\bGer\b', r'\bSpa\b', r'\bIta\b', r'\bDut\b',  # 3-letter codes
            r'\bEnglish\b', r'\bFrench\b', r'\bGerman\b', r'\bSpanish\b', r'\bItalian\b', r'\bDutch\b',  # Full names
            r'\bPortuguese\b', r'\bSwedish\b', r'\bNorwegian\b', r'\bDanish\b', r'\bFinnish\b',
            r'\bPolish\b', r'\bRussian\b', r'\bJapanese\b', r'\bKorean\b', r'\bChinese\b'
        ]

        # Casino game detection patterns - more specific to avoid false positives
        self.casino_game_patterns = [
            # Generic casino terms (very specific)
            r'\bcasino\b', r'\bvegas\b', r'\blasvegas\b', r'\blas vegas\b',
            r'\bgambling\b', r'\bjackpot\b',

            # Card games (specific gambling contexts)
            r'\bpoker\b', r'\btexas hold\b', r'\bholdem\b', r'\bblackjack\b', r'\bblack jack\b',
            r'\bbaccarat\b', r'\bsolitaire\b', r'\bklondike\b', r'\bfreecell\b',
            r'\bpai gow\b', r'\bpaigow\b', r'\bgin rummy\b', r'\brummy\b',

            # Table games
            r'\broulette\b', r'\bcraps\b', r'\bkeno\b', r'\bbingo\b',

            # Slot machines
            r'\bslots?\b', r'\bslot machine\b', r'\bfruit machine\b',
            r'\bone arm bandit\b', r'\bcherry master\b',

            # Specific well-known casino game titles and series
            r'\bvegas stakes\b', r'\bcasino kid\b', r'\bworld class poker\b',
            r'\bcaesars palace\b', r'\btrump castle\b',
            r'\blas vegas dream\b', r'\batlantic city action\b', r'\bmonte carlo casino\b',

            # Japanese gambling games (specific titles)
            r'\bpachinko\b', r'\bmahjong\b', r'\bmah jong\b', r'\bmah-jong\b',
            r'\bhanafuda\b',

            # Casino-specific gambling terms (not generic)
            r'\bchuck a luck\b', r'\bwheel of fortune\b(?! - )', # Exclude "Wheel of Fortune - [game show]"

            # Casino locations (when clearly casino context)
            r'\bmonte carlo casino\b', r'\batlantic city casino\b', r'\breno casino\b',
            r'\briverboat casino\b',

            # Very specific casino money terms (avoid generic uses)
            r'\bcasino chip\b', r'\bpoker chip\b', r'\bgaming chip\b',
        ]

        # Exclusion patterns - ROMs that contain these should NOT be flagged as casino games
        self.casino_exclusion_patterns = [
            # Comic book/superhero terms
            r'\bspider.?man\b', r'\bvenom\b', r'\bcarnage\b', r'\blethal\b',
            r'\bsuperman\b', r'\bbatman\b', r'\bx.?men\b', r'\bavengers\b',
            r'\bmarvel\b', r'\bdc comics\b', r'\bwolverine\b', r'\bhulk\b',
            r'\bcaptain america\b', r'\biron man\b', r'\bjustice league\b',

            # Sci-fi/space terms
            r'\bstar trek\b', r'\bstarfleet\b', r'\bbridge simulator\b',
            r'\bstar wars\b', r'\benterprise\b', r'\bstarship\b',
            r'\balien\b', r'\bspace\b.*\binvaders\b', r'\bgalaga\b',

            # Sports/racing games (might have "cards" or "deck")
            r'\bskateboard\b', r'\bskate\b', r'\bsnowboard\b',
            r'\bsurf\b', r'\brace\b(?!.*casino)', r'\btrack\b(?!.*casino)',
            r'\bfootball\b', r'\bbaseball\b', r'\bbasketball\b', r'\bhockey\b',

            # RPG/strategy terms (card-based games that aren't gambling)
            r'\bpokemon\b', r'\bdigimon\b', r'\byu-gi-oh\b', r'\bmagic the gathering\b',
            r'\bduel\b.*\bmasters\b', r'\bcard\b.*\bbattle\b', r'\btcg\b', r'\bccg\b',

            # Adventure/puzzle games
            r'\bsolitaire\b(?!.*casino)', r'\bpyramid\b(?!.*casino)',
            r'\bmario\b', r'\bzelda\b', r'\bkirby\b', r'\byoshi\b',
            r'\bsonic\b', r'\bmegaman\b', r'\bmega man\b', r'\bcastlevania\b',
            r'\bmetroid\b', r'\bfinal fantasy\b', r'\bdragon quest\b',

            # Action/adventure terms that might conflict
            r'\bbridge\b(?!.*casino)', # "bridge" card game vs "starship bridge"
            r'\bboat\b(?!.*casino)', # Exclude unless specifically casino boat
            r'\bchip\b(?!.*casino)', # Computer chips, not casino chips
            r'\bslot\b(?!.*machine)', # Time slots, expansion slots, not slot machines

            # Board games that aren't gambling
            r'\bmonopoly\b', r'\brisk\b(?!.*casino)', r'\bscrabble\b',
            r'\bchess\b', r'\bcheckers\b', r'\bgo\b(?!.*casino)',

            # Game show context (not gambling)
            r'\bwheel of fortune\b.*\bgame show\b',
            r'\bjeopardy\b', r'\bfamily feud\b', r'\bprice is right\b',
            r'\bgame show\b', r'\btrivia\b(?!.*casino)',

            # Fighting games (might use "deck" in different context)
            r'\bstreet fighter\b', r'\bmortal kombat\b', r'\btekken\b',
            r'\bking of fighters\b', r'\bsamurai shodown\b',
        ]

        # Adult game detection patterns
        self.adult_game_patterns = [
            # Explicit adult terms
            r'\bhentai\b', r'\bporn\b', r'\bporno\b', r'\bxxx\b',
            r'\badult\b', r'\berotic\b', r'\bsexy\b', r'\bnude\b', r'\bnaked\b',
            r'\bbishoujo\b', r'\becchi\b', r'\bbishounen\b',

            # Japanese adult game terms
            r'\beroges?\b', r'\bgalge\b', r'\botome\b', r'\bdating sim\b',
            r'\bvisual novel\b.*\badult\b', r'\brenai\b',

            # Specific known adult titles/series (based on research)
            r'\bsuper\s+maruo\b', r'\bbishoujo\s+shashinkan\b', r'\bstudio\s+cut\b',
            r'\bbodycon quest\b', r'\babakareshi musume\b',
            r'\bhoney peach\b', r'\bnight life\b', r'\bmidnight\b.*\blove\b',

            # Adult content descriptors
            r'\bplayboy\b', r'\bpenthouse\b', r'\bhustler\b',
            r'\bstriptease\b', r'\bstrip\b.*\bpoker\b', r'\blingerie\b',

            # Pattern indicators often found in adult titles
            r'\b18\+\b', r'\badults? only\b', r'\bmature\b.*\bcontent\b',
            r'\bunlicensed\b.*\badult\b', r'\bhomebrew\b.*\badult\b',

            # Common adult game naming patterns
            r'\bgirls?\b.*\bunlocked\b', r'\bseduction\b', r'\btemptation\b',
            r'\bforbidden\b.*\blove\b', r'\bpassion\b.*\bnight\b',
        ]

        # Adult game exclusion patterns - games that might match adult patterns but are NOT adult games
        self.adult_exclusion_patterns = [
            # Family-friendly games that might have words like "love", "night", etc.
            r'\bmario\b', r'\bzelda\b', r'\bpokemon\b', r'\bsonic\b',
            r'\bkirby\b', r'\byoshi\b', r'\bdonkey kong\b',
            r'\bmegaman\b', r'\bmega man\b', r'\bfinal fantasy\b',
            r'\bdragon quest\b', r'\bchrono\b', r'\bsecret of\b',

            # Context that excludes adult meaning
            r'\bnight.*\btrap\b', r'\bmidnight.*\bresistance\b',
            r'\badult.*\bswim\b', r'\bmature.*\btree\b', r'\bsexy.*\bparodius\b',

            # Sports/racing games with "nude" colors
            r'\bnude.*\brace\b', r'\bnude.*\bcar\b',
        ]

        # Version detection patterns - for identifying ROM versions
        self.version_patterns = [
            # Standard version formats
            r'\(v?(\d+)\.(\d+)(?:\.(\d+))?\)',  # (v1.0), (1.1), (v2.3.1)
            r'\[v?(\d+)\.(\d+)(?:\.(\d+))?\]',  # [v1.0], [1.1], [v2.3.1]
            r'\(ver\.?\s*(\d+)(?:\.(\d+))?(?:\.(\d+))?\)',  # (ver 1), (ver. 2.1)
            r'\[ver\.?\s*(\d+)(?:\.(\d+))?(?:\.(\d+))?\]',  # [ver 1], [ver. 2.1]
            r'\(version\s*(\d+)(?:\.(\d+))?(?:\.(\d+))?\)',  # (version 1.0)
            r'\[version\s*(\d+)(?:\.(\d+))?(?:\.(\d+))?\]',  # [version 1.0]
            # Revision formats
            r'\(r(?:ev)?\.?\s*(\d+)\)',  # (r1), (rev 2), (rev. 3)
            r'\[r(?:ev)?\.?\s*(\d+)\]',  # [r1], [rev 2], [rev. 3]
            r'\(revision\s*(\d+)\)',  # (revision 1)
            r'\[revision\s*(\d+)\]',  # [revision 1]
            # Alpha/Beta with version
            r'\((alpha|beta)\s*(\d+)(?:\.(\d+))?\)',  # (alpha 1), (beta 2.1)
            r'\[(alpha|beta)\s*(\d+)(?:\.(\d+))?\]',  # [alpha 1], [beta 2.1]
        ]

        # Save state file extensions (should be excluded from duplicate detection)
        self.save_state_extensions = {
            '.srm', '.sav', '.rtc', '.fla',  # Save files (SRAM, etc.)
            '.st0', '.st1', '.st2', '.st3', '.st4', '.st5', '.st6', '.st7', '.st8', '.st9',  # Save states
            '.fc0', '.fc1', '.fc2', '.fc3', '.fc4', '.fc5', '.fc6', '.fc7', '.fc8', '.fc9',  # FCE Ultra states
            '.zs0', '.zs1', '.zs2', '.zs3', '.zs4', '.zs5', '.zs6', '.zs7', '.zs8', '.zs9',  # ZSNES states
            '.sm0', '.sm1', '.sm2', '.sm3', '.sm4', '.sm5', '.sm6', '.sm7', '.sm8', '.sm9',  # SNES9x states
            '.vb0', '.vb1', '.vb2', '.vb3', '.vb4', '.vb5', '.vb6', '.vb7', '.vb8', '.vb9',  # VisualBoy states
            '.ds0', '.ds1', '.ds2', '.ds3', '.ds4', '.ds5', '.ds6', '.ds7', '.ds8', '.ds9'   # DeSmuME states
        }

        # Format preference ranking (higher number = better format)
        # Uncompressed native formats are generally preferred over compressed
        self.format_preference = {
            # Compressed formats (lowest preference)
            '.zip': 1, '.7z': 1, '.rar': 1,

            # Generic formats
            '.rom': 5, '.bin': 5, '.img': 5, '.raw': 5,

            # Nintendo formats (native preferred)
            '.nes': 10, '.fds': 9, '.unif': 8, '.unf': 8, '.nsf': 6, '.nsfe': 6,  # NES/Famicom + audio
            '.sfc': 10, '.smc': 9, '.snes': 10, '.bs': 8, '.spc': 6,  # SNES/Super Famicom + audio/satellaview
            '.gb': 10, '.gbc': 10, '.cgb': 10, '.sgb': 9, '.dmg': 9, '.gbx': 8,  # Game Boy series + extended
            '.gba': 10, '.agb': 9, '.mb': 8, '.srl': 9,  # Game Boy Advance + multiboot
            '.n64': 10, '.z64': 10, '.v64': 9, '.u64': 8, '.rom64': 7, '.n64rom': 7, '.usa': 6, '.pal': 6, '.jap': 6,  # Nintendo 64 + region variants
            '.nds': 10, '.dsi': 9, '.ids': 8, '.srl': 9, '.nds.gba': 7,  # Nintendo DS/DSi + slot-2
            '.3ds': 10, '.cia': 9, '.3dsx': 8, '.cci': 7, '.cxi': 6, '.app': 5, '.tmd': 4, '.tik': 4,  # Nintendo 3DS + tickets
            '.gcm': 10, '.tgc': 9, '.iso': 9, '.ciso': 8, '.wia': 8, '.gcz': 7, '.wbfs': 6, '.rvz': 6, '.nkit': 5,  # GameCube/Wii + compressed
            '.xci': 10, '.nsp': 9, '.nro': 8, '.nca': 7, '.nacp': 6, '.nso': 6, '.npdm': 5,  # Nintendo Switch + homebrew

            # Sega formats
            '.md': 10, '.smd': 9, '.gen': 10, '.sg': 8, '.sgd': 8,  # Mega Drive/Genesis + SG-1000
            '.32x': 10, '.32c': 9,  # 32X + cartridge format
            '.sms': 10, '.gg': 10, '.mvs': 9, '.sc': 8, '.sf7000': 7,  # Master System/Game Gear + older systems
            '.chd': 9, '.cue': 8, '.gdi': 8, '.mds': 7, '.ccd': 7, '.cdi': 7, '.mdf': 6, '.nrg': 5, '.toc': 6, '.m3u': 5, '.dat': 4, '.lst': 4,  # Disc formats + playlists

            # Sony formats
            '.pbp': 9, '.cso': 7, '.dax': 6, '.prx': 8,  # PSP + compressed formats
            '.psv': 8, '.psx': 9, '.ecm': 6, '.ape': 5, '.sub': 4, '.psf': 5, '.minipsf': 5, '.psf2': 5, '.minipsf2': 5,  # PlayStation + audio
            '.ps2': 9, '.elf': 8, '.irx': 7, '.cnf': 6,  # PlayStation 2 + homebrew
            '.pkg': 8, '.rap': 7, '.psn': 6, '.p3t': 5,  # PlayStation 3 + themes
            '.vpk': 8, '.suprx': 7, '.skprx': 6,  # PlayStation Vita + homebrew

            # Other console formats
            '.pce': 10, '.sgx': 9, '.hes': 6,  # PC Engine/TurboGrafx-16 + audio
            '.tg16': 9, '.huc': 8,  # TurboGrafx-16
            '.ngp': 10, '.ngc': 9, '.ngpc': 10, '.pocket': 8,  # Neo Geo Pocket + Color
            '.ws': 10, '.wsc': 10, '.pc2': 8,  # WonderSwan + Pocket Challenge
            '.a26': 10, '.a78': 10,  # Atari 2600/7800
            '.lnx': 10, '.lyx': 9, '.o': 7,  # Atari Lynx + homebrew
            '.jag': 10, '.j64': 9, '.abs': 8, '.cof': 7,  # Atari Jaguar + dev formats
            '.int': 10, '.itv': 9,  # Intellivision
            '.col': 10, '.cv': 9,  # ColecoVision
            '.vec': 10, '.gam': 8,  # Vectrex + multicart
            '.o2': 10,  # Odyssey 2
            
            # Microsoft Systems
            '.xbe': 9, '.xex': 8, '.xcp': 7, '.xbx': 6,  # Xbox + Xbox 360
            '.xiso': 8, '.000': 7, '.dvd': 6,  # Xbox ISO formats
            '.god': 7, '.xbla': 6, '.xbx1': 5,  # Xbox Live Arcade + Xbox One
            
            # Additional Handheld Systems
            '.min': 10, '.pokemini': 10,  # Pokemon Mini
            '.vb': 10, '.vboy': 10,  # Virtual Boy
            '.sx1': 10, '.sx2': 10,  # Watara Supervision

            # Computer formats
            '.d64': 10, '.t64': 9, '.prg': 8, '.d81': 9, '.d82': 9, '.g64': 8, '.p64': 8, '.x64': 8, '.p00': 7, '.s64': 7, '.d71': 8, '.d80': 8,  # Commodore + extended
            '.cas': 8, '.wav': 6, '.cdt': 7,  # Cassette formats + Amstrad
            '.tap': 9, '.tzx': 8, '.z80': 9, '.sna': 9, '.scl': 8, '.trd': 8,  # ZX Spectrum + snapshots + disks
            '.adf': 10, '.dms': 8, '.ipf': 9, '.hdf': 8, '.lha': 7, '.lzx': 6,  # Amiga + hard drives + archives
            '.st': 10, '.msa': 8, '.dim': 7, '.stx': 9,  # Atari ST + Pasti format
            
            # Additional Computer Systems
            '.cpc': 9, '.msx': 9, '.oric': 8, '.sam': 8, '.mgt': 8,  # Various computer systems
            '.ti99': 8, '.tifiles': 7,  # TI-99/4A
            '.apple2': 9, '.do': 8, '.po': 8, '.nib': 7, '.woz': 10,  # Apple II + WOZ format (preferred)
            '.m5': 8, '.pzx': 7,  # Sord M5 + PZX tape format
            '.coleco': 8, '.adam': 8,  # Coleco Adam
            '.dragon': 8, '.vdk': 7, '.dmk': 7,  # Dragon + disk formats
            '.coco': 8,  # Color Computer

            # Arcade & MAME
            '.neo': 10, '.aes': 10, '.mvs': 10, '.ngm': 9, '.mame': 8,  # Neo Geo/MAME

            # Development & misc
            '.dol': 9, '.wad': 8, '.forwarder': 7,  # Various homebrew formats + Wii channels
            '.xex': 9, '.atr': 8, '.car': 8,  # Atari formats + cartridge
            '.dsk': 9, '.ima': 8, '.vfd': 7, '.hfe': 6, '.mfm': 5, '.td0': 6,  # Disk images + specialized formats
            '.scummvm': 8, '.gog': 7, '.dos': 6,  # Modern formats
            '.flash': 5, '.swf': 4,  # Flash games (lower priority)
            '.love': 7, '.tic': 6,  # Modern indie formats

            # BIOS & firmware
            '.bios': 8, '.firmware': 8,
            
            # Additional compressed formats
            '.gz': 2, '.bz2': 2,  # Additional compression formats (low priority)
            
            # SNES copier formats
            '.swc': 8, '.fig': 7, '.mgd': 6, '.ufo': 6,  # Super Wild Card, Pro Fighter, Multi Game Doctor, UFO formats
            
            # Save files and states (very low priority for cleanup)
            '.srm': 3, '.sav': 3, '.rtc': 3, '.fla': 3,  # Save RAM, Real Time Clock, Flash saves
            '.st0': 2, '.st1': 2, '.st2': 2, '.st3': 2, '.st4': 2, '.st5': 2, '.st6': 2, '.st7': 2, '.st8': 2, '.st9': 2,  # Generic save states
            '.fc0': 2, '.fc1': 2, '.fc2': 2, '.fc3': 2, '.fc4': 2, '.fc5': 2, '.fc6': 2, '.fc7': 2, '.fc8': 2, '.fc9': 2,  # FCE Ultra save states
            '.zs0': 2, '.zs1': 2, '.zs2': 2, '.zs3': 2, '.zs4': 2, '.zs5': 2, '.zs6': 2, '.zs7': 2, '.zs8': 2, '.zs9': 2,  # ZSNES save states
            '.sm0': 2, '.sm1': 2, '.sm2': 2, '.sm3': 2, '.sm4': 2, '.sm5': 2, '.sm6': 2, '.sm7': 2, '.sm8': 2, '.sm9': 2,  # SNES9x save states
            '.vb0': 2, '.vb1': 2, '.vb2': 2, '.vb3': 2, '.vb4': 2, '.vb5': 2, '.vb6': 2, '.vb7': 2, '.vb8': 2, '.vb9': 2,  # VisualBoy save states
            '.ds0': 2, '.ds1': 2, '.ds2': 2, '.ds3': 2, '.ds4': 2, '.ds5': 2, '.ds6': 2, '.ds7': 2, '.ds8': 2, '.ds9': 2   # DeSmuME save states
        }

        # Comprehensive ROM file extensions
        self.rom_extensions = {
            # Nintendo Systems
            '.nes', '.fds', '.unf', '.unif', '.nsf', '.nsfe',  # NES/Famicom + Audio formats
            '.smc', '.sfc', '.snes', '.swc', '.fig', '.mgd', '.ufo', '.spc', '.bs',  # SNES/Super Famicom + Audio + Satellaview
            '.gb', '.gbc', '.cgb', '.sgb', '.dmg', '.gbx',  # Game Boy series + extended formats
            '.gba', '.agb', '.mb', '.srl',  # Game Boy Advance + multiboot
            '.n64', '.z64', '.v64', '.u64', '.rom64', '.n64rom', '.usa', '.pal', '.jap',  # Nintendo 64 + region variants
            '.nds', '.dsi', '.ids', '.srl', '.nds.gba',  # Nintendo DS/DSi + slot-2 formats
            '.3ds', '.cia', '.3dsx', '.cci', '.cxi', '.app', '.tmd', '.tik',  # Nintendo 3DS + tickets/metadata
            '.gcm', '.gcz', '.iso', '.wbfs', '.rvz', '.nkit', '.ciso', '.wia', '.tgc',  # GameCube/Wii + compressed formats
            '.xci', '.nsp', '.nro', '.nca', '.nacp', '.nso', '.npdm',  # Nintendo Switch + homebrew

            # Sega Systems
            '.md', '.smd', '.gen', '.bin', '.sg', '.sgd', '.rom',  # Mega Drive/Genesis + SG-1000
            '.32x', '.32c',  # 32X + cartridge format
            '.sms', '.gg', '.mvs', '.sc', '.sf7000',  # Master System/Game Gear + SC-3000 + SF-7000
            '.cue', '.chd', '.mds', '.ccd', '.toc', '.m3u',  # Sega CD/Saturn/Dreamcast + playlists
            '.gdi', '.cdi', '.mdf', '.nrg', '.dat', '.lst',  # Dreamcast + TOSEC formats

            # Sony Systems
            '.pbp', '.prx', '.cso', '.dax',  # PSP + compressed formats
            '.psv', '.psx', '.ecm', '.ape', '.sub', '.psf', '.minipsf', '.psf2', '.minipsf2',  # PlayStation + audio
            '.ps2', '.elf', '.irx', '.cnf',  # PlayStation 2 + homebrew + config
            '.pkg', '.rap', '.psn', '.p3t',  # PlayStation 3 + themes
            '.vpk', '.suprx', '.skprx',  # PlayStation Vita + homebrew

            # Other Consoles
            '.pce', '.sgx', '.hes',  # PC Engine/TurboGrafx-16 + audio
            '.tg16', '.huc', '.pce',  # TurboGrafx-16
            '.ngp', '.ngc', '.pocket', '.ngpc',  # Neo Geo Pocket + Color
            '.ws', '.wsc', '.pc2',  # WonderSwan + Pocket Challenge
            '.a26', '.a78', '.bin',  # Atari 2600/7800
            '.lnx', '.lyx', '.o',  # Atari Lynx + homebrew
            '.jag', '.j64', '.rom', '.abs', '.cof', '.bin',  # Atari Jaguar + dev formats
            '.int', '.itv', '.rom', '.bin',  # Intellivision
            '.col', '.cv', '.rom', '.bin',  # ColecoVision
            '.vec', '.gam', '.bin',  # Vectrex + multicart
            '.o2', '.bin', '.rom',  # Odyssey 2
            '.dsk', '.d64', '.t64', '.prg', '.p00', '.s64', '.x64',  # Commodore + extended
            '.cas', '.wav', '.tap', '.cdt',  # Cassette formats + Amstrad
            '.tap', '.tzx', '.z80', '.sna', '.scl', '.trd',  # ZX Spectrum + snapshots + disks
            '.adf', '.dms', '.ipf', '.hdf', '.lha', '.lzx',  # Amiga + hard drives + archives
            '.st', '.msa', '.dim', '.stx',  # Atari ST + Pasti format

            # Arcade & MAME
            '.chd', '.mame', '.zip',  # MAME formats
            '.neo', '.mvs', '.aes', '.ngm',  # Neo Geo formats
            '.zip', '.7z', '.rar', '.gz', '.bz2',  # Compressed formats
            
            # Microsoft Systems
            '.xbe', '.xex', '.xcp', '.xbx',  # Xbox + Xbox 360
            '.xiso', '.000', '.dvd',  # Xbox ISO formats
            '.god', '.xbla', '.xbx1',  # Xbox Live Arcade + Xbox One
            
            # Additional Handheld Systems  
            '.min', '.pokemini',  # Pokemon Mini
            '.vb', '.vboy',  # Virtual Boy
            '.sx1', '.sx2',  # Watara Supervision

            # Generic & Save Files
            '.rom', '.bin', '.img', '.raw',  # Generic ROM formats
            '.srm', '.sav', '.rtc', '.fla',  # Save files (SRAM, etc.)
            '.st0', '.st1', '.st2', '.st3', '.st4', '.st5', '.st6', '.st7', '.st8', '.st9',  # Save states
            '.fc0', '.fc1', '.fc2', '.fc3', '.fc4', '.fc5', '.fc6', '.fc7', '.fc8', '.fc9',  # FCE Ultra states
            '.zs0', '.zs1', '.zs2', '.zs3', '.zs4', '.zs5', '.zs6', '.zs7', '.zs8', '.zs9',  # ZSNES states
            '.sm0', '.sm1', '.sm2', '.sm3', '.sm4', '.sm5', '.sm6', '.sm7', '.sm8', '.sm9',  # SNES9x states
            '.vb0', '.vb1', '.vb2', '.vb3', '.vb4', '.vb5', '.vb6', '.vb7', '.vb8', '.vb9',  # VisualBoy states
            '.ds0', '.ds1', '.ds2', '.ds3', '.ds4', '.ds5', '.ds6', '.ds7', '.ds8', '.ds9',  # DeSmuME states

            # Firmware & BIOS
            '.bios', '.firmware', '.bin', '.rom',

            # Homebrew & Development
            '.elf', '.dol', '.wad', '.forwarder',  # Various homebrew formats + Wii channels
            '.a78', '.a26', '.xex', '.atr', '.cas', '.car',  # Atari formats + cartridge
            '.d81', '.d82', '.g64', '.p64', '.x64', '.d71', '.d80', '.d82',  # Additional Commodore formats
            '.dsk', '.img', '.ima', '.vfd', '.hfe', '.mfm', '.td0',  # Disk images + Kryoflux
            
            # Additional Computer Systems
            '.cpc', '.dsk',  # Amstrad CPC
            '.msx', '.dsk', '.cas',  # MSX systems
            '.oric', '.tap', '.dsk',  # Oric computers
            '.sam', '.dsk', '.mgt',  # SAM Coupe
            '.ti99', '.tifiles',  # TI-99/4A
            '.apple2', '.do', '.po', '.nib', '.woz',  # Apple II + WOZ format
            '.m5', '.pzx',  # Sord M5 + PZX tape format
            '.coleco', '.adam',  # Coleco Adam
            '.dragon', '.vdk', '.dmk',  # Dragon + VDK disk format
            '.coco', '.cas', '.wav',  # Color Computer
            
            # Modern/Emulation formats  
            '.scummvm', '.gog', '.dos',  # ScummVM, GOG, DOS games
            '.flash', '.swf',  # Flash games
            '.love', '.tic',  # LÖVE 2D, TIC-80
        }

    def load_config(self):
        """Load configuration from config.ini if it exists"""
        config_path = Path('config.ini')
        if config_path.exists():
            try:
                config = configparser.ConfigParser()
                config.read('config.ini')

                # Load version handling settings
                if 'VERSION_HANDLING' in config:
                    self.detect_versions = config.getboolean('VERSION_HANDLING', 'detect_versions', fallback=True)
                    self.older_version_action = config.get('VERSION_HANDLING', 'older_version_action', fallback='review')

                    # Validate action setting
                    if self.older_version_action not in ['delete', 'review', 'keep']:
                        print(f"{Colors.YELLOW}Warning: Invalid older_version_action '{self.older_version_action}', using 'review'{Colors.RESET}")
                        self.older_version_action = 'review'

                # Load region priority settings
                if 'REGION_PRIORITY' in config:
                    priority_str = config.get('REGION_PRIORITY', 'priority_order', fallback='USA, World, Europe, Japan')
                    # Parse comma-separated list and clean up whitespace
                    self.region_priority = [region.strip() for region in priority_str.split(',')]
                    # Validate that priority list contains at least one valid region
                    valid_regions = set(self.region_patterns.keys())
                    if not any(region in valid_regions for region in self.region_priority):
                        print(f"{Colors.YELLOW}Warning: Invalid region_priority, using defaults{Colors.RESET}")
                        self.region_priority = ['USA', 'World', 'Europe', 'Japan']

                # Load scanning settings
                if 'SCANNING' in config:
                    self.scan_subfolders = config.getboolean('SCANNING', 'scan_subfolders', fallback=False)

                if 'OUTPUT' in config:
                    self.log_file = config.get('OUTPUT', 'log_file', fallback='rom_cleanup_log.txt')

            except Exception as e:
                print(f"{Colors.YELLOW}Warning: Could not load config.ini: {e}{Colors.RESET}")

    def get_base_filename(self, filename):
        """Remove extension and get normalized base name for duplicate detection"""
        name = Path(filename).stem
        # Remove compression extension if present
        if Path(name).suffix.lower() in ['.7z', '.zip', '.rar']:
            name = Path(name).stem

        # Normalize for duplicate detection by removing region and special tags
        # This helps match games like "Final Fantasy (USA).zip" with "Final Fantasy.nes"
        normalized_name = name

        # Remove region patterns
        for region_patterns in self.region_patterns.values():
            for pattern in region_patterns:
                # Convert pattern to match parentheses/brackets format for removal
                if pattern.startswith(r'\(') and pattern.endswith(r'\)'):
                    # Remove parentheses version: (USA), (Europe), etc.
                    normalized_name = re.sub(pattern, '', normalized_name, flags=re.IGNORECASE)
                elif pattern.startswith(r'\[') and pattern.endswith(r'\]'):
                    # Remove brackets version: [USA], [Europe], etc.
                    normalized_name = re.sub(pattern, '', normalized_name, flags=re.IGNORECASE)

        # Remove special version patterns
        for special_patterns in self.special_patterns.values():
            for pattern in special_patterns:
                normalized_name = re.sub(pattern, '', normalized_name, flags=re.IGNORECASE)

        # Remove version patterns for duplicate detection
        for pattern in self.version_patterns:
            normalized_name = re.sub(pattern, '', normalized_name, flags=re.IGNORECASE)

        # Remove common formatting patterns that might remain
        # Remove multiple spaces, leading/trailing spaces, and empty parentheses/brackets
        normalized_name = re.sub(r'\s*\(\s*\)', '', normalized_name)  # Empty parentheses
        normalized_name = re.sub(r'\s*\[\s*\]', '', normalized_name)  # Empty brackets
        normalized_name = re.sub(r'\s+', ' ', normalized_name)        # Multiple spaces
        normalized_name = normalized_name.strip()                     # Leading/trailing spaces

        return normalized_name

    def has_translation(self, filename):
        """Check if filename contains translation indicators"""
        for pattern in self.translation_patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                return True
        return False

    def is_language_code(self, text):
        """Check if text is a language code rather than a region"""
        for pattern in self.language_code_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def is_casino_game(self, filename):
        """Check if filename indicates a casino/gambling game"""
        # Remove file extension and normalize for checking
        name = Path(filename).stem.lower()

        # First check exclusion patterns - if any match, it's NOT a casino game
        for pattern in self.casino_exclusion_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                return False

        # Then check against casino game patterns
        for pattern in self.casino_game_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                return True
        return False

    def is_adult_game(self, filename):
        """Check if filename indicates an adult/pornographic game"""
        # Remove file extension and normalize for checking
        name = Path(filename).stem.lower()

        # First check exclusion patterns - if any match, it's NOT an adult game
        for pattern in self.adult_exclusion_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                return False

        # Then check against adult game patterns
        for pattern in self.adult_game_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                return True
        return False

    def detect_regions(self, filename):
        """Detect regions from filename"""
        regions = []
        filename_upper = filename.upper()

        # First, check for comma-separated regions in parentheses/brackets
        # Pattern like "(USA, Europe)" or "[Japan, Asia]"
        multi_region_matches = re.findall(r'[\(\[](.*?)[\)\]]', filename)

        for match in multi_region_matches:
            # Split by comma and check each part
            parts = [part.strip() for part in match.split(',')]

            for part in parts:
                # Skip if this part is a language code
                if self.is_language_code(part):
                    continue

                # Check if this part matches any known region
                for region, patterns in self.region_patterns.items():
                    for pattern in patterns:
                        # Create a test string to match against
                        test_string = f'({part})'
                        if re.search(pattern, test_string, re.IGNORECASE):
                            if region not in regions:
                                regions.append(region)
                            break

        # If no regions found from comma-separated check, use original method
        if not regions:
            for region, patterns in self.region_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, filename, re.IGNORECASE):
                        regions.append(region)
                        break

        # Look for unknown region patterns and log them
        if not regions:
            # Check for any parentheses or brackets that might contain regions
            unknown_matches = re.findall(r'\(([^)]+)\)', filename) + re.findall(r'\[([^\]]+)\]', filename)
            for match in unknown_matches:
                # Skip known special version patterns
                is_special = False
                for special_patterns in self.special_patterns.values():
                    for pattern in special_patterns:
                        if re.search(pattern, f'({match})', re.IGNORECASE) or re.search(pattern, f'[{match}]', re.IGNORECASE):
                            is_special = True
                            break
                    if is_special:
                        break

                # Skip if this looks like a multi-region listing we already processed
                if ',' in match:
                    continue

                if not is_special and len(match) <= 20:  # Reasonable length for region codes
                    self.unknown_regions.add(match)

        # Special case: Japanese ROMs with translation tags should be treated as USA
        if self.has_translation(filename):
            # Check if this is a Japanese ROM
            has_japan = 'Japan' in regions

            if has_japan:
                # Remove Japan and add USA instead
                regions = [r for r in regions if r != 'Japan']
                if 'USA' not in regions:
                    regions.append('USA')
            elif not regions or regions == ['Unknown']:
                # If no region detected but has translation, assume it's translated to English (USA)
                regions = ['USA']

        # Default to USA for ROMs with no region tags (most common case)
        if not regions or regions == ['Unknown']:
            regions = ['USA']

        return regions

    def get_primary_region(self, filename):
        """Get the primary region for a ROM based on priority settings.

        For multi-region ROMs like 'Game (USA, Europe).zip', this determines which
        region should be considered 'primary' for duplicate handling and organization.

        Priority is determined by:
        1. First region found that matches the priority list (self.region_priority)
        2. If no regions match priority list, use the first region detected

        Returns: The primary region string (e.g., 'USA', 'Europe', etc.)
        """
        regions = self.detect_regions(filename)

        if not regions:
            return 'USA'  # Default fallback

        # Check if any region matches our priority list, in priority order
        for priority_region in self.region_priority:
            if priority_region in regions:
                return priority_region

        # If no priority match, return first detected region
        return regions[0]

    def detect_special_versions(self, filename):
        """Detect special versions from filename"""
        specials = []
        found_patterns = []

        for special, patterns in self.special_patterns.items():
            for pattern in patterns:
                if re.search(pattern, filename, re.IGNORECASE):
                    specials.append(special)
                    found_patterns.append(pattern)
                    break

        # Look for unknown special version patterns and log them
        unknown_matches = re.findall(r'\(([^)]+)\)', filename) + re.findall(r'\[([^\]]+)\]', filename)
        for match in unknown_matches:
            # Skip if this match was already identified as a known pattern
            is_known = False

            # Check if it's a known special pattern
            for pattern in found_patterns:
                if re.search(pattern, f'({match})', re.IGNORECASE) or re.search(pattern, f'[{match}]', re.IGNORECASE):
                    is_known = True
                    break

            # Check if it's a known region pattern
            if not is_known:
                for region_patterns in self.region_patterns.values():
                    for pattern in region_patterns:
                        if re.search(pattern, f'({match})', re.IGNORECASE) or re.search(pattern, f'[{match}]', re.IGNORECASE):
                            is_known = True
                            break
                    if is_known:
                        break

            # If not known and looks like it could be a special version, log it
            if not is_known and len(match) <= 20:
                # Common patterns that might indicate special versions
                if any(keyword in match.lower() for keyword in ['v', 'rev', 'ver', 'alt', 'final', 'test', 'debug']):
                    self.unknown_specials.add(match)

        return specials

    def detect_version(self, filename):
        """Detect version information from filename and return version tuple for comparison"""
        for pattern in self.version_patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                # Handle different pattern types by checking the pattern string
                if r'(alpha|beta)' in pattern:
                    # Alpha/Beta versions: (alpha 1), (beta 2.1)
                    version_type = groups[0].lower()  # 'alpha' or 'beta'
                    major = int(groups[1]) if len(groups) > 1 and groups[1] else 0
                    minor = int(groups[2]) if len(groups) > 2 and groups[2] else 0
                    # Alpha < Beta < Release, so alpha=0, beta=1, release=2
                    type_priority = 0 if version_type == 'alpha' else 1
                    return (type_priority, major, minor, 0)
                    
                elif r'r(?:ev)?' in pattern or 'revision' in pattern:
                    # Revision versions: (r1), (rev 2)
                    revision = int(groups[0]) if groups[0] else 0
                    return (2, 0, 0, revision)  # Type 2 = release with revision
                    
                else:
                    # Standard versions: (v1.0), (1.1), (2.3.1)
                    major = int(groups[0]) if groups[0] else 0
                    minor = int(groups[1]) if len(groups) > 1 and groups[1] else 0
                    patch = int(groups[2]) if len(groups) > 2 and groups[2] else 0
                    return (2, major, minor, patch)  # Type 2 = release version
                    
        # No version found - assume it's a release version 1.0.0.0
        return (2, 1, 0, 0)

    def compare_versions(self, version1, version2):
        """Compare two version tuples, return True if version1 is newer than version2"""
        # version format: (type_priority, major, minor, patch_or_revision)
        # Higher values indicate newer versions
        return version1 > version2

    def is_rom_file(self, filename):
        """Check if file is a ROM based on extension"""
        return Path(filename).suffix.lower() in self.rom_extensions

    def is_save_state(self, filename):
        """Check if file is a save state or save file"""
        return Path(filename).suffix.lower() in self.save_state_extensions

    def is_multi_file_format(self, filename):
        """Check if file is a multi-file format (CHD, CUE, BIN, etc.)"""
        multi_file_extensions = {'.chd', '.cue', '.bin', '.gdi', '.cdi', '.m3u', '.iso', '.mdf', '.nrg'}
        return Path(filename).suffix.lower() in multi_file_extensions

    def is_folder_based_game(self, folder_path):
        """
        Detect if a folder contains a multi-disc/arcade game.

        Returns True if:
        - Folder has 2+ CHD files (multi-disc game)
        - Folder has 2+ CUE files (multi-disc game)
        - Folder has 1+ CUE + 1+ BIN files (CUE/BIN set)
        - Folder has 1+ CHD + 1+ ZIP files (arcade game with CHD audio/video)
        - Folder has 1+ ISO + related files (ISO-based multi-disc)
        """
        if not folder_path.is_dir():
            return False

        # Count relevant file types
        chd_count = 0
        cue_count = 0
        bin_count = 0
        zip_count = 0
        iso_count = 0
        m3u_count = 0

        try:
            for file_path in folder_path.iterdir():
                if file_path.is_file():
                    ext = file_path.suffix.lower()
                    if ext == '.chd':
                        chd_count += 1
                    elif ext == '.cue':
                        cue_count += 1
                    elif ext == '.bin':
                        bin_count += 1
                    elif ext == '.zip':
                        zip_count += 1
                    elif ext == '.iso':
                        iso_count += 1
                    elif ext == '.m3u':
                        m3u_count += 1
        except (PermissionError, OSError):
            return False

        # Multi-disc CHD game (2+ CHD files)
        if chd_count >= 2:
            return True

        # Multi-disc CUE game (2+ CUE files)
        if cue_count >= 2:
            return True

        # CUE/BIN set (1+ CUE with 1+ BIN)
        if cue_count >= 1 and bin_count >= 1:
            return True

        # Arcade game (CHD + ZIP combo - audio/video + ROM data)
        if chd_count >= 1 and zip_count >= 1:
            return True

        # Multi-disc ISO game (2+ ISO files)
        if iso_count >= 2:
            return True

        # M3U playlist indicates multi-disc set
        if m3u_count >= 1 and (chd_count >= 1 or cue_count >= 1 or iso_count >= 1):
            return True

        return False

    def get_format_preference(self, filename):
        """Get format preference score (higher = better)"""
        ext = Path(filename).suffix.lower()
        return self.format_preference.get(ext, 0)

    def get_best_format_rom(self, rom_files):
        """From a list of ROM files with the same base name, return the best format"""
        if not rom_files:
            return None

        # Filter out save states
        actual_roms = [rom for rom in rom_files if not self.is_save_state(rom.name)]

        if not actual_roms:
            return None

        # Sort by format preference (highest score first)
        best_rom = max(actual_roms, key=lambda rom: self.get_format_preference(rom.name))
        return best_rom

    def get_best_version_rom(self, rom_files):
        """From a list of ROM files with the same base name, return the newest version"""
        if not rom_files:
            return None

        # Filter out save states
        actual_roms = [rom for rom in rom_files if not self.is_save_state(rom.name)]

        if not actual_roms:
            return None

        # Sort by version (newest first), then by format preference as tiebreaker
        best_rom = max(actual_roms, key=lambda rom: (
            self.detect_version(rom.name),
            self.get_format_preference(rom.name)
        ))
        return best_rom

    def group_roms_by_base_and_version(self, rom_files):
        """Group ROMs by base name, separating different versions"""
        groups = {}
        
        for rom_file in rom_files:
            if self.is_save_state(rom_file.name):
                continue
                
            base_name = self.get_base_filename(rom_file.name)
            version = self.detect_version(rom_file.name)
            
            # Create a key that includes both base name and version
            # This allows us to separate different versions of the same game
            version_key = f"{base_name}__v{version[0]}.{version[1]}.{version[2]}.{version[3]}"
            
            if version_key not in groups:
                groups[version_key] = []
            groups[version_key].append(rom_file)
            
        return groups

    def analyze_directory(self, directory_path='.', silent=False):
        """Analyze ROM files in directory"""
        directory_path = Path(directory_path)

        if not directory_path.exists():
            if not silent:
                print(f"Directory {directory_path} does not exist!")
            return

        # Define folders to exclude from scanning (all output folders created by this script)
        # Includes cleanup folders, content folders, and region folders
        excluded_folders = {
            'ROM_DELETE', 'ROM_REVIEW',  # Cleanup folders
            'Adult', 'Casino', 'Beta-Proto',  # Content organization folders
            'Europe', 'Japan', 'Asia', 'Australia', 'Brazil', 'Canada',  # Region folders
            'China', 'France', 'Germany', 'Italy', 'Korea', 'Netherlands',
            'Spain', 'Sweden', 'Taiwan', 'UK', 'World'
        }

        # Collect all ROM files, excluding our cleanup folders
        rom_files = []
        folder_games = []  # NEW: List of folder-based games (multi-disc/arcade)

        if self.scan_subfolders:
            # Recursive scan (current behavior)
            for file_path in directory_path.rglob('*'):
                if file_path.is_file() and self.is_rom_file(file_path.name):
                    # Check if file is in any excluded folder
                    if not any(excluded_folder in file_path.parts for excluded_folder in excluded_folders):
                        rom_files.append(file_path)
        else:
            # Only scan the parent directory (non-recursive)
            for file_path in directory_path.iterdir():
                if file_path.is_file() and self.is_rom_file(file_path.name):
                    rom_files.append(file_path)

        # NEW: Scan for folder-based games (multi-disc/arcade)
        # Only scan immediate subdirectories, not excluded folders
        for item in directory_path.iterdir():
            if item.is_dir() and item.name not in excluded_folders:
                if self.is_folder_based_game(item):
                    folder_games.append(item)

        # Check if we found anything
        if not rom_files and not folder_games:
            if not silent:
                print(f"{Colors.YELLOW}No ROM files or folder-based games found in the directory!{Colors.RESET}")
            return

        # Statistics counters
        region_stats = Counter()
        special_stats = Counter()
        base_names = defaultdict(list)
        casino_games_count = 0
        adult_games_count = 0

        if not silent:
            scan_mode_text = "including subfolders" if self.scan_subfolders else "parent folder only"
            print(f"\n{Colors.CYAN}{'='*70}{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.WHITE}ROM Collection Analysis{Colors.RESET}")
            print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
            print(f"{Colors.WHITE}Scanning directory: {Colors.CYAN}{directory_path.absolute()}{Colors.WHITE} ({scan_mode_text}){Colors.RESET}")
            print(f"{Colors.WHITE}Total ROM files found: {Colors.CYAN}{len(rom_files)}{Colors.RESET}\n")

        # Process each ROM file
        for rom_file in rom_files:
            filename = rom_file.name
            base_name = self.get_base_filename(filename)

            # Get primary region only (for multi-region ROMs, use highest priority)
            primary_region = self.get_primary_region(filename)
            region_stats[primary_region] += 1

            # Detect special versions
            specials = self.detect_special_versions(filename)
            for special in specials:
                special_stats[special] += 1

            # Check for casino games
            if self.is_casino_game(filename):
                casino_games_count += 1

            # Check for adult games
            if self.is_adult_game(filename):
                adult_games_count += 1

            # Track for duplicate detection
            base_names[base_name].append(rom_file)

        # Calculate duplicates for return data
        duplicates = {name: files for name, files in base_names.items() if len(files) > 1}

        # Display results only if not silent
        if not silent:
            # Display region statistics
            print(f"{Colors.BOLD}{Colors.CYAN}REGION STATISTICS{Colors.RESET}")
            print(f"{Colors.CYAN}{'─'*70}{Colors.RESET}")
            if region_stats:
                for region, count in region_stats.most_common():
                    percentage = (count / len(rom_files)) * 100
                    print(f"{Colors.WHITE}{region:15}: {Colors.CYAN}{count:4}{Colors.WHITE} files ({percentage:.1f}%){Colors.RESET}")
            else:
                print(f"{Colors.DIM}No regions detected{Colors.RESET}")

            # Display special version statistics
            print(f"\n{Colors.BOLD}{Colors.CYAN}SPECIAL VERSIONS{Colors.RESET}")
            print(f"{Colors.CYAN}{'─'*70}{Colors.RESET}")
            if special_stats:
                for special, count in special_stats.most_common():
                    print(f"{Colors.WHITE}{special:15}: {Colors.CYAN}{count:4}{Colors.WHITE} files{Colors.RESET}")
            else:
                print(f"{Colors.DIM}No special versions detected{Colors.RESET}")

            # Display casino games
            print(f"\n{Colors.BOLD}{Colors.CYAN}CASINO GAMES{Colors.RESET}")
            print(f"{Colors.CYAN}{'─'*70}{Colors.RESET}")
            if casino_games_count > 0:
                print(f"{Colors.WHITE}Casino/Gambling games: {Colors.CYAN}{casino_games_count}{Colors.WHITE} files{Colors.RESET}")
            else:
                print(f"{Colors.DIM}No casino games detected{Colors.RESET}")

            # Display adult games
            print(f"\n{Colors.BOLD}{Colors.CYAN}ADULT GAMES{Colors.RESET}")
            print(f"{Colors.CYAN}{'─'*70}{Colors.RESET}")
            if adult_games_count > 0:
                print(f"{Colors.WHITE}Adult/Mature content games: {Colors.CYAN}{adult_games_count}{Colors.WHITE} files{Colors.RESET}")
            else:
                print(f"{Colors.DIM}No adult games detected{Colors.RESET}")

            # Display duplicates with format analysis
            print(f"\n{Colors.BOLD}{Colors.CYAN}DUPLICATE DETECTION{Colors.RESET}")
            print(f"{Colors.CYAN}{'─'*70}{Colors.RESET}")
            if duplicates:
                actual_duplicates = {}
                # Filter out duplicates where all files are save states
                for base_name, files in duplicates.items():
                    non_save_files = [f for f in files if not self.is_save_state(f.name)]
                    if len(non_save_files) > 1:  # Only count as duplicate if multiple non-save files
                        actual_duplicates[base_name] = files

                if actual_duplicates:
                    print(f"{Colors.WHITE}Found {Colors.CYAN}{len(actual_duplicates)}{Colors.WHITE} sets of duplicates:{Colors.RESET}")
                    for base_name, files in actual_duplicates.items():
                        non_save_files = [f for f in files if not self.is_save_state(f.name)]
                        save_files = [f for f in files if self.is_save_state(f.name)]

                        print(f"\n'{base_name}' ({len(non_save_files)} ROM copies")
                        if save_files:
                            print(f"                + {len(save_files)} save files):")
                        else:
                            print("):")

                        # Show ROM files with format preference and version info
                        if non_save_files:
                            best_rom = self.get_best_format_rom(files)
                            best_version_rom = self.get_best_version_rom(non_save_files) if self.detect_versions else None
                            
                            for file_path in non_save_files:
                                file_size = file_path.stat().st_size if file_path.exists() else 0
                                regions = ', '.join(self.detect_regions(file_path.name))
                                specials = ', '.join(self.detect_special_versions(file_path.name))
                                preference = self.get_format_preference(file_path.name)

                                extras = f" [Regions: {regions}]" if regions != 'USA' else ""
                                extras += f" [Special: {specials}]" if specials else ""
                                extras += f" [Preference: {preference}]"
                                
                                # Add version information if version detection is enabled
                                if self.detect_versions:
                                    version = self.detect_version(file_path.name)
                                    extras += f" [Version: {version[1]}.{version[2]}.{version[3]}]"

                                best_format_marker = f" {Colors.GREEN}<- BEST FORMAT{Colors.RESET}" if file_path == best_rom else ""
                                best_version_marker = f" {Colors.GREEN}<- NEWEST VERSION{Colors.RESET}" if file_path == best_version_rom and best_version_rom != best_rom else ""
                                print(f"  {Colors.WHITE}ROM: {file_path.name} ({file_size:,} bytes){extras}{best_format_marker}{best_version_marker}{Colors.RESET}")

                        # Show save files separately
                        for file_path in save_files:
                            file_size = file_path.stat().st_size if file_path.exists() else 0
                            print(f"  {Colors.DIM}SAVE: {file_path.name} ({file_size:,} bytes) [Save State/File]{Colors.RESET}")
                else:
                    print(f"{Colors.DIM}No ROM duplicates found (save states excluded){Colors.RESET}")
            else:
                print(f"{Colors.DIM}No duplicates found{Colors.RESET}")

            print(f"\n{Colors.BOLD}{Colors.CYAN}SUMMARY{Colors.RESET}")
            print(f"{Colors.CYAN}{'─'*70}{Colors.RESET}")
            print(f"{Colors.WHITE}Total single-file ROMs: {Colors.CYAN}{len(rom_files)}{Colors.RESET}")
            if folder_games:
                print(f"{Colors.WHITE}Folder-based games: {Colors.CYAN}{len(folder_games)}{Colors.RESET} {Colors.DIM}(multi-disc/arcade){Colors.RESET}")
            print(f"{Colors.WHITE}Unique games: {Colors.CYAN}{len(base_names)}{Colors.RESET}")
            print(f"{Colors.WHITE}Duplicate sets: {Colors.CYAN}{len(duplicates)}{Colors.RESET}")
            print(f"{Colors.WHITE}Regions found: {Colors.CYAN}{len([r for r in region_stats.keys() if r != 'Unknown'])}{Colors.RESET}")
            print(f"{Colors.WHITE}Special versions: {Colors.CYAN}{sum(special_stats.values())}{Colors.RESET}")
            print(f"{Colors.WHITE}Casino games: {Colors.CYAN}{casino_games_count}{Colors.RESET}")
            print(f"{Colors.WHITE}Adult games: {Colors.CYAN}{adult_games_count}{Colors.RESET}")

        # Process folder-based games for statistics (region detection from folder names)
        folder_game_regions = Counter()
        folder_game_specials = Counter()
        for folder_game in folder_games:
            folder_name = folder_game.name
            # Get primary region from folder name
            primary_region = self.get_primary_region(folder_name)
            folder_game_regions[primary_region] += 1

            # Detect special versions from folder name
            specials = self.detect_special_versions(folder_name)
            for special in specials:
                folder_game_specials[special] += 1

        # Return data for interactive mode
        return {
            'rom_files': rom_files,
            'folder_games': folder_games,  # NEW: List of folder-based games
            'folder_game_count': len(folder_games),  # NEW: Count
            'has_folder_games': len(folder_games) > 0,  # NEW: Flag for conditional UI
            'folder_game_regions': folder_game_regions,  # NEW: Region stats for folders
            'folder_game_specials': folder_game_specials,  # NEW: Special version stats for folders
            'region_stats': region_stats,
            'special_stats': special_stats,
            'duplicates': duplicates,
            'base_names': base_names,
            'casino_games_count': casino_games_count,
            'adult_games_count': adult_games_count
        }

    def create_folders(self):
        """Create delete and review folders if they don't exist"""
        folders = ['ROM_DELETE', 'ROM_REVIEW']
        for folder in folders:
            Path(folder).mkdir(exist_ok=True)
        return folders

    def log_unknowns(self):
        """Log unknown regions and specials to file"""
        if self.unknown_regions or self.unknown_specials:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"\n=== ROM Cleanup Log - {timestamp} ===\n")

                if self.unknown_regions:
                    f.write("Unknown Regions Found:\n")
                    for region in sorted(self.unknown_regions):
                        f.write(f"  - {region}\n")

                if self.unknown_specials:
                    f.write("Unknown Special Versions Found:\n")
                    for special in sorted(self.unknown_specials):
                        f.write(f"  - {special}\n")

    def move_files_by_criteria(self, rom_files, criteria_type, criteria_value, destination_folder):
        """Move files matching specific criteria to destination folder"""
        moved_files = []

        for rom_file in rom_files:
            should_move = False

            if criteria_type == 'region':
                regions = self.detect_regions(rom_file.name)
                should_move = criteria_value in regions
            elif criteria_type == 'special':
                specials = self.detect_special_versions(rom_file.name)
                should_move = criteria_value in specials
            elif criteria_type == 'unknown_region':
                regions = self.detect_regions(rom_file.name)
                should_move = 'Unknown' in regions

            if should_move:
                try:
                    destination = Path(destination_folder) / rom_file.name
                    # Handle duplicate names in destination
                    counter = 1
                    original_dest = destination
                    while destination.exists():
                        stem = original_dest.stem
                        suffix = original_dest.suffix
                        destination = original_dest.parent / f"{stem}_{counter}{suffix}"
                        counter += 1

                    shutil.move(str(rom_file), str(destination))
                    moved_files.append(rom_file.name)
                except Exception as e:
                    print(f"{Colors.RED}Error moving {rom_file.name}: {e}{Colors.RESET}")

        return moved_files

    def move_files_keep_main_regions(self, rom_files, destination_folder):
        """Move all ROMs except USA, Europe, Japan, and World to destination folder"""
        keep_regions = {'USA', 'Europe', 'Japan', 'World'}
        moved_files = []

        for rom_file in rom_files:
            regions = self.detect_regions(rom_file.name)

            # If file has no regions from the keep list, move it
            should_move = not any(region in keep_regions for region in regions)

            if should_move:
                try:
                    destination = Path(destination_folder) / rom_file.name
                    # Handle duplicate names in destination
                    counter = 1
                    original_dest = destination
                    while destination.exists():
                        stem = original_dest.stem
                        suffix = original_dest.suffix
                        destination = original_dest.parent / f"{stem}_{counter}{suffix}"
                        counter += 1

                    shutil.move(str(rom_file), str(destination))
                    moved_files.append(rom_file.name)
                except Exception as e:
                    print(f"{Colors.RED}Error moving {rom_file.name}: {e}{Colors.RESET}")

        return moved_files

    def move_all_special_versions(self, rom_files, destination_folder):
        """Move all ROMs with special versions to destination folder"""
        moved_files = []

        for rom_file in rom_files:
            specials = self.detect_special_versions(rom_file.name)

            if specials:  # If file has any special versions
                try:
                    destination = Path(destination_folder) / rom_file.name
                    # Handle duplicate names in destination
                    counter = 1
                    original_dest = destination
                    while destination.exists():
                        stem = original_dest.stem
                        suffix = original_dest.suffix
                        destination = original_dest.parent / f"{stem}_{counter}{suffix}"
                        counter += 1

                    shutil.move(str(rom_file), str(destination))
                    moved_files.append(rom_file.name)
                except Exception as e:
                    print(f"{Colors.RED}Error moving {rom_file.name}: {e}{Colors.RESET}")

        return moved_files

    def move_inferior_format_duplicates(self, rom_files, destination_folder):
        """Move inferior format duplicates to destination folder, keeping only the best format of each ROM"""
        moved_files = []

        # Group files by base name
        base_names = defaultdict(list)
        for rom_file in rom_files:
            base_name = self.get_base_filename(rom_file.name)
            base_names[base_name].append(rom_file)

        # Process each group of duplicates
        for base_name, files in base_names.items():
            # Filter out save states and check if we have actual ROM duplicates
            rom_files_only = [f for f in files if not self.is_save_state(f.name)]

            if len(rom_files_only) > 1:  # Only process if we have multiple ROM files
                # Find the best format ROM
                best_rom = self.get_best_format_rom(files)

                if best_rom:
                    # Move all other ROM files (inferior formats)
                    for rom_file in rom_files_only:
                        if rom_file != best_rom:
                            try:
                                destination = Path(destination_folder) / rom_file.name
                                # Handle duplicate names in destination
                                counter = 1
                                original_dest = destination
                                while destination.exists():
                                    stem = original_dest.stem
                                    suffix = original_dest.suffix
                                    destination = original_dest.parent / f"{stem}_{counter}{suffix}"
                                    counter += 1

                                shutil.move(str(rom_file), str(destination))
                                moved_files.append(rom_file.name)
                            except Exception as e:
                                print(f"{Colors.RED}Error moving {rom_file.name}: {e}{Colors.RESET}")

        return moved_files

    def organize_roms_by_region(self, rom_files, exclude_usa=True):
        """Organize ROMs into region-based subfolders"""
        moved_files = []
        region_folders_created = set()

        # Region folder mapping (using consistent folder names)
        region_folder_mapping = {
            'USA': 'USA',
            'Europe': 'Europe',
            'Japan': 'Japan',
            'Asia': 'Asia',
            'Australia': 'Australia',
            'Brazil': 'Brazil',
            'Canada': 'Canada',
            'China': 'China',
            'France': 'France',
            'Germany': 'Germany',
            'Italy': 'Italy',
            'Korea': 'Korea',
            'Netherlands': 'Netherlands',
            'Spain': 'Spain',
            'Sweden': 'Sweden',
            'Taiwan': 'Taiwan',
            'UK': 'UK',
            'World': 'World'
        }

        for rom_file in rom_files:
            # Get the primary region based on priority settings
            primary_region = self.get_primary_region(rom_file.name)

            # Skip USA ROMs if exclude_usa is True
            if exclude_usa and primary_region == 'USA':
                continue

            # Check if this region has a folder mapping
            target_region = None
            if primary_region in region_folder_mapping:
                target_region = primary_region

            if target_region:
                folder_name = region_folder_mapping[target_region]
                folder_path = Path(folder_name)

                # Create folder if it doesn't exist
                if folder_name not in region_folders_created:
                    folder_path.mkdir(exist_ok=True)
                    region_folders_created.add(folder_name)
                    print(f"{Colors.GREEN}Created folder: {Colors.WHITE}{folder_name}{Colors.RESET}")

                try:
                    destination = folder_path / rom_file.name
                    # Handle duplicate names in destination
                    counter = 1
                    original_dest = destination
                    while destination.exists():
                        stem = original_dest.stem
                        suffix = original_dest.suffix
                        destination = original_dest.parent / f"{stem}_{counter}{suffix}"
                        counter += 1

                    shutil.move(str(rom_file), str(destination))
                    moved_files.append((rom_file.name, folder_name))
                except Exception as e:
                    print(f"{Colors.RED}Error moving {rom_file.name}: {e}{Colors.RESET}")

        return moved_files, region_folders_created

    def organize_folder_games_by_region(self, folder_games, exclude_usa=True):
        """Organize folder-based games (multi-disc/arcade) into region-based subfolders"""
        moved_folders = []
        region_folders_created = set()

        # Region folder mapping (using consistent folder names)
        region_folder_mapping = {
            'USA': 'USA',
            'Europe': 'Europe',
            'Japan': 'Japan',
            'Asia': 'Asia',
            'Australia': 'Australia',
            'Brazil': 'Brazil',
            'Canada': 'Canada',
            'China': 'China',
            'France': 'France',
            'Germany': 'Germany',
            'Italy': 'Italy',
            'Korea': 'Korea',
            'Netherlands': 'Netherlands',
            'Spain': 'Spain',
            'Sweden': 'Sweden',
            'Taiwan': 'Taiwan',
            'UK': 'UK',
            'World': 'World'
        }

        for folder_game in folder_games:
            # Get the primary region from folder name
            primary_region = self.get_primary_region(folder_game.name)

            # Skip USA folders if exclude_usa is True
            if exclude_usa and primary_region == 'USA':
                continue

            # Check if this region has a folder mapping
            target_region = None
            if primary_region in region_folder_mapping:
                target_region = primary_region

            if target_region:
                folder_name = region_folder_mapping[target_region]
                folder_path = Path(folder_name)

                # Create region folder if it doesn't exist
                if folder_name not in region_folders_created:
                    folder_path.mkdir(exist_ok=True)
                    region_folders_created.add(folder_name)
                    print(f"{Colors.GREEN}Created folder: {Colors.WHITE}{folder_name}{Colors.RESET}")

                try:
                    destination = folder_path / folder_game.name
                    # Handle duplicate folder names in destination
                    counter = 1
                    original_dest = destination
                    while destination.exists():
                        destination = original_dest.parent / f"{original_dest.name}_{counter}"
                        counter += 1

                    shutil.move(str(folder_game), str(destination))
                    moved_folders.append((folder_game.name, folder_name))
                    print(f"{Colors.CYAN}Moved folder: {Colors.WHITE}{folder_game.name}{Colors.CYAN} -> {folder_name}/{Colors.RESET}")
                except Exception as e:
                    print(f"{Colors.RED}Error moving folder {folder_game.name}: {e}{Colors.RESET}")

        return moved_folders, region_folders_created

    def move_casino_games(self, rom_files, destination_folder='Casino'):
        """Move casino/gambling games to Casino subfolder"""
        moved_files = []
        casino_folder_created = False

        for rom_file in rom_files:
            if self.is_casino_game(rom_file.name):
                # Create Casino folder if it doesn't exist
                if not casino_folder_created:
                    casino_path = Path(destination_folder)
                    casino_path.mkdir(exist_ok=True)
                    casino_folder_created = True
                    print(f"{Colors.GREEN}Created folder: {Colors.WHITE}{destination_folder}{Colors.RESET}")

                try:
                    destination = Path(destination_folder) / rom_file.name
                    # Handle duplicate names in destination
                    counter = 1
                    original_dest = destination
                    while destination.exists():
                        stem = original_dest.stem
                        suffix = original_dest.suffix
                        destination = original_dest.parent / f"{stem}_{counter}{suffix}"
                        counter += 1

                    shutil.move(str(rom_file), str(destination))
                    moved_files.append(rom_file.name)
                except Exception as e:
                    print(f"{Colors.RED}Error moving {rom_file.name}: {e}{Colors.RESET}")

        return moved_files, casino_folder_created

    def move_adult_games(self, rom_files, destination_folder='Adult'):
        """Move adult/pornographic games to Adult subfolder"""
        moved_files = []
        adult_folder_created = False

        for rom_file in rom_files:
            if self.is_adult_game(rom_file.name):
                # Create Adult folder if it doesn't exist
                if not adult_folder_created:
                    adult_path = Path(destination_folder)
                    adult_path.mkdir(exist_ok=True)
                    adult_folder_created = True
                    print(f"{Colors.GREEN}Created folder: {Colors.WHITE}{destination_folder}{Colors.RESET}")

                try:
                    destination = Path(destination_folder) / rom_file.name
                    # Handle duplicate names in destination
                    counter = 1
                    original_dest = destination
                    while destination.exists():
                        stem = original_dest.stem
                        suffix = original_dest.suffix
                        destination = original_dest.parent / f"{stem}_{counter}{suffix}"
                        counter += 1

                    shutil.move(str(rom_file), str(destination))
                    moved_files.append(rom_file.name)
                except Exception as e:
                    print(f"{Colors.RED}Error moving {rom_file.name}: {e}{Colors.RESET}")

        return moved_files, adult_folder_created

    def move_older_version_duplicates(self, rom_files, destination_folder):
        """Move older version duplicates to destination folder, keeping only the newest version of each ROM"""
        moved_files = []

        # Group files by base name
        base_names = defaultdict(list)
        for rom_file in rom_files:
            base_name = self.get_base_filename(rom_file.name)
            base_names[base_name].append(rom_file)

        # Process each group of potential version duplicates
        for base_name, files in base_names.items():
            # Filter out save states
            rom_files_only = [f for f in files if not self.is_save_state(f.name)]

            if len(rom_files_only) > 1:  # Only process if we have multiple ROM files
                # Check if these are actually different versions
                versions_found = []
                for rom_file in rom_files_only:
                    version = self.detect_version(rom_file.name)
                    versions_found.append(version)
                
                # Only process if we have different versions
                if len(set(versions_found)) > 1:
                    # Find the newest version ROM
                    best_rom = self.get_best_version_rom(rom_files_only)

                    if best_rom:
                        # Move all other ROM files (older versions)
                        for rom_file in rom_files_only:
                            if rom_file != best_rom:
                                try:
                                    destination = Path(destination_folder) / rom_file.name
                                    # Handle duplicate names in destination
                                    counter = 1
                                    original_dest = destination
                                    while destination.exists():
                                        stem = original_dest.stem
                                        suffix = original_dest.suffix
                                        destination = original_dest.parent / f"{stem}_{counter}{suffix}"
                                        counter += 1

                                    shutil.move(str(rom_file), str(destination))
                                    moved_files.append(rom_file.name)
                                    
                                    # Log the version information
                                    old_version = self.detect_version(rom_file.name)
                                    new_version = self.detect_version(best_rom.name)
                                    print(f"  Moved older version: {rom_file.name} (v{old_version[1]}.{old_version[2]}.{old_version[3]}) -> kept {best_rom.name} (v{new_version[1]}.{new_version[2]}.{new_version[3]})")
                                    
                                except Exception as e:
                                    print(f"{Colors.RED}Error moving {rom_file.name}: {e}{Colors.RESET}")

        return moved_files

    def review_folder_contents(self, folder_name):
        """Show contents of a cleanup folder"""
        folder_path = Path(folder_name)

        if not folder_path.exists():
            print(f"Folder '{folder_name}' does not exist.")
            return []

        files = []
        for file_path in folder_path.iterdir():
            if file_path.is_file() and self.is_rom_file(file_path.name):
                files.append(file_path)

        if not files:
            print(f"Folder '{folder_name}' is empty.")
            return files

        print(f"\n=== {folder_name.upper()} CONTENTS ===")
        print(f"{Colors.CYAN}Found {len(files)} ROM files:{Colors.RESET}")

        for i, file_path in enumerate(files, 1):
            file_size = file_path.stat().st_size if file_path.exists() else 0
            regions = ', '.join(self.detect_regions(file_path.name))
            specials = ', '.join(self.detect_special_versions(file_path.name))

            extras = f" [Regions: {regions}]" if regions != 'Unknown' else ""
            extras += f" [Special: {specials}]" if specials else ""

            print(f"{i:3}. {file_path.name} ({file_size:,} bytes){extras}")

        return files

    def empty_folder(self, folder_name):
        """Empty a cleanup folder"""
        folder_path = Path(folder_name)

        if not folder_path.exists():
            print(f"Folder '{folder_name}' does not exist.")
            return False

        files_removed = 0
        for file_path in folder_path.iterdir():
            if file_path.is_file():
                try:
                    file_path.unlink()
                    files_removed += 1
                except Exception as e:
                    print(f"{Colors.RED}Error removing {file_path.name}: {e}{Colors.RESET}")

        if files_removed > 0:
            print(f"{Colors.GREEN}Removed {Colors.CYAN}{files_removed}{Colors.GREEN} files from '{folder_name}' folder.{Colors.RESET}")
            return True
        else:
            print(f"Folder '{folder_name}' was already empty.")
            return False

    def remove_folder(self, folder_name):
        """Remove a cleanup folder entirely"""
        folder_path = Path(folder_name)

        if not folder_path.exists():
            print(f"Folder '{folder_name}' does not exist.")
            return False

        try:
            # Remove all files first
            self.empty_folder(folder_name)
            # Remove the directory
            folder_path.rmdir()
            print(f"{Colors.GREEN}Removed '{folder_name}' folder.{Colors.RESET}")
            return True
        except Exception as e:
            print(f"{Colors.RED}Error removing '{folder_name}' folder: {e}{Colors.RESET}")
            return False

    def remove_script(self):
        """Remove the ROM cleanup script"""
        script_path = Path(__file__)
        try:
            script_path.unlink()
            print(f"ROM cleanup script '{script_path.name}' has been removed.")
            return True
        except Exception as e:
            print(f"{Colors.RED}Error removing script: {e}{Colors.RESET}")
            return False

    def move_beta_proto_games(self, rom_files, destination_folder='Beta-Proto'):
        """Move beta and prototype games to Beta-Proto subfolder"""
        moved_files = []
        folder_created = False

        for rom_file in rom_files:
            specials = self.detect_special_versions(rom_file.name)

            # Check if this ROM has Beta, Proto, or Alpha tags
            if any(special in ['Beta', 'Proto', 'Alpha'] for special in specials):
                # Create Beta-Proto folder if it doesn't exist
                if not folder_created:
                    folder_path = Path(destination_folder)
                    folder_path.mkdir(exist_ok=True)
                    folder_created = True
                    print(f"{Colors.GREEN}Created folder: {Colors.WHITE}{destination_folder}{Colors.RESET}")

                try:
                    destination = Path(destination_folder) / rom_file.name
                    # Handle duplicate names in destination
                    counter = 1
                    original_dest = destination
                    while destination.exists():
                        stem = original_dest.stem
                        suffix = original_dest.suffix
                        destination = original_dest.parent / f"{stem}_{counter}{suffix}"
                        counter += 1

                    shutil.move(str(rom_file), str(destination))
                    moved_files.append(rom_file.name)
                except Exception as e:
                    print(f"{Colors.RED}Error moving {rom_file.name}: {e}{Colors.RESET}")

        return moved_files, folder_created

    def handle_duplicate_regions(self, rom_files):
        """Handle duplicate ROMs by keeping only the highest priority region.

        For example, if you have both "Game (USA).zip" and "Game (Europe).zip",
        this will keep only the USA version (based on region_priority setting) and
        move the Europe version to ROM_DELETE folder.
        """
        moved_files = []
        delete_folder = Path('ROM_DELETE')
        delete_folder.mkdir(exist_ok=True)

        # Group files by base name
        base_names = defaultdict(list)
        for rom_file in rom_files:
            base_name = self.get_base_filename(rom_file.name)
            base_names[base_name].append(rom_file)

        # Process each group of potential duplicates
        for base_name, files in base_names.items():
            # Filter out save states
            rom_files_only = [f for f in files if not self.is_save_state(f.name)]

            if len(rom_files_only) > 1:  # Multiple ROMs of same game
                # Find the ROM with highest priority region
                best_rom = None
                best_priority = float('inf')

                for rom_file in rom_files_only:
                    primary_region = self.get_primary_region(rom_file.name)

                    # Get priority index (lower is better)
                    try:
                        priority = self.region_priority.index(primary_region)
                    except ValueError:
                        # Region not in priority list, assign low priority
                        priority = len(self.region_priority)

                    if priority < best_priority:
                        best_priority = priority
                        best_rom = rom_file

                # Move all other ROM files (lower priority regions)
                if best_rom:
                    for rom_file in rom_files_only:
                        if rom_file != best_rom:
                            try:
                                destination = delete_folder / rom_file.name
                                # Handle duplicate names in destination
                                counter = 1
                                original_dest = destination
                                while destination.exists():
                                    stem = original_dest.stem
                                    suffix = original_dest.suffix
                                    destination = original_dest.parent / f"{stem}_{counter}{suffix}"
                                    counter += 1

                                shutil.move(str(rom_file), str(destination))
                                moved_files.append(rom_file.name)
                            except Exception as e:
                                print(f"{Colors.RED}Error moving {rom_file.name}: {e}{Colors.RESET}")

        return moved_files

    def recommended_cleanup(self, rom_files, folder_games=None):
        """Perform recommended cleanup operations in optimal order.

        This is the main recommended workflow that:
        1. Moves adult games to Adult folder
        2. Moves casino games to Casino folder
        3. Moves beta/proto games to Beta-Proto folder
        4. Organizes non-USA ROMs into region-based folders
        5. Organizes folder-based games by region (if detected)
        6. Handles duplicates by keeping only the highest priority region

        Args:
            rom_files: List of Path objects for single-file ROMs
            folder_games: Optional list of Path objects for folder-based games

        Returns: Summary dictionary with counts and lists of moved files
        """
        if folder_games is None:
            folder_games = []

        has_folder_games = len(folder_games) > 0

        summary = {
            'adult_moved': [],
            'casino_moved': [],
            'beta_proto_moved': [],
            'region_organized': [],
            'folder_games_organized': [],
            'duplicates_removed': []
        }

        # Adjust step count based on whether we have folder games
        total_steps = 6 if has_folder_games else 5

        print(f"\n{Colors.CYAN}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.WHITE}PERFORMING RECOMMENDED CLEANUP{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")

        # Step 1: Move adult games
        print(f"\n{Colors.CYAN}[1/{total_steps}] Moving adult content games to 'Adult' folder...{Colors.RESET}")
        adult_moved, adult_folder_created = self.move_adult_games(rom_files, 'Adult')
        summary['adult_moved'] = adult_moved
        if adult_moved:
            print(f"  {Colors.GREEN}✓ Moved {Colors.CYAN}{len(adult_moved)}{Colors.GREEN} adult game(s){Colors.RESET}")
            # Remove moved files from rom_files list
            rom_files = [f for f in rom_files if f.name not in adult_moved]
        else:
            print(f"  {Colors.GREEN}✓ No adult games found{Colors.RESET}")

        # Step 2: Move casino games
        print(f"\n{Colors.CYAN}[2/{total_steps}] Moving casino/gambling games to 'Casino' folder...{Colors.RESET}")
        casino_moved, casino_folder_created = self.move_casino_games(rom_files, 'Casino')
        summary['casino_moved'] = casino_moved
        if casino_moved:
            print(f"  {Colors.GREEN}✓ Moved {Colors.CYAN}{len(casino_moved)}{Colors.GREEN} casino game(s){Colors.RESET}")
            # Remove moved files from rom_files list
            rom_files = [f for f in rom_files if f.name not in casino_moved]
        else:
            print(f"  {Colors.GREEN}✓ No casino games found{Colors.RESET}")

        # Step 3: Move beta/proto games
        print(f"\n{Colors.CYAN}[3/{total_steps}] Moving beta/prototype games to 'Beta-Proto' folder...{Colors.RESET}")
        beta_proto_moved, beta_proto_folder_created = self.move_beta_proto_games(rom_files, 'Beta-Proto')
        summary['beta_proto_moved'] = beta_proto_moved
        if beta_proto_moved:
            print(f"  {Colors.GREEN}✓ Moved {Colors.CYAN}{len(beta_proto_moved)}{Colors.GREEN} beta/proto game(s){Colors.RESET}")
            # Remove moved files from rom_files list
            rom_files = [f for f in rom_files if f.name not in beta_proto_moved]
        else:
            print(f"  {Colors.GREEN}✓ No beta/proto games found{Colors.RESET}")

        # Step 4: Organize non-USA ROMs by region
        print(f"\n{Colors.CYAN}[4/{total_steps}] Organizing non-USA ROMs into region-based folders...{Colors.RESET}")
        region_organized, regions_created = self.organize_roms_by_region(rom_files, exclude_usa=True)
        summary['region_organized'] = region_organized
        if region_organized:
            print(f"  {Colors.GREEN}✓ Organized {Colors.CYAN}{len(region_organized)}{Colors.GREEN} ROM(s) into {Colors.CYAN}{len(regions_created)}{Colors.GREEN} region folder(s){Colors.RESET}")
            # Remove moved files from rom_files list
            moved_filenames = [filename for filename, folder in region_organized]
            rom_files = [f for f in rom_files if f.name not in moved_filenames]
        else:
            print(f"  {Colors.GREEN}✓ No non-USA ROMs to organize{Colors.RESET}")

        # Step 5: Organize folder-based games (if any detected)
        current_step = 5
        if has_folder_games:
            print(f"\n{Colors.CYAN}[{current_step}/{total_steps}] Organizing folder-based games by region (multi-disc/arcade)...{Colors.RESET}")
            folder_organized, folder_regions_created = self.organize_folder_games_by_region(folder_games, exclude_usa=True)
            summary['folder_games_organized'] = folder_organized
            if folder_organized:
                print(f"  {Colors.GREEN}✓ Organized {Colors.CYAN}{len(folder_organized)}{Colors.GREEN} folder game(s) into {Colors.CYAN}{len(folder_regions_created)}{Colors.GREEN} region folder(s){Colors.RESET}")
            else:
                print(f"  {Colors.GREEN}✓ No non-USA folder games to organize{Colors.RESET}")
            current_step += 1

        # Final step: Handle duplicate regions
        print(f"\n{Colors.CYAN}[{current_step}/{total_steps}] Removing duplicate ROMs (keeping highest priority region)...{Colors.RESET}")
        duplicates_removed = self.handle_duplicate_regions(rom_files)
        summary['duplicates_removed'] = duplicates_removed
        if duplicates_removed:
            print(f"  {Colors.GREEN}✓ Moved {Colors.CYAN}{len(duplicates_removed)}{Colors.GREEN} duplicate(s) to ROM_DELETE folder{Colors.RESET}")
        else:
            print(f"  {Colors.GREEN}✓ No regional duplicates found{Colors.RESET}")

        # Print summary
        print(f"\n{Colors.CYAN}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}RECOMMENDED CLEANUP COMPLETE{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
        total_moved = (len(summary['adult_moved']) + len(summary['casino_moved']) +
                      len(summary['beta_proto_moved']) + len(summary['region_organized']) +
                      len(summary['folder_games_organized']) + len(summary['duplicates_removed']))
        print(f"\n{Colors.BOLD}{Colors.WHITE}Total files processed: {Colors.CYAN}{total_moved}{Colors.RESET}")
        print(f"  {Colors.WHITE}• Adult games: {Colors.CYAN}{len(summary['adult_moved'])}{Colors.RESET}")
        print(f"  {Colors.WHITE}• Casino games: {Colors.CYAN}{len(summary['casino_moved'])}{Colors.RESET}")
        print(f"  {Colors.WHITE}• Beta/Proto games: {Colors.CYAN}{len(summary['beta_proto_moved'])}{Colors.RESET}")
        print(f"  {Colors.WHITE}• Region organized: {Colors.CYAN}{len(summary['region_organized'])}{Colors.RESET}")
        if has_folder_games:
            print(f"  {Colors.WHITE}• Folder games organized: {Colors.CYAN}{len(summary['folder_games_organized'])}{Colors.RESET}")
        print(f"  {Colors.WHITE}• Duplicates removed: {Colors.CYAN}{len(summary['duplicates_removed'])}{Colors.RESET}")
        print()

        return summary

    def show_advanced_options_menu(self, analysis_data):
        """Advanced options menu with all individual cleanup operations"""
        rom_files = analysis_data['rom_files']
        region_stats = analysis_data['region_stats']
        special_stats = analysis_data['special_stats']
        casino_games_count = analysis_data.get('casino_games_count', 0)
        adult_games_count = analysis_data.get('adult_games_count', 0)

        # NEW: Get folder game data
        folder_games = analysis_data.get('folder_games', [])
        has_folder_games = analysis_data.get('has_folder_games', False)
        folder_game_count = analysis_data.get('folder_game_count', 0)

        # Create folders
        delete_folder, review_folder = self.create_folders()

        while True:
            print(f"\n{Colors.CYAN}╔{'═'*68}╗{Colors.RESET}")
            print(f"{Colors.CYAN}║{Colors.BOLD}{Colors.WHITE}{'ADVANCED CLEANUP OPTIONS'.center(68)}{Colors.RESET}{Colors.CYAN}║{Colors.RESET}")
            print(f"{Colors.CYAN}╚{'═'*68}╝{Colors.RESET}")

            # Calculate bulk operation counts dynamically from current files
            non_main_regions_count = 0
            all_specials_count = 0
            inferior_format_count = 0

            # Group files by base name to count duplicates
            base_names = defaultdict(list)
            for rom_file in rom_files:
                base_name = self.get_base_filename(rom_file.name)
                base_names[base_name].append(rom_file)

            for rom_file in rom_files:
                regions = self.detect_regions(rom_file.name)
                specials = self.detect_special_versions(rom_file.name)

                # Count files that would be moved by "keep main regions" operation
                if not any(region in ['USA', 'Europe', 'Japan', 'World'] for region in regions):
                    non_main_regions_count += 1

                # Count files that would be moved by "move all specials" operation
                if specials:
                    all_specials_count += 1

            # Count inferior format duplicates
            for base_name, files in base_names.items():
                rom_files_only = [f for f in files if not self.is_save_state(f.name)]
                if len(rom_files_only) > 1:  # Multiple ROM formats of same game
                    best_rom = self.get_best_format_rom(files)
                    if best_rom:
                        # Count how many would be moved (all except the best)
                        inferior_format_count += len([f for f in rom_files_only if f != best_rom])

            # Count version duplicates (if version detection is enabled)
            older_version_count = 0
            if self.detect_versions:
                # Group ROMs by base name and find version conflicts
                for base_name, files in base_names.items():
                    rom_files_only = [f for f in files if not self.is_save_state(f.name)]
                    if len(rom_files_only) > 1:
                        # Check if these are different versions of the same ROM
                        versions_found = []
                        for rom_file in rom_files_only:
                            version = self.detect_version(rom_file.name)
                            versions_found.append(version)
                        
                        # If we have different versions, count older ones for cleanup
                        if len(set(versions_found)) > 1:  # Different versions detected
                            best_rom = self.get_best_version_rom(rom_files_only)
                            if best_rom:
                                older_version_count += len([f for f in rom_files_only if f != best_rom])

            # Count files that would be organized by region
            region_organization_count = 0
            current_casino_games_count = 0
            current_adult_games_count = 0
            for rom_file in rom_files:
                regions = self.detect_regions(rom_file.name)
                # Count non-USA ROMs that would be organized
                if 'USA' not in regions and any(region in ['Europe', 'Japan', 'Asia', 'Australia', 'Brazil', 'Canada', 'China', 'France', 'Germany', 'Italy', 'Korea', 'Netherlands', 'Spain', 'Sweden', 'Taiwan', 'UK', 'World'] for region in regions):
                    region_organization_count += 1

                # Count casino games
                if self.is_casino_game(rom_file.name):
                    current_casino_games_count += 1

                # Count adult games
                if self.is_adult_game(rom_file.name):
                    current_adult_games_count += 1

            # NEW: Count folder games that would be organized
            folder_organization_count = 0
            if has_folder_games:
                for folder_game in folder_games:
                    primary_region = self.get_primary_region(folder_game.name)
                    if primary_region != 'USA':
                        folder_organization_count += 1

            # Bulk operations
            print(f"\n{Colors.BRIGHT_CYAN}┌{'─'*68}┐{Colors.RESET}")
            print(f"{Colors.BRIGHT_CYAN}│{Colors.BOLD}{Colors.YELLOW} ⚡ BULK OPERATIONS{Colors.RESET}{' '*50}{Colors.BRIGHT_CYAN}│{Colors.RESET}")
            print(f"{Colors.BRIGHT_CYAN}│{Colors.DIM}   Automated operations that process multiple files at once{Colors.RESET}{' '*9}{Colors.BRIGHT_CYAN}│{Colors.RESET}")
            print(f"{Colors.BRIGHT_CYAN}└{'─'*68}┘{Colors.RESET}")
            bulk_options = {}
            option_num = 1

            if region_organization_count > 0:
                print(f"{Colors.BRIGHT_GREEN}{option_num:2}.{Colors.RESET} {Colors.WHITE}Organize non-USA ROMs into region-based folders{Colors.RESET} {Colors.CYAN}({region_organization_count} files){Colors.RESET}")
                print(f"    {Colors.DIM}Sorts Europe, Japan, Asia ROMs into their own folders{Colors.RESET}")
                bulk_options[option_num] = ('bulk_organize_regions', 'organize_by_region')
                option_num += 1

            # NEW: Conditional folder game organization option
            if has_folder_games and folder_organization_count > 0:
                print(f"{Colors.BRIGHT_GREEN}{option_num:2}.{Colors.RESET} {Colors.WHITE}Organize folder-based games by region{Colors.RESET} {Colors.CYAN}({folder_organization_count} folders){Colors.RESET}")
                print(f"    {Colors.DIM}Multi-disc CD games and arcade games (CHD, CUE/BIN sets){Colors.RESET}")
                bulk_options[option_num] = ('bulk_organize_folder_games', 'organize_folder_games')
                option_num += 1

            if current_casino_games_count > 0:
                print(f"{Colors.BRIGHT_GREEN}{option_num:2}.{Colors.RESET} {Colors.WHITE}Move casino/gambling games to Casino folder{Colors.RESET} {Colors.CYAN}({current_casino_games_count} files){Colors.RESET}")
                print(f"    {Colors.DIM}Poker, slots, blackjack, roulette, pachinko games{Colors.RESET}")
                bulk_options[option_num] = ('bulk_casino_games', 'move_casino_games')
                option_num += 1

            if current_adult_games_count > 0:
                print(f"{Colors.BRIGHT_GREEN}{option_num:2}.{Colors.RESET} {Colors.WHITE}Move adult/mature content games to Adult folder{Colors.RESET} {Colors.CYAN}({current_adult_games_count} files){Colors.RESET}")
                print(f"    {Colors.DIM}Games with mature/adult content ratings{Colors.RESET}")
                bulk_options[option_num] = ('bulk_adult_games', 'move_adult_games')
                option_num += 1

            if non_main_regions_count > 0:
                print(f"{Colors.BRIGHT_GREEN}{option_num:2}.{Colors.RESET} {Colors.WHITE}Keep only USA/Europe/Japan/World regions{Colors.RESET} {Colors.CYAN}({non_main_regions_count} files){Colors.RESET}")
                print(f"    {Colors.DIM}Removes less common regions (Asia, Brazil, Korea, etc.){Colors.RESET}")
                bulk_options[option_num] = ('bulk_keep_main', 'keep_main_regions')
                option_num += 1

            if all_specials_count > 0:
                print(f"{Colors.BRIGHT_GREEN}{option_num:2}.{Colors.RESET} {Colors.WHITE}Move all special versions to review folder{Colors.RESET} {Colors.CYAN}({all_specials_count} files){Colors.RESET}")
                print(f"    {Colors.DIM}Beta, Proto, Alpha, Demo, Hack, Translation versions{Colors.RESET}")
                bulk_options[option_num] = ('bulk_specials', 'move_all_specials')
                option_num += 1

            if inferior_format_count > 0:
                print(f"{Colors.BRIGHT_GREEN}{option_num:2}.{Colors.RESET} {Colors.WHITE}Keep only best format of duplicate ROMs{Colors.RESET} {Colors.CYAN}({inferior_format_count} files){Colors.RESET}")
                print(f"    {Colors.DIM}Keeps version with save file, or uncompressed over .zip/.7z{Colors.RESET}")
                bulk_options[option_num] = ('bulk_format_cleanup', 'move_inferior_formats')
                option_num += 1

            if older_version_count > 0 and self.detect_versions:
                action_text = "delete folder" if self.older_version_action == "delete" else "review folder"
                print(f"{Colors.BRIGHT_GREEN}{option_num:2}.{Colors.RESET} {Colors.WHITE}Keep only newest version of duplicate ROMs{Colors.RESET} {Colors.CYAN}({older_version_count} files){Colors.RESET}")
                print(f"    {Colors.DIM}Removes v1.0 if v1.1 exists, keeps latest version only{Colors.RESET}")
                bulk_options[option_num] = ('bulk_version_cleanup', 'move_older_versions')
                option_num += 1

            # Region options
            print(f"\n{Colors.BRIGHT_CYAN}┌{'─'*68}┐{Colors.RESET}")
            print(f"{Colors.BRIGHT_CYAN}│{Colors.BOLD}{Colors.MAGENTA} 🌍 INDIVIDUAL REGIONS{Colors.RESET}{' '*48}{Colors.BRIGHT_CYAN}│{Colors.RESET}")
            print(f"{Colors.BRIGHT_CYAN}│{Colors.DIM}   Target specific regions for removal (USA, Europe, Japan, etc.){Colors.RESET}{' '*4}{Colors.BRIGHT_CYAN}│{Colors.RESET}")
            print(f"{Colors.BRIGHT_CYAN}└{'─'*68}┘{Colors.RESET}")
            region_options = {}

            for region, count in region_stats.most_common():
                if region != 'Unknown' and count > 0:
                    print(f"{Colors.YELLOW}{option_num:2}.{Colors.RESET} Move {Colors.WHITE}{region}{Colors.RESET} ROMs to delete folder {Colors.DIM}({count} files){Colors.RESET}")
                    region_options[option_num] = ('region', region)
                    option_num += 1

            # Unknown regions option
            unknown_count = region_stats.get('Unknown', 0)
            if unknown_count > 0:
                print(f"{Colors.YELLOW}{option_num:2}.{Colors.RESET} Move {Colors.WHITE}Unknown Region{Colors.RESET} ROMs to review folder {Colors.DIM}({unknown_count} files){Colors.RESET}")
                region_options[option_num] = ('unknown_region', 'Unknown')
                option_num += 1

            # Special version options
            print(f"\n{Colors.BRIGHT_CYAN}┌{'─'*68}┐{Colors.RESET}")
            print(f"{Colors.BRIGHT_CYAN}│{Colors.BOLD}{Colors.BLUE} 🎮 INDIVIDUAL SPECIAL VERSIONS{Colors.RESET}{' '*37}{Colors.BRIGHT_CYAN}│{Colors.RESET}")
            print(f"{Colors.BRIGHT_CYAN}│{Colors.DIM}   Non-final releases: Beta, Proto, Demo, Hack, Translation, etc.{Colors.RESET}{' '*3}{Colors.BRIGHT_CYAN}│{Colors.RESET}")
            print(f"{Colors.BRIGHT_CYAN}└{'─'*68}┘{Colors.RESET}")
            special_options = {}

            for special, count in special_stats.most_common():
                if count > 0:
                    print(f"{Colors.YELLOW}{option_num:2}.{Colors.RESET} Move {Colors.WHITE}{special}{Colors.RESET} ROMs to delete folder {Colors.DIM}({count} files){Colors.RESET}")
                    special_options[option_num] = ('special', special)
                    option_num += 1

            # Management options
            print(f"\n{Colors.BRIGHT_CYAN}┌{'─'*68}┐{Colors.RESET}")
            print(f"{Colors.BRIGHT_CYAN}│{Colors.BOLD}{Colors.RED} ⚙️  MANAGEMENT{Colors.RESET}{' '*53}{Colors.BRIGHT_CYAN}│{Colors.RESET}")
            print(f"{Colors.BRIGHT_CYAN}│{Colors.DIM}   Review cleanup folders, toggle settings, and system options{Colors.RESET}{' '*6}{Colors.BRIGHT_CYAN}│{Colors.RESET}")
            print(f"{Colors.BRIGHT_CYAN}└{'─'*68}┘{Colors.RESET}")
            management_options = {}

            # Check if cleanup folders exist and have content
            delete_folder_path = Path('ROM_DELETE')
            review_folder_path = Path('ROM_REVIEW')

            delete_files = []
            review_files = []

            if delete_folder_path.exists():
                delete_files = [f for f in delete_folder_path.iterdir() if f.is_file() and self.is_rom_file(f.name)]

            if review_folder_path.exists():
                review_files = [f for f in review_folder_path.iterdir() if f.is_file() and self.is_rom_file(f.name)]

            if delete_files:
                print(f"{Colors.MAGENTA}{option_num:2}.{Colors.RESET} {Colors.WHITE}Review ROM_DELETE folder{Colors.RESET} {Colors.DIM}({len(delete_files)} files){Colors.RESET}")
                management_options[option_num] = ('review_delete', 'ROM_DELETE')
                option_num += 1

            if review_files:
                print(f"{Colors.MAGENTA}{option_num:2}.{Colors.RESET} {Colors.WHITE}Review ROM_REVIEW folder{Colors.RESET} {Colors.DIM}({len(review_files)} files){Colors.RESET}")
                management_options[option_num] = ('review_review', 'ROM_REVIEW')
                option_num += 1

            if delete_files or review_files:
                print(f"{Colors.MAGENTA}{option_num:2}.{Colors.RESET} {Colors.WHITE}Empty and remove cleanup folders{Colors.RESET}")
                management_options[option_num] = ('cleanup_all', 'all')
                option_num += 1

            print(f"{Colors.RED}{option_num:2}.{Colors.RESET} {Colors.WHITE}Remove this script and exit{Colors.RESET}")
            management_options[option_num] = ('remove_script', 'script')
            option_num += 1

            # Scanning options
            scan_mode_text = f"{Colors.GREEN}subfolders{Colors.RESET}" if self.scan_subfolders else f"{Colors.CYAN}parent folder only{Colors.RESET}"
            print(f"{Colors.MAGENTA}{option_num:2}.{Colors.RESET} {Colors.WHITE}Toggle scanning mode{Colors.RESET} {Colors.DIM}(currently: {scan_mode_text}{Colors.DIM}){Colors.RESET}")
            management_options[option_num] = ('toggle_scan_mode', 'scan')
            option_num += 1

            # Combine all options
            all_options = {**bulk_options, **region_options, **special_options, **management_options}

            # Back to main menu option
            print(f"\n{Colors.BRIGHT_CYAN}┌{'─'*68}┐{Colors.RESET}")
            back_option_num = option_num
            print(f"{Colors.BRIGHT_CYAN}│{Colors.RESET} {Colors.BRIGHT_BLUE}{back_option_num:2}.{Colors.RESET} {Colors.BOLD}{Colors.WHITE}← Back to Main Menu{Colors.RESET}{' '*47}{Colors.BRIGHT_CYAN}│{Colors.RESET}")
            option_num += 1

            # Exit option
            exit_option_num = option_num
            print(f"{Colors.BRIGHT_CYAN}│{Colors.RESET} {Colors.BRIGHT_RED}{exit_option_num:2}.{Colors.RESET} {Colors.BOLD}{Colors.WHITE}Exit Script{Colors.RESET}{' '*54}{Colors.BRIGHT_CYAN}│{Colors.RESET}")
            print(f"{Colors.BRIGHT_CYAN}└{'─'*68}┘{Colors.RESET}")

            print(f"\n{Colors.DIM}Enter multiple numbers separated by spaces (e.g., '1 3 5'), or 'b' for back:{Colors.RESET}")

            try:
                user_input = input(f"{Colors.YELLOW}Select options: {Colors.RESET}").strip().lower()

                if user_input == 'b' or user_input == 'back':
                    print(f"{Colors.CYAN}Returning to main menu...{Colors.RESET}")
                    return  # Return to main menu

                if user_input == 'q' or user_input == 'quit':
                    print("Exiting script!")
                    import sys
                    sys.exit(0)

                if not user_input:
                    print("Please enter at least one option number.")
                    continue

                # Parse multiple selections
                try:
                    choices = [int(x.strip()) for x in user_input.split() if x.strip().isdigit()]
                except ValueError:
                    print("Please enter valid numbers separated by spaces.")
                    continue

                if not choices:
                    print("Please enter valid numbers.")
                    continue

                # Check if back to main menu option was selected
                if back_option_num in choices:
                    print(f"{Colors.CYAN}Returning to main menu...{Colors.RESET}")
                    return  # Return to main menu

                # Check if exit option was selected
                if exit_option_num in choices:
                    print("Exiting script!")
                    import sys
                    sys.exit(0)

                # Validate all choices
                invalid_choices = [choice for choice in choices if choice not in all_options]
                if invalid_choices:
                    print(f"Invalid option(s): {', '.join(map(str, invalid_choices))}")
                    continue

                # Show confirmation of selected operations
                print(f"\n{'='*60}")
                print("SELECTED OPERATIONS:")
                print(f"{'='*60}")

                selected_operations = []
                total_files_to_move = 0

                for choice in choices:
                    criteria_type, criteria_value = all_options[choice]

                    if criteria_type == 'bulk_organize_regions':
                        description = f"Organize non-USA ROMs into region-based folders"
                        count = region_organization_count
                    elif criteria_type == 'bulk_organize_folder_games':
                        description = f"Organize folder-based games by region"
                        count = folder_organization_count
                    elif criteria_type == 'bulk_casino_games':
                        description = f"Move casino/gambling games to Casino folder"
                        count = current_casino_games_count
                    elif criteria_type == 'bulk_adult_games':
                        description = f"Move adult/mature content games to Adult folder"
                        count = current_adult_games_count
                    elif criteria_type == 'bulk_keep_main':
                        description = f"Keep only USA/Europe/Japan/World - move all other regions to delete folder"
                        count = non_main_regions_count
                    elif criteria_type == 'bulk_specials':
                        description = f"Move all special versions to review folder"
                        count = all_specials_count
                    elif criteria_type == 'bulk_format_cleanup':
                        description = f"Keep only best format of duplicate ROMs - move inferior formats to delete folder"
                        count = inferior_format_count
                    elif criteria_type == 'bulk_version_cleanup':
                        action_text = "delete folder" if self.older_version_action == "delete" else "review folder"
                        description = f"Keep only newest version of duplicate ROMs - move older versions to {action_text}"
                        count = older_version_count
                    elif criteria_type == 'region':
                        count = region_stats.get(criteria_value, 0)
                        description = f"Move {criteria_value} ROMs to delete folder"
                    elif criteria_type == 'special':
                        count = special_stats.get(criteria_value, 0)
                        description = f"Move {criteria_value} ROMs to delete folder"
                    elif criteria_type == 'unknown_region':
                        count = region_stats.get('Unknown', 0)
                        description = f"Move Unknown Region ROMs to review folder"
                    elif criteria_type == 'review_delete':
                        count = len([f for f in Path('ROM_DELETE').iterdir() if f.is_file() and self.is_rom_file(f.name)] if Path('ROM_DELETE').exists() else [])
                        description = f"Review ROM_DELETE folder"
                    elif criteria_type == 'review_review':
                        count = len([f for f in Path('ROM_REVIEW').iterdir() if f.is_file() and self.is_rom_file(f.name)] if Path('ROM_REVIEW').exists() else [])
                        description = f"Review ROM_REVIEW folder"
                    elif criteria_type == 'cleanup_all':
                        count = 0  # Management operation, no files moved
                        description = f"Empty and remove cleanup folders"
                    elif criteria_type == 'remove_script':
                        count = 0  # Management operation, no files moved
                        description = f"Remove this script and exit"
                    elif criteria_type == 'toggle_scan_mode':
                        count = 0  # Configuration change, no files moved
                        new_mode = "parent folder only" if self.scan_subfolders else "subfolders"
                        description = f"Toggle scanning mode to {new_mode}"
                    else:
                        count = 0
                        description = f"Unknown operation"

                    # For management operations, always add them (don't check count > 0)
                    if criteria_type in ['review_delete', 'review_review', 'cleanup_all', 'remove_script', 'toggle_scan_mode']:
                        selected_operations.append((choice, criteria_type, criteria_value, description, count))
                        if count > 0:
                            total_files_to_move += count
                            print(f"{choice:2}. {description} ({count} files)")
                        else:
                            print(f"{choice:2}. {description}")
                    elif count > 0:
                        selected_operations.append((choice, criteria_type, criteria_value, description, count))
                        total_files_to_move += count
                        print(f"{choice:2}. {description} ({count} files)")

                if not selected_operations:
                    print("No files to move with selected operations.")
                    continue

                print(f"\nTotal files to be moved: {total_files_to_move}")
                print(f"{'='*60}")

                # Confirmation
                confirm = input(f"{Colors.YELLOW}Proceed with these operations? (y/N): {Colors.RESET}").strip().lower()
                if confirm not in ['y', 'yes']:
                    print("Operations cancelled.")
                    continue

                # Execute all selected operations
                print(f"\nExecuting {len(selected_operations)} operations...")
                for choice, criteria_type, criteria_value, description, count in selected_operations:
                    print(f"\n→ {description}")

                    moved_files = []

                    # Handle bulk operations
                    if criteria_type == 'bulk_organize_regions':
                        organized_files, folders_created = self.organize_roms_by_region(rom_files, exclude_usa=True)
                        moved_files = [filename for filename, folder in organized_files]

                        if organized_files:
                            print(f"  Created {len(folders_created)} region folders: {', '.join(sorted(folders_created))}")
                            # Update stats - remove organized files from region stats
                            for filename, folder in organized_files:
                                # Find and update the region stats
                                for rom_file in rom_files:
                                    if rom_file.name == filename:
                                        regions = self.detect_regions(rom_file.name)
                                        for region in regions:
                                            if region in region_stats and region_stats[region] > 0:
                                                region_stats[region] -= 1
                                        break

                    elif criteria_type == 'bulk_organize_folder_games':
                        # NEW: Handle folder-based game organization
                        organized_folders, folders_created = self.organize_folder_games_by_region(folder_games, exclude_usa=True)
                        moved_files = [folder_name for folder_name, folder in organized_folders]

                        if organized_folders:
                            print(f"  Organized {len(organized_folders)} folder game(s) into {len(folders_created)} region folder(s)")
                            print(f"  Region folders created: {', '.join(sorted(folders_created))}")

                    elif criteria_type == 'bulk_casino_games':
                        moved_files, casino_folder_created = self.move_casino_games(rom_files)

                        if moved_files:
                            print(f"  Created Casino folder with {len(moved_files)} games")

                    elif criteria_type == 'bulk_adult_games':
                        moved_files, adult_folder_created = self.move_adult_games(rom_files)

                        if moved_files:
                            print(f"  Created Adult folder with {len(moved_files)} games")

                    elif criteria_type == 'bulk_keep_main':
                        moved_files = self.move_files_keep_main_regions(rom_files, delete_folder)

                        if moved_files:
                            # Update region stats - zero out all non-main regions
                            for region in list(region_stats.keys()):
                                if region not in ['USA', 'Europe', 'Japan', 'World']:
                                    region_stats[region] = 0

                    elif criteria_type == 'bulk_specials':
                        moved_files = self.move_all_special_versions(rom_files, review_folder)

                        if moved_files:
                            # Zero out all special stats
                            for special in special_stats:
                                special_stats[special] = 0

                    elif criteria_type == 'bulk_format_cleanup':
                        moved_files = self.move_inferior_format_duplicates(rom_files, delete_folder)

                        # No specific stats to update - duplicate counts will be recalculated on rescan

                    elif criteria_type == 'bulk_version_cleanup':
                        target_folder = delete_folder if self.older_version_action == "delete" else review_folder
                        moved_files = self.move_older_version_duplicates(rom_files, target_folder)

                        # No specific stats to update - duplicate counts will be recalculated on rescan

                    elif criteria_type in ['review_delete', 'review_review']:
                        # Handle folder review
                        print(f"\nReviewing {criteria_value} folder contents:")
                        files = self.review_folder_contents(criteria_value)
                        if files:
                            print(f"\nOptions for {criteria_value}:")
                            print("1. Empty this folder")
                            print("2. Remove this folder entirely")
                            print("3. Return to main menu")

                            try:
                                folder_choice = input(f"{Colors.YELLOW}Select option (1-3): {Colors.RESET}").strip()
                                if folder_choice == '1':
                                    self.empty_folder(criteria_value)
                                elif folder_choice == '2':
                                    self.remove_folder(criteria_value)
                                elif folder_choice == '3':
                                    pass
                                else:
                                    print("Invalid choice.")
                            except (ValueError, KeyboardInterrupt):
                                print(f"{Colors.CYAN}Returning to main menu.{Colors.RESET}")

                        moved_files = []  # No files moved in review operation

                    elif criteria_type == 'cleanup_all':
                        # Handle cleanup of all folders
                        print(f"\nCleaning up all folders...")
                        confirm = input(f"{Colors.YELLOW}This will remove all files and folders. Continue? (y/N): {Colors.RESET}").strip().lower()
                        if confirm in ['y', 'yes']:
                            removed_folders = []
                            if Path('ROM_DELETE').exists():
                                if self.remove_folder('ROM_DELETE'):
                                    removed_folders.append('ROM_DELETE')
                            if Path('ROM_REVIEW').exists():
                                if self.remove_folder('ROM_REVIEW'):
                                    removed_folders.append('ROM_REVIEW')

                            if removed_folders:
                                print(f"Removed folders: {', '.join(removed_folders)}")
                            else:
                                print("No folders to remove.")
                        else:
                            print("Cleanup cancelled.")

                        moved_files = []  # No files moved in cleanup operation

                    elif criteria_type == 'remove_script':
                        # Handle script removal
                        print(f"\nRemoving ROM cleanup script...")
                        confirm = input(f"{Colors.YELLOW}This will delete the script file. Continue? (y/N): {Colors.RESET}").strip().lower()
                        if confirm in ['y', 'yes']:
                            if self.remove_script():
                                print("Script removed. Exiting...")
                                return  # Exit the function completely
                        else:
                            print("Script removal cancelled.")

                        moved_files = []  # No files moved in script removal

                    elif criteria_type == 'toggle_scan_mode':
                        # Handle scanning mode toggle
                        old_mode = "subfolders" if self.scan_subfolders else "parent folder only"
                        self.scan_subfolders = not self.scan_subfolders
                        new_mode = "subfolders" if self.scan_subfolders else "parent folder only"
                        print(f"Scanning mode changed from '{old_mode}' to '{new_mode}'")
                        print("The directory will be rescanned with the new setting.")
                        moved_files = []  # No files moved in mode toggle

                    else:
                        # Handle individual region/special operations
                        # Determine destination folder
                        if criteria_type == 'unknown_region':
                            destination = review_folder
                        else:
                            destination = delete_folder

                        moved_files = self.move_files_by_criteria(rom_files, criteria_type, criteria_value, destination)

                        if moved_files:
                            # Update stats
                            if criteria_type == 'region':
                                region_stats[criteria_value] = 0
                            elif criteria_type == 'special':
                                special_stats[criteria_value] = 0
                            elif criteria_type == 'unknown_region':
                                region_stats['Unknown'] = 0

                    # Display moved files
                    if moved_files:
                        print(f"  Moved {len(moved_files)} files")
                        if len(moved_files) <= 5:
                            for filename in moved_files:
                                print(f"    - {filename}")
                        else:
                            for filename in moved_files[:3]:
                                print(f"    - {filename}")
                            print(f"    ... and {len(moved_files) - 3} more files")

                        # Remove moved files from analysis data
                        rom_files[:] = [f for f in rom_files if f.name not in moved_files]
                    else:
                        print(f"  No files found to move")

                print(f"\nAll {len(selected_operations)} operations completed!")

                # Rescan the directory to get updated counts
                print("\nRescanning directory for updated analysis...")
                updated_analysis = self.analyze_directory(directory_path='.', silent=True)

                if updated_analysis and updated_analysis['rom_files']:
                    # Update the analysis data with fresh scan results
                    rom_files[:] = updated_analysis['rom_files']
                    region_stats.clear()
                    region_stats.update(updated_analysis['region_stats'])
                    special_stats.clear()
                    special_stats.update(updated_analysis['special_stats'])

                    remaining_files = len(rom_files)
                    print(f"Rescan complete - {remaining_files} ROM files remaining")
                else:
                    print("Rescan complete - No ROM files remaining!")
                    break

            except ValueError:
                print("Please enter a valid number.")
            except KeyboardInterrupt:
                print("\n\nScript interrupted by user.")
                break

    def interactive_cleanup(self, analysis_data):
        """Main interactive menu with recommended cleanup and advanced options"""
        import sys

        while True:
            rom_files = analysis_data['rom_files']
            region_stats = analysis_data['region_stats']
            special_stats = analysis_data['special_stats']

            # NEW: Get folder game data
            folder_games = analysis_data.get('folder_games', [])
            has_folder_games = analysis_data.get('has_folder_games', False)
            folder_game_count = analysis_data.get('folder_game_count', 0)
            folder_game_regions = analysis_data.get('folder_game_regions', Counter())

            # Dynamically count all categories from current ROM files
            casino_games_count = 0
            adult_games_count = 0
            beta_proto_count = 0
            non_usa_region_count = 0
            duplicate_region_count = 0

            # NEW: Count folder games by region
            folder_non_usa_count = 0
            for folder_game in folder_games:
                primary_region = self.get_primary_region(folder_game.name)
                if primary_region != 'USA':
                    folder_non_usa_count += 1

            # Count casino games, adult games, beta/proto games, and non-USA ROMs
            for rom_file in rom_files:
                # Check for casino games
                if self.is_casino_game(rom_file.name):
                    casino_games_count += 1

                # Check for adult games
                if self.is_adult_game(rom_file.name):
                    adult_games_count += 1

                # Check for beta/proto games
                specials = self.detect_special_versions(rom_file.name)
                if any(special in ['Beta', 'Proto', 'Alpha'] for special in specials):
                    beta_proto_count += 1

                # Check for non-USA ROMs
                regions = self.detect_regions(rom_file.name)
                if 'USA' not in regions and any(region in ['Europe', 'Japan', 'Asia', 'Australia', 'Brazil', 'Canada', 'China', 'France', 'Germany', 'Italy', 'Korea', 'Netherlands', 'Spain', 'Sweden', 'Taiwan', 'UK', 'World'] for region in regions):
                    non_usa_region_count += 1

            # Count potential regional duplicates
            base_names = defaultdict(list)
            for rom_file in rom_files:
                base_name = self.get_base_filename(rom_file.name)
                base_names[base_name].append(rom_file)

            for base_name, files in base_names.items():
                rom_files_only = [f for f in files if not self.is_save_state(f.name)]
                if len(rom_files_only) > 1:
                    # Check if they have different regions
                    regions_found = set()
                    for rom_file in rom_files_only:
                        primary_region = self.get_primary_region(rom_file.name)
                        regions_found.add(primary_region)
                    if len(regions_found) > 1:
                        duplicate_region_count += len(rom_files_only) - 1

            # Display main menu with visual flourishes
            print(f"\n{Colors.CYAN}╔{'═'*68}╗{Colors.RESET}")
            print(f"{Colors.CYAN}║{' '*68}║{Colors.RESET}")
            print(f"{Colors.CYAN}║{Colors.BOLD}{Colors.WHITE}{'ROM CLEANUP TOOL - MAIN MENU'.center(68)}{Colors.RESET}{Colors.CYAN}║{Colors.RESET}")
            print(f"{Colors.CYAN}║{' '*68}║{Colors.RESET}")
            print(f"{Colors.CYAN}╚{'═'*68}╝{Colors.RESET}")

            print(f"\n{Colors.CYAN}┌{'─'*68}┐{Colors.RESET}")
            print(f"{Colors.CYAN}│{Colors.BRIGHT_GREEN} 1. RECOMMENDED CLEANUP [RECOMMENDED]{Colors.RESET}".ljust(78) + f"{Colors.CYAN}│{Colors.RESET}")
            print(f"{Colors.CYAN}├{'─'*68}┤{Colors.RESET}")
            print(f"{Colors.CYAN}│{' '*68}│{Colors.RESET}")
            print(f"{Colors.CYAN}│{Colors.WHITE}   This option performs a comprehensive, automated cleanup:{Colors.RESET}".ljust(78) + f"{Colors.CYAN}│{Colors.RESET}")
            print(f"{Colors.CYAN}│{' '*68}│{Colors.RESET}")

            # Build the action list dynamically based on what's found
            actions = []
            if adult_games_count > 0:
                actions.append(f"{Colors.GREEN}   ✓{Colors.WHITE} Move {Colors.CYAN}{adult_games_count}{Colors.WHITE} adult game(s) to 'Adult' folder{Colors.RESET}")
            if casino_games_count > 0:
                actions.append(f"{Colors.GREEN}   ✓{Colors.WHITE} Move {Colors.CYAN}{casino_games_count}{Colors.WHITE} casino game(s) to 'Casino' folder{Colors.RESET}")
            if beta_proto_count > 0:
                actions.append(f"{Colors.GREEN}   ✓{Colors.WHITE} Move {Colors.CYAN}{beta_proto_count}{Colors.WHITE} beta/proto game(s) to 'Beta-Proto' folder{Colors.RESET}")

            # NEW: Show folder game organization if detected
            if has_folder_games and folder_non_usa_count > 0:
                actions.append(f"{Colors.GREEN}   ✓{Colors.WHITE} Organize {Colors.CYAN}{folder_non_usa_count}{Colors.WHITE} folder game(s) by region {Colors.DIM}(multi-disc/arcade){Colors.RESET}")

            if non_usa_region_count > 0:
                actions.append(f"{Colors.GREEN}   ✓{Colors.WHITE} Organize {Colors.CYAN}{non_usa_region_count}{Colors.WHITE} single-file ROM(s) by region{Colors.RESET}")
            if duplicate_region_count > 0:
                actions.append(f"{Colors.GREEN}   ✓{Colors.WHITE} Remove {Colors.CYAN}{duplicate_region_count}{Colors.WHITE} regional duplicate(s){Colors.RESET}")

            if actions:
                for action in actions:
                    print(f"{Colors.CYAN}│{Colors.RESET}" + action.ljust(78) + f"{Colors.CYAN}│{Colors.RESET}")
            else:
                print(f"{Colors.CYAN}│{Colors.GREEN}   ✓ Your collection is already well organized!{Colors.RESET}".ljust(78) + f"{Colors.CYAN}│{Colors.RESET}")

            print(f"{Colors.CYAN}│{' '*68}│{Colors.RESET}")
            print(f"{Colors.CYAN}│{Colors.DIM}   USA ROMs remain in main directory. Other regions organized.{Colors.RESET}".ljust(78) + f"{Colors.CYAN}│{Colors.RESET}")
            print(f"{Colors.CYAN}│{Colors.DIM}   Priority order: USA > World > Europe > Japan{Colors.RESET}".ljust(78) + f"{Colors.CYAN}│{Colors.RESET}")
            if has_folder_games:
                print(f"{Colors.CYAN}│{Colors.DIM}   Folder games: {folder_game_count} detected (will be organized as folders){Colors.RESET}".ljust(78) + f"{Colors.CYAN}│{Colors.RESET}")
            print(f"{Colors.CYAN}│{' '*68}│{Colors.RESET}")
            print(f"{Colors.CYAN}└{'─'*68}┘{Colors.RESET}")

            print(f"\n{Colors.CYAN}┌{'─'*68}┐{Colors.RESET}")
            print(f"{Colors.CYAN}│{Colors.BRIGHT_BLUE} 2. Advanced Options{Colors.RESET}".ljust(78) + f"{Colors.CYAN}│{Colors.RESET}")
            print(f"{Colors.CYAN}├{'─'*68}┤{Colors.RESET}")
            print(f"{Colors.CYAN}│{Colors.WHITE}   Access individual cleanup operations for fine-grained control.{Colors.RESET}".ljust(78) + f"{Colors.CYAN}│{Colors.RESET}")
            print(f"{Colors.CYAN}│{Colors.WHITE}   Choose specific regions, formats, or versions to manage.{Colors.RESET}".ljust(78) + f"{Colors.CYAN}│{Colors.RESET}")
            print(f"{Colors.CYAN}└{'─'*68}┘{Colors.RESET}")

            print(f"\n{Colors.CYAN}┌{'─'*68}┐{Colors.RESET}")
            print(f"{Colors.CYAN}│{Colors.BRIGHT_RED} 3. Exit{Colors.RESET}".ljust(78) + f"{Colors.CYAN}│{Colors.RESET}")
            print(f"{Colors.CYAN}└{'─'*68}┘{Colors.RESET}")

            print(f"\n{Colors.CYAN}{'═'*70}{Colors.RESET}")
            try:
                choice = input(f"{Colors.YELLOW}Select an option (1-3): {Colors.RESET}").strip()

                if choice == '1':
                    # Run recommended cleanup
                    if not rom_files:
                        print(f"\n{Colors.YELLOW}No ROM files found to clean up!{Colors.RESET}")
                        continue

                    print(f"\n{Colors.CYAN}╔{'═'*68}╗{Colors.RESET}")
                    print(f"{Colors.CYAN}║{Colors.BOLD}{Colors.WHITE}{' RECOMMENDED CLEANUP PREVIEW'.center(68)}{Colors.RESET}{Colors.CYAN}║{Colors.RESET}")
                    print(f"{Colors.CYAN}╚{'═'*68}╝{Colors.RESET}")

                    total_to_process = (adult_games_count + casino_games_count +
                                      beta_proto_count + non_usa_region_count +
                                      folder_non_usa_count + duplicate_region_count)

                    if total_to_process == 0:
                        print(f"\n{Colors.GREEN}Your ROM collection is already well organized!{Colors.RESET}")
                        print(f"{Colors.GREEN}No cleanup actions needed.{Colors.RESET}")
                        input(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
                        continue

                    print(f"\n{Colors.BOLD}{Colors.WHITE}Total files to be processed: {Colors.CYAN}{total_to_process}{Colors.RESET}")
                    print(f"  {Colors.WHITE}• Adult games: {Colors.CYAN}{adult_games_count}{Colors.RESET}")
                    print(f"  {Colors.WHITE}• Casino games: {Colors.CYAN}{casino_games_count}{Colors.RESET}")
                    print(f"  {Colors.WHITE}• Beta/Proto games: {Colors.CYAN}{beta_proto_count}{Colors.RESET}")
                    print(f"  {Colors.WHITE}• Non-USA ROMs to organize: {Colors.CYAN}{non_usa_region_count}{Colors.RESET}")
                    if has_folder_games and folder_non_usa_count > 0:
                        print(f"  {Colors.WHITE}• Folder games to organize: {Colors.CYAN}{folder_non_usa_count}{Colors.RESET}")
                    print(f"  {Colors.WHITE}• Regional duplicates: {Colors.CYAN}{duplicate_region_count}{Colors.RESET}")

                    print(f"\n{Colors.CYAN}{'─'*70}{Colors.RESET}")
                    confirm = input(f"\n{Colors.YELLOW}Proceed with recommended cleanup? (y/N): {Colors.RESET}").strip().lower()

                    if confirm in ['y', 'yes']:
                        # Perform recommended cleanup (pass folder_games if detected)
                        summary = self.recommended_cleanup(rom_files, folder_games=folder_games)

                        # Rescan directory
                        print(f"\n{Colors.CYAN}{'─'*70}{Colors.RESET}")
                        print(f"{Colors.CYAN}Rescanning directory...{Colors.RESET}")
                        updated_analysis = self.analyze_directory(directory_path='.', silent=True)

                        if updated_analysis and updated_analysis['rom_files']:
                            analysis_data.update(updated_analysis)
                            remaining_files = len(updated_analysis['rom_files'])
                            print(f"{Colors.GREEN}Rescan complete - {Colors.CYAN}{remaining_files}{Colors.GREEN} ROM files remaining in main directory{Colors.RESET}")
                        else:
                            print(f"{Colors.GREEN}Rescan complete - No ROM files remaining in main directory!{Colors.RESET}")

                        input(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
                    else:
                        print(f"\n{Colors.YELLOW}Recommended cleanup cancelled.{Colors.RESET}")
                        input(f"{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")

                elif choice == '2':
                    # Show advanced options menu
                    self.show_advanced_options_menu(analysis_data)

                    # After returning from advanced menu, rescan
                    print(f"\n{Colors.CYAN}Rescanning directory...{Colors.RESET}")
                    updated_analysis = self.analyze_directory(directory_path='.', silent=True)
                    if updated_analysis:
                        analysis_data.update(updated_analysis)
                        remaining_files = len(updated_analysis.get('rom_files', []))
                        print(f"{Colors.GREEN}Rescan complete - {Colors.CYAN}{remaining_files}{Colors.GREEN} ROM files remaining{Colors.RESET}")

                elif choice == '3':
                    print(f"\n{Colors.GREEN}Thank you for using ROM Cleanup Tool!{Colors.RESET}")
                    print(f"{Colors.GREEN}Goodbye!{Colors.RESET}")
                    sys.exit(0)

                elif choice.lower() in ['q', 'quit', 'exit']:
                    print(f"\n{Colors.GREEN}Thank you for using ROM Cleanup Tool!{Colors.RESET}")
                    print(f"{Colors.GREEN}Goodbye!{Colors.RESET}")
                    sys.exit(0)

                else:
                    print(f"\n{Colors.RED}Invalid choice. Please select 1, 2, or 3.{Colors.RESET}")
                    input(f"{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")

            except KeyboardInterrupt:
                print(f"\n\n{Colors.YELLOW}Script interrupted by user.{Colors.RESET}")
                print(f"{Colors.GREEN}Goodbye!{Colors.RESET}")
                sys.exit(0)
            except Exception as e:
                print(f"\n{Colors.RED}Error: {e}{Colors.RESET}")
                input(f"{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")


def main():
    parser = argparse.ArgumentParser(description='ROM Cleanup Tool - Organize and clean up ROM collections')
    parser.add_argument('--organize-regions', action='store_true',
                       help='Organize non-USA ROMs into region-based folders and exit')
    parser.add_argument('--include-usa', action='store_true',
                       help='Include USA ROMs when organizing by region (default: exclude USA ROMs)')
    parser.add_argument('--organize-casino', action='store_true',
                       help='Move casino/gambling games to Casino folder and exit')
    parser.add_argument('--organize-adult', action='store_true',
                       help='Move adult/mature content games to Adult folder and exit')
    parser.add_argument('--directory', '-d', type=str, default='.',
                       help='Directory to process (default: current directory)')

    args = parser.parse_args()

    analyzer = ROMAnalyzer()

    # Analyze specified directory
    analysis_data = analyzer.analyze_directory(args.directory)

    if analysis_data and analysis_data['rom_files']:
        # Log any unknown regions/specials
        analyzer.log_unknowns()

        # Handle command line region organization
        if args.organize_regions:
            print(f"{Colors.CYAN}{'═'*70}{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.WHITE}ORGANIZING ROMS BY REGION{Colors.RESET}")
            print(f"{Colors.CYAN}{'═'*70}{Colors.RESET}")
            exclude_usa = not args.include_usa
            if exclude_usa:
                print(f"{Colors.CYAN}Note: USA ROMs will remain in the main directory{Colors.RESET}")
            else:
                print(f"{Colors.CYAN}Note: All ROMs including USA will be organized{Colors.RESET}")

            organized_files, folders_created = analyzer.organize_roms_by_region(
                analysis_data['rom_files'], exclude_usa=exclude_usa)

            if organized_files:
                print(f"\n{Colors.GREEN}Successfully organized {Colors.CYAN}{len(organized_files)}{Colors.GREEN} ROM files{Colors.RESET}")
                print(f"{Colors.GREEN}Created {Colors.CYAN}{len(folders_created)}{Colors.GREEN} region folders: {Colors.WHITE}{', '.join(sorted(folders_created))}{Colors.RESET}")

                # Show summary by folder
                folder_counts = {}
                for filename, folder in organized_files:
                    folder_counts[folder] = folder_counts.get(folder, 0) + 1

                print(f"\n{Colors.WHITE}Files moved per region:{Colors.RESET}")
                for folder, count in sorted(folder_counts.items()):
                    print(f"  {Colors.WHITE}{folder}: {Colors.CYAN}{count}{Colors.WHITE} files{Colors.RESET}")
            else:
                print(f"{Colors.YELLOW}No ROMs found to organize (all ROMs may already be USA region){Colors.RESET}")
        elif args.organize_casino:
            print(f"{Colors.CYAN}{'═'*70}{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.WHITE}ORGANIZING CASINO GAMES{Colors.RESET}")
            print(f"{Colors.CYAN}{'═'*70}{Colors.RESET}")
            print(f"{Colors.CYAN}Moving casino/gambling games to Casino folder...{Colors.RESET}")

            moved_files, casino_folder_created = analyzer.move_casino_games(analysis_data['rom_files'])

            if moved_files:
                print(f"\n{Colors.GREEN}Successfully moved {Colors.CYAN}{len(moved_files)}{Colors.GREEN} casino games to Casino folder{Colors.RESET}")
                if casino_folder_created:
                    print(f"{Colors.GREEN}Created Casino folder{Colors.RESET}")

                # Show moved files
                print(f"\n{Colors.WHITE}Moved casino games:{Colors.RESET}")
                for filename in moved_files[:10]:  # Show first 10 files
                    print(f"  {Colors.WHITE}- {filename}{Colors.RESET}")
                if len(moved_files) > 10:
                    print(f"  {Colors.DIM}... and {len(moved_files) - 10} more files{Colors.RESET}")
            else:
                print(f"{Colors.YELLOW}No casino games found to organize{Colors.RESET}")
        elif args.organize_adult:
            print(f"{Colors.CYAN}{'═'*70}{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.WHITE}ORGANIZING ADULT GAMES{Colors.RESET}")
            print(f"{Colors.CYAN}{'═'*70}{Colors.RESET}")
            print(f"{Colors.CYAN}Moving adult/mature content games to Adult folder...{Colors.RESET}")

            moved_files, adult_folder_created = analyzer.move_adult_games(analysis_data['rom_files'])

            if moved_files:
                print(f"\n{Colors.GREEN}Successfully moved {Colors.CYAN}{len(moved_files)}{Colors.GREEN} adult games to Adult folder{Colors.RESET}")
                if adult_folder_created:
                    print(f"{Colors.GREEN}Created Adult folder{Colors.RESET}")

                # Show moved files
                print(f"\n{Colors.WHITE}Moved adult games:{Colors.RESET}")
                for filename in moved_files[:10]:  # Show first 10 files
                    print(f"  {Colors.WHITE}- {filename}{Colors.RESET}")
                if len(moved_files) > 10:
                    print(f"  {Colors.DIM}... and {len(moved_files) - 10} more files{Colors.RESET}")
            else:
                print(f"{Colors.YELLOW}No adult games found to organize{Colors.RESET}")
        else:
            # Start interactive cleanup
            analyzer.interactive_cleanup(analysis_data)
    else:
        print(f"{Colors.YELLOW}No ROM files found in directory: {args.directory}{Colors.RESET}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.RESET}")
    finally:
        input(f"\n{Colors.YELLOW}Press Enter to exit...{Colors.RESET}")