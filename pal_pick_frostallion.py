# 测伤害大法判断唤冬兽词条脚本
# 使用此脚本时，尽量将帕鲁的生命回复倍率设置在 2，主角的受伤害倍率设置为最低，主角和帕鲁饱食度下降速度为最低
# 确保食物袋里面有足够的食物
# 尽量使用四速，满血量和防御加成的空涡龙，这样可以加快筛选速率

from tools import *
import datetime
import json5
import os
import winsound

settings = None
hpAddr = None
xAddr = None
yAddr = None


def GetAscii(x):
    return ord(x[0])


def LoadSettings():
    global settings, hpAddr, xAddr, yAddr
    with open("./settings.json", "r", encoding="utf-8") as js:
        settings = json5.load(js)
        hpAddr = int(settings["hpAddr"], 16)
        xAddr = int(settings["xAddr"], 16)
        yAddr = xAddr - 8


def MoveToFight():
    # 让空涡龙进食
    Sleep(3000)
    while ReadMemory("int", hpAddr) / 1000 < 3000:
        Sleep(100)

    KeyDown(GetAscii("F"))
    Sleep(2500)
    KeyUp(GetAscii("F"))
    KeyDown(VK_SPACE)
    Sleep(250)
    KeyUp(VK_SPACE)

    fightX = settings["fightX"]
    fightY = settings["fightY"]
    while True:
        KeyDown(GetAscii("W"))
        Sleep(1)
        KeyUp(GetAscii("W"))
        x = ReadMemory("float", xAddr)
        y = ReadMemory("float", yAddr)
        if abs(x - fightX) < 0.03 and abs(y - fightY) < 0.03:
            break


def MoveToRest():
    restX = settings["restX"]
    restY = settings["restY"]
    while True:
        KeyDown(GetAscii("S"))
        Sleep(1)
        KeyUp(GetAscii("S"))
        x = ReadMemory("float", xAddr)
        y = ReadMemory("float", yAddr)
        if abs(x - restX) < 0.03 and abs(y - restY) < 0.03:
            break

    KeyDown(VK_CONTROL)
    Sleep(250)
    KeyUp(VK_CONTROL)
    KeyDown(GetAscii("F"))
    Sleep(1000)
    KeyUp(GetAscii("F"))


def Shoot():
    RightDown()
    Sleep(750)
    LeftClick()
    Sleep(100)
    RightUp()


def GetTargetDamage():
    # 呆了半分钟都没有受到伤害直接回去
    # 这可能是因为没子弹或者唤冬兽没受到伤害或者刷没
    checkInterval = 20
    targetCnt = int(60 * 1000 / checkInterval)
    damage = 0
    acceptDamageRanges = settings["acceptDamageRanges"]
    rejectDamageRanges = settings["rejectDamageRanges"]

    for cnt in range(targetCnt):
        if cnt == int(targetCnt / 2) and int(damage) == 0:
            Shoot()

        # 通过检测空涡龙的血量来测试技能伤害
        hp = ReadMemory("int", hpAddr) / 1000
        Sleep(checkInterval)
        damage = hp - ReadMemory("int", hpAddr) / 1000
        if damage <= 0:
            continue

        for [low, high] in acceptDamageRanges:
            if damage >= low and damage <= high:
                return damage

        for [low, high] in rejectDamageRanges:
            if damage >= low and damage <= high:
                return -damage  # 不符合的伤害以负数形式返回

    return 0


def Logger(count: int, damage: int):
    timeStr = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    outStr = f"{timeStr}, count:{count}, damage:{int(damage)}"
    print(outStr)
    with open("record.txt", "a") as file:
        file.write(outStr + "\n")
    with open("count.txt", "w") as file:
        file.write(str(count) + "\n")


if __name__ == "__main__":
    # 给玩家的准备时间: 3s
    Sleep(3000)
    LoadSettings()
    OpenProcessByWindow(className=None, windowName="Pal  ")

    count = 0
    if os.path.exists("count.txt"):
        with open("count.txt", "r") as file:
            count = int(file.readline())

    while True:
        MoveToFight()
        # 避免唤冬兽没刷出来
        Sleep(2000)
        Shoot()
        damage = GetTargetDamage()
        count += 1
        Logger(count, damage)
        if damage > 0:
            # 响铃
            winsound.Beep(600, settings["reminderDuration"])
            break
        MoveToRest()
        if damage == 0:  # 伤害为零直接休息一分钟, 用于填充子弹
            Sleep(1000 * 60)
