# %%
import pandas as pd
from dash import Dash, html, dcc, dash_table, Input, Output, no_update, State, callback
import dash_ag_grid as dag
import plotly.express as px
import dash_bootstrap_components as dbc
import numpy as np
import json
import geopandas as gpd
import os
import warnings
warnings.filterwarnings('ignore')
from utils import get_data # openAPI를 이용하여 아파트 이미지와 뉴스 데이터를 가져오는 모듈
import pytz
from datetime import datetime

DATA_PATH = './assets/data/'
df_basic = pd.read_csv(DATA_PATH + '2024-01-23_08-57-59apt_basic_data.csv', parse_dates=['거래일'], date_format='%Y-%m-%d')
df_price = pd.read_csv(DATA_PATH + '2024-01-23_08-57-59apt_price_data.csv', parse_dates=['거래일'], date_format='%Y-%m-%d')
area_top10 = df_basic['전용면적'].value_counts().sort_values(ascending=False).head(10).index.sort_values().tolist()

# tz = pytz.timezone('Asia/Seoul')
# seoul_now = datetime.now(tz).strftime('%Y-%m-%d')

# %%
### 인터랙션 컴포넌트 ---------------------------------------------------------
## 날짜 선택
date_pick = dcc.DatePickerRange(
    id='date-picker-range-input', 
    min_date_allowed=df_price['거래일'].min().date(),
    max_date_allowed=df_price['거래일'].max().date(),
    initial_visible_month=df_price['거래일'].max().date(),
    end_date=df_price['거래일'].max().date(),
    display_format='YYYY-MM-DD',
    start_date_placeholder_text='시작일',
    end_date_placeholder_text='종료일',
    clearable=False, # True: 날짜 선택값 삭제 가능
    style={'font-size': '4px'})
## 자치구 선택
drop_gu = dcc.Dropdown(
    id='dropdown_gu',
    options=df_basic['자치구'].unique(), 
    placeholder='자치구 선택')
## 전용면적 선택
drop_area = dcc.Dropdown(
    id='dropdown_area',
    options=[{'label': str(i) + '㎡', 'value': i} for i in area_top10],
    placeholder='면적(㎡) 선택')

### 인트로 ------------------------------------------------------------------
## 최고가 Tpop5
def draw_high_price_tbl(df):
    df['거래일'] = df['거래일'].dt.strftime('%Y-%m-%d')
    df_high = df.sort_values(by='거래금액', ascending=False)
    df_high = df_high.drop_duplicates(subset='일련번호', keep='first') 
    df_high.reset_index(drop=False, inplace=True) # 맵에서 index가 필요하므로 컬럼으로 변환하여 활용
    tbl = dag.AgGrid(
        id='high_price_tbl_2', # *** 테이블 행 선택시 콜백함수의 Input으로 사용하기 위하여 id를 지정함
        rowData = df_high.head(5).to_dict('records'),
        defaultColDef={'resizable': True, 'sortable': True, 'filter': True},
        columnDefs=[
            {'field': '행정동'},
            {'field': '아파트'},
            {'field': '층', 'width': 80},
            {
                'field': '전용면적', 
                'valueFormatter': {'function': 'params.value + "㎡"'}, # 전용면적에 단위를 추가함
                'width': 120
            },
            {'field': '거래일', 'width': 120, 'cellRenderer': 'dateCellRenderer'},
            {
                'headerName': '거래금액(만원)', 
                'field': '거래금액',
                'type': 'numericColumn', # 오른쪽 정렬 
                'valueFormatter': {'function': 'd3.format(",")(params.value)'}, # 천단위 쉼표
            },
        ],
        dashGridOptions={'rowSelection': 'single'},
        selectedRows=df_high.head(1).to_dict('records'), # 콜백함수의 Input으로 사용하기 위하여 선택된 행을 지정함
        columnSize='sizeToFit', # 컬럼 사이즈를 자동으로 조정함,
        style={'height': 270, 'width': '100%'}, 
    )
    return tbl

## 최저가 Tpop5
def draw_low_price_tbl(df):
    df_low = df.sort_values(by='거래금액', ascending=True)
    df_low = df_low.drop_duplicates(subset='일련번호', keep='first') 
    df_low.reset_index(drop=False, inplace=True) # 맵에서 index가 필요하므로 컬럼으로 변환하여 활용
    tbl = dag.AgGrid(
        id='low-price-tbl-2', # *** 테이블 행 선택시 콜백함수의 Input으로 사용하기 위하여 id를 지정함
        rowData = df_low.head(5).to_dict('records'),
        defaultColDef={'resizable': True, 'sortable': True, 'filter': True},
        columnDefs=[
            {'field': '행정동'},
            {'field': '아파트'},
            {'field': '층', 'width': 80},
            {
                'field': '전용면적', 
                'valueFormatter': {'function': 'params.value + "㎡"'}, # 전용면적에 단위를 추가함
                'width': 120
            },
            {'field': '거래일', 'width': 120, 'cellRenderer': 'dateCellRenderer'},
            {
                'headerName': '거래금액(만원)', 
                'field': '거래금액',
                'type': 'numericColumn', # 오른쪽 정렬 
                'valueFormatter': {'function': 'd3.format(",")(params.value)'}, # 천단위 쉼표
            },
        ],
        dashGridOptions={'rowSelection': 'single'},
        selectedRows=df_low.head(1).to_dict('records'), # 콜백함수의 Input으로 사용하기 위하여 선택된 행을 지정함
        columnSize='sizeToFit', # 컬럼 사이즈를 자동으로 조정함,
        style={'height': 270, 'width': '100%'}, 
    )
    return tbl

