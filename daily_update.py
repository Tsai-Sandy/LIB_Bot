import pymongo

myclient = pymongo.MongoClient("mongodb+srv://user_try:library@cluster0.4ejzf.gcp.mongodb.net/test")
mydb = myclient["LIB"]
mycol = mydb["player"]

players = mycol.find()
newValue = {"$set": {"Ans_flag": 0, "startTime": "", "endTime": ""}}
mycol.update_many({}, newValue)