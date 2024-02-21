import pandas as pd
from dash import Dash, html, dcc, dash_table, Input, Output, no_update, State, callback
import dash_bootstrap_components as dbc
import warnings
warnings.filterwarnings('ignore')
from utils import callbacks # 콜백 함수를 모아놓은 모듈

app = Dash(__name__,
           suppress_callback_exceptions=True,
           external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP])

#### 데이터 로드 =================================================================
DATA_PATH = '/home/datainworld/assets/data/'
df_basic = pd.read_csv(DATA_PATH + 'apt_basic_data.csv', parse_dates=['거래일'], date_format='%Y-%m-%d')
df_price = pd.read_csv(DATA_PATH + 'apt_price_data.csv', parse_dates=['거래일'], date_format='%Y-%m-%d')
area_top10 = df_basic['전용면적'].value_counts().sort_values(ascending=False).head(10).index.sort_values().tolist()

#### 탭 스타일 지정 ============================================================
tabs_styles = {'height': '55px', 'width': '500px'}

#### 필터링 인터랙션 ===========================================================
### 1. 날짜 필터링
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
### 2. 자치구 필터링
drop_gu = dcc.Dropdown(
    id='dropdown-gu',
    options=df_basic['자치구'].unique(),
    placeholder='자치구 선택')
### 3. 전용면적 필터링
drop_size = dcc.Dropdown(
    id='dropdown-size',
    options=[{'label': str(i) + '㎡', 'value': i} for i in area_top10],
    placeholder='면적(㎡) 선택')

