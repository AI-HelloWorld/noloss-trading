import React, { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard'
import Header from './components/Header'
import Navigation from './components/Navigation'
import MarketPricesPage from './components/MarketPricesPage'
import { APIService } from './services/api'
import { useLanguage } from './locales'

function App() {
  const { t } = useLanguage()
  const [currentPage, setCurrentPage] = useState('dashboard')
  const [portfolioData, setPortfolioData] = useState(null)
  const [trades, setTrades] = useState([])
  const [portfolioHistory, setPortfolioHistory] = useState([])
  const [aiDecisions, setAiDecisions] = useState([])
  const [status, setStatus] = useState(null)
  const [ws, setWs] = useState(null)

  useEffect(() => {
    // 初始加载数据
    loadInitialData()

    // 建立WebSocket连接（实时推送钱包余额）
    connectWebSocket()

    // 定期刷新数据 - 更频繁以确保余额同步
    const interval = setInterval(loadInitialData, 5000) // 每5秒刷新一次（实时模式）

    return () => {
      clearInterval(interval)
      if (ws) {
        ws.close()
      }
    }
  }, [])

  const loadInitialData = async () => {
    try {
      const [portfolio, tradesData, history, decisions, statusData] = await Promise.all([
        APIService.getPortfolio(),
        APIService.getTrades(50),
        APIService.getPortfolioHistory(30),
        APIService.getAIDecisions(20),
        APIService.getStatus()
      ])

      console.log('💰 实时钱包余额更新:', portfolio)
      console.log('总资产:', portfolio.total_balance, 'USDT')
      console.log('现金余额:', portfolio.cash_balance, 'USDT')
      console.log('持仓价值:', portfolio.positions_value, 'USDT')
      
      setPortfolioData(portfolio)
      setTrades(tradesData)
      setPortfolioHistory(history)
      setAiDecisions(decisions)
      setStatus(statusData)
    } catch (error) {
      console.error('加载数据失败:', error)
    }
  }

  const connectWebSocket = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws`
    
    const websocket = new WebSocket(wsUrl)

    websocket.onopen = () => {
      console.log('WebSocket连接已建立')
    }

    websocket.onmessage = (event) => {
      const message = JSON.parse(event.data)
      
      if (message.type === 'portfolio_update') {
        console.log('📡 WebSocket收到实时钱包余额更新:', message.data)
        console.log('💰 总资产:', message.data.total_balance, 'USDT')
        console.log('💵 现金余额:', message.data.cash_balance, 'USDT')
        console.log('📊 持仓价值:', message.data.positions_value, 'USDT')
        console.log('🎯 持仓数据:', message.data.positions)
        console.log('✅ 钱包同步标记:', message.wallet_synced)
        
        setPortfolioData(message.data)
        if (message.recent_trades) {
          console.log('收到新交易数据:', message.recent_trades)
          setTrades(prev => {
            // 合并新交易，避免重复
            const existingIds = new Set(prev.map(t => t.id))
            const newTrades = message.recent_trades.filter(t => !existingIds.has(t.id))
            return [...newTrades, ...prev].slice(0, 50)
          })
        }
      }
    }

    websocket.onerror = (error) => {
      console.error('WebSocket错误:', error)
    }

    websocket.onclose = () => {
      console.log('WebSocket连接已关闭，5秒后重连...')
      setTimeout(connectWebSocket, 5000)
    }

    setWs(websocket)
  }

  return (
    <div className="min-h-screen">
      <Header status={status} />
      <Navigation currentPage={currentPage} onPageChange={setCurrentPage} />
      <main className="container mx-auto px-4 py-8">
        {currentPage === 'dashboard' && (
          <Dashboard
            portfolioData={portfolioData}
            trades={trades}
            portfolioHistory={portfolioHistory}
            aiDecisions={aiDecisions}
          />
        )}
        {currentPage === 'market' && (
          <MarketPricesPage />
        )}
      </main>
    </div>
  )
}

export default App

