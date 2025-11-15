import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
import requests
import json

# FastAPI后端URL
API_BASE_URL = "http://localhost:8000/api"

# 创建Dash应用
app = dash.Dash(__name__)
app.title = "AI交易平台仪表盘"

# 简化的布局
app.layout = html.Div([
    html.H1("AI加密货币交易平台", style={'textAlign': 'center'}),
    
    # 自动刷新组件
    dcc.Interval(
        id='interval-component',
        interval=30*1000,  # 30秒刷新一次
        n_intervals=0
    ),
    
    # 账户净值图表
    html.Div([
        html.H3("账户净值趋势"),
        dcc.Graph(id='account-value-chart')
    ]),
    
    # 持仓分布图表
    html.Div([
        html.H3("持仓分布"),
        dcc.Graph(id='positions-pie-chart')
    ]),
    
    # 交易记录表格
    html.Div([
        html.H3("最近交易记录"),
        html.Div(id='trades-table')
    ]),
    
    # 策略解释
    html.Div([
        html.H3("AI策略解释"),
        html.Div(id='strategies-content')
    ])
])

def fetch_data_from_api(endpoint):
    """从FastAPI获取数据"""
    try:
        print(f"正在获取数据: {endpoint}")
        response = requests.get(f"{API_BASE_URL}/{endpoint}", timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"获取数据成功: {endpoint}, 数据量: {len(data) if isinstance(data, list) else 'N/A'}")
        return data
    except Exception as e:
        print(f"获取数据失败 {endpoint}: {e}")
        return []

@app.callback(
    [Output('account-value-chart', 'figure'),
     Output('positions-pie-chart', 'figure'),
     Output('trades-table', 'children'),
     Output('strategies-content', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_dashboard(n_intervals):
    """更新仪表盘数据"""
    print(f"回调函数被触发，n_intervals: {n_intervals}")
    
    # 获取账户净值数据
    account_data = fetch_data_from_api('account_value?days=30')
    
    # 创建账户净值趋势图
    if account_data:
        df_account = pd.DataFrame(account_data)
        df_account['timestamp'] = pd.to_datetime(df_account['timestamp'])
        
        account_fig = go.Figure()
        account_fig.add_trace(go.Scatter(
            x=df_account['timestamp'],
            y=df_account['equity_usd'],
            mode='lines+markers',
            name='账户净值',
            line=dict(color='#2E86AB', width=3)
        ))
        
        account_fig.update_layout(
            title="账户净值变化趋势",
            xaxis_title="时间",
            yaxis_title="净值 (USD)",
            height=400
        )
    else:
        account_fig = go.Figure()
        account_fig.add_annotation(
            text="暂无数据",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        account_fig.update_layout(height=400)
    
    # 获取持仓数据
    positions_data = fetch_data_from_api('positions')
    
    # 创建持仓分布饼图
    if positions_data:
        df_positions = pd.DataFrame(positions_data)
        
        positions_fig = go.Figure(data=[go.Pie(
            labels=df_positions['symbol'],
            values=df_positions['size_pct'],
            hole=.3
        )])
        positions_fig.update_layout(title="持仓分布", height=400)
    else:
        positions_fig = go.Figure()
        positions_fig.add_annotation(
            text="暂无持仓数据",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        positions_fig.update_layout(height=400)
    
    # 获取交易记录
    trades_data = fetch_data_from_api('trades')
    
    # 创建交易记录表格
    if trades_data:
        df_trades = pd.DataFrame(trades_data)
        trades_table = html.Table([
            html.Thead([
                html.Tr([html.Th("时间"), html.Th("币种"), html.Th("方向"), html.Th("价格"), html.Th("数量")])
            ]),
            html.Tbody([
                html.Tr([
                    html.Td(trade['timestamp'][:19] if 'timestamp' in trade else 'N/A'),
                    html.Td(trade['symbol'] if 'symbol' in trade else 'N/A'),
                    html.Td(trade['side'] if 'side' in trade else 'N/A'),
                    html.Td(f"${trade['price']:.4f}" if 'price' in trade else 'N/A'),
                    html.Td(f"{trade['amount']:.4f}" if 'amount' in trade else 'N/A')
                ]) for trade in df_trades.head(10).to_dict('records')
            ])
        ])
    else:
        trades_table = html.P("暂无交易记录")
    
    # 获取策略数据
    strategies_data = fetch_data_from_api('strategies')
    
    # 创建策略解释
    if strategies_data:
        strategies_content = []
        for strategy in strategies_data[:3]:  # 只显示前3条
            strategy_card = html.Div([
                html.H4(f"{strategy.get('model_name', 'N/A')} - {strategy.get('symbol', 'N/A')}"),
                html.P(f"决策: {strategy.get('decision', 'N/A')} (置信度: {strategy.get('confidence', 0):.2f})"),
                html.P(strategy.get('strategy_text', '无策略解释')),
                html.Hr()
            ])
            strategies_content.append(strategy_card)
    else:
        strategies_content = html.P("暂无策略数据")
    
    print("回调函数执行完成")
    return account_fig, positions_fig, trades_table, strategies_content

if __name__ == '__main__':
    print("启动简化版AI交易平台仪表盘...")
    print("访问地址: http://localhost:3000")
    print("数据每30秒自动刷新")
    app.run_server(debug=True, host='0.0.0.0', port=3000)
