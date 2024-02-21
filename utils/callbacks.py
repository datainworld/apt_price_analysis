import pandas as pd
from dash import Dash, html, dcc, dash_table, Input, Output, no_update, State, callback
import dash_ag_grid as dag
import plotly.express as px
import dash_bootstrap_components as dbc
import json
import geopandas as gpd
import os
import warnings
warnings.filterwarnings('ignore')
from utils import get_data # openAPI를 이용하여 아파트 이미지와 뉴스 데이터를 가져오는 모듈
from utils import get_graph # 아파트 거래 데이터를 이용하여 그래프를 그리는 모듈

def get_callbacks(app, df_basic, df_price, area_top10):

### 1. 거래가격 ------------------------------------------------------------------

    ## 1.1 아파트 거래가격 분포
    @app.callback(
        Output("avg-price-card", "children"),
        Output("median-price-card", "children"),
        Output("mode-price-card", "children"),
        Output("price-histogram", "figure"),
        Input('dropdown-gu', 'value'),
        Input('dropdown-size', 'value'),
        Input('date-picker-range-input', 'start_date'),
        Input('date-picker-range-input', 'end_date'),
        Input("price-radio", "value"))
    def draw_price_card(gu, size, start_date, end_date, value):
        df_temp = df_basic.copy()
        if start_date and end_date: # 시작일과 종료일이 선택된 경우
            df_temp = df_temp[(df_temp['거래일'] >= start_date) & (df_temp['거래일'] <= end_date)]
        if gu: # 자치구가 선택된 경우
            df_temp = df_temp[df_temp['자치구'] == gu]
        if size: # 면적이 선택된 경우
            df_temp = df_temp[df_temp['전용면적'] == size]
        if value == 'unit':
            df_temp['거래금액'] = df_temp['거래금액'] / df_temp['전용면적']
        # 평균가격, 중위가격, 최빈가격 카드에 표시할 값
        avg_price = df_temp['거래금액'].mean().round(0)
        formatted_avg_price = '{:,.0f}'.format(avg_price)
        median_price = df_temp['거래금액'].median().round(0)
        formatted_median_price = '{:,.0f}'.format(median_price)
        mode_price = df_temp['거래금액'].mode().round(0)
        formatted_mode_price = '{:,.0f}'.format(mode_price[0])
        low_price = df_temp['거래금액'].min().round(0)
        formatted_low_price = '{:,.0f}'.format(low_price)
        high_price = df_temp['거래금액'].max().round(0)
        formatted_high_price = '{:,.0f}'.format(high_price)
        #df_basic 거래금액 컬럼의 히스토그램 차트
        fig = px.histogram(df_temp, x='거래금액', nbins=50)
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=300)
        fig.update_yaxes(title='거래건수', tickformat=',')
        fig.update_xaxes(title='거래금액(단위:만원)',tickformat=',')
        fig.add_vline(x=avg_price, line_width=2, line_dash="dash", line_color="red")
        fig.add_vline(x=median_price, line_width=2, line_dash="dash", line_color="blue")
        fig.add_vline(x=mode_price[0], line_width=2, line_dash="dash", line_color="green")
        fig.add_vline(x=low_price, line_width=2, line_dash="dash", line_color="black")
        fig.add_vline(x=high_price, line_width=2, line_dash="dash", line_color="black")
        fig.add_annotation(
            x=avg_price,
            text="평균가격(" + formatted_avg_price + ")",
            font=dict(size=13, color='red'),
            showarrow=True,
            arrowhead=5,
            arrowcolor='red',
            ax=100, # x축 위치 조정
            yshift=150) # y축 위치 조정
        fig.add_annotation(
            x=median_price,
            text="중위가격(" + formatted_median_price + ")",
            font=dict(size=13, color='blue'),
            showarrow=True,
            arrowhead=5,
            arrowcolor='blue',
            ax=100, # x축 위치 조정
            yshift=100) # y축 위치 조정
        fig.add_annotation(
            x=mode_price[0],
            text="최빈가격(" + formatted_mode_price + ")",
            font=dict(size=13, color='green'),
            showarrow=True,
            arrowhead=5,
            arrowcolor='green',
            ax=100, # x축 위치 조정
            yshift=50) # y축 위치 조정
        fig.add_annotation(
            x=low_price,
            text="최저가격(" + formatted_low_price + ")",
            font=dict(size=13, color='black'),
            showarrow=True,
            arrowhead=5,
            arrowcolor='black',
            ax=100, # x축 위치 조정
            yshift=00) # y축 위치 조정
        fig.add_annotation(
            x=high_price,
            text="최고가격(" + formatted_high_price + ")",
            font=dict(size=13, color='black'),
            showarrow=True,
            arrowhead=5,
            arrowcolor='black',
            ax=-100, # x축 위치 조정
            yshift=200) # y축 위치 조정
        return formatted_avg_price, formatted_median_price, formatted_mode_price, fig

    ## 1.2 최고가 거래 Top
    @app.callback(
        Output('high-price-grid', 'children'),
        Input('dropdown-gu', 'value'),
        Input('dropdown-size', 'value'),
        Input('date-picker-range-input', 'start_date'),
        Input('date-picker-range-input', 'end_date'))
    def update_high_price(gu, size, start_date, end_date):
        df = df_basic.copy()
        if start_date and end_date: # 시작일과 종료일이 선택된 경우
            df = df[(df['거래일'] >= start_date) & (df['거래일'] <= end_date)]
        if gu: # 자치구가 선택된 경우
            df = df[df['자치구'] == gu]
        if size: # 면적이 선택된 경우
            df = df[df['전용면적'] == size]
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

    ## 1.3 최고가 상세보기
    @app.callback(
        Output("collapse-graph-top5", "is_open"),
        Input("collapse-button-top5", "n_clicks"),
        State("collapse-graph-top5", "is_open"))
    def toggle_collapse_top5(n, is_open):
        if n:
            return not is_open
        return is_open

    ## 1.4 최고가 테이블 행 선택시 라인차트와 맵 그래프 출력
    @app.callback(
        Output('high-price-map', 'figure'),
        Output('high-price-line', 'figure'),
        Input('high_price_tbl_2', 'selectedRows'))
    def update_table_map_line(row):
        index = row[0]['index']
        unit = row[0]['거래단위']
        df_map = df_basic[df_basic.index == index]
        df_line = df_basic[df_basic['거래단위'] == unit]
        return get_graph.draw_price_map(df_map), get_graph.draw_price_line(df_line)

    ## 1.5 최고 거래가 테이블 행 선택시 아파트 이미지 출력
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

    ## 1.6 최저가 거래 Top5
    @app.callback(
        Output('low-price-grid', 'children'),
        Input('dropdown-gu', 'value'),
        Input('dropdown-size', 'value'),
        Input('date-picker-range-input', 'start_date'),
        Input('date-picker-range-input', 'end_date'))
    def update_high_price(gu, size, start_date, end_date):
        df = df_basic.copy()
        if start_date and end_date: # 시작일과 종료일이 선택된 경우
            df = df[(df['거래일'] >= start_date) & (df['거래일'] <= end_date)]
        if gu: # 자치구가 선택된 경우
            df = df[df['자치구'] == gu]
        if size: # 면적이 선택된 경우
            df = df[df['전용면적'] == size]
        df = df.sort_values(by='거래금액', ascending=True)
        df = df.drop_duplicates(subset='일련번호', keep='first')
        df.reset_index(drop=False, inplace=True) # 맵에서 index가 필요하므로 컬럼으로 변환하여 활용
        tbl = dag.AgGrid(
            id='low-price-tbl-2', # *** 테이블 행 선택시 콜백함수의 Input으로 사용하기 위하여 id를 지정함
            rowData = df.head(5).to_dict('records'),
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
            selectedRows=df.head(1).to_dict('records'), # 콜백함수의 Input으로 사용하기 위하여 선택된 행을 지정함
            columnSize='sizeToFit', # 컬럼 사이즈를 자동으로 조정함,
            style={'height': 270, 'width': '100%'},
        )
        return tbl

    ## 1.7 최저가 상세보기
    @app.callback(
        Output("collapse-graph-low5", "is_open"),
        Input("collapse-button-low5", "n_clicks"),
        State("collapse-graph-low5", "is_open"))
    def toggle_collapse_low5(n, is_open):
        if n:
            return not is_open
        return is_open

    # 1.8 최저가 테이블 행 선택시 라인차트와 맵 그래프 출력
    @app.callback(
        Output('low-price-map', 'figure'),
        Output('low-price-line', 'figure'),
        Input('low-price-tbl-2', 'selectedRows'))
    def update_table_map_line(row):
        index = row[0]['index']
        unit = row[0]['거래단위']
        df_map = df_basic[df_basic.index == index]
        df_line = df_basic[df_basic['거래단위'] == unit]
        return get_graph.draw_price_map(df_map), get_graph.draw_price_line(df_line)

    # 1.9 최저가 테이블 행 선택시 아파트 이미지 출력
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

    ## 1.10 관련 뉴스
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

