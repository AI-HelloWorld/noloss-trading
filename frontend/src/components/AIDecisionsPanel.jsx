import React from 'react'
import { format } from 'date-fns'
import { Brain, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { useLanguage } from '../locales'

const AIDecisionsPanel = ({ decisions }) => {
  const { t } = useLanguage()
  if (!decisions || decisions.length === 0) {
    return (
      <div className="card h-96 flex items-center justify-center">
        <p className="text-gray-500">{t('aiDecisions.noDecisions')}</p>
      </div>
    )
  }

  const getDecisionIcon = (decision) => {
    switch (decision) {
      case 'buy':
        return <TrendingUp className="w-5 h-5 text-green-500" />
      case 'sell':
      case 'short':
        return <TrendingDown className="w-5 h-5 text-red-500" />
      default:
        return <Minus className="w-5 h-5 text-gray-500" />
    }
  }

  const getDecisionText = (decision) => {
    const decisionMap = {
      buy: t('aiDecisions.buy'),
      sell: t('aiDecisions.sell'),
      hold: t('aiDecisions.hold'),
      short: t('aiDecisions.short'),
      cover: t('aiDecisions.cover')
    }
    return decisionMap[decision] || decision
  }

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'text-green-600'
    if (confidence >= 0.6) return 'text-yellow-600'
    return 'text-orange-600'
  }

  const getDecisionColor = (decision) => {
    switch (decision) {
      case 'buy':
        return 'text-success'
      case 'sell':
      case 'short':
        return 'text-danger'
      case 'hold':
        return 'text-gold-400'
      case 'cover':
        return 'text-blue-400'
      default:
        return 'text-gold-400'
    }
  }

  return (
    <div className="card h-[calc(100vh-450px)] min-h-96 flex flex-col">
      <div className="flex items-center space-x-3 mb-6">
        <Brain className="w-7 h-7 text-gold-400" />
        <h3 className="text-2xl font-display font-bold gold-text">{t('aiDecisions.title')}</h3>
      </div>
      
      <div className="flex-1 overflow-y-auto space-y-3">
        {decisions.map((decision, index) => (
          <div 
            key={decision.id || `decision-${index}`} 
            className="border-2 border-dark-200 rounded-lg p-4 hover:border-gold-400/50 hover:bg-dark-100 transition-all duration-300"
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                {getDecisionIcon(decision.decision)}
                <span className="font-bold text-gold-400 text-base">{decision.symbol}</span>
              </div>
              <span className="text-xs text-dark-700 font-mono">
                {format(new Date(decision.timestamp), 'MM/dd HH:mm')}
              </span>
            </div>
            
            <div className="flex items-center justify-between mb-3">
              <span className={`text-base font-bold ${getDecisionColor(decision.decision)}`}>
                {getDecisionText(decision.decision)}
              </span>
              <span className={`text-sm font-bold ${getConfidenceColor(decision.confidence)}`}>
                {t('aiDecisions.confidence')}: {(decision.confidence * 100).toFixed(0)}%
              </span>
            </div>
            
            <p className="text-sm text-white leading-relaxed line-clamp-3">
              {decision.reasoning}
            </p>
            
            {decision.executed && (
              <span className="inline-block mt-3 px-3 py-1.5 text-xs font-bold rounded-lg bg-blue-500/20 text-blue-400 border border-blue-500/50">
                ✓ {t('aiDecisions.executed')}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default AIDecisionsPanel

