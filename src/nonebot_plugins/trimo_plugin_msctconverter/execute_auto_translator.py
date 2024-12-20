# -*- coding: utf-8 -*-


'''

   Copyright © 2022 Team-Ryoun

   Licensed under the Apache License, Version 2.0 (the "License");
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0


'''

# 自动转换exe指令格式
import uuid



def isfloatable(sth: str) -> bool:
    try:float(sth);return True
    except:return False    


# 极限挑战
# execute @a[name="abc 123"] ~~ ~ execute @s ~9 346 ~-8 detect ^6 ^7 ^2 concrete 18 execute @p[r=3,scores={a=3}] 324 ~324 5 scoreboard players add @s[tag="999 888aasd asd "] QWE_AS 2

# /execute @a~~~/w @s aaa

# execute@s[tag="[]]  666"]~ 1~576detect^6^^66concrete 1 execute @s         [scores={n=0}] ~ ~ ~0.09 execute@s~~~detect 0 0 0 bedrock -1 execute@a [name="999\"]]] jjj\""]~~ ~/execute@s[tag="℃♞\""]~ 32 ~5423 execute@s~~~detect ~~-1~ redstone_block 0 give @s   [scores={name=12..}] command_block 1 1 {"name_tag":["\"a ":"b你 KKK\""]}

# 感谢 尘风、籽怼、邯潘阳(Happy2018New) 为本程序的试错提供了非常有效的支持
# 也感谢 尘风、Happy2018New、Dislink Sforza 为作者提供相关参考意见


