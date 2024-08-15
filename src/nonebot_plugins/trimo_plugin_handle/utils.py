import json
import random
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Tuple

# from watchdog.observers import Observer
# from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from PIL import ImageFont
from PIL.Image import Image as IMG
from PIL.ImageFont import FreeTypeFont
from pypinyin import Style, pinyin

resource_dir = Path(__file__).parent / "resources"
fonts_dir = resource_dir / "fonts"
data_dir = resource_dir / "data"
idiom_path = data_dir / "idioms.txt"
answer_path = data_dir / "answers.json"
answer_hard_path = data_dir / "answers_hard.json"


LEGAL_PHRASES = [
    idiom.strip() for idiom in idiom_path.open("r", encoding="utf-8").readlines()
]
ANSWER_PHRASES: List[Dict[str, str]] = json.load(
    answer_path.open("r", encoding="utf-8")
)
HARD_ANSWER_PHRASES: List[Dict[str, str]] = json.load(
    answer_hard_path.open("r", encoding="utf-8")
)

# class LegalPhrasesModifiedHandler(FileSystemEventHandler):
#     """
#     Handler for resource file changes
#     """

#     def on_modified(self, event):
#         print(f"{event.src_path} modified, reloading resource...")
#         if "idioms.txt" in event.src_path:
#             global LEGAL_PHRASES
#             LEGAL_PHRASES = [
#                 idiom.strip()
#                 for idiom in idiom_path.open("r", encoding="utf-8").readlines()
#             ]
#         elif "answers.json" in event.src_path:
#             global ANSWER_PHRASES
#             ANSWER_PHRASES = json.load(
#                 answer_path.open("r", encoding="utf-8")
#             )


# Observer().schedule(
#     LegalPhrasesModifiedHandler(),
#     data_dir,
#     recursive=False,
#     event_filter=FileModifiedEvent,
# )


def legal_idiom(word: str) -> bool:
    return word in LEGAL_PHRASES


def random_idiom(is_hard: bool = False) -> Tuple[str, str]:
    answer = random.choice(HARD_ANSWER_PHRASES if is_hard else ANSWER_PHRASES)
    return answer["word"], answer["explanation"]


# fmt: off
# 声母
INITIALS = [
    "zh", "z", "y", "x", "w", "t", "sh", "s", "r", "q", "p",
    "n", "m", "l", "k", "j", "h", "g", "f", "d", "ch", "c", "b"
]
# 韵母
FINALS = [
    "ün", "üe", "üan", "ü", "uo", "un", "ui", "ue", "uang",
    "uan", "uai","ua", "ou", "iu", "iong", "ong", "io", "ing",
    "in", "ie", "iao", "iang", "ian", "ia", "er", "eng", "en",
    "ei", "ao", "ang", "an", "ai", "u", "o", "i", "e", "a"
]
# fmt: on


def get_pinyin(idiom: str) -> List[Tuple[str, str, str]]:
    pys = pinyin(idiom, style=Style.TONE3, v_to_u=True)
    results = []
    for p in pys:
        py = p[0]
        if py[-1].isdigit():
            tone = py[-1]
            py = py[:-1]
        else:
            tone = ""
        initial = ""
        for i in INITIALS:
            if py.startswith(i):
                initial = i
                break
        final = ""
        for f in FINALS:
            if py.endswith(f):
                final = f
                break
        results.append((initial, final, tone))  # 声母，韵母，声调
    return results


def save_jpg(frame: IMG) -> BytesIO:
    output = BytesIO()
    frame = frame.convert("RGB")
    frame.save(output, format="jpeg")
    return output


def load_font(name: str, fontsize: int) -> FreeTypeFont:
    return ImageFont.truetype(str(fonts_dir / name), fontsize, encoding="utf-8")