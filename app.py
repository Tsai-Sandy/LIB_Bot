from http import client
import os
from dotenv import load_dotenv
from flask import Flask, request, abort
import pymongo
import random
import time
from collections import Counter
from check_ans import CheckAns
# from PIL import Image, ImageDraw, ImageFont
# import pyimgur

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

app = Flask(__name__)

load_dotenv(encoding="utf-8")
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
client_img = os.environ.get('CLIENT_ID')

myclient = pymongo.MongoClient("mongodb+srv://user_try:library@cluster0.4ejzf.gcp.mongodb.net/test")
mydb = myclient["LIB"]
mycol = mydb["player"]
anscol = mydb["Question"]
rank = mydb["rank"]

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    print(body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@handler.add(FollowEvent)
def handle_follow(event):
    UserId = event.source.user_id
    profile = line_bot_api.get_profile(UserId)
    player_data = {
        "PlayerName": profile.display_name,
        "PlayerId": UserId,
        "ID_Flag": False,
        "studentID": "", # 學號
        "majorGrade": "", # 系級
        "Ans_flag": 0,
        "Question": [], # 使用題目
        "startTime": "", # 請求題目時間
        "endTime": "", # 正確回傳結束時間
        "Days": 0, # 參與天數
        "score": 0, # 換算後的分數
        
    }
    mycol.insert_one(player_data)

@handler.add(UnfollowEvent)
def handle_unfollow(event):
    UserId = event.source.user_id
    del_player = {"PlayerId": UserId}
    mycol.delete_one(del_player)

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    UserId = event.source.user_id
    profile = line_bot_api.get_profile(UserId)
    player_information = mycol.find_one({"PlayerId": UserId})

    if event.message.text == "活動說明":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='1. 在選單中按下"登錄資訊"，依照提示輸入系級學號（僅需輸入 1 次，請輸入真實資訊，以利得獎時確認身分）\n\n\
2. 按下開始猜題即會開始計時（每日00:00 會重置）\n\n\
3. 猜題方式類似《Wordle》網頁猜字遊戲\n\n\
4. 題目為 5 位數字，為 ISBN 後 5 碼（有數字重複機率）\n\n\
5. 每人題目可能不同，猜對數字後依照提示回傳最終答案\n\n\
6. 最終答案正確，將會停計時，並依據所用秒數換算為當日積分\n\n\
7. 只有最終答案正確才會紀錄參與天數喔，欲拿到 5 日參與獎請務必達到最後\n\n\
8. 點擊"排行榜"後可查看當前積分，與前 10 名排名（排名每 10 分鐘更新）')
        )

    elif event.message.text == "登錄參加資訊":
        if player_information["ID_Flag"] == False:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請傳送系級學號\n（格式：登錄資訊 圖資五 408040000）")
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"您已登錄資訊：{player_information['majorGrade']} {player_information['studentID']}\n若要修改請以此格式傳送\n（格式：修改資訊 圖資五 408040000）")
            )

    elif event.message.text[0:4] == "登錄資訊":
        if player_information["ID_Flag"] == True:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"您已登錄資訊：{player_information['majorGrade']} {player_information['studentID']}\n若要修改請以此格式傳送\n修改資訊 圖資五 408040000）")
            )
        else:
            Text = (event.message.text).split(" ")
            newValue = {"$set": {"ID_Flag": True, "studentID": Text[2], "majorGrade": Text[1]}}
            mycol.update_one({"PlayerId": UserId}, newValue)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"資訊已更新：{Text[1]} {Text[2]}")
            )
    
    elif event.message.text[0:4] == "修改資訊":
        if player_information["ID_Flag"] == False:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"您尚未登錄資訊喔！請先登錄資訊\n（格式：登錄資訊 圖資五 408040000）")
            )
        else:
            Text = (event.message.text).split(" ")
            newValue = {"$set": {"studentID": Text[2], "majorGrade": Text[1]}}
            mycol.update_one({"PlayerId": UserId}, newValue)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"資訊已更新：{Text[1]} {Text[2]}")
            )

    elif event.message.text == "開始猜題":
        if player_information["ID_Flag"] == False:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"您尚未登錄資訊喔！請先登錄資訊，再回來重按猜題喔\n（格式：登錄資訊 圖資五 408040000）")
            )
        else:
            if player_information["Ans_flag"] == 0:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="開始計時\n題目已產生，題目為 5 位數字，為 ISBN 後 5 碼（有數字重複機率）")
                )
                ans_id = str(random.randint(1,3))
                while (ans_id in player_information["Question"]) and (len(player_information["Question"]) < 3):
                    ans_id = str(random.randint(1,3))
                Q_org = player_information["Question"]
                Q_org.append(ans_id)
                newValue = {"$set": {"startTime": time.time(), "Question": Q_org, "Ans_flag": 1}}
                mycol.update_one({"PlayerId": UserId}, newValue)
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="已領取過題目")
                )
    # 排行榜
    if event.message.text == "排行榜":
        text = ""
        R = 1
        for i in rank.find():
            text = text + f"第{R}名\t{i['student']}\t{i['score']}分\n"
            R += 1
        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"您的積分：{player_information['score']}\n\n排行榜:\n{text}")
            )

    # 猜數字、要加判斷答案格式、位置正確錯誤的
    elif player_information["Ans_flag"]==1:
        player_A = event.message.text
        player_Q = anscol.find_one({"Q_id": player_information["Question"][-1]})
        Q_isbn = player_Q["ISBN"]
        if len(player_A) != 5:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="答案格式錯誤")
            )

        reply = []
        if player_A == Q_isbn: # 答案正確
            newValue = {"$set": {"Ans_flag": 2}}
            mycol.update_one({"PlayerId": UserId}, newValue)
            img_link = CheckAns(player_A, [2]*5, client_img)
            reply.append(ImageSendMessage(original_content_url=img_link, preview_image_url=img_link))
            reply.append(TextSendMessage(text=f"答案正確！\n{player_Q['hint']}"))
            line_bot_api.reply_message(
                event.reply_token,
                reply
                # TextSendMessage(text=f"答案正確！\n{img_link}")
            )
        else:
            correct = []
            for i in Q_isbn:
                correct.append(i)
            correct_count = Counter(correct)
            compare_ans = [0] * 5 # 0: 沒有 1: 有位置錯誤 2: 完全正確
            for i in range(0,5):
                if player_A[i] == Q_isbn[i]:
                    compare_ans[i] = 2
                    correct_count[player_A[i]] -= 1
            for i in range(0,5):
                if compare_ans[i] == 2:
                    continue
                else:
                    if player_A[i] in Q_isbn:
                        if correct_count[player_A[i]] == 0:
                            continue
                        else:
                            compare_ans[i] = 1
                            correct_count[player_A[i]] -= 1
                       
            reply.append(TextSendMessage(text="答案錯誤"))
            img_link = CheckAns(player_A, compare_ans, client_img)
            #reply.append(TextSendMessage(text=img_link))
            
            reply.append(ImageSendMessage(original_content_url=img_link, preview_image_url=img_link))
            
            try:
                line_bot_api.reply_message(
                    event.reply_token,
                    reply
                )
            except:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="圖片回傳失敗")
                )  

    # 回傳正確答案
    elif player_information["Ans_flag"]==2:
        player_A = event.message.text
        player_Q = anscol.find_one({"Q_id": player_information["Question"][-1]})
        if player_A == player_Q["answer"]:
            day = player_information["Days"]
            score = player_information["score"]
            TIME = time.time()
            time_interval = player_information["startTime"] - TIME
            score = score + int((86400 - time_interval) * 0.02) # 得分換算
            newValue = {"$set": {"endTime": TIME, "Ans_flag": 3, "Days": day+1, "score": score}}
            mycol.update_one({"PlayerId": UserId}, newValue)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"答案正確！停止計時\n當前積分：{score}") # 加上當前分數
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="答案錯誤，請確認有無多打空白格")
            )
    
    
if __name__ == "__main__":
    app.run()