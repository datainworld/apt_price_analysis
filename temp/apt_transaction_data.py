import pandas as pd
import numpy as np
import PublicDataReader as pdr
from datetime import datetime, timedelta
from urllib.parse import urlparse
import requests
from dotenv import load_dotenv
import os

HEADER = os.getenv('kakao_header')
APT_DATA_API_KEY = os.getenv('apt_data_api_key')

### 기본 아파트 거래 데이터 생성 =========================================================================

## 주소 지오코딩 함수 -----------------------------------------------------------------------------------
def geocoding(addr): # 주소 지오코딩 
  url = "https://dapi.kakao.com/v2/local/search/address.json?&query=" + addr
  result = requests.get(urlparse(url).geturl(), headers=HEADER)
  json_obj=result.json()
  address = json_obj['documents'][0]['address']
  coordiante = address['region_3depth_h_name'], address['x'], address['y']
  return coordiante

## 기본 실거래가 데이터 생성 함수 -----------------------------------------------------------------------
def make_basic_data(month): # 기본 데이터 수집
    dristrict_code = pdr.code_hdong()
    seoul_gu_code = dristrict_code[dristrict_code['시도명'] == '서울특별시']['시군구코드'].unique()
    seoul_gu_code = np.delete(seoul_gu_code, 0) # 자치구가 아닌 서울시 코드('11000')를 삭제한다.
    
    # 데이터 수집기간 설정
    end_month = datetime.today().strftime('%Y%m') # 오늘 날짜
    start_month = (datetime.today() - timedelta(days=month)).strftime('%Y%m') 
    
    # 조건에 따라 데이터 수집
    api = pdr.TransactionPrice(APT_DATA_API_KEY) # api 키를 이용하여 실거래가 데이터 수집 객체 생성
    df = pd.DataFrame()
    for i in seoul_gu_code:
        df_tmp = api.get_data(
            property_type='아파트', 
            trade_type='매매', 
            sigungu_code=i, 
            start_year_month=start_month,
            end_year_month=end_month
        )
        df = pd.concat([df, df_tmp], ignore_index=True)
    
    # 단지 데이터 생성
    df_danji = df.drop_duplicates(subset='일련번호', keep='first', ignore_index=True) # 단지코드 중복 제거
    df_danji['자치구'] = df_danji['지역코드'].map(lambda x: dristrict_code[dristrict_code['시군구코드'] == x]['시군구명'].values[0]) # 지역코드를 자치구명으로 변경하여 추가
    df_danji['주소'] = '서울시' + ' ' + df_danji['자치구'] + ' ' + df_danji['법정동'] + ' ' + df_danji['지번'] # 주소 컬럼 추가

    # 단지별 위경도좌표 생성(주소 지오코딩)
    for i, row in df_danji.iterrows():
        try:
            df_danji.loc[i, '행정동'], df_danji.loc[i, '경도'], df_danji.loc[i, '위도'] = geocoding(row['주소'])
        except:
            df_danji.loc[i, '행정동'], df_danji.loc[i, '경도'], df_danji.loc[i, '위도'] = np.nan, np.nan, np.nan

    df_danji = df_danji[['일련번호', '아파트', '건축년도', '자치구', '행정동', '주소', '위도', '경도']]

    # 호별 거래 데이터 생성
    df['거래일'] = df['년'].astype(str) + '-' + df['월'].astype(str) + '-' + df['일'].astype(str) # df에 거래일 컬럼 추가
    df_ho = df[['일련번호', '층', '전용면적', '거래일', '거래금액', '거래유형', '해제사유발생일', '해제여부', '등기일자']] # df에서 필요한 컬럼만 추출하여 df_ho에 저장
    ddf = pd.merge(df_ho, df_danji, on='일련번호', how='left') # df_ho와 단지 데이터와 병합
    ddf = ddf[ddf['행정동'].notnull()] # ddf에서 '행정동' 이 nan-null인 행을 제거한다.
    ddf['전용면적'] = ddf['전용면적'].map(lambda x: int(x)) # ['전용면적']의 유니크한 값을 최소화 하기 소수점 이하의 값을 버린다.
    ddf['거래단위'] = ddf['일련번호'] + '_' + ddf['전용면적'].astype(str) # 단지와 전용면적을 결합한 거래단위 컬럼 추가 
    ddf['거래일'] = pd.to_datetime(ddf['거래일']) # 거래일을 datetime 형식으로 변환
    ddf.sort_values(by='거래일', ascending=True, inplace=True) # 거래일을 기준으로 오름차순 정렬    
    return ddf


### 호별 직전 거래 데이터 생성 ================================================================================
def check_before_price(unit, df): # 직전 거래일과 거래금액을 반환하는 함수
    df_tmp = df[df['거래단위'] == unit].sort_index(ascending=True).reset_index(drop=True) # 거래단위가 unit인 데이터프레임 ddf_tmp 생성
    if len(df_tmp) >= 2: # ddf_tmp의 행이 2개 이상인 경우
        return df_tmp.iloc[-2]['거래일'], df_tmp.iloc[-2]['거래금액']  # ddf_tmp에서 뒤에서 두 번째 행의 거래일과 거래금액을 반환
    else: # 그렇지 않은 경우 NaN을 반환
        return np.NAN, np.NaN

def make_price_data(df):
    df_price = df.copy()
    df_price.drop_duplicates(subset=['거래단위'], keep='last', inplace=True) # 거래단위 중복 제거(가장 최근 거래만 남김)
    for i, row in df_price.iterrows():          
        df_price.loc[i, '직전거래일'], df_price.loc[i, '직전거래금액'] = check_before_price(row['거래단위'], df)
    df_price.dropna(subset=['직전거래일'], inplace=True)  # 직전 거래일이 NaN인 행 삭제       
    df_price['차액'] = (df_price['거래금액'] - df_price['직전거래금액']) # 직전 거래일과 직전 거래금액 컬럼 추가
    df_price['변화율'] = (df_price['차액'] / df_price['직전거래금액'] * 100).round(2) # 변화율을 계산하여 열 추가
    df_price['변화'] = df_price['차액'].apply(lambda x: '상승' if x > 0 else '하락' if x < 0 else '유지') # 차액에 따라 변화를 표시하는 열 추가
    df_price['직전거래금액'] = df_price['직전거래금액'].astype(int)  # 직전 거래금액과 차액을 정수형으로 변환
    df_price['차액'] = df_price['차액'].astype(int)  # 직전 거래금액과 차액을 정수형으로 변환  
    df_price['거래일'] = pd.to_datetime(df_price['거래일']) # 거래일을 datetime 형식으로 변환  
    df_price.set_index('거래일', inplace=True, drop=False) # 거래일을 인덱스로 설정
    df_price.sort_index(ascending=True, inplace=True) # 거래일을 기준으로 오름차순 정렬
    return df_price