def draw_high_price_line(df):
    fig = px.line(
        df,
        x='거래일', 
        y='거래금액', 
        text='거래금액',)
    fig.update_traces(textposition='bottom center')
    fig.update_xaxes(title='') #type='category'
    fig.update_yaxes(title='', showticklabels=False) 
    fig.update_layout( margin={"r":0,"t":0,"l":0,"b":0}, height=230)
    return fig
    
def draw_high_price_map(df):
    df = df.head(1)
    fig = px.scatter_mapbox(
        df, 
        lat='위도', 
        lon='경도', 
        center=dict(lat=df['위도'].values[0], lon=df['경도'].values[0]),  
        zoom=15, 
        mapbox_style='open-street-map')
    fig.update_traces(marker=dict(size=50, color='red', opacity=0.5))
    fig.update_layout(margin={"r":0,"t":1,"l":0,"b":1}, height=300, width=400, )
    return fig

## 거래건수 ------------------------------------------------------------------

def draw_line(df):  # 기간별 아파트 거래건수를 선그래프로 표시
    ddf = df.copy()
    ddf.set_index('거래일', inplace=True, drop=False)
    cnt = ddf.resample('D')['일련번호'].count().reset_index()
    fig = px.line(cnt, x='거래일', y='일련번호')
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=7, label='1주', step='day', stepmode='backward'),
                dict(count=1, label='1개월', step='month', stepmode='backward'),
                dict(count=3, label='3개월', step='month', stepmode='backward'),
                dict(count=6, label='6개월', step='month', stepmode='backward'),
                dict(count=1, label='1년', step='year', stepmode='backward'),
                dict(step='all')
            ])
        ),
        title=''
    )
    fig.update_yaxes(title='')
    fig.update_layout(margin={"r":0,"t":15,"l":0,"b":0}, height=300)
    return fig

def draw_choropleth(df): # 자치구별 거래건수를 코로플레스 맵으로 표시
    path = './assets/map/'
    with open(path + 'geo_sgg.geojson', 'rt', encoding='utf-8') as fp:
        gu_map_json = json.load(fp) # 서울시 자치구별 경계정보를 가진 geojson 파일
    gu_shp = gpd.read_file(path + 'LARD_ADM_SECT_SGG_11.shp', encoding='cp949') # 자치구별 코드와 경계정보를 가진 데이터셋

    gu_deal_cnt = df.groupby('자치구')['거래금액'].count().reset_index(name='거래건수') # 자치구별 거래건수 집계
    gu_deal_cnt = gu_deal_cnt.join(gu_shp.set_index('SGG_NM')['ADM_SECT_C'], on='자치구') # 자치구별 코드 추가

    fig = px.choropleth_mapbox(
        data_frame=gu_deal_cnt,
        geojson=gu_map_json,
        featureidkey='properties.ADM_SECT_C',
        locations='ADM_SECT_C',
        color='거래건수',
        color_continuous_scale='Reds',
        range_color=(gu_deal_cnt['거래건수'].min(), gu_deal_cnt['거래건수'].max()),
        mapbox_style='carto-positron',
        center={'lat':37.5502, 'lon':126.982},
        hover_name='자치구',
        hover_data={'ADM_SECT_C':False, '거래건수':True},
        zoom=9,
        opacity=0.8,
    )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=300)
    return fig

def draw_count_table(df): 
    cnt_top_100 = df['일련번호'].value_counts().head(100).reset_index(name='거래건수')
    df_cnt_top100 = cnt_top_100.join(df.set_index('일련번호')[['자치구', '행정동', '아파트', '건축년도']], on='일련번호').drop_duplicates()
    df_cnt_top100 = df_cnt_top100[['자치구', '행정동', '아파트', '건축년도', '거래건수']]
    tbl = dash_table.DataTable(
        data = df_cnt_top100.to_dict('records'),
        columns=[{'id': c, 'name': c} for c in df_cnt_top100.columns],
        style_cell={'textAlign': 'center', 'font-size': 12, 'overflow': 'hidden', 'textOverflow': 'ellipsis', 'maxWidth': 0,}, 
        style_header={'backgroundColor': 'white', 'fontWeight': 'bold'},    
        style_data={'border': '1px solid gray'}, 
        style_table={'height' : '340px', 'overflowY': 'auto'}, # horizontal scroll
        style_as_list_view=True,
        page_size=10, # 한 페이지에 표시할 행 수
        fixed_rows={'headers': True}, # 헤더 고정
        sort_action='native',
        sort_mode='multi'
        )
    return tbl

