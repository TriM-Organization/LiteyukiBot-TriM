import json
import random
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Tuple, Union, Literal, TypedDict

# from watchdog.observers import Observer
# from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from PIL import ImageFont
from PIL.Image import Image as IMG
from PIL.ImageFont import FreeTypeFont
from pypinyin import Style, pinyin

resource_dir = Path(__file__).parent / "resources"
fonts_dir = resource_dir / "fonts"
data_dir = resource_dir / "data"
handle_common_idiom_path = data_dir / "common_idioms.json"
handle_all_idiom_path = data_dir / "idioms.json"
handle_answer_path = data_dir / "answers.json"


class IdiomEntry(TypedDict):
    """
    成语答案类型
    """

    explanation: str
    pinyin: List[str]


HANDLE_COMMON_PHRASES: List[str] = json.load(
    handle_common_idiom_path.open("r", encoding="utf-8")
)
HANDLE_LEGAL_PHRASES: List[str] = json.load(
    handle_all_idiom_path.open("r", encoding="utf-8")
)
HANDLE_ANSWER_PHRASES: Dict[str, IdiomEntry] = json.load(
    handle_answer_path.open("r", encoding="utf-8")
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

# 答案转换器
# json.dump({ i["word"]:{"explanation":i["explanation"], "pinyin":(lambda x : [i for j in pinyin(x, style=Style.TONE3, v_to_u=True) for i in j])(i["word"])} for i in json.load(open("answers_hard-old.json",encoding="utf-8"))},open("answers.json", "w",encoding="utf-8"), ensure_ascii=False, indent=4)


def legal_idiom(word: str) -> bool:
    return word in HANDLE_LEGAL_PHRASES


def random_idiom(is_hard: bool = False) -> Tuple[str, str]:
    answer = random.choice(HANDLE_LEGAL_PHRASES if is_hard else HANDLE_COMMON_PHRASES)
    return answer, HANDLE_ANSWER_PHRASES[answer]["explanation"]


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


def split_pinyin(py: str) -> Tuple[str, str, str]:
    """
    py: 输入的拼音
    return: 返回一个三元组，分别表示该拼音的声母，韵母，声调
    """

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
    return initial, final, tone


def get_pinyin(
    idiom: str,
) -> List[Tuple[str, str, str]]:
    """
    idiom: 输入的汉字
    return: 返回一个元组，每个元素是一个三元组，分别表示该汉字的声母，韵母，声调
    """
    if idiom_entry := HANDLE_ANSWER_PHRASES.get(idiom):
        pinyin_per_char = idiom_entry["pinyin"]
        if not pinyin_per_char:
            pinyin_per_char = [
                j for i in pinyin(idiom, style=Style.TONE3, v_to_u=True) for j in i
            ]
            idiom_entry["pinyin"] = pinyin_per_char.copy()
            handle_answer_path.open("w", encoding="utf-8").write(
                json.dumps(HANDLE_ANSWER_PHRASES, ensure_ascii=False, indent=4)
            )
    else:
        pinyin_per_char = [
            j for i in pinyin(idiom, style=Style.TONE3, v_to_u=True) for j in i
        ]

    return [split_pinyin(py) for py in pinyin_per_char]


def save_jpg(frame: IMG) -> BytesIO:
    output = BytesIO()
    frame = frame.convert("RGB")
    frame.save(output, format="jpeg")
    return output


def load_font(name: str, fontsize: int) -> FreeTypeFont:
    return ImageFont.truetype(str(fonts_dir / name), fontsize, encoding="utf-8")
