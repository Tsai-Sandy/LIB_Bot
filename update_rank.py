import pymongo
import pandas
import datetime

myclient = pymongo.MongoClient("mongodb+srv://user_try:library@cluster0.4ejzf.gcp.mongodb.net/test")
mydb = myclient["LIB"]
mycol = mydb["player"]
rank = mydb["rank"]

rank.delete_many({}) # 清空資料表
player_information = mycol.find().sort("score", -1) #按照分數高到低排序
count = 1
for i in player_information:
	if count <= 10: # 只取10個
		rank_data = {
			"rank" : count,
			"student" : i["studentID"],
			"score" : i["score"]
		}
		rank.insert_one(rank_data) #寫入
	else:
		break
	count += 1

now = datetime.datetime.now()
txt = '上次更新時間為：' + str(now)
df = pandas.DataFrame([txt], index=['UpdateTime'])

df.to_csv('log_rank.csv', header=False)