def draw_count_map(df):
    cnt_top_100 = df['일련번호'].value_counts().head(100).reset_index(name='거래건수')
    df_cnt_top100 = cnt_top_100.join(df_basic.set_index('일련번호')[['자치구', '행정동', '아파트', '건축년도', '위도', '경도']], on='일련번호').drop_duplicates()
    fig = px.scatter_mapbox(
        df_cnt_top100, 
        lat="위도",  # 위도 열
        lon="경도",  # 경도 열
        size="거래건수",  # 색상 열
        center=dict(lat=37.5502, lon=126.982),  # 지도 중심 좌표 (서울시청)
        zoom=9,  # 확대/축소 레벨
        mapbox_style='open-street-map',  # 지도 스타일
        hover_name='아파트',  # 호버링 시 표시될 이름
        hover_data=['행정동'])  # 호버링 시 표시될 데이터
    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},  # 그래프 여백 설정
        height=380,  # 그래프 높이 설정
        showlegend=False)  # 범례 표시 여부 설정
    fig.update_traces(marker=dict(color='red', opacity=0.5))
    return fig

def draw_count_line(df):
    ddf = df.copy()
    ddf.set_index('거래일', inplace=True, drop=False)
    top5 = ddf['전용면적'].value_counts().head(5).index
    cnt_top5 = ddf[ddf['전용면적'].isin(top5)]
    cnt_top5_month = cnt_top5.groupby(['전용면적', '자치구']).resample('M')['일련번호'].count().reset_index() #
    fig = px.line(cnt_top5_month, x='거래일', y='일련번호', color='전용면적', facet_col='자치구', facet_col_wrap=5)
    fig.update_yaxes(title='')
    fig.update_xaxes(title='')
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=600)
    return fig

## 가격변화 ------------------------------------------------------------------

# 인터랙선 콜백 처리
def draw_pie(df):
    tot = len(df)  # df 행의 수를 하여 tot 변수에 저장
    df = df['변화'].value_counts().reset_index()
    fig = px.pie(df, values='count', names='변화', color='변화', hole=0.4,
                color_discrete_map={'상승':'red', '하락':'blue', '유지':'green'})
    fig.update_traces(textposition='inside',
                    direction='clockwise', 
                    textinfo='percent+label',
                    textfont_size=14,
                    showlegend=False)
    fig.update_layout(annotations=[dict(text=tot, x=0.5, y=0.5, font_size=20, showarrow=False)], 
                      margin={"r":0,"t":0,"l":0,"b":0}, 
                      height=200)
    return fig

def draw_hist(df):
    fig = px.histogram(df, x='변화율', nbins=50)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=200)
    return fig

def draw_map(df):
    # px.set_mapbox_access_token(setting.mapbox_key)  # Mapbox API 토큰 설정 
    fig = px.scatter_mapbox(df, 
                  lat="위도",  # 위도 열
                  lon="경도",  # 경도 열
                  color="변화",  # 색상 열
                  color_discrete_map={'상승':'red', '하락':'blue', '유지':'green'},  # 색상 매핑
                  center=dict(lat=37.5502, lon=126.982),  # 지도 중심 좌표 (서울시청)
                  zoom=9,  # 확대/축소 레벨
                  mapbox_style='open-street-map',  # 지도 스타일
                  hover_name='아파트',  # 호버링 시 표시될 이름
                  hover_data=['행정동'])  # 호버링 시 표시될 데이터
    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},  # 그래프 여백 설정
        height=300,  # 그래프 높이 설정
        showlegend=False)  # 범례 표시 여부 설정
    fig.update_traces(marker=dict(size=15))
    return fig

def draw_facet_pie(df):
    ddf = df.groupby(['자치구','변화'])['일련번호'].count().reset_index()
    fig = px.pie(ddf, values='일련번호', names='변화', 
                 color='변화', color_discrete_map={'상승':'red', '하락':'blue', '유지':'green'},
                 facet_col='자치구', facet_col_wrap=5)
    fig.update_traces(direction='clockwise')
    fig.update_layout(height=600)
    return fig

