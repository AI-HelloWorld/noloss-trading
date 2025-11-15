import React from 'react'
import { Activity, Bot, TrendingUp, Zap } from 'lucide-react'
import { useLanguage } from '../locales'
import LanguageSwitcher from './LanguageSwitcher'

// X (Twitter) 图标组件
const XIcon = ({ className }) => (
  <svg
    viewBox="0 0 24 24"
    className={className}
    fill="currentColor"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.251L5.25 4.126H3.927z"/>
  </svg>
)

const Header = ({ status }) => {
  const { t } = useLanguage()
  return (
    <header className="sticky top-0 z-50 bg-gradient-to-b from-dark-50/98 via-dark-50/95 to-dark-50/98 backdrop-blur-xl border-b-2 border-gold-400/20 shadow-xl shadow-black/30">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <div className="absolute inset-0 bg-gold-400 blur-2xl opacity-25 animate-pulse"></div>
              <div className="absolute inset-0 bg-gradient-to-r from-gold-400/20 to-gold-500/20 rounded-lg"></div>
              <Zap className="w-10 h-10 text-gold-400 relative z-10 drop-shadow-[0_0_8px_rgba(252,213,53,0.5)]" strokeWidth={2.5} />
            </div>
            <div>
              <h1 className="text-3xl font-bold gold-text tracking-tight drop-shadow-lg">
                NoLoss7.com
              </h1>
              <p className="text-gold-500/80 text-xs font-semibold mt-0.5 tracking-wide uppercase">
                {t('dashboard.subtitle')}
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* X (Twitter) 链接 */}
            <a
              href="https://x.com/Qubyt_E3A"
              target="_blank"
              rel="noopener noreferrer"
              className="glass-card px-3 py-1.5 rounded-lg hover:border-gold-400/30 transition-all duration-300 group"
              title="关注我们的X账号"
            >
              <XIcon className="w-5 h-5 text-gray-400 group-hover:text-gold-400 transition-colors" />
            </a>

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
