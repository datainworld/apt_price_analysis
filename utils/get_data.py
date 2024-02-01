
def apt_image(y, x, danji_id, dong, name): # 구글 스트리트 뷰 API를 이용해 아파트 이미지를 수집하는 함수
    import requests
    from PIL import Image, ImageDraw, ImageFont
    import io
    import os
    from dotenv import load_dotenv

    load_dotenv(verbose=True)
    API_KEY = os.getenv('GOOGLE_STREET_VIEW_API_KEY')

    IMAGE_PATH ='C:/PythonDev/소스 코드/apt/src/assets/apt_img/'
    FONT_PATH = 'C:/PythonDev/소스 코드/apt/src//assets/Fonts/malgun.ttf'

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
    img_list[0].save(IMAGE_PATH + danji_id + '.gif', save_all=True, append_images=img_list[1:], duration=1000, loop=0)  # 이미지 리스트를 IMAGE_PATH 폴더에 GIF 파일로 저장

def apt_news(): # 네이버 검색 API를 이용해 아파트 관련 뉴스를 수집하는 함수
    import urllib.request
    import json
    import pandas as pd
    import os
    from dotenv import load_dotenv

    load_dotenv(verbose=True)
    ID = os.getenv('NAVER_ID')
    SECRET = os.getenv('NAVER_SECRET')
    query = urllib.parse.quote("서울시 아파트 거래")
    idx = 0
    display = 10
    start = 1
    end = 10
    sort = "sim"

    df = pd.DataFrame(columns=("Title", "OriginalLink", "Link", "Description", "PublicationData"))

    for start_index in range(start, end, display):
        url = "https://openapi.naver.com/v1/search/news?query=" + query \
            + "&display=" + str(display) \
            + "&start=" + str(start_index) \
            + "&sort=" + sort
        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", ID)
        request.add_header("X-Naver-Client-Secret", SECRET)
        response = urllib.request.urlopen(request)
        rescode = response.getcode()

        if (rescode == 200):
            tmp = json.load(response)
            for item in tmp['items']:
                try:
                    df.loc[idx] = [item['title'], item['originallink'], item['link'], item['description'],
                                        item['pubDate']]
                except:
                    continue
                idx += 1
        else:
            print("Error Code:" + rescode)

    df['PublicationData'] = pd.to_datetime(df['PublicationData']) # PublicationData 컬럼을 날짜형으로 변환
    df.sort_values(by=['PublicationData'], ascending=False, inplace=True) # 날짜를 기준으로 내림차순 정렬
    df['PublicationData'] = df['PublicationData'].dt.strftime('%Y-%m-%d %H:%M') # 날짜를 YYYY-MM-DD HH:MM 형식으로 변경
    # Remove <b> and </b> tags from the Title and Description columns
    df['Title'] = df['Title'].str.replace("<b>", "").str.replace("</b>", "").str.replace("&quot;", "")
    df['Description'] = df['Description'].str.replace("<b>", "").str.replace("</b>", "").str.replace("&quot;", "")
    return df