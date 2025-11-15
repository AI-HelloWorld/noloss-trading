import React from 'react'
import { format } from 'date-fns'
import { ArrowUpCircle, ArrowDownCircle, MinusCircle } from 'lucide-react'
import { useLanguage } from '../locales'

const TradesTable = ({ trades }) => {
  const { t } = useLanguage()
  if (!trades || trades.length === 0) {
    return (
      <div className="card">
        <h3 className="text-2xl font-display font-bold gold-text mb-6">{t('trades.title')}</h3>
        <p className="text-white text-lg font-semibold">{t('trades.noTrades')}</p>
      </div>
    )
  }

  const getSideIcon = (side) => {
    switch (side) {
      case 'buy':
        return <ArrowUpCircle className="w-6 h-6 text-success" strokeWidth={2.5} />
      case 'sell':
      case 'short':
        return <ArrowDownCircle className="w-6 h-6 text-danger" strokeWidth={2.5} />
      default:
        return <MinusCircle className="w-6 h-6 text-gold-400" strokeWidth={2.5} />
    }
  }

  const getSideText = (side) => {
    const sideMap = {
      buy: t('trades.buy'),
      sell: t('trades.sell'),
      short: t('trades.short'),
      cover: t('trades.cover')
    }
    return sideMap[side] || side
  }

  return (
    <div className="card">
      <h3 className="text-2xl font-display font-bold gold-text mb-6">{t('trades.title')}</h3>
      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead className="bg-dark-100 border-b-2 border-gold-400">
            <tr>
              <th className="px-6 py-4 text-left text-sm font-black text-gold-400 uppercase tracking-wider">
                {t('trades.time')}
              </th>
              <th className="px-6 py-4 text-left text-sm font-black text-gold-400 uppercase tracking-wider">
                {t('trades.symbol')}
              </th>
              <th className="px-6 py-4 text-left text-sm font-black text-gold-400 uppercase tracking-wider">
                {t('trades.type')}
              </th>
              <th className="px-6 py-4 text-left text-sm font-black text-gold-400 uppercase tracking-wider">
                {t('trades.price')}
              </th>
              <th className="px-6 py-4 text-left text-sm font-black text-gold-400 uppercase tracking-wider">
                {t('trades.amount')}
              </th>
              <th className="px-6 py-4 text-left text-sm font-black text-gold-400 uppercase tracking-wider">
                {t('trades.totalValue')}
              </th>
              <th className="px-6 py-4 text-left text-sm font-black text-gold-400 uppercase tracking-wider">
                {t('trades.pnl')}
              </th>
              <th className="px-6 py-4 text-left text-sm font-black text-gold-400 uppercase tracking-wider">
                {t('trades.aiModel')}
              </th>
              <th className="px-6 py-4 text-left text-sm font-black text-gold-400 uppercase tracking-wider">
                {t('trades.status')}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-dark-200">
            {trades.map((trade, index) => (
              <tr key={trade.id || `trade-${index}`} className="hover:bg-dark-100 transition-all duration-200 border-l-2 border-transparent hover:border-gold-400">
                <td className="px-6 py-4 whitespace-nowrap text-base text-white font-mono font-semibold">
                  {format(new Date(trade.timestamp), 'MM/dd HH:mm:ss')}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-lg font-black text-gold-400">{trade.symbol}</span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center space-x-2">
                    {getSideIcon(trade.side)}
                    <span className="text-base font-bold text-white">{getSideText(trade.side)}</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-base text-white font-bold font-mono">
                  ${trade.price?.toFixed(2)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-base text-white font-semibold font-mono">
                  {trade.amount?.toFixed(4)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-lg text-gold-400 font-black font-mono">
                  ${trade.total_value?.toFixed(2)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {trade.profit_loss !== null && trade.profit_loss !== undefined ? (
                    <div className="text-base font-black font-mono">
                      <div className={trade.profit_loss >= 0 ? 'text-success' : 'text-danger'}>
                        {trade.profit_loss >= 0 ? '+' : ''}${trade.profit_loss.toFixed(2)}
                      </div>
                      {trade.profit_loss_percentage !== null && trade.profit_loss_percentage !== undefined && (
                        <div className={`text-sm mt-1 ${trade.profit_loss >= 0 ? 'text-success' : 'text-danger'}`}>
                          {trade.profit_loss_percentage >= 0 ? '+' : ''}{trade.profit_loss_percentage.toFixed(2)}%
                        </div>
                      )}
                    </div>
                  ) : (
                    <span className="text-gray-500 text-sm">--</span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-white font-medium">
                  {trade.ai_model}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {trade.success ? (
                    <span className="px-3 py-2 text-sm font-black rounded-lg bg-success/20 text-success border-2 border-success/50">
                      {t('trades.success')}
                    </span>
                  ) : (
                    <span className="px-3 py-2 text-sm font-black rounded-lg bg-danger/20 text-danger border-2 border-danger/50">
                      {t('trades.failed')}
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default TradesTable