### 2.거래건수 ------------------------------------------------------------------

    ## 2.1 기간별 아파트 매매 건수
    @app.callback(
        Output('transaction-count-line', 'figure'),
        Input('dropdown-gu', 'value'),
        Input('dropdown-size', 'value'))
    def update_transaction_count_line(gu, size):
        df = df_basic.copy()
        if gu:
            df = df[df['자치구'] == gu]
        if size:
            df = df[df['전용면적'] == size]
        df.set_index('거래일', inplace=True, drop=False)
        cnt = df.resample('D')['일련번호'].count().reset_index()
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
                ]),
            ),
            title='',
            tickformat='%y-%m'
        )
        fig.update_yaxes(title='')
        fig.update_layout(margin={"r":0,"t":15,"l":0,"b":0}, height=300)
        return fig

    ## 2.2 자치구별 아파트 매매 건수
    @app.callback(
        Output('transaction-count-map-cholopleth', 'figure'),
        Input('dropdown-size', 'value'),
        Input('date-picker-range-input', 'start_date'),
        Input('date-picker-range-input', 'end_date'))
    def update_transaction_count_map(size, start_date, end_date):
        df = df_basic.copy()
        if start_date and end_date: # 시작일과 종료일이 선택된 경우
            df = df[(df['거래일'] >= start_date) & (df['거래일'] <= end_date)]
        if size: # 면적이 선택된 경우
            df = df[df['전용면적'] == size]
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

    ## 2.3 아파트별 매매 건수(테이블)
    @app.callback(
        Output('transaction-count-grid', 'children'),
        Input('dropdown-gu', 'value'),
        Input('dropdown-size', 'value'),
        Input('date-picker-range-input', 'start_date'),
        Input('date-picker-range-input', 'end_date'))
    def update_transaction_count_grid(gu, size, start_date, end_date):
        df = df_basic.copy()
        if start_date and end_date:
            df = df[(df['거래일'] >= start_date) & (df['거래일'] <= end_date)]
        if gu:
            df = df[df['자치구'] == gu]
        if size:
            df = df[df['전용면적'] == size]
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

    ## 2.4 아파트별 매매 건수(지도)
    @app.callback(
        Output('transaction-count-map-bubble', 'figure'),
        Input('dropdown-gu', 'value'),
        Input('dropdown-size', 'value'),
        Input('date-picker-range-input', 'start_date'),
        Input('date-picker-range-input', 'end_date'))
    def update_transaction_count_map(gu, size, start_date, end_date):
        df = df_basic.copy()
        if start_date and end_date:
            df = df[(df['거래일'] >= start_date) & (df['거래일'] <= end_date)]
        if gu:
            df = df[df['자치구'] == gu]
        if size:
            df = df[df['전용면적'] == size]
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

    ## 2.5 자치구 면적별 매매건수 변화 추이
    @app.callback(
        Output('transaction-count-facet-line', 'figure'),
        Input('date-picker-range-input', 'start_date'),
        Input('date-picker-range-input', 'end_date'))
    def update_transaction_count_fact(start_date, end_date):
        df = df_basic.copy()
        if start_date and end_date:
            df = df[(df['거래일'] >= start_date) & (df['거래일'] <= end_date)]
        df.set_index('거래일', inplace=True, drop=False)
        top5 = df['전용면적'].value_counts().head(5).index
        cnt_top5 = df[df['전용면적'].isin(top5)]
        cnt_top5_month = cnt_top5.groupby(['전용면적', '자치구']).resample('M')['일련번호'].count().reset_index() #
        fig = px.line(cnt_top5_month, x='거래일', y='일련번호', color='전용면적', facet_col='자치구', facet_col_wrap=5)
        fig.update_yaxes(title='')
        fig.update_xaxes(title='')
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=600)
        return fig