#### 화면 구성 ================================================================
app.layout = dbc.Container([
    dbc.Row([
        html.H1('서울시 아파트 거래 데이터 분석', className='text-center mt-4'),
        html.H4('plotly Dash 예제 프로젝트', className='text-center mb-4'),
    ]),
    dbc.Row([
        dbc.Col([
            html.H5([html.I(className='bi bi-check-circle-fill me-2'), '조건 필터링'], className='mt-4 text-danger'),
            date_pick,
            drop_gu,
            drop_size,
            html.P('평균가격, 중위가격, 최빈가격에 대한 설명은...')
            ], className='border border-primary rounded p-3 bg-light mt-1 mb-3', width=2),
        dbc.Col([
            dcc.Tabs([
                ### 1. 인트로 탭 섹션 -----------------------------------------------------
                dcc.Tab(
                    label='거래가격',
                    children=[
                        ## 1. 거래가격 분포
                        dbc.Card([
                            dbc.CardHeader("아파트 거래가격 분포"),
                            dbc.CardBody([
                                dbc.Row(
                                    dcc.RadioItems(
                                        id='price-radio',
                                        options=[
                                            {'label': ' 아파트 가격   ', 'value': 'apt'},
                                            {'label': ' 평방미터(㎡)당 가격', 'value': 'unit'}],
                                        value='apt',
                                        inline=True), class_name='mb-3',
                                ),
                                dbc.Row([
                                    dbc.Col(
                                        dbc.Card([
                                            dbc.CardBody([
                                                    html.P("최빈가격", className="card-text text-center fs-5 fw-bolder lh-1"),
                                                    html.H5(id="mode-price-card", className="card-title text-center fs-1 fw-bolder lh-1", style={'color': 'green'}),
                                                    html.P("(단위 : 만원)", className="card-text text-center"),

                                                ]),
                                        ],style={'border-width': '2px', 'border-color': 'green', 'border-radius': '15px'}  ), width=3
                                    ),
                                    dbc.Col(
                                        dbc.Card([
                                            dbc.CardBody([
                                                    html.P("중위가격", className="card-text text-center fs-5 fw-bolder lh-1"),
                                                    html.H5(id="median-price-card", className="card-title text-center fs-1 fw-bolder lh-1", style={'color': 'blue'}),
                                                    html.P("단위 : 만원", className="card-text text-center"),
                                                ]),
                                        ],style={'border-width': '2px', 'border-color': 'blue', 'border-radius': '15px'}  ), width=3
                                    ),
                                    dbc.Col(
                                        dbc.Card([
                                            dbc.CardBody([
                                                    html.P("평균가격", className="card-text text-center fs-5 fw-bolder lh-1"),
                                                    html.H5(id="avg-price-card", className="card-title text-center fs-1 fw-bolder lh-1", style={'color': 'red'}),
                                                    html.P("단위: 만원", className="card-text text-center"),
                                                ]),
                                        ],style={'border-width': '2px', 'border-color': 'red', 'border-radius': '15px'}  ), width=3
                                    ),
                                ], className='mb-5 justify-content-center'),
                                dbc.Row([
                                    dbc.Col(dcc.Graph(id="price-histogram"), width=12),
                                ])
                            ]),
                        ], className='mt-3'),
                        dbc.Card([
                            dbc.CardHeader([html.I(className='bi bi-building me-2'), '최고가 거래 Top 5']),
                            dbc.CardBody([
                                ## 1.2 최고가 거래 Top 5
                                html.Div(id='high-price-grid'),
                                ## 1.3 최고가 상세보기
                                html.Div([
                                    dbc.Button("상세보기", id="collapse-button-top5", className="mt-3 mb-2 opacity-75", color="primary", n_clicks=0),
                                    dbc.Collapse([
                                        dbc.Row([
                                            ## 1.4 아파트 위치
                                            dbc.Col([
                                                html.H6('아파트 위치', className='text-center mb-2'),
                                                html.Div(dcc.Graph(id='high-price-map'), className='m-auto'),
                                            ], width=6, ),
                                            ## 1.5 아파트 인근 모습
                                            dbc.Col([
                                                html.H6('아파트 인근 모습', className='text-center mb-2'),
                                                html.Div(id='high-apt-image'),
                                            ], width=6),
                                        ]),
                                        ## 1.6 거래금액 추이
                                        html.Div([
                                            html.H6('거래금액 추이', className='text-center mb-2'),
                                            dcc.Graph(id='high-price-line')
                                        ], className='mt-3'),
                                    ], id="collapse-graph-top5", is_open=False)
                                ]),
                            ])
                        ], className='mt-3'),
                        dbc.Card([
                            dbc.CardHeader([html.I(className='bi bi-building me-2'), '최저가 거래 Top 5']),
                            dbc.CardBody([
                                ## 1.7 최저가 거래 Top 5
                                html.Div(id='low-price-grid'),
                                ## 1.8 최저가 상세보기
                                html.Div([
                                    dbc.Button("상세보기", id="collapse-button-low5", className="mt-3 mb-2 opacity-75", color="primary", n_clicks=0),
                                    dbc.Collapse([
                                        dbc.Row([
                                            ## 1.9 아파트 위치
                                            dbc.Col([
                                                html.H6('아파트 위치', className='text-center mb-2'),
                                                html.Div(dcc.Graph(id='low-price-map'), className='m-auto'),
                                            ], width=6, ),
                                            ## 1.10 아파트 인근 모습
                                            dbc.Col([
                                                html.H6('아파트 인근 모습', className='text-center mb-2'),
                                                html.Div(id='low-apt-image'),
                                            ], width=6),
                                        ]),
                                        ## 1.11 거래금액 추이
                                        html.Div([
                                            html.H6('거래금액 추이', className='text-center mb-2'),
                                            dcc.Graph(id='low-price-line')
                                        ], className='mt-3'),
                                    ], id="collapse-graph-low5", is_open=False)
                                ]),
                            ])
                        ], className='mt-3'),
                        ## 1.12 관련 뉴스
                        dbc.Card([
                            dbc.CardHeader([html.I(className='bi bi-building me-2'), '관련 뉴스(news.naver.com)_1시간마다 업데이트']),
                            dbc.CardBody([
                                html.Div(id='apt-news'),
                                dcc.Interval(id='interval-news', interval=1000*60*60, n_intervals=0) # 1시간마다 뉴스 업데이트
                            ])
                        ], className='mt-3'),
                    ]
                ),
                ### 2. 거래건수 탭 섹션 -----------------------------------------------------
                dcc.Tab(
                    label='거래건수',
                    children=[
                        ## 2.1 기간별 아파트 매매 건수
                        dbc.Card([
                            dbc.CardHeader([html.I(className='bi bi-calendar3 me-2'), '기간별 아파트 매매 건수']),
                            dbc.CardBody([
                                html.Small('기간 버튼을 클릭하거나 아래 그래프의 범위를 드래그하여 기간을 선택하세요.', className='card-text text-primary mb-3'),
                                dcc.Graph(id='transaction-count-line'),
                                #dcc.Graph(figure=draw_line(df_basic)),
                            ]),
                        ], className='mt-3'),
                        ## 2.2 자치구별 아파트 매매 건수
                        dbc.Card([
                            dbc.CardHeader([html.I(className='bi bi-border-outer me-2'), '자치구별 아파트 매매 건수']),
                            dbc.CardBody([
                                html.P('지도에 마우스를 올리면 자치구와 거래건수를 확인할 수 있습니다.', className='card-text text-primary mb-3'),
                                dcc.Graph(id='transaction-count-map-cholopleth'),
                                #dcc.Graph(figure=draw_choropleth(df_basic)),
                            ]),
                        ], className='mt-2'),
                        dbc.Row([
                            ## 2.3 아파트별 매매 건수(테이블)
                            dbc.Col(
                                dbc.Card([
                                    dbc.CardHeader([html.I(className='bi bi-building-fill me-2'), '아파트별 매매 건수(테이블)']),
                                    dbc.CardBody([
                                        html.P('컬럼 옆의 삼각 아이콘을 클릭하면 정렬됩니다.', className='card-text text-primary mb-3'),
                                        html.Div(id='transaction-count-grid')
                                        #draw_count_table(df_basic),
                                    ])
                                ]), width=5
                            ),
                            ## 2.4 아파트별 매매 건수(지도)
                            dbc.Col(
                                dbc.Card([
                                    dbc.CardHeader([html.I(className='bi bi-building-fill-check me-2'), '아파트별 매매 건수(지도)']),
                                    dbc.CardBody([
                                        html.P('붉은색 원은 아파트의 위치이며, 원의 크기는 매매 건수를 표시합니다.', className='card-text text-primary mb-3'),
                                        dcc.Graph(id='transaction-count-map-bubble')
                                        #dcc.Graph(figure=draw_count_map(df_basic)),
                                    ])
                                ]), width=7)
                            ], className='mt-2'),
                        ## 2.5 자치구 면적별 매매건수 변화 추이
                        dbc.Card([
                            dbc.CardHeader([html.I(className='bi bi-graph-up-arrow me-2'), '자치구 면적별 매매건수 변화 추이']),
                            dbc.CardBody([
                                html.P('자치구의 전용 면적별 매매건수 변화 추이를 표시합니다.', className='card-text text-primary mb-3'),
                                dcc.Graph(id='transaction-count-facet-line'),
                                #dcc.Graph(figure=draw_count_line(df_basic)),
                                ])
                            ], className='mt-2')
                    ]
                ),
                ### 3. 가격변화 탭 섹션 -----------------------------------------------------
                dcc.Tab(
                    label='가격변화',
                    children=[
                        dbc.Row([
                            ## 3.1 거래가격 변화 분포(파이 차트)
                            dbc.Col(
                                dbc.Card([
                                    dbc.CardHeader([html.I(className='bi bi-pie-chart-fill me-2'), '거래가격 변화 분포']),
                                    dbc.CardBody(dcc.Graph(id='price-change-pie')),
                                ]), width=5
                            ),
                            ## 3.2 거래가격 변화율 분포(히스토그램)
                            dbc.Col(
                                dbc.Card([
                                    dbc.CardHeader([html.I(className='bi bi-bar-chart-fill me-2'), '거래가격 변화율 분포']),
                                    dbc.CardBody(dcc.Graph(id='price-change-hist')),
                                ]), width=7
                            ),
                        ], className='mt-3'),
                        ## 3.3 매매가 변화 지도
                        dbc.Card([
                            dbc.CardHeader([html.I(className='bi bi-geo-alt-fill me-2'), '매매가 변화 지도 - 상승(붉은원) | 하락(파란원)']),
                            dbc.CardBody(dcc.Graph(id='price_change_map')),
                        ], className='mt-3'),
                        ## 3.4 자치구별 변화율 파이차트
                        html.Div([
                            dbc.Button("자치구별 변화율 파이차트", id="collapse-button-price", className="mb-3 mt-3", color="primary", n_clicks=0),
                            dbc.Collapse(dcc.Graph(id='price-change-facet-pie'), id="collapse-graph-price", is_open=False)
                        ]),
                        dbc.Card([
                            ## 3.5 아파트별 매매가 변화
                            dbc.CardHeader([html.I(className='bi bi-building-fill me-2'), '아파트별 매매가 변화 - 해당 행을 선택하면 상세사항 확인 가능']),
                            dbc.CardBody([
                                html.Div(id='price-change-grid'),
                                dbc.Row([
                                    ## 3.6 아파트 위치
                                    dbc.Col([
                                        html.H6('아파트 위치', className='text-center mb-2'),
                                        html.Div(dcc.Graph(id='price-change-grid-map'), className='m-auto'),
                                    ], width=6, ),
                                    ## 3.7 아파트 인근 모습
                                    dbc.Col([
                                        html.H6('아파트 인근 모습', className='text-center mb-2'),
                                        html.Div(id='price-change-grid-image'),
                                    ], width=6),
                                    ## 3.8 거래금액 추이
                                    dcc.Graph(id='price-change-grid-line'),
                                ]),

                            ]),
                        ], className='mt-3'),
                    ]
                )
            ], style=tabs_styles)
        ], width=10),
    ]),
    dbc.Row([
    html.P('designed by 데이터공작 | www.datagongjak.com', className='text-center mt-3 mb-4')
    ]),
])

callbacks.get_callbacks(app, df_basic, df_price, area_top10)

if __name__ == '__main__':
    app.run()