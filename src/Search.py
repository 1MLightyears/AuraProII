"""
增强型奥拉II

搜索并统计character的数据

"""

# MainForm.py中的一次完整的搜索流程应当是：
# Step 1:通过ESI api获取角色ID(SearchName)
# Step 2:通过zkb api获取角色统计信息
# Step 3:通过zkb api获取角色KM-hash表
# Step 4:对前n个km进行分析(SearchKM)
# Step 5:得到的json只给出id，把characterID翻译为玩家角色名
# Step 6:返回

import requests as rq
from time import sleep
from json import loads, dump

from PyQt5.QtCore import QMutex

from Base import settings, getNamebyID, TMsgEntry, Valuable, history, RGB2Hex, MDStyleStr, SaveFile, log

MutSearchName = QMutex()
MutSearchKM = QMutex()

def SearchName(name: str = '',ID:int=-1,is_strict=False):
    """
    获取角色ID与zkb统计信息。
    name(str):角色名
    ID(int):如果已有角色ID则跳过搜索characterID的步骤
    is_strict(bool):严格模式，只搜索与name完全一致的角色名
    """
    global MutSearchName
    MutSearchName.lock()
    Msg = {}
    log("SearchName:name={name},ID={ID},is_strict={is_strict}".format(name=name,ID=ID,is_strict=is_strict))
    #characterID
    if ID < 0:  #如果没有给出characterID
        name = name.strip(" \n")
        for i in history:
            if i.upper() == name.upper():
                name = i
                ID = history[name]["characterID"]
                break
        if ID < 0:  #搜索历史记录未命中
            log("SearchName:历史记录未命中")
            strict = "&strict=true" if is_strict else "&strict=false"
            url=r"https://esi.evetech.net/latest/search/?categories=character&datasource=tranquility&language=en-us&search="+name.replace(" ", "+")+strict
            try:

                with rq.get(url,timeout=5) as ret:
                    ret = loads(ret.content)
            except Exception as e:
                log("SearchName:"+str(e),level="error")
                Msg.update({"Error":"esiError"})
                MutSearchName.unlock()
                return Msg
            if "character" in ret:
                ID = ret["character"]
                if (len(ID) > 1):
                    log("SearchName:命中{l}/{lmax}个结果".format(l=len(ID),lmax=settings["ResultCountLimit"]))
                    #有多个命中结果
                    if len(ID) < settings["ResultCountLimit"]:
                        Msg.update({"NameList":ID})
                        MutSearchName.unlock()
                        return Msg
                    else:
                        #结果过多
                        Msg.update({
                            "TooManyResults": TMsgEntry("搜索结果数量超过" + \
                                str(settings["ResultCountLimit"]) + "个，改为严格模式...",
                                style_str=MDStyleStr(
                                    color=settings["clHint"],
                                    font_size=settings["labelFontSize"]
                            )),
                            "name": name
                            })
                        MutSearchName.unlock()
                        return Msg
                else:
                    ID=ID[0]
            else:
                Msg.update({"Error": "NoSuchCharacterError"})
                log("SearchName:esi查询失败:{name}".format(name=name),level="warning")
                MutSearchName.unlock()
                return Msg
        Msg.update({"SearchName": [name, ID]})

    #zkb
    url = r"https://zkillboard.com/api/stats/characterID/" + str(ID) + r"/"
    try:
        with rq.get(url,timeout=5) as ret:
            ret = loads(ret.content)
    except Exception as e:
        Msg.update({"Error":"zkbError"})
        MutSearchName.unlock()
        return Msg

    #角色信息为None
    if (ret == {}) or (ret["info"] == None):
        Msg.update({"SearchKB": {"noSuchPlayer":TMsgEntry("没有"+name+"的统计数据",style_str=MDStyleStr(color=settings["clHint"],font_size=settings["labelFontSize"]))}})
        MutSearchName.unlock()
        return Msg

    if "dangerRatio" not in ret:
        ret["dangerRatio"]=0
    danger_ratio_color = (int(ret["dangerRatio"] / 100 * 255),
        int((1 - (ret["dangerRatio"] / 100)) * 255),0)

    if "gangRatio" not in ret:
        ret["gangRatio"]=100
    solo_ratio_color = (int((1 - (ret["gangRatio"] / 100)) * 255),
        int(ret["gangRatio"] / 100 * 255),0)

    Msg.update({"SearchKB": {

            "name": [ret["info"]["name"], TMsgEntry(r"<a href='https://zkillboard.com/character/" + str(ID) + r"' style='color:blue'>" + ret["info"]["name"] + "</a>",
                style_str=MDStyleStr(color=settings["clURL"],font_size=settings["labelFontSize"]))],

            "dangerRatio":[ret["dangerRatio"],TMsgEntry("危险度:" + str(ret["dangerRatio"]) + "%",
                style_str=MDStyleStr(color=danger_ratio_color,font_size=settings["labelFontSize"]))],

            "soloRatio": [ret["gangRatio"],TMsgEntry("solo率:" + str(100-ret["gangRatio"]) + "%",
                style_str=MDStyleStr(color=solo_ratio_color,font_size=settings["labelFontSize"]))],

            "topShips": [[i["shipTypeID"] for i in ret["topLists"][3]["values"][:3]],TMsgEntry("最高击杀舰船:" + ','.join([
                    getNamebyID(i["shipTypeID"])+ "(" + str(i["kills"]) + "次)"
                    for i in ret["topLists"][3]["values"][:3]
                    if i["shipName"] != "Capsule"
                ]),
                style_str=MDStyleStr(color=settings["cltopShips"],font_size=settings["labelFontSize"]))],

            "topSolarSystem":[[i["solarSystemName"] for i in ret["topLists"][4]["values"][:3]],TMsgEntry("最常出没:"+','.join([
                    i["solarSystemName"] + "(" + str(i["kills"]) + "次)"
                    for i in ret["topLists"][4]["values"][:3]
                ]),
                style_str=MDStyleStr(color=settings["cltopSolarSystem"],font_size=settings["labelFontSize"]))]}})

    history.update({ret["info"]["name"]: {"characterID": ID}})
    SaveFile(history,settings["workingDir"]+"history.json")

    #getKMList
    url = r"https://zkillboard.com/api/kills/characterID/" + str(ID) + r"/"
    try:
        with rq.get(url,timeout=5) as ret:
            ret = loads(ret.content)
    except Exception as e:
        log("getKMList:"+str(e),level="error")
        Msg.update({"Error":"getKMListError"})
        MutSearchName.unlock()
        return Msg

    #玩家可能没有击杀km
    if ret == []:
        Msg.update({"getKMList": []})
        MutSearchName.unlock()
        return Msg

    km_count = min(settings["KMCounts"],len(ret))
    killmail_pairs = [(ret[i]["killmail_id"], ret[i]["zkb"]["hash"]) for i in range(km_count)]
    remap = []
    label_list = [TMsgEntry(str(i+1)+".最近km("+Valuable(ret[i]["zkb"]["totalValue"])+' isk)',
            style_str=MDStyleStr(color=settings["clKM"],font_size=settings["labelFontSize"]),
            ClickEvent=SearchKM,
            ClickArgs=(ID, killmail_pairs[i][0], killmail_pairs[i][1])) for i in range(len(killmail_pairs))]
    for i in killmail_pairs:
        remap.append([i, label_list[0], {}])
        label_list = label_list[1:]
    Msg.update({"getKMList": remap})
    log("getKMList:完成")
    MutSearchName.unlock()
    return Msg

