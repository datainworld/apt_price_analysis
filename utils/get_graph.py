import plotly.express as px

# 최고가 Top5와 최저가 Top5를 선그래프로 출력
def draw_price_line(df):
    fig = px.line(
        df,
        x='거래일', 
        y='거래금액', 
        text='거래금액',)
    fig.update_traces(textposition='bottom center')
    fig.update_xaxes(title='', tickformat='%y-%m-%d')  #type='category'
    fig.update_yaxes(title='', showticklabels=False) 
    fig.update_layout( margin={"r":0,"t":0,"l":0,"b":0}, height=230)
    return fig

# 최고가 Top5와 최저가 Top5를 지도그래프로 출력    
def draw_price_map(df):
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