def draw_price_table(df):
    tbl = dash_table.DataTable(
        id='price_table', # *** 테이블 행 선택시 콜백함수의 Input으로 사용하기 위하여 id를 지정함
        data = df.to_dict('records'),
        columns=[{'id': c, 'name': c} for c in df.columns],
        style_cell={'textAlign': 'center', 'font-size': 12, 'overflow': 'hidden',
        'textOverflow': 'ellipsis', 'maxWidth': 0,}, 
        style_header={'backgroundColor': 'white', 'fontWeight': 'bold'},    
        style_data={'border': '1px solid gray'}, 
        style_table={'height' : '300px', 'overflowY': 'auto'}, # horizontal scroll
        style_as_list_view=True,
        page_size=20, # 한 페이지에 표시할 행 수
        fixed_rows={'headers': True}, # 헤더 고정
        style_data_conditional=[ # 조건부 서식(텍스트 색) 지정
            {'if': {'column_id': '변화율', 'filter_query': '{변화율} > 0'}, 'color': 'red'},
            {'if': {'column_id': '변화율', 'filter_query': '{변화율} = 0'}, 'color': 'green'},
            {'if': {'column_id': '변화율', 'filter_query': '{변화율} < 0'}, 'color': 'blue'}],
        sort_action='native',
        sort_mode='multi',
        row_selectable='single',
        selected_rows=[0])
    return tbl

def draw_table_line(df):
    fig = px.line(df, x='거래일', y='거래금액', text='거래금액')
    fig.update_traces(textposition='bottom center')
    fig.update_xaxes(title='') #type='category'
    fig.update_yaxes(title='', showticklabels=False) 
    fig.update_layout( margin={"r":0,"t":0,"l":0,"b":0}, height=230)
    return fig

def draw_table_map(df):
    fig = px.scatter_mapbox(df, lat='위도', lon='경도', 
                            color='변화', color_discrete_map={'상승':'red', '하락':'blue', '유지':'green'},
                            center=dict(lat=df['위도'].values[0], lon=df['경도'].values[0]),  
                            zoom=15, mapbox_style='open-street-map')
    fig.update_traces(marker=dict(size=50, color='red', opacity=0.5))
    fig.update_layout(margin={"r":0,"t":1,"l":0,"b":1}, height=300)
    return fig

# %%

