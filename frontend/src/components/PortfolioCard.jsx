import React from 'react'
import { TrendingUp, TrendingDown, Activity, Target } from 'lucide-react'
import { useLanguage } from '../locales'

const PortfolioCard = ({ portfolioData }) => {
  const { t } = useLanguage()
  if (!portfolioData) {
    return (
      <div className="card">
        <p className="text-gray-500">{t('common.loading')}</p>
      </div>
    )
  }

  const {
    total_balance,
    cash_balance,
    positions_value,
    total_pnl,
    total_pnl_percentage,
    initial_balance,
    total_trades,
    win_rate
  } = portfolioData

  // 固定起始资金为175
  const INITIAL_CAPITAL = 175
  
  // 计算盈亏：当前钱包余额 - 起始资金
  const calculated_pnl = cash_balance - INITIAL_CAPITAL
  
  // 计算百分比：钱包余额 / 起始资金 - 1（转换为百分比）
  const calculated_pnl_percentage = ((cash_balance / INITIAL_CAPITAL) - 1) * 100
  
  // 在控制台显示实时余额数据
  console.log('💳 PortfolioCard显示实时钱包余额:', {
    cash_balance,
    positions_value,
    INITIAL_CAPITAL,
    calculated_pnl,
    calculated_pnl_percentage
  })

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {/* 总盈亏 -(Portfolio Card) 基于起始资金175计算 */}
      <div className={`card border-2 hover:shadow-2xl transform hover:scale-[1.02] transition-all duration-300 relative overflow-hidden ${
        calculated_pnl >= 0 
          ? 'bg-gradient-to-br from-success/25 via-success/15 to-dark-50/90 border-success/60 hover:border-success hover:shadow-success/40' 
          : 'bg-gradient-to-br from-danger/25 via-danger/15 to-dark-50/90 border-danger/60 hover:border-danger hover:shadow-danger/40'
      }`}>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-base text-white font-bold mb-1 flex items-center gap-2">
              {t('portfolio.totalPnL')}
              <span className="text-xs bg-blue-500 text-white px-2 py-1 rounded-full font-bold">基于$175</span>
            </p>
            <h2 className={`text-5xl font-display font-black mt-1 tracking-tight ${calculated_pnl >= 0 ? 'text-success' : 'text-danger'}`}>
              {calculated_pnl >= 0 ? '+' : ''}${calculated_pnl?.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
            </h2>
            <p className={`text-lg mt-2 font-black ${calculated_pnl >= 0 ? 'text-success' : 'text-danger'}`}>
              {calculated_pnl_percentage >= 0 ? '+' : ''}{calculated_pnl_percentage.toFixed(2)}%
            </p>
          </div>
          {calculated_pnl >= 0 ? (
            <TrendingUp className="w-16 h-16 text-success" strokeWidth={2.5} />
          ) : (
            <TrendingDown className="w-16 h-16 text-danger" strokeWidth={2.5} />
          )}
        </div>
      </div>

      {/* 钱包余额 */}
      <div className="card bg-gradient-to-br from-dark-100 via-dark-50 to-dark-100 border-2 border-gold-400/30 hover:border-gold-400/60 hover:shadow-2xl hover:shadow-gold-400/30 transform hover:scale-[1.02] transition-all duration-300 relative overflow-hidden group">
        <div className="absolute top-0 right-0 w-32 h-32 bg-gold-400/5 rounded-full blur-3xl group-hover:bg-gold-400/10 transition-all"></div>
        <div className="flex items-center justify-between relative z-10">
          <div>
            <p className="text-base text-dark-700 font-bold mb-1 flex items-center gap-2">
              {t('portfolio.walletBalance')}
              <span className="text-xs bg-gradient-to-r from-gold-400 to-gold-500 text-dark-50 px-2.5 py-1 rounded-full font-bold animate-pulse shadow-lg">实时钱包</span>
            </p>
            <h2 className="text-5xl font-display font-black mt-1 text-dark-700 tracking-tight drop-shadow-sm">${cash_balance?.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</h2>
            <p className="text-base mt-2 text-gold-500 font-bold">{t('portfolio.positions')}: ${positions_value?.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</p>
          </div>
          <Activity className="w-16 h-16 text-gold-400 drop-shadow-[0_0_12px_rgba(252,213,53,0.4)]" strokeWidth={2} />
        </div>
      </div>

      {/* 交易统计 */}
      <div className="card group bg-gradient-to-br from-dark-50/95 to-dark-100/95 border-gold-400/10 hover:border-gold-400/30 transition-all duration-500">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <p className="text-sm text-gray-400 font-medium mb-2">{t('portfolio.tradingStats')}</p>
            <h2 className="text-4xl number-display mt-1 text-white">{total_trades || 0}</h2>
            <p className="text-sm mt-2 text-gold-400/80 font-medium">交易次数</p>
          </div>
          <Target className="w-12 h-12 text-gold-400/70 group-hover:text-gold-400 transition-colors" strokeWidth={2} />
        </div>
      </div>
    </div>
  )
}

export default PortfolioCard

