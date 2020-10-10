"""
增强型奥拉II

定义了初始化，设定，类型，通用工具函数。
"""
from json import load,dump
from os.path import exists

from default import default_settings

#设置
settings=None
#历史记录
history = {}
#版本
version="v0.1.1"

def LoadFile(file_name:str,default={}):
    """
    读取文件。
    file_name(str):文件路径名
    """
    o={}
    if not exists(file_name):
        log("没有找到文件" + file_name,level="error")
        return default
    with open(file_name, "r",encoding="utf-8") as f:
        try:
            o = load(f)
        except:
            o = {}
    return o

def SaveFile(content, file_name: str):
    """
    存储文件。
    content(Any):写到文件内的内容。
    file_name(str):文件路径名。
    """
    with open(file_name, 'w', encoding="utf-8") as f:
        dump(content, f, ensure_ascii=False, indent=4, separators=(",", ":"))

def getNamebyID(ID):
    """
    从typesID.json中获取ID对应的物品名称（自动选取翻译）。
    ID(int):物品ID
    """
    global typeID, settings
    if isinstance(ID, int):
        ID=str(ID)
    ret = typeID[ID]["name"]
    if settings["lang"] in ret:
        return ret[settings["lang"]]
    else:
        return ret["en"]

def SerializeMsgEntry(d):
    """
    递归抽取所有的MsgEntry。
    """
    ret = []
    if isinstance(d, dict):
        d=d.values()
    for i in d:
        if (isinstance(i, dict)) or (isinstance(i, list)):
            ret += SerializeMsgEntry(i)
        elif isinstance(i, TMsgEntry):
            ret.append(i)
    return ret

def Valuable(v: int):
    """
    将数字金额转换成k,m,b,t的形式。
    v(int):金额。
    """
    char_list=" kmbt"
    for i in range(len(char_list)):
        if v < 10 ** (3*i+3):
            return str(int(round(v / 10 ** (3*i)))) + char_list[i]

def Existsin(d, *args):
    """
    查询某键是否在某字典/列表中。
    d(list or dict):要搜索的字典/列表。
    *args(str):键值路径。
    """
    if not (isinstance(d, list) or isinstance(d, dict)):
        return False
    index=args[0]
    if index in d:
        args = args[1:]
        if args != ():
            return Existsin(d[index], *args)
        else:
            return True
    else:
        return False

def RGB2Hex(rgb):
    """
    把十进制rgb元组转化为html标签的十六进制color值
    rgb(tuple,list):十进制颜色值
    """
    strs = '#'
    for i in rgb:
        num = int(i)#将str转int
        #将R、G、B分别转化为16进制拼接转换并大写
        strs += str(hex(num))[-2:].replace('x','0').upper()
    return strs

def MDStyleStr(color=None, font_size=None):
    """
    创建Html格式的字体标签用于MarkDown
    color(tuple,str):十进制RGB颜色(tuple)或十六进制颜色#******
    font_size(int,str):字号
    """
    ret="<"

    if (color or font_size):
        ret+="font"
    if color != None:
        if isinstance(color, tuple):
            color = RGB2Hex(color)
    ret += (" color="+color) if color else ""

    if font_size != None:
        font_size = str(font_size)
    ret+=(" size="+font_size) if font_size else ""

    ret += ">"

    return ret

def log(text: str = "",level:str="info",end="\n"):
    """
    记录日志。
    text(str):要添加进日志的内容。
    """
    try:
        if settings["logFile"] != "":
            with open(settings["logFile"], "a", encoding="utf-8") as f:
                f.write(level + ':' + text + end)
    except:
        print("无法记录log")

class TMsgEntry():
    """
    信息条目。
    每一个信息条目应当可以被一个TMsgLabel显示。
    由kmsearch获取的信息应被封装在TMsgEntry组成的字典中被传给MainForm。
    text(str):要显示的内容
    style_str(str):字体格式。
               由于setStyleSheet()函数没有效果，因此换成Markdown渲染器
    OnClick(func):单击事件
    """
    def __init__(self,text='',style_str='',left=10,top=50,ClickEvent=None,ClickArgs=None):
        self.text = text
        self.style_str = style_str
        self.ClickEvent = ClickEvent
        self.ClickArgs = ClickArgs
        self.left = left
        self.top = top

if __name__ == "Base":
    #init
    settings = default_settings

    #载入数据文件
    #载入settings
    if exists("settings.json"):
        p = "settings.json"
    else:
        p = "..\\settings.json"
    if exists(p):
        r = LoadFile(p)
        if r != {}:
            log("settings加载完成")
            settings.update(r)
        else:
            log("设置文件出现错误，使用默认设置")
    SaveFile(settings,"settings.json")
    history = LoadFile(settings["workingDir"] + "history.json")
    log("history加载完成")
    l = len(history.keys())
    while l > settings["historyLimit"]:
        history.popitem()

    #载入typeIDs.json
    log("typeID加载完成")
    typeID = LoadFile(settings["workingDir"] + "typeIDs.json")

    #导入字体
    font_path = settings["font_path"]