def get_callbacks(app):
### 인트로 ------------------------------------------------------------------
    ## 거래 추이
    @app.callback(
        Output('trend', 'figure'),
        Input('dropdown_gu', 'value'),
        Input('dropdown_area', 'value'),
        Input('date-picker-range-input', 'start_date'),
        Input('date-picker-range-input', 'end_date'))
    def update_trend(gu, area, start_date, end_date):
        df = df_basic.copy()
        if start_date and end_date:
            df = df[(df['거래일'] >= start_date) & (df['거래일'] <= end_date)]
        if gu:
            df = df[df['자치구'] == gu]
        if area:
            df = df[df['전용면적'] == area]
        # 거래일별 아파트 거래건수 선그래프를 출력한다.
        df_trend = df.groupby('거래일')['일련번호'].count().reset_index()
        fig = px.line(df_trend, x='거래일', y='일련번호')
        fig.update_xaxes(title='', tickformat='%y-%m-%d') 
        fig.update_yaxes(title='', showticklabels=False) 
        fig.update_layout( margin={"r":0,"t":0,"l":0,"b":0}, height=250)
        return fig            
        
    ## 최고 및 최저 거래가 테이블
    @app.callback(  
        Output('high_price_tbl', 'children'), 
        Output('low-price-tbl', 'children'), 
        Input('dropdown_gu', 'value'),
        Input('dropdown_area', 'value'),
        Input('date-picker-range-input', 'start_date'),
        Input('date-picker-range-input', 'end_date'))
    def update_high_price(gu, area, start_date, end_date):
        df = df_basic.copy()
        if start_date and end_date: # 시작일과 종료일이 선택된 경우
            df = df[(df['거래일'] >= start_date) & (df['거래일'] <= end_date)]
        if gu: # 자치구가 선택된 경우       
            df = df[df['자치구'] == gu]
        if area: # 면적이 선택된 경우
            df = df[df['전용면적'] == area]
        return draw_high_price_tbl(df), draw_low_price_tbl(df)   
    
    # 최고 거래가 테이블 행 선택시 라인차트와 맵 그래프 출력
    @app.callback(
        Output('high_price_map', 'figure'),
        Output('high_price_line', 'figure'), 
        Input('high_price_tbl_2', 'selectedRows'))
    def update_table_map_line(row):
        index = row[0]['index']
        unit = row[0]['거래단위']
        df_map = df_basic[df_basic.index == index]
        df_line = df_basic[df_basic['거래단위'] == unit]
        return draw_high_price_map(df_map), draw_high_price_line(df_line)

    # 최고 거래가 테이블 행 선택시 아파트 이미지 출력
    @app.callback(
        Output('high-apt-image', 'children'), 
        Input('high_price_tbl_2', 'selectedRows'))
    def update_photo(row):
        lat = row[0]['위도']
        lon = row[0]['경도']
        danji_id = row[0]['일련번호']
        dong = row[0]['행정동']
        name = row[0]['아파트']    
        path = './assets/apt_img/'
        # path에 danji_id.gif 파일이 있으면 이미지를 출력함
        if row[0]['일련번호'] + '.gif' in os.listdir(path):
            img = html.Img(src=path + row[0]['일련번호'] + '.gif')
        else:
            get_data.apt_image(lat, lon, danji_id, dong, name)
            img = html.Img(src=path + row[0]['일련번호'] + '.gif', height=300, width=400)
        return img
    
    # 최저 거래가 테이블 행 선택시 라인차트와 맵 그래프 출력
    @app.callback(
        Output('low-price-map', 'figure'),
        Output('low-price-line', 'figure'), 
        Input('low-price-tbl-2', 'selectedRows'))
    def update_table_map_line(row):
        index = row[0]['index']
        unit = row[0]['거래단위']
        df_map = df_basic[df_basic.index == index]
        df_line = df_basic[df_basic['거래단위'] == unit]
        return draw_high_price_map(df_map), draw_high_price_line(df_line)

    # 최저 거래가 테이블 행 선택시 아파트 이미지 출력
    @app.callback(
        Output('low-apt-image', 'children'), 
        Input('low-price-tbl-2', 'selectedRows'))
    def update_photo(row):
        lat = row[0]['위도']
        lon = row[0]['경도']
        danji_id = row[0]['일련번호']
        dong = row[0]['행정동']
        name = row[0]['아파트']    
        path = './assets/apt_img/'
        # path에 danji_id.gif 파일이 있으면 이미지를 출력함
        if row[0]['일련번호'] + '.gif' in os.listdir(path):
            img = html.Img(src=path + row[0]['일련번호'] + '.gif')
        else:
            get_data.apt_image(lat, lon, danji_id, dong, name)
            img = html.Img(src=path + row[0]['일련번호'] + '.gif', height=300, width=400)
        return img

    # collapse top5
    @app.callback(
        Output("collapse-graph-top5", "is_open"), 
        Input("collapse-button-top5", "n_clicks"), 
        State("collapse-graph-top5", "is_open"))
    def toggle_collapse_top5(n, is_open):
        if n:
            return not is_open
        return is_open
    
    # collapse low5
    @app.callback(
        Output("collapse-graph-low5", "is_open"), 
        Input("collapse-button-low5", "n_clicks"), 
        State("collapse-graph-low5", "is_open"))
    def toggle_collapse_low5(n, is_open):
        if n:
            return not is_open
        return is_open
   
    ## 관련 뉴스
    @app.callback(
        Output('apt-news', 'children'),
        Input('interval-news', 'n_intervals'))
    def update_news(n):
        df_news = pd.DataFrame(get_data.apt_news()) # 뉴스 데이터를 가져와서 데이터프레임으로 변환
        news_grid = dag.AgGrid(
            id = 'grid',
            rowData = df_news.to_dict('records'),
            columnDefs=[
                {"field": "Title", "headerName": "제목", "editable": True, "wrapText": True, "cellStyle": {"wordBreak": "normal", "lineHeight": "unset"}, "width": 200}, 
                {"field": "Description", "headerName": "내용", "editable": True, "wrapText": True,  "cellStyle": {"wordBreak": "normal", "lineHeight": "unset"}, "width": 450}, 
                {"field": "PublicationData", "headerName": "발행일시", "editable": True, "width": 150},        
                {"field": "OriginalLink", "headerName": "원문링크", "editable": True, "cellRenderer": "markdown"},
            ],
            defaultColDef={"resizable": True},
            columnSize="sizeToFit",
            dashGridOptions={"rowHeight": 80})
        return news_grid

