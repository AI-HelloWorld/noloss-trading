import React, { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown, RefreshCw, Clock, Activity, Target } from 'lucide-react'
import { APIService } from '../services/api'
import { format } from 'date-fns'
import { useLanguage } from '../locales'

const MarketPricesPage = () => {
  const { t } = useLanguage()
  const [marketData, setMarketData] = useState([])
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState(null)
  const [autoRefresh, setAutoRefresh] = useState(true)

  useEffect(() => {
    loadMarketData()
    
    if (autoRefresh) {
      const interval = setInterval(loadMarketData, 10000) // 每10秒刷新
      return () => clearInterval(interval)
    }
  }, [autoRefresh])

  const loadMarketData = async () => {
    try {
      const data = await APIService.getMarketData()
      
      // 去重，只保留每个交易对的最新数据
      const uniqueData = {}
      data.forEach(item => {
        if (!uniqueData[item.symbol] || new Date(item.timestamp) > new Date(uniqueData[item.symbol].timestamp)) {
          uniqueData[item.symbol] = item
        }
      })
      
      setMarketData(Object.values(uniqueData).sort((a, b) => b.volume_24h - a.volume_24h))
      setLastUpdate(new Date())
      setLoading(false)
    } catch (error) {
      console.error(t('marketPrices.error'), error)
      setLoading(false)
    }
  }

  const formatPrice = (price) => {
    if (!price) return '$0.00'
    return `$${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 6 })}`
  }

  const formatVolume = (volume) => {
    if (!volume) return '$0'
    if (volume >= 1000000) {
      return `$${(volume / 1000000).toFixed(2)}M`
    }
    if (volume >= 1000) {
      return `$${(volume / 1000).toFixed(2)}K`
    }
    return `$${volume.toFixed(2)}`
  }

  const getPriceChangeColor = (change) => {
    if (!change) return 'text-white'
    return change >= 0 ? 'text-success' : 'text-danger'
  }

  const getPriceChangeIcon = (change) => {
    if (!change) return null
    return change >= 0 ? 
      <TrendingUp className="w-4 h-4" /> : 
      <TrendingDown className="w-4 h-4" />
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 text-gold-400 animate-spin mx-auto mb-4" />
          <p className="text-white text-xl font-semibold">{t('marketPrices.loading')}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 顶部控制栏 */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-display font-bold gold-text mb-2">📈 {t('marketPrices.title')}</h2>
            <div className="flex items-center space-x-2 text-sm text-dark-600">
              <Clock className="w-4 h-4" />
              <span>{t('marketPrices.lastUpdate')}: {lastUpdate ? format(lastUpdate, 'HH:mm:ss') : '-'}</span>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-4 py-2 rounded-lg font-bold transition-all duration-300 ${
                autoRefresh
                  ? 'bg-success/20 text-success border-2 border-success/50'
                  : 'bg-dark-200 text-white border-2 border-dark-400'
              }`}
            >
              {autoRefresh ? `🟢 ${t('marketPrices.autoRefresh')}` : `⭕ ${t('marketPrices.paused')}`}
            </button>
            
            <button
              onClick={loadMarketData}
              className="btn btn-primary flex items-center space-x-2"
            >
              <RefreshCw className="w-4 h-4" />
              <span>{t('marketPrices.manualRefresh')}</span>
            </button>
          </div>
        </div>
      </div>

      {/* 市场数据表格 */}
      <div className="card">
        {marketData.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-white text-lg font-semibold">{t('marketPrices.noData')}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-dark-100 border-b-2 border-gold-400">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-black text-gold-400 uppercase tracking-wider">
                    {t('marketPrices.rank')}
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-black text-gold-400 uppercase tracking-wider">
                    {t('marketPrices.symbol')}
                  </th>
                  <th className="px-6 py-4 text-right text-sm font-black text-gold-400 uppercase tracking-wider">
                    {t('marketPrices.price')}
                  </th>
                  <th className="px-6 py-4 text-right text-sm font-black text-gold-400 uppercase tracking-wider">
                    {t('marketPrices.change24h')}
                  </th>
                  <th className="px-6 py-4 text-right text-sm font-black text-gold-400 uppercase tracking-wider">
                    {t('marketPrices.high24h')}
                  </th>
                  <th className="px-6 py-4 text-right text-sm font-black text-gold-400 uppercase tracking-wider">
                    {t('marketPrices.low24h')}
                  </th>
                  <th className="px-6 py-4 text-right text-sm font-black text-gold-400 uppercase tracking-wider">
                    {t('marketPrices.volume24h')}
                  </th>
                  <th className="px-6 py-4 text-right text-sm font-black text-gold-400 uppercase tracking-wider">
                    {t('marketPrices.updateTime')}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-200">
                {marketData.map((item, index) => (
                  <tr
                    key={item.symbol}
                    className="hover:bg-dark-100 transition-all duration-200 border-l-2 border-transparent hover:border-gold-400"
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-lg font-black text-gold-400">#{index + 1}</span>
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-lg font-black text-white">{item.symbol}</span>
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <span className="text-lg font-black text-white font-mono">
                        {formatPrice(item.price)}
                      </span>
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <div className={`flex items-center justify-end space-x-1 text-base font-black ${getPriceChangeColor(item.change_24h)}`}>
                        {getPriceChangeIcon(item.change_24h)}
                        <span>
                          {item.change_24h >= 0 ? '+' : ''}{item.change_24h?.toFixed(2)}%
                        </span>
                      </div>
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <span className="text-base text-success font-bold font-mono">
                        {formatPrice(item.high_24h)}
                      </span>
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <span className="text-base text-danger font-bold font-mono">
                        {formatPrice(item.low_24h)}
                      </span>
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <span className="text-base text-gold-400 font-black font-mono">
                        {formatVolume(item.volume_24h)}
                      </span>
                    </td>
                    
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <span className="text-xs text-dark-600 font-mono">
                        {format(new Date(item.timestamp), 'HH:mm:ss')}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 底部统计信息 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card bg-gradient-to-br from-dark-100 via-dark-50 to-dark-100 border-2 border-success/50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white font-bold mb-1">{t('marketPrices.risingPairs')}</p>
              <h3 className="text-4xl font-display font-black text-success">
                {marketData.filter(item => item.change_24h > 0).length}
              </h3>
            </div>
            <TrendingUp className="w-12 h-12 text-success" strokeWidth={2.5} />
          </div>
        </div>

        <div className="card bg-gradient-to-br from-dark-100 via-dark-50 to-dark-100 border-2 border-danger/50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white font-bold mb-1">{t('marketPrices.fallingPairs')}</p>
              <h3 className="text-4xl font-display font-black text-danger">
                {marketData.filter(item => item.change_24h < 0).length}
              </h3>
            </div>
            <TrendingDown className="w-12 h-12 text-danger" strokeWidth={2.5} />
          </div>
        </div>

        <div className="card bg-gradient-to-br from-dark-100 via-dark-50 to-dark-100 border-2 border-gold-400/50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white font-bold mb-1">{t('marketPrices.totalPairs')}</p>
              <h3 className="text-4xl font-display font-black text-gold-400">
                {marketData.length}
              </h3>
            </div>
            <Activity className="w-12 h-12 text-gold-400" strokeWidth={2} />
          </div>
        </div>
      </div>
    </div>
  )
}

export default MarketPricesPage

