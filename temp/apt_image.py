import requests
from PIL import Image, ImageDraw, ImageFont
import io
import os
import setting

API_KEY = setting.GOOGLE_STREET_VIEW_API_KEY
IMAGE_PATH = 'assets/apt_img/'
FONT_PATH = 'assets/Fonts/malgun.ttf'

def take_apt_image(y, x, danji_id, dong, name): 
    path = IMAGE_PATH
    heading_list = list(range(-45, 360-45, 90))
    img_list = []
    for heading in heading_list:
        lat, lon = y, x    
        fov = "120"
        pitch = "30"
        google_api_key = API_KEY
        url = f"https://maps.googleapis.com/maps/api/streetview?size=400x300&location={lat},{lon}&fov={fov}&heading={heading}&pitch={pitch}&key={API_KEY}"
        response = requests.get(url)  # Google Street View API로 이미지 요청
        bytes_data = response.content  # 응답으로 받은 이미지 데이터
        img = Image.open(io.BytesIO(bytes_data))  # 이미지 데이터를 PIL Image 객체로 변환
        draw = ImageDraw.Draw(img)  # 이미지에 그리기 객체 생성
        draw.text((15,15), dong + ' ' + name, font=ImageFont.truetype(FONT_PATH, 16), fill=(0,0,0))  # 이미지에 동과 이름 텍스트 추가
        img_list.append(img)  # 이미지 리스트에 추가
    img_list[0].save(path + danji_id + '.gif', save_all=True, append_images=img_list[1:], duration=1000, loop=0)  # 이미지 리스트를 GIF 파일로 저장