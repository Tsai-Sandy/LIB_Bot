import os
from dotenv import load_dotenv
import pymongo
import pandas
import datetime

load_dotenv(encoding="utf-8")

myclient = pymongo.MongoClient(os.getenv('MONGO_CLIENT_URI'))
mydb = myclient["LIB"]
mycol = mydb["player"]

players = mycol.find()
newValue = {"$set": {"Ans_flag": 0, "startTime": "", "endTime": ""}}
mycol.update_many({}, newValue)

now = datetime.datetime.now()
txt = '上次更新時間為：' + str(now)
df = pandas.DataFrame([txt], index=['UpdateTime'])

df.to_csv('log_daily.csv', header=False)