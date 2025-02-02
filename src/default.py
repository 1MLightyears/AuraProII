"""
增强型奥拉 II Python ver.
20200906

默认设置

"""

default_settings={
    "//1":"（字符串）语言",
    "lang":"zh",
    "//2":"（整数）信息文字字号",
    "labelFontSize":4,
    "//3":"（整数）每次获取的最多KM数",
    "KMCounts":3,
    "//4":"（整数）玩家名字搜索结果显示上限，超过将自动进入严格模式",
    "ResultCountLimit":20,
    "//5":"（0~1）窗体透明度",
    "WindowOpacity":0.9,
    "//6":"（整数）历史记录最大数量。为了限制history.json的文件大小和每次花在查找历史记录的时间，该值不宜过大。",
    "historyLimit":99,
    "//7":"（字符串）搜索快捷键",
    "SearchShortCut":"Ctrl+Alt+F",

    "//8":"（字符串）链接文本字色",
    "clURL":"#24ABF2",
    "//9":"（字符串）错误文本字色",
    "clFailed":"#FF0000",
    "//10":"（字符串）提示文本字色",
    "clHint":"#9F9F9F",
    "//11":"（字符串）最高击杀舰船字色",
    "cltopShips":"#FDD835",
    "//12":"（字符串）最高击杀星系字色",
    "cltopSolarSystem":"#FDD835",
    "//13":"（字符串）km字色",
    "clKM":"#FFFFFF",
    "//14":"（字符串）使用舰船字色",
    "clshipType":"#FF8080",
    "//15":"（字符串）主武器类型字色",
    "clweaponType":"#B04BB0",
    "//16":"（字符串）候选搜索结果字色",
    "claddName":"#FC7C21",
    "//17":"（字符串）状态栏字色,该项为rgba四元素元组形式的字符串",
    "clStatusBar":"(127,127,127,127)",

    "//18":"（字符串）工作目录",
    "workingDir":"",
    "//19":"（字符串）字体文件(暂时无法生效)",
    "font_path":{
        "zh":"fonts\\OPPOSans-M.ttf"
    },
    "//20":"（字符串）调试信息保存文件",
    "logFile":"",
    "//21":"（字符串）背景图片路径",
    "backgroundPath":"background1.png"
}