### 거래건수 ----------------------------------------------------------------

    @app.callback(
        Output('pie', 'figure'),
        Input('dropdown_gu', 'value'),
        Input('dropdown_area', 'value'),
        Input('date-picker-range-input', 'start_date'),
        Input('date-picker-range-input', 'end_date'))
    def update_pie(gu, area, start_date, end_date):
        df = df_price.copy()
        if start_date and end_date:
            df = df[(df['거래일'] >= start_date) & (df['거래일'] <= end_date)]
        if gu:
            df = df[df['자치구'] == gu]
        if area:
            df = df[df['전용면적'] == area]
        return draw_pie(df)
        
    @app.callback(
        Output('hist', 'figure'), 
        Input('dropdown_gu', 'value'))
    def update_hist(val):
        if val is None:
            return draw_hist(df_price)
        else:
            df = df_price[df_price['자치구']==val] 
            return draw_hist(df)    
        
    @app.callback(
        Output('map', 'figure'), 
        Input('dropdown_gu', 'value'))
    def update_map(val):
        if val is None:
            return draw_map(df_price)
        else:
            df = df_price[df_price['자치구']==val] 
            return draw_map(df)    
        
    @app.callback(
        Output('facet_pie', 'figure'), 
        Input('dropdown_gu', 'value'))
    def update_facet_pie(val):
        if val is None:
            return draw_facet_pie(df_price)
        else:
            df = df_price[df_price['자치구']==val] 
            return draw_facet_pie(df)    

    ## 거래가 변화 테이블
    @app.callback(  
        Output('price-trend-table', 'children'), 
        Input('dropdown_gu', 'value'),
        Input('dropdown_area', 'value'),
        Input('date-picker-range-input', 'start_date'),
        Input('date-picker-range-input', 'end_date'))
    def update_price_trend_table(gu, area, start_date, end_date):
        df = df_price.copy()
        # df = df[['행정동', '아파트', '전용면적', '거래일', '거래금액', '직전거래일', '직전거래금액', '변화율']]
        df['거래일'] = df['거래일'].dt.strftime('%Y-%m-%d')
        df.sort_values(by='변화율', ascending=False, inplace=True)
        df.reset_index(drop=False, inplace=True) # 맵에서 index가 필요하므로 컬럼으로 변환하여 활용
        if start_date and end_date: # 시작일과 종료일이 선택된 경우
            df = df[(df['거래일'] >= start_date) & (df['거래일'] <= end_date)]
        if gu: # 자치구가 선택된 경우       
            df = df[df['자치구'] == gu]
        if area: # 면적이 선택된 경우
            df = df[df['전용면적'] == area]
        grid = dag.AgGrid(
            id='price-trend-2', # *** 테이블 행 선택시 콜백함수의 Input으로 사용하기 위하여 id를 지정함
            rowData = df.to_dict('records'),
            defaultColDef={'resizable': True, 'sortable': True, 'filter': True},
            columnDefs=[
                {'field': '행정동'},
                {'field': '아파트'},
                {'field': '전용면적', 'valueFormatter': {'function': 'params.value + "㎡"'}}, # 단위 추가
                {'field': '거래일', 'cellRenderer': 'dateCellRenderer'},
                {'field': '거래금액','headerName': '거래금액(만원)', 'type': 'numericColumn','valueFormatter': {'function': 'd3.format(",")(params.value)'}}, # 오른 정렬, 천단위 쉼표
                {'field': '직전거래일', 'cellRenderer': 'dateCellRenderer'},
                {'field': '직전거래금액','headerName': '직전거래금액', 'type': 'numericColumn','valueFormatter': {'function': 'd3.format(",")(params.value)'}}, # 오른 정렬, 천단위 쉼표
                {'field': '변화율', 'valueFormatter': {'function': 'params.value + "%"'}}, # 단위 추가
                {'field': '변화'},
            ],
            dashGridOptions={'rowSelection': 'single'},
            selectedRows=df.head(1).to_dict('records'), # 콜백함수의 Input으로 사용하기 위하여 선택된 행을 지정함
            columnSize='sizeToFit', # 컬럼 사이즈를 자동으로 조정함,
            style={'height': 270, 'width': '100%'}, 
        )
        return grid  
     
    @app.callback(
        Output('table-map', 'figure'), 
        Output('table-line', 'figure'), 
        Input('price-trend-2', 'selectedRows'))
    def update_table_line_map(row):
        index = row[0]['index']
        unit = row[0]['거래단위']
        df_map = df_price[df_price.index == index]
        df_line = df_basic[df_basic['거래단위'] == unit]
        return draw_high_price_map(df_map), draw_high_price_line(df_line)

    # 테이블 행 선택시 아파트 이미지 출력
    @app.callback(
        Output('table-image', 'children'), 
        Input('price-trend-2', 'selectedRows'))
    def update_photo(row):
        lat = row[0]['위도']
        lon = row[0]['경도']
        danji_id = row[0]['일련번호']
        dong = row[0]['행정동']
        name = row[0]['아파트']    
        path = './assets/apt_img/'
        # path에 danji_id.gif 파일이 있으면 이미지를 출력함
        if row[0]['일련번호'] + '.gif' in os.listdir(path):
            img = html.Img(src=path + row[0]['일련번호'] + '.gif')
        else:
            get_data.apt_image(lat, lon, danji_id, dong, name)
            img = html.Img(src=path + row[0]['일련번호'] + '.gif', height=300, width=400)
        return img

    @app.callback(
        Output('div_table', 'children'), 
        Input('dropdown_gu', 'value'))
    def update_price_table(val):
        if val is None:
            df_table = df_price[['행정동', '아파트', '전용면적', '거래일', '거래금액', '직전거래일', '직전거래금액', '변화율']]
            return draw_price_table(df_table)
        else:
            df_table = df_price[df_price['자치구']==val]
            ddf_table = df_table[['행정동', '아파트', '전용면적', '거래일', '거래금액', '직전거래일', '직전거래금액', '변화율']] 
            return draw_price_table(ddf_table)   
        
    ### 테이블의 행 선택시 라인차트와 맵 그래프 출력
    @app.callback(
        Output('table_line', 'figure'), 
        Output('table_map', 'figure'), 
        Input('price_table', 'selected_rows'))
    def update_table_line_map(row):
        if row is None:
            return no_update
        else:
            unit_num = df_price[df_price.index == row[0]]['거래단위'].values[0]
            df_line = df_basic[df_basic['거래단위'] == unit_num]
            df_map = df_price[df_price['거래단위'] == unit_num]
            return draw_table_line(df_line), draw_table_map(df_map)
        
    ### collapse
    @app.callback(
        Output("collapse-graph-price", "is_open"), 
        Input("collapse-button-price", "n_clicks"), 
        State("collapse-graph-price", "is_open"))
    def toggle_collapse_price(n, is_open):
        if n:
            return not is_open
        return is_open
        
    return 



