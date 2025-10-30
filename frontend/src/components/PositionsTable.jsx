import React from 'react'
import { useLanguage } from '../locales'

const PositionsTable = ({ positions }) => {
  const { t } = useLanguage()
  
  // 添加调试信息
  console.log('PositionsTable接收到的positions:', positions)
  console.log('positions类型:', typeof positions)
  console.log('positions长度:', positions?.length)
  
  if (!positions || positions.length === 0) {
    return (
      <div className="card">
        <h3 className="text-2xl font-display font-bold gold-text mb-4">{t('portfolio.currentPositions')}</h3>
        <p className="text-white">{t('portfolio.noPositions')}</p>
      </div>
    )
  }

  return (
    <div className="card">
      <h3 className="text-2xl font-display font-bold gold-text mb-6">{t('portfolio.currentPositions')}</h3>
      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead className="bg-dark-100 border-b-2 border-gold-400/50">
            <tr>
              <th className="px-6 py-4 text-left text-xs font-bold text-gold-400 uppercase tracking-wider">
                {t('portfolio.symbol')}
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gold-400 uppercase tracking-wider">
                {t('portfolio.type')}
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gold-400 uppercase tracking-wider">
                {t('portfolio.amount')}
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gold-400 uppercase tracking-wider">
                {t('portfolio.avgPrice')}
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gold-400 uppercase tracking-wider">
                {t('portfolio.currentPrice')}
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gold-400 uppercase tracking-wider">
                {t('portfolio.positionValue')}
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gold-400 uppercase tracking-wider">
                {t('portfolio.unrealizedPnL')}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-dark-200">
            {positions.map((position, idx) => {
              const positionValue = Math.abs(position.amount) * position.current_price
              
              // 根据持仓类型计算盈亏
              let pnl, pnlPercent
              if (position.position_type === 'short') {
                // 做空：盈亏 = (入场价格 - 当前价格) × 数量绝对值
                pnl = (position.average_price - position.current_price) * Math.abs(position.amount)
                pnlPercent = ((position.average_price - position.current_price) / position.average_price) * 100
              } else {
                // 做多：盈亏 = (当前价格 - 入场价格) × 数量
                pnl = (position.current_price - position.average_price) * position.amount
                pnlPercent = ((position.current_price - position.average_price) / position.average_price) * 100
              }
              
              // 调试信息
              console.log(`持仓 ${position.symbol}:`, {
                type: position.position_type,
                amount: position.amount,
                avgPrice: position.average_price,
                currentPrice: position.current_price,
                pnl: pnl,
                pnlPercent: pnlPercent
              })
              
              return (
                <tr key={position.symbol || `position-${idx}`} className="hover:bg-dark-100 transition-all duration-200 border-l-2 border-transparent hover:border-gold-400">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-lg font-black text-gold-400">{position.symbol}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-3 py-2 text-sm font-black rounded-lg border-2 ${
                      position.position_type === 'long' 
                        ? 'bg-success/20 text-success border-success/50' 
                        : 'bg-danger/20 text-danger border-danger/50'
                    }`}>
                      {position.position_type === 'long' ? t('portfolio.long') : t('portfolio.short')}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-base text-white font-semibold font-mono">
                    {position.amount?.toFixed(4)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-base text-white font-bold font-mono">
                    ${position.average_price?.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-base text-white font-bold font-mono">
                    ${position.current_price?.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-lg font-black text-gold-400 font-mono">
                    ${positionValue?.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className={`text-base font-black ${pnl >= 0 ? 'text-success' : 'text-danger'}`}>
                      {pnl >= 0 ? '+' : ''}${pnl?.toFixed(2)}
                      <span className="text-sm ml-1 font-black">
                        ({pnl >= 0 ? '+' : ''}{pnlPercent?.toFixed(2)}%)
                      </span>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default PositionsTable
