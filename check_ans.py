from PIL import Image, ImageDraw, ImageFont
import pyimgur #imgur api

dic_x = {
	0: 0,
	1: 444,
	2: 888,
	3: 1332,
	4: 1776
}

dic_ans_status = {
	0: "gray",
	1: "yellow",
	2: "green"
}

def CheckAns(guset, index, CLIENT_ID):
    mother_image = Image.open("./img/base.jpg")

    for i in range(len(index)):
        img = Image.open("./img/" + dic_ans_status[index[i]] + ".jpg")

        try:
            # ====== 在色塊上寫上文字 ====== #
            Drawing = ImageDraw.Draw(img)
            Myfont = ImageFont.truetype(r'./font/arial.ttf', size=300)
            Drawing.text((140, 120), guset[i], fill='rgb(0,0,0)', font=Myfont)
        except:
            print("寫文字失敗")
            return "寫文字失敗"

        try:
            # ====== 在母圖上貼上對應小圖 ====== # 
            mother_image.paste(img, (dic_x[i], 0))
        except:
            print("母子圖合成失敗")
            return "母子圖合成失敗"

    try:
        # 存檔
        mother_image.save("./img/ans.jpg")
    except:
        print("存檔失敗")
        return "存檔失敗"

    im = pyimgur.Imgur(CLIENT_ID)
    uploaded_img = im.upload_image("./img/ans.jpg", title="Uploaded with PyImgur")

    return uploaded_img.link