def SearchKM(character_id:int,killmail_id: int = 0, killmail_hash: str = ''):
    """
    获取一个特定的km
    character_id(int):角色id
    killmail_id(int):该killmail的id
    killmail_hash(str):由ccp给出的km哈希值
    """
    global MutSearchKM
    MutSearchKM.lock()
    Msg = {}
    log("SearchKM:character_id={character_id},killmail_id={killmail_id},killmail_hash={killmail_hash}".format(character_id=character_id,killmail_id=killmail_id,killmail_hash=killmail_hash))
    url = r"https://esi.evetech.net/latest/killmails/"\
            + str(killmail_id)\
            + r"/" + killmail_hash + r"/?datasource=tranquility"
    try:
        with rq.get(url,timeout=5) as ret:
            ret = loads(ret.content)
    except Exception as e:
        log("SearchKM:"+str(e),level="error")
        Msg.update({"Error":"SearchKMError"})
        MutSearchKM.unlock()
        return -1

    Msg = {"SearchKM": {"time": [ret["killmail_time"].replace('T', ' ').replace('Z', ''),TMsgEntry("  ("+ret["killmail_time"].replace('T', ' ').replace('Z', ''+")"),
                                style_str=MDStyleStr(color=settings["clHint"],font_size=settings["labelFontSize"]))
                            ],
                        "victimShip": [ret["victim"]["ship_type_id"],TMsgEntry(
                                r"&nbsp;&nbsp;<a href='https://zkillboard.com/kill/"+str(killmail_id)+r"/' style='color:blue'>击毁:"+getNamebyID(ret["victim"]["ship_type_id"])+r"</a>",
                                style_str=MDStyleStr(color=settings["clURL"],font_size=settings["labelFontSize"]))
                            ]
                        }}
    for i in ret["attackers"]:
        if ("character_id"in i)and(i["character_id"] == character_id):
            ship=getNamebyID(i["ship_type_id"]) if "ship_type_id" in i else "(?)"
            weapon = getNamebyID(i["weapon_type_id"]) if "weapon_type_id" in i else "(?)"
            if ship == weapon:
                weapon="(混合)"
            Msg["SearchKM"].update({
                "shipType":[ship,TMsgEntry(
                    "   · " + ship,
                    style_str=MDStyleStr(color=settings["clshipType"],font_size=settings["labelFontSize"])
                    )],
                "weaponType":[weapon,TMsgEntry(
                    "   · " + weapon,
                    style_str=MDStyleStr(color=settings["clweaponType"],font_size=settings["labelFontSize"])
                    )]})
            break
    log("SearchKM:完成")
    MutSearchKM.unlock()
    return Msg

def addName(ID: int,no:int=0):
    """
    为characterID获取name。
    ID(int):要搜索name的ID。
    no(int):第no个搜索项。
    """
    url=r"https://esi.evetech.net/latest/characters/"+str(ID)+r"/?datasource=tranquility"
    Msg = {"addName": []}
    try:
        with rq.get(url,timeout=5) as ret:
            ret = loads(ret.content)
    except Exception as e:
        log("addName:" + str(e), level="error")
        return Msg

    log("addName:ID={ID}已获取到".format(ID=ID))
    if "name" in ret:
        history.update({ret["name"]:{"characterID":ID}})
        Msg["addName"].append([ID,
            TMsgEntry(ret["name"],
            ClickEvent=SearchName,
            ClickArgs=(ret["name"],ID),
            style_str=MDStyleStr(color=settings["claddName"],font_size=settings["labelFontSize"]))]
        )
    return Msg