#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Plotly Dash 可视化仪表盘
整合FastAPI后端数据，提供实时交易数据可视化
"""
import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import asyncio
import threading
import time

# 配置API基础URL
API_BASE_URL = "http://localhost:8000/api"

# 创建Dash应用
app = dash.Dash(__name__)
app.title = "AI交易平台仪表盘"

# 自定义样式
app.layout = html.Div([
    # 页面标题
    html.Div([
        html.H1("AI加密货币交易平台", 
                style={'textAlign': 'center', 'color': '#2E86AB', 'marginBottom': '30px'}),
        html.P("实时交易数据监控与分析", 
               style={'textAlign': 'center', 'color': '#666', 'fontSize': '18px'})
    ]),
    
    # 自动刷新组件
    dcc.Interval(
        id='interval-component',
        interval=30*1000,  # 30秒刷新一次
        n_intervals=0
    ),
    
    # 第一行：账户净值和持仓分布
    html.Div([
        # 账户净值趋势图
        html.Div([
            html.H3("账户净值趋势", style={'textAlign': 'center', 'marginBottom': '20px'}),
            dcc.Graph(id='account-value-chart')
        ], style={'width': '60%', 'display': 'inline-block', 'padding': '10px'}),
        
        # 持仓分布饼图
        html.Div([
            html.H3("持仓分布", style={'textAlign': 'center', 'marginBottom': '20px'}),
            dcc.Graph(id='positions-pie-chart')
        ], style={'width': '40%', 'display': 'inline-block', 'padding': '10px'})
    ]),
    
    # 第二行：交易记录表格
    html.Div([
        html.H3("最近交易记录", style={'textAlign': 'center', 'marginBottom': '20px'}),
        html.Div(id='trades-table')
    ], style={'marginTop': '30px', 'padding': '10px'}),
    
    # 第三行：策略解释
    html.Div([
        html.H3("AI策略解释", style={'textAlign': 'center', 'marginBottom': '20px'}),
        html.Div(id='strategies-content')
    ], style={'marginTop': '30px', 'padding': '10px'})
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
            line=dict(color='#2E86AB', width=3),
            marker=dict(size=6)
        ))
        
        account_fig.update_layout(
            title="账户净值变化趋势",
            xaxis_title="时间",
            yaxis_title="净值 (USD)",
            hovermode='x unified',
            template='plotly_white',
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
        
        positions_fig = px.pie(
            df_positions, 
            values='size_pct', 
            names='symbol',
            title="持仓分布",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        positions_fig.update_traces(textposition='inside', textinfo='percent+label')
        positions_fig.update_layout(height=400)
    else:
        positions_fig = go.Figure()
        positions_fig.add_annotation(
            text="暂无持仓数据",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        positions_fig.update_layout(height=400)
    
    # 获取交易记录
    trades_data = fetch_data_from_api('trades?limit=20')
    
    # 创建交易记录表格
    if trades_data:
        df_trades = pd.DataFrame(trades_data)
        df_trades['timestamp'] = pd.to_datetime(df_trades['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        trades_table = dash_table.DataTable(
            data=df_trades.to_dict('records'),
            columns=[
                {"name": "时间", "id": "timestamp", "type": "datetime"},
                {"name": "交易对", "id": "symbol"},
                {"name": "方向", "id": "side"},
                {"name": "价格", "id": "price", "type": "numeric", "format": {"specifier": ".4f"}},
                {"name": "数量", "id": "amount", "type": "numeric", "format": {"specifier": ".6f"}},
                {"name": "总价值", "id": "total_value", "type": "numeric", "format": {"specifier": ".2f"}},
                {"name": "盈亏", "id": "profit_loss", "type": "numeric", "format": {"specifier": ".2f"}},
                {"name": "AI模型", "id": "ai_model"},
                {"name": "成功", "id": "success", "type": "text"}
            ],
            style_cell={'textAlign': 'center', 'fontSize': '12px'},
            style_header={'backgroundColor': '#2E86AB', 'color': 'white', 'fontWeight': 'bold'},
            style_data_conditional=[
                {
                    'if': {'filter_query': '{profit_loss} > 0'},
                    'backgroundColor': '#d4edda',
                    'color': 'black',
                },
                {
                    'if': {'filter_query': '{profit_loss} < 0'},
                    'backgroundColor': '#f8d7da',
                    'color': 'black',
                }
            ],
            page_size=10,
            sort_action="native"
        )
    else:
        trades_table = html.Div("暂无交易记录", style={'textAlign': 'center', 'color': '#666'})
    
    # 获取策略数据
    strategies_data = fetch_data_from_api('strategies?limit=5')
    
    # 创建策略解释内容
    if strategies_data:
        strategies_content = []
        for strategy in strategies_data:
            strategy_card = html.Div([
                html.Div([
                    html.H4(f"{strategy['model_name']} - {strategy['symbol']}", 
                           style={'color': '#2E86AB', 'marginBottom': '10px'}),
                    html.P(f"决策: {strategy['decision']} (置信度: {strategy['confidence']:.2f})", 
                          style={'fontWeight': 'bold', 'marginBottom': '10px'}),
                    html.P(strategy['strategy_text'], 
                          style={'backgroundColor': '#f8f9fa', 'padding': '15px', 'borderRadius': '5px', 
                                'borderLeft': '4px solid #2E86AB'}),
                    html.Small(f"时间: {strategy['timestamp']}", 
                             style={'color': '#666', 'marginTop': '10px', 'display': 'block'})
                ], style={'marginBottom': '20px', 'padding': '15px', 'border': '1px solid #ddd', 
                         'borderRadius': '8px', 'backgroundColor': 'white'})
            ])
            strategies_content.append(strategy_card)
    else:
        strategies_content = html.Div("暂无策略数据", style={'textAlign': 'center', 'color': '#666'})
    
    return account_fig, positions_fig, trades_table, strategies_content

# 添加自定义CSS样式
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f5f5f5;
                margin: 0;
                padding: 0;
            }
            .dash-table-container {
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .dash-graph {
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

if __name__ == '__main__':
    print("启动AI交易平台仪表盘...")
    print("访问地址: http://localhost:3000")
    print("数据每30秒自动刷新")
    app.run_server(debug=True, host='0.0.0.0', port=3000)
