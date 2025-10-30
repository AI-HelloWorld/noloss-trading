import React from 'react'
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart, ReferenceLine } from 'recharts'
import { format } from 'date-fns'
import { useLanguage } from '../locales'

const PortfolioChart = ({ data }) => {
  const { t } = useLanguage()
  const INITIAL_CAPITAL = 175
  
  if (!data || data.length === 0) {
    return (
      <div className="card h-96 flex items-center justify-center">
        <p className="text-gray-400 text-sm">{t('portfolio.noHistoryData')}</p>
      </div>
    )
  }

  // 计算Y轴范围（以175为基准，显示上下波动）
  const values = data.map(item => item.cash_balance || INITIAL_CAPITAL)
  const minValue = Math.min(...values, INITIAL_CAPITAL)
  const maxValue = Math.max(...values, INITIAL_CAPITAL)
  const padding = Math.max((maxValue - minValue) * 0.2, 10) // 20% padding，最少10
  
  const chartData = data.map(item => ({
    timestamp: format(new Date(item.timestamp), 'MM/dd HH:mm'),
    '钱包余额': item.cash_balance || INITIAL_CAPITAL,
  }))

  return (
    <div className="card">
      <ResponsiveContainer width="100%" height={400}>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="colorBalance" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#fbbf24" stopOpacity={0.6}/>
              <stop offset="95%" stopColor="#fbbf24" stopOpacity={0.05}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#3f3f46" opacity={0.2} />
          <XAxis 
            dataKey="timestamp" 
            stroke="#71717a"
            style={{ fontSize: '11px', fontWeight: '500', fill: '#71717a' }}
            tick={{ fill: '#71717a' }}
          />
          <YAxis 
            stroke="#71717a"
            style={{ fontSize: '11px', fontWeight: '500', fill: '#71717a' }}
            tick={{ fill: '#71717a' }}
            domain={[Math.max(minValue - padding, INITIAL_CAPITAL - 50), maxValue + padding]}
            tickFormatter={(value) => {
              const diff = value - INITIAL_CAPITAL
              if (Math.abs(diff) < 0.01) return '$175'
              const sign = diff > 0 ? '+' : ''
              return `${sign}$${diff.toFixed(1)}`
            }}
          />
          {/* 基准线（175） */}
          <ReferenceLine 
            y={INITIAL_CAPITAL} 
            stroke="#71717a" 
            strokeWidth={1} 
            strokeDasharray="5 5"
            strokeOpacity={0.5}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#18181b', 
              border: '1px solid rgba(251, 191, 36, 0.3)',
              borderRadius: '8px',
              padding: '10px',
              color: '#ffffff',
              fontWeight: '500'
            }}
            labelStyle={{ color: '#fbbf24', fontWeight: '600', marginBottom: '6px', fontSize: '12px' }}
            itemStyle={{ color: '#ffffff', fontWeight: '500', fontSize: '13px' }}
            formatter={(value) => {
              const diff = value - INITIAL_CAPITAL
              const diffPercent = ((value / INITIAL_CAPITAL) - 1) * 100
              return [
                `$${value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})} (${diff >= 0 ? '+' : ''}${diffPercent.toFixed(2)}%)`,
                ''
              ]
            }}
          />
          {/* 钱包余额线 - 金色 */}
          <Area 
            type="monotone" 
            dataKey="钱包余额" 
            stroke="#fbbf24" 
            fillOpacity={1}
            fill="url(#colorBalance)"
            strokeWidth={2.5}
            dot={false}
            activeDot={{ r: 4, fill: '#fbbf24', strokeWidth: 2, stroke: '#0a0a0a' }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

export default PortfolioChart
