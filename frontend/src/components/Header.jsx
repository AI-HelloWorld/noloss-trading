import React from 'react'
import { Activity, Bot, TrendingUp, Zap } from 'lucide-react'
import { useLanguage } from '../locales'
import LanguageSwitcher from './LanguageSwitcher'

const Header = ({ status }) => {
  const { t } = useLanguage()
  return (
    <header className="sticky top-0 z-50 bg-gradient-to-b from-dark-50/98 via-dark-50/95 to-dark-50/98 backdrop-blur-xl border-b border-gold-400/10 shadow-lg shadow-black/20">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <div className="absolute inset-0 bg-gold-400 blur-2xl opacity-20 animate-pulse"></div>
              <Zap className="w-10 h-10 text-gold-400 relative z-10" strokeWidth={2.5} />
            </div>
            <div>
              <h1 className="text-3xl font-bold gold-text tracking-tight">
                NoLoss7.com
              </h1>
              <p className="text-gold-400/70 text-xs font-medium mt-0.5 tracking-wide">
                {t('dashboard.subtitle')}
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* 语言切换 */}
            <LanguageSwitcher />

            {/* 系统状态 - 精简版 */}
            <div className="flex items-center space-x-2 glass-card px-3 py-1.5 rounded-lg">
              <div className={`w-2 h-2 rounded-full ${status?.system === 'online' ? 'bg-success pulse-gold' : 'bg-danger'}`}></div>
              <span className="text-xs font-semibold text-gray-300">
                {status?.system === 'online' ? t('aiTeam.online') : t('aiTeam.offline')}
              </span>
            </div>
            
            {/* 交易状态 - 精简版 */}
            <div className="flex items-center space-x-2 glass-card px-3 py-1.5 rounded-lg">
              <TrendingUp className={`w-4 h-4 ${status?.trading_enabled ? 'text-success' : 'text-gray-500'}`} />
              <span className="text-xs font-semibold text-gray-300">
                {t('common.auto')}: <span className={status?.trading_enabled ? 'text-success' : 'text-gray-500'}>
                  {status?.trading_enabled ? t('common.open') : t('common.close')}
                </span>
              </span>
            </div>
          </div>
        </div>
        
        {/* AI团队状态 - 简化显示 */}
        {status?.agent_team?.members && (
          <div className="mt-4 pt-4 border-t border-gold-400/10">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Bot className="w-4 h-4 text-gold-400/80" />
                <span className="text-xs font-semibold text-gold-400/80">
                  {status.agent_team.team_size} {t('common.experts')}
                </span>
              </div>
              <div className="flex space-x-1">
                {status.agent_team.members.slice(0, 7).map((member, idx) => (
                  <div
                    key={`${member.role}_${member.model}_${idx}`}
                    className={`w-2 h-2 rounded-full transition-all ${
                      member.status === 'active' 
                        ? 'bg-success shadow-lg shadow-success/50' 
                        : 'bg-gray-600'
                    }`}
                    title={member.name}
                  />
                ))}
                {status.agent_team.members.length > 7 && (
                  <span className="text-xs text-gray-500 ml-1">+{status.agent_team.members.length - 7}</span>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </header>
  )
}

export default Header