### 3.가격변화 ----------------------------------------------------------------

    ## 3.1 거래가격 변화 분포(파이 차트)
    @app.callback(
        Output('price-change-pie', 'figure'),
        Input('dropdown-gu', 'value'),
        Input('dropdown-size', 'value'),
        Input('date-picker-range-input', 'start_date'),
        Input('date-picker-range-input', 'end_date'))
    def update_pie(gu, size, start_date, end_date):
        df = df_price.copy()
        if start_date and end_date:
            df = df[(df['거래일'] >= start_date) & (df['거래일'] <= end_date)]
        if gu:
            df = df[df['자치구'] == gu]
        if size:
            df = df[df['전용면적'] == size]
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

    ## 3.2 거래가격 변화율 분포(히스토그램)
    @app.callback(
        Output('price-change-hist', 'figure'),
        Input('dropdown-gu', 'value'),
        Input('dropdown-size', 'value'),
        Input('date-picker-range-input', 'start_date'),
        Input('date-picker-range-input', 'end_date'))
    def update_hist(gu, size, start_date, end_date):
        df = df_price.copy()
        if start_date and end_date:
            df = df[(df['거래일'] >= start_date) & (df['거래일'] <= end_date)]
        if gu:
            df = df[df['자치구'] == gu]
        if size:
            df = df[df['전용면적'] == size]
        fig = px.histogram(df, x='변화율', nbins=50)
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=200)
        return fig

    ## 3.3 매매가 변화 지도
    @app.callback(
        Output('price_change_map', 'figure'),
        Input('dropdown-gu', 'value'),
        Input('dropdown-size', 'value'),
        Input('date-picker-range-input', 'start_date'),
        Input('date-picker-range-input', 'end_date'))
    def update_map(gu, size, start_date, end_date):
        df = df_price.copy()
        if start_date and end_date:
            df = df[(df['거래일'] >= start_date) & (df['거래일'] <= end_date)]
        if gu:
            df = df[df['자치구'] == gu]
        if size:
            df = df[df['전용면적'] == size]
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
        fig.update_traces(
            marker=dict(size=10),
            opacity=0.3) # 마커 투명도 설정
        return fig

   ## 3.4 자치구별 변화율 파이차트 버튼
    @app.callback(
        Output("collapse-graph-price", "is_open"),
        Input("collapse-button-price", "n_clicks"),
        State("collapse-graph-price", "is_open"))
    def toggle_collapse_price(n, is_open):
        if n:
            return not is_open
        return is_open

   ## 3.5 자치구별 변화율 파이차트
    @app.callback(
        Output('price-change-facet-pie', 'figure'),
        Input('dropdown-gu', 'value'),
        Input('dropdown-size', 'value'),
        Input('date-picker-range-input', 'start_date'),
        Input('date-picker-range-input', 'end_date'))
    def update_facet_pie(gu, size, start_date, end_date):
        df = df_price.copy()
        if start_date and end_date:
            df = df[(df['거래일'] >= start_date) & (df['거래일'] <= end_date)]
        if gu:
            df = df[df['자치구'] == gu]
        if size:
            df = df[df['전용면적'] == size]

        df = df.groupby(['자치구','변화'])['일련번호'].count().reset_index()
        fig = px.pie(df, values='일련번호', names='변화',
                    color='변화', color_discrete_map={'상승':'red', '하락':'blue', '유지':'green'},
                    facet_col='자치구', facet_col_wrap=5)
        fig.update_traces(direction='clockwise')
        fig.update_layout(height=600)
        return fig

    ## 3.6 아파트별 매매가 변화
    @app.callback(
        Output('price-change-grid', 'children'),
        Input('dropdown-gu', 'value'),
        Input('dropdown-size', 'value'),
        Input('date-picker-range-input', 'start_date'),
        Input('date-picker-range-input', 'end_date'))
    def update_price_trend_table(gu, size, start_date, end_date):
        df = df_price.copy()
        # df = df[['행정동', '아파트', '전용면적', '거래일', '거래금액', '직전거래일', '직전거래금액', '변화율']]
        df['거래일'] = df['거래일'].dt.strftime('%Y-%m-%d')
        df.sort_values(by='변화율', ascending=False, inplace=True)
        df.reset_index(drop=False, inplace=True) # 맵에서 index가 필요하므로 컬럼으로 변환하여 활용
        if start_date and end_date: # 시작일과 종료일이 선택된 경우
            df = df[(df['거래일'] >= start_date) & (df['거래일'] <= end_date)]
        if gu: # 자치구가 선택된 경우
            df = df[df['자치구'] == gu]
        if size: # 면적이 선택된 경우
            df = df[df['전용면적'] == size]
        grid = dag.AgGrid(
            id='price-change-grid-inner', # *** 테이블 행 선택시 콜백함수의 Input으로 사용하기 위하여 id를 지정함
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

    ## 3.7 테이블 행 선택시 라인차트와 맵 그래프 출력
    @app.callback(
        Output('price-change-grid-map', 'figure'),
        Output('price-change-grid-line', 'figure'),
        Input('price-change-grid-inner', 'selectedRows'))
    def update_table_line_map(row):
        index = row[0]['index']
        unit = row[0]['거래단위']
        df_map = df_price[df_price.index == index]
        df_line = df_basic[df_basic['거래단위'] == unit]
        return get_graph.draw_price_map(df_map), get_graph.draw_price_line(df_line)

    ## 3.8 테이블 행 선택시 아파트 이미지 출력
    @app.callback(
        Output('price-change-grid-image', 'children'),
        Input('price-change-grid-inner', 'selectedRows'))
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