def auto_translate(sentence:str):
    '''传入一行旧的execute指令，则将其转换为新格式
    :param sentence: 旧的execute指令
    :return: 新的execute指令
    '''


    if not 'execute' in sentence:
        return sentence
    elif 'run' in sentence:
        return sentence[:sentence.find('run')+4]+auto_translate(sentence[sentence.find('run')+4:])

    # 避免不规范的语法
    sentence = ((__ := str(uuid.uuid4()),strings:=[(r"\"",__),], sentence.replace(r"\"",__)) if r"\"" in sentence else (None,strings:=[],sentence))[2]


    # 如果有字符串包含其中
    # 我们可以看作一个神奇的pattern
    def foreSentence(sent,ptnA,ptnB):
        startcatch = False
        tempstring = ""
        for i in sent:
            if startcatch:
                if i == ptnB:
                    startcatch = False
                    tpp = '{}'.format(tempstring)
                    tag = str(uuid.uuid4())
                    sent = sent.replace(tpp,tag)
                    strings.append((tpp,tag))
                    tempstring = ""
                else:
                    tempstring += i
            else:
                if i == ptnA:
                    startcatch = True
                    # tempstring += i
        # print(ptnA,ptnB,sent)
        return sent
    
    # print(sentence,"\n")
    # 如果选择器的中括号包括空格
    sentence = ((sentence[:sentence.find("@")+2]+sentence[sentence.find('['):]) if (sum(0 if i == ' ' else 1 for i in sentence[sentence.find('@')+2:sentence.find('[')])==0) else sentence).replace("/"," ").lower()


    sentence = foreSentence(foreSentence(foreSentence(sentence,'"','"'),"[","]"),"{","}")
    list_sentence = list(sentence)
    # 如果有神奇的东西在坐标后面，那就神奇了
    for i in range(len(list_sentence)):
        if list_sentence[i] in ('^','~'):
            j = i + 1
            while ((isfloatable("".join(list_sentence[i+1:j+1])))or(list_sentence[i+1] == "-" and isfloatable("".join(list_sentence[i+1:j+2]))))and j <= len(list_sentence):
                j += 1
            # print(j,"\t","".join(sentence[j:]))
            if list_sentence[j] == " " or isfloatable(list_sentence[j]):
                continue
            else:
                list_sentence.insert(j,' ')
    
    sentence = "".join(list_sentence)
    
    def backfor_sentence(a):
        return [(a := a.replace(tag,tpp)) for tpp,tag in strings[::-1]][-1] if strings else a

    # 下面是重点，只有我和老天爷看得懂
    if 'detect' in sentence[:sentence.find("execute",8) if "execute" in sentence[8:] else -1]:
        ___ = [ j for i in [[i,] if sum([isfloatable(_) for _ in i]) else ((["~"+j for j in i[1:].split("~")] if i.startswith("~") else ["~"+j for j in i.split("~")]) if "~" in i else ([i,] if not "^" in i else (["^"+j for j in i[1:].split("^")] if i.startswith("^") else ["^"+j for j in i.split("^")]))) for i in sentence[sentence.find("detect")+6:].strip().split(" ",4)] for j in i ]
        
        ____ = " ".join(___[3:]).split(" ")

        return backfor_sentence('execute as {0} positioned as @s positioned {1} if block {2} {3} {4} at @s positioned {1} run {5}'.format(sentence[sentence.find("execute")+7:(sentence.find("]") if "[" in sentence[:sentence.find("@")+5] else sentence.find("@")+1)+1].strip(),sentence[(sentence.find("]") if "[" in sentence[:sentence.find("@")+3] else sentence.find("@")+1)+1:sentence.find("detect")-1].strip()," ".join(___[0:3]),____[0],____[1],auto_translate(" ".join(____[2:]))))
        
    else:

        ___ = [ j for i in [[i,] if sum([isfloatable(_) for _ in i]) else ((["~"+j for j in i[1:].split("~")] if i.startswith("~") else ["~"+j for j in i.split("~")]) if "~" in i else ([i,] if not "^" in i else (["^"+j for j in i[1:].split("^")] if i.startswith("^") else ["^"+j for j in i.split("^")]))) for i in sentence[(sentence.find("]") if ("]" in sentence)and(sum(0 if i == ' ' else 1 for i in sentence[sentence.find('@')+2:sentence.find('[')])==0) else sentence.find("@")+1)+1:].strip().split(" ",4)] for j in i ]

        return backfor_sentence('execute as {0} positioned as @s positioned {1} at @s positioned {1} run {2}'.format(sentence[sentence.find("execute")+7:(sentence.find("]") if "[" in sentence[:sentence.find("@")+5] else sentence.find("@")+1)+1].strip(), " ".join(___[0:3]),auto_translate(" ".join(___[3:]))))
        
    # 我是一个善良的人，没有用下面这个恶心你们
    # backSentence('execute as {0} positioned as @s positioned {1} if block {2} {3} {4} at @s positioned {1} run {5}'.format(sentence[sentence.find("execute")+7:(sentence.find("]") if "[" in sentence[:sentence.find("@")+5] else sentence.find("@")+1)+1].strip(),sentence[(sentence.find("]") if "[" in sentence[:sentence.find("@")+3] else sentence.find("@")+1)+1:sentence.find("detect")-1].strip()," ".join([ j for i in [[i,] if sum([isfloatable(_) for _ in i]) else ((["~"+j for j in i[1:].split("~")] if i.startswith("~") else ["~"+j for j in i.split("~")]) if "~" in i else ([i,] if not "^" in i else (["^"+j for j in i[1:].split("^")] if i.startswith("^") else ["^"+j for j in i.split("^")]))) for i in sentence[sentence.find("detect")+6:].strip().split(" ",4)] for j in i ][0:3])," ".join([ j for i in [[i,] if sum([isfloatable(_) for _ in i]) else ((["~"+j for j in i[1:].split("~")] if i.startswith("~") else ["~"+j for j in i.split("~")]) if "~" in i else ([i,] if not "^" in i else (["^"+j for j in i[1:].split("^")] if i.startswith("^") else ["^"+j for j in i.split("^")]))) for i in sentence[sentence.find("detect")+6:].strip().split(" ",4)] for j in i ][3:]).split(" ")[0]," ".join([ j for i in [[i,] if sum([isfloatable(_) for _ in i]) else ((["~"+j for j in i[1:].split("~")] if i.startswith("~") else ["~"+j for j in i.split("~")]) if "~" in i else ([i,] if not "^" in i else (["^"+j for j in i[1:].split("^")] if i.startswith("^") else ["^"+j for j in i.split("^")]))) for i in sentence[sentence.find("detect")+6:].strip().split(" ",4)] for j in i ][3:]).split(" ")[1],autoTranslate(" ".join(" ".join([ j for i in [[i,] if sum([isfloatable(_) for _ in i]) else ((["~"+j for j in i[1:].split("~")] if i.startswith("~") else ["~"+j for j in i.split("~")]) if "~" in i else ([i,] if not "^" in i else (["^"+j for j in i[1:].split("^")] if i.startswith("^") else ["^"+j for j in i.split("^")]))) for i in sentence[sentence.find("detect")+6:].strip().split(" ",4)] for j in i ][3:]).split(" ")[2:])))) if 'detect' in sentence[:sentence.find("execute",8) if "execute" in sentence[8:] else -1] else backSentence('execute as {0} positioned as @s positioned {1} at @s positioned {1} run {2}'.format(sentence[sentence.find("execute")+7:(sentence.find("]") if "[" in sentence[:sentence.find("@")+5] else sentence.find("@")+1)+1].strip(), " ".join([ j for i in [[i,] if sum([isfloatable(_) for _ in i]) else ((["~"+j for j in i[1:].split("~")] if i.startswith("~") else ["~"+j for j in i.split("~")]) if "~" in i else ([i,] if not "^" in i else (["^"+j for j in i[1:].split("^")] if i.startswith("^") else ["^"+j for j in i.split("^")]))) for i in sentence[(sentence.find("]") if ("]" in sentence)and(sum(0 if i == ' ' else 1 for i in sentence[sentence.find('@')+2:sentence.find('[')])==0) else sentence.find("@")+1)+1:].strip().split(" ",4)] for j in i ][0:3]),autoTranslate(" ".join([ j for i in [[i,] if sum([isfloatable(_) for _ in i]) else ((["~"+j for j in i[1:].split("~")] if i.startswith("~") else ["~"+j for j in i.split("~")]) if "~" in i else ([i,] if not "^" in i else (["^"+j for j in i[1:].split("^")] if i.startswith("^") else ["^"+j for j in i.split("^")]))) for i in sentence[(sentence.find("]") if ("]" in sentence)and(sum(0 if i == ' ' else 1 for i in sentence[sentence.find('@')+2:sentence.find('[')])==0) else sentence.find("@")+1)+1:].strip().split(" ",4)] for j in i ][3:]))))



        
def __main__():
    '''主函数
    '''
    while True:
        try:
            sentence = input()
            print()
            print(auto_translate(sentence))
            print("="*10)
        except EOFError:
            break
        # except Exception as e:
        #     print(e)
        #     continue


if __name__ == "__main__":
    __main__()

# 没写完，我也不知道咋写，但是总得写不是吗