# %%
app = Dash(__name__, 
           suppress_callback_exceptions=True, 
           external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP]
           )

tabs_styles = {'height': '55px', 'width': '500px'}

app.layout = dbc.Container([
    dbc.Row([
        html.H1('서울시 아파트 거래 분석 대시보드', className='text-center mt-4'),
        html.H4('plotly Dash 예제 프로젝트', className='text-center, mb-4'),
    ]),
    dbc.Row([
        dbc.Col([
            html.H5([html.I(className='bi bi-check-circle-fill me-2'), '조건 필터링'], className='mt-4 text-danger'),
            date_pick,
            drop_gu,
            drop_area,
            html.P(seoul_now)
            ], className='border border-primary rounded p-3 bg-light mt-1 mb-3', width=2),
        dbc.Col([
            dcc.Tabs([
                dcc.Tab(
                    label='인트로',
                    children=[
                        dbc.Card([
                            dbc.CardHeader([html.I(className='bi bi-building me-2'), '거래추이']),
                            dbc.CardBody([
                                dcc.Graph(id='trend'),   
                            ])
                        ], className='mt-3'),
                        dbc.Card([
                            dbc.CardHeader([html.I(className='bi bi-building me-2'), '최고가 거래 Top 5']),
                            dbc.CardBody([
                                html.Div(id='high_price_tbl'),
                                html.Div([
                                    dbc.Button("상세보기", id="collapse-button-top5", className="mt-3 mb-2 opacity-75", color="primary", n_clicks=0),
                                    dbc.Collapse([
                                        dbc.Row([
                                            dbc.Col([
                                                html.H6('아파트 위치', className='text-center mb-2'), 
                                                html.Div(dcc.Graph(id='high_price_map'), className='m-auto'), 
                                            ], width=6, ),
                                            dbc.Col([
                                                html.H6('아파트 인근 모습', className='text-center mb-2'),
                                                html.Div(id='high-apt-image'),
                                            ], width=6),
                                        ]),
                                        html.Div([
                                            html.H6('거래금액 추이', className='text-center mb-2'),
                                            dcc.Graph(id='high_price_line')
                                        ], className='mt-3'),                                             
                                    ], id="collapse-graph-top5", is_open=False)
                                ]),                
                            ])
                        ], className='mt-3'),
                        dbc.Card([
                            dbc.CardHeader([html.I(className='bi bi-building me-2'), '최저가 거래 Top 5']),
                            dbc.CardBody([
                                html.Div(id='low-price-tbl'),
                                html.Div([
                                    dbc.Button("상세보기", id="collapse-button-low5", className="mt-3 mb-2 opacity-75", color="primary", n_clicks=0),
                                    dbc.Collapse([
                                        dbc.Row([
                                            dbc.Col([
                                                html.H6('아파트 위치', className='text-center mb-2'), 
                                                html.Div(dcc.Graph(id='low-price-map'), className='m-auto'), 
                                            ], width=6, ),
                                            dbc.Col([
                                                html.H6('아파트 인근 모습', className='text-center mb-2'),
                                                html.Div(id='low-apt-image'),
                                            ], width=6),
                                        ]),
                                        html.Div([
                                            html.H6('거래금액 추이', className='text-center mb-2'),
                                            dcc.Graph(id='low-price-line')
                                        ], className='mt-3'),                                             
                                    ], id="collapse-graph-low5", is_open=False)
                                ]),                
                            ])
                        ], className='mt-3'),
                        dbc.Card([
                            dbc.CardHeader([html.I(className='bi bi-building me-2'), '관련 뉴스(news.naver.com)_1시간마다 업데이트']),
                            dbc.CardBody([
                                html.Div(id='apt-news'),
                                dcc.Interval(id='interval-news', interval=1000*60*60, n_intervals=0) # 1시간마다 뉴스 업데이트       
                            ])
                        ], className='mt-3'),
                    ]
                ),
                dcc.Tab(
                    label='거래건수',
                    children=[
                        dbc.Card([
                            dbc.CardHeader([html.I(className='bi bi-calendar3 me-2'), '기간별 아파트 매매 건수']),
                            dbc.CardBody([
                                html.Small('기간 버튼을 클릭하거나 아래 그래프의 범위를 드래그하여 기간을 선택하세요.', className='card-text text-primary mb-3'),
                                dcc.Graph(figure=draw_line(df_basic)),
                            ]), 
                        ], className='mt-3'),
                        dbc.Card([
                            dbc.CardHeader([html.I(className='bi bi-border-outer me-2'), '자치구별 아파트 매매 건수']),
                            dbc.CardBody([
                                html.P('지도에 마우스를 올리면 자치구와 거래건수를 확인할 수 있습니다.', className='card-text text-primary mb-3'),
                                dcc.Graph(figure=draw_choropleth(df_basic)),
                            ]), 
                        ], className='mt-2'),                                                         
                        dbc.Row([
                            dbc.Col(
                                dbc.Card([
                                    dbc.CardHeader([html.I(className='bi bi-building-fill me-2'), '아파트별 매매 건수(테이블)']),                                
                                    dbc.CardBody([
                                        html.P('컬럼 옆의 삼각 아이콘을 클릭하면 정렬됩니다.', className='card-text text-primary mb-3'),
                                        draw_count_table(df_basic),
                                    ])
                                ]), width=5
                            ),
                            dbc.Col(
                                dbc.Card([
                                    dbc.CardHeader([html.I(className='bi bi-building-fill-check me-2'), '아파트별 매매 건수(지도)']),     
                                    dbc.CardBody([
                                        html.P('붉은색 원은 아파트의 위치이며, 원의 크기는 매매 건수를 표시합니다.', className='card-text text-primary mb-3'),
                                        dcc.Graph(figure=draw_count_map(df_basic)),
                                    ])
                                ]), width=7)
                            ], className='mt-2'),
                        dbc.Card([
                            dbc.CardHeader([html.I(className='bi bi-graph-up-arrow me-2'), '자치구 면적별 매매건수 변화 추이']),
                            dbc.CardBody(dcc.Graph(figure=draw_count_line(df_basic)))
                        ], className='mt-2'),                                             
                        dbc.Card([
                            dbc.CardHeader([html.I(className='bi bi-graph-up-arrow me-2'),
                            dbc.CardBody([
                                html.P('자치구의 전용 면적별 매매건수 변화 추이를 표시합니다.', className='card-text text-primary mb-3'),
                                dcc.Graph(figure=draw_count_line(df_basic)),
                                ])
                            ], className='mt-2')                                             
                        ])
                    ]
                ),
                dcc.Tab(
                    label='가격변화',
                    children=[
                        dbc.Row([
                            dbc.Col(
                                dbc.Card([
                                    dbc.CardHeader([html.I(className='bi bi-pie-chart-fill me-2'), '거래가격 변화 분포']),
                                    dbc.CardBody(dcc.Graph(id='pie')),
                                ]), width=5
                            ),
                            dbc.Col(
                                dbc.Card([
                                    dbc.CardHeader([html.I(className='bi bi-bar-chart-fill me-2'), '거래가격 변화율 분포']),
                                    dbc.CardBody(dcc.Graph(id='hist')),
                                ]), width=7
                            ),                            
                        ], className='mt-3'),
                        dbc.Card([
                            dbc.CardHeader([html.I(className='bi bi-geo-alt-fill me-2'), '매매가 변화 지도 - 상승(붉은원) | 하락(파란원)']),
                            dbc.CardBody(dcc.Graph(id='map')),
                        ], className='mt-3'),
                        html.Div([
                            dbc.Button("자치구별 변화율 파이차트", id="collapse-button-price", className="mb-3 mt-3", color="primary", n_clicks=0),
                            dbc.Collapse(dcc.Graph(id='facet_pie'), id="collapse-graph-price", is_open=False)
                        ]),
                        dbc.Card([
                            dbc.CardHeader([html.I(className='bi bi-building-fill me-2'), '아파트별 매매가 변화 - 해당 행을 선택하면 상세사항 확인 가능']),
                            dbc.CardBody([
                                html.Div(id='price-trend-table'),
                                dbc.Row([
                                    dbc.Col([
                                        html.H6('아파트 위치', className='text-center mb-2'), 
                                        html.Div(dcc.Graph(id='table-map'), className='m-auto'), 
                                    ], width=6, ),
                                    dbc.Col([
                                        html.H6('아파트 인근 모습', className='text-center mb-2'),
                                        html.Div(id='table-image'),
                                    ], width=6),
                                    dcc.Graph(id='table-line'),
                                ]),
                                
                            ]),
                        ], className='mt-3'),

                       
                    ]
                )
            ], style=tabs_styles)
        ], width=10),
    ]), 
    dbc.Row([
    html.P('made by 데이터공작소', className='text-center mt-3 mb-4')
    ]),
])

get_callbacks(app)

if __name__ == '__main__':
    app.run()

# %%



