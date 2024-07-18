import random

from pathlib import Path


from typing import Dict, List, Tuple
from PIL import ImageFont

from PIL.ImageFont import FreeTypeFont

# from watchdog.observers import Observer
# from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from pypinyin import Style, pinyin

resource_dir = Path(__file__).parent / "resources"
fonts_dir = resource_dir / "fonts"
data_dir = resource_dir / "data"
idiom_path = resource_dir / "idioms_p.txt"




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


def get_pinyin_of_n(word: str, which: int) -> List[Tuple[str, str, str]]:
    pys = pinyin(word, style=Style.TONE3, v_to_u=True,heteronym=True)[which]
    # py = p[0]
    results = []
    for py in pys:
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






LEGAL_PHRASES = [
    idiom.strip() for idiom in idiom_path.open("r", encoding="utf-8").readlines()
]
sorted_phrases = dict([i for j in [[(py[0]+py[1],{"":[],"1":[],"2":[],"3":[],"4":[]}) for py in get_pinyin_of_n(idiom[0],0)] for idiom in LEGAL_PHRASES] for i in j])

for idiom in LEGAL_PHRASES:
    for py in get_pinyin_of_n(idiom[0],0):
        sorted_phrases[py[0]+py[1]][py[2]].append(idiom)


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
#             sorted_phrases = dict([i for j in [[(py[0]+py[1],{"":[],"1":[],"2":[],"3":[],"4":[]}) for py in get_pinyin_of_n(idiom[0],0)] for idiom in LEGAL_PHRASES] for i in j])

#             for idiom in LEGAL_PHRASES:
#                 for py in get_pinyin_of_n(idiom[0],0):
#                     sorted_phrases[py[0]+py[1]][py[2]].append(idiom)


# Observer().schedule(
#     LegalPhrasesModifiedHandler(),
#     data_dir,
#     recursive=False,
#     event_filter=FileModifiedEvent,
# )


def legal_idiom(word: str) -> bool:
    return word in LEGAL_PHRASES


def random_idiom() -> str:
    return random.choice(LEGAL_PHRASES)

def legal_patted_idiom(former:str, laster: str, diff_word: bool,homophonic: bool) -> bool:
    """
    判断成语是否符合接龙条件

    Parameters
    ==========
    former: str
        前一个成语
    laster: str
        后一个成语
    diff_word: bool
        异字模式：接龙之字无须一致
    homophonic: bool
        谐音模式：接龙之字可不同音调
    
    """
    return legal_idiom(laster) and legal_idiom(former) and ((((len({i[:2] for i in get_pinyin_of_n(laster[0],0)}.intersection({i[:2] for i in get_pinyin_of_n(former[-1],0)})))>0) if homophonic else (get_pinyin_of_n(laster,0)[0] == get_pinyin_of_n(former,-1)[0])) if diff_word else (former[-1] == laster[0] if homophonic else ((former[-1] == laster[0])and(get_pinyin_of_n(laster,0)[0] == get_pinyin_of_n(former,-1)[0]))))





def get_idiom(idiom: str,diff_word: bool,homophonic: bool) -> str:
    return random.choice(([k for o in [[i for j in sorted_phrases[py[0]+py[1]].values() for i in j] for py in get_pinyin_of_n(idiom[-1],0)] for k in o] if homophonic else sorted_phrases[(py:=get_pinyin_of_n(idiom,-1)[0])[0]+py[1]][py[2]])if diff_word else ([k for o in [[i for j in sorted_phrases[py[0]+py[1]].values() for i in j if i[0] == idiom[-1]] for py in get_pinyin_of_n(idiom[-1],0)] for k in o] if homophonic else (lambda py:[i for i in sorted_phrases[py[0]+py[1]][py[2]] if i[0] == idiom[-1]])(get_pinyin_of_n(idiom,-1)[0])))



def load_font(name: str, fontsize: int) -> FreeTypeFont:
    return ImageFont.truetype(str(fonts_dir / name), fontsize, encoding="utf-8")
