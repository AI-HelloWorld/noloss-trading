import React, { useState, useEffect } from 'react'
import { Users, Brain, TrendingUp, Newspaper, AlertTriangle, Shield, X } from 'lucide-react'
import { APIService } from '../services/api'
import { useLanguage } from '../locales'

const AgentTeamPanel = () => {
  const { t } = useLanguage()
  const [teamStatus, setTeamStatus] = useState(null)
  const [selectedAgent, setSelectedAgent] = useState(null)

  useEffect(() => {
    loadTeamStatus()
    const interval = setInterval(loadTeamStatus, 30000) // 每30秒刷新
    return () => clearInterval(interval)
  }, [])

  const loadTeamStatus = async () => {
    try {
      const data = await APIService.getTeamStatus()
      setTeamStatus(data)
    } catch (error) {
      console.error(t('aiTeam.loadError'), error)
    }
  }

  const getRoleIcon = (role) => {
    const icons = {
      'technical_analyst': TrendingUp,
      'sentiment_analyst': Brain,
      'fundamental_analyst': Shield,
      'news_analyst': Newspaper,
      'risk_manager': AlertTriangle,
      'portfolio_manager': Users
    }
    const Icon = icons[role] || Brain
    return <Icon className="w-5 h-5" />
  }

  const getRoleColor = (role) => {
    const colors = {
      'technical_analyst': 'blue',
      'sentiment_analyst': 'purple',
      'fundamental_analyst': 'green',
      'news_analyst': 'orange',
      'risk_manager': 'red',
      'portfolio_manager': 'indigo'
    }
    return colors[role] || 'gray'
  }

  if (!teamStatus) {
    return (
      <div className="card">
        <h3 className="text-2xl font-display font-bold gold-text mb-4">{t('aiTeam.title')}</h3>
        <p className="text-white">{t('common.loading')}</p>
      </div>
    )
  }

  return (
    <>
      <div className="card py-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Users className="w-5 h-5 text-gold-400" />
            <h3 className="text-lg font-display font-bold gold-text">{t('aiTeam.title')}</h3>
          </div>
          <span className="text-sm text-gold-400 font-bold">
            {teamStatus.team_size} {t('aiTeam.experts')}
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2 mb-4">
          {teamStatus.members.map((member, idx) => {
            const color = getRoleColor(member.role)
            return (
              <div
                key={`${member.role}_${member.model}_${idx}`}
                onClick={() => setSelectedAgent(member)}
                className={`border border-${color}-400/50 rounded-lg p-2 bg-dark-100 hover:bg-dark-200 hover:border-${color}-400 transition-all duration-300 text-center cursor-pointer transform hover:scale-105`}
              >
                <div className={`inline-block p-1.5 bg-${color}-500/20 rounded-lg text-${color}-400 mb-1`}>
                  {getRoleIcon(member.role)}
                </div>
                <h4 className="font-bold text-white text-xs mb-1">{member.name}</h4>
                <span className={`inline-block px-2 py-0.5 text-[10px] font-bold rounded ${
                  member.status === 'active'
                    ? 'bg-success/20 text-success'
                    : 'bg-dark-300 text-dark-600'
                }`}>
                  {member.status === 'active' ? '●' : '○'}
                </span>
              </div>
            )
          })}
        </div>

        {/* 协同决策流程 */}
        <div className="mt-4 p-3 bg-dark-100 border-2 border-gold-400/30 rounded-lg">
          <h4 className="font-bold text-gold-400 mb-2 text-sm">🎯 {t('aiTeam.decisionProcess')}</h4>
          <ol className="text-xs text-white space-y-1 font-medium">
            <li>1️⃣ {t('aiTeam.step1')}</li>
            <li>2️⃣ {t('aiTeam.step2')}</li>
            <li>3️⃣ {t('aiTeam.step3')}</li>
            <li>4️⃣ {t('aiTeam.step4')}</li>
          </ol>
        </div>
      </div>

      {/* 分析师详情模态框 */}
      {selectedAgent && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" onClick={() => setSelectedAgent(null)}>
          <div className="bg-dark-50 border-2 border-gold-400 rounded-xl p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className={`p-3 bg-${getRoleColor(selectedAgent.role)}-500/20 rounded-lg text-${getRoleColor(selectedAgent.role)}-400`}>
                  {getRoleIcon(selectedAgent.role)}
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-white">{selectedAgent.name}</h3>
                  <p className="text-gold-400 text-sm">{selectedAgent.role}</p>
                </div>
              </div>
              <button 
                onClick={() => setSelectedAgent(null)}
                className="p-2 hover:bg-dark-100 rounded-lg transition-colors"
              >
                <X className="w-6 h-6 text-white" />
              </button>
            </div>

            {/* 当前状态 */}
            <div className="mb-4">
              <h4 className="text-lg font-bold text-gold-400 mb-2">📊 {t('aiTeam.currentStatus')}</h4>
              <div className="bg-dark-100 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-white font-semibold">{t('aiTeam.status')}:</span>
                  <span className={`px-3 py-1 text-sm font-bold rounded-lg ${
                    selectedAgent.status === 'active'
                      ? 'bg-success/20 text-success border border-success/50'
                      : 'bg-dark-300 text-dark-600 border border-dark-400'
                  }`}>
                    {selectedAgent.status === 'active' ? t('aiTeam.online') : t('aiTeam.offline')}
                  </span>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-dark-600">{t('aiTeam.roleType')}:</span>
                    <span className="text-white font-semibold">{selectedAgent.role}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-dark-600">{t('aiTeam.priority')}:</span>
                    <span className="text-white font-semibold">
                      {selectedAgent.role === 'risk_manager' ? t('aiTeam.highestVeto') : 
                       selectedAgent.role === 'portfolio_manager' ? t('aiTeam.highestDecision') : t('aiTeam.standard')}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* 职责说明 */}
            <div className="mb-4">
              <h4 className="text-lg font-bold text-gold-400 mb-2">💼 {t('aiTeam.responsibilities')}</h4>
              <div className="bg-dark-100 rounded-lg p-4">
                <p className="text-white text-sm leading-relaxed">
                  {selectedAgent.role === 'technical_analyst' && t('aiTeam.technicalAnalystDesc')}
                  {selectedAgent.role === 'sentiment_analyst' && t('aiTeam.sentimentAnalystDesc')}
                  {selectedAgent.role === 'fundamental_analyst' && t('aiTeam.fundamentalAnalystDesc')}
                  {selectedAgent.role === 'news_analyst' && t('aiTeam.newsAnalystDesc')}
                  {selectedAgent.role === 'risk_manager' && t('aiTeam.riskManagerDesc')}
                  {selectedAgent.role === 'portfolio_manager' && t('aiTeam.portfolioManagerDesc')}
                </p>
              </div>
            </div>

            {/* 最近活动（模拟数据） */}
            <div>
              <h4 className="text-lg font-bold text-gold-400 mb-2">📋 {t('aiTeam.recentActivity')}</h4>
              <div className="bg-dark-100 rounded-lg p-4 space-y-2">
                <div className="text-sm text-white">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-2 h-2 rounded-full bg-success"></div>
                    <span className="text-dark-600">{t('aiTeam.tenMinutesAgo')}</span>
                  </div>
                  <p className="ml-4">{t('aiTeam.completedAnalysis', { symbol: 'BTCUSDT', confidence: '0.85' })}</p>
                </div>
                <div className="text-sm text-white">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-2 h-2 rounded-full bg-success"></div>
                    <span className="text-dark-600">{t('aiTeam.oneHourAgo')}</span>
                  </div>
                  <p className="ml-4">{t('aiTeam.completedAnalysis', { symbol: 'ETHUSDT', confidence: '0.72' })}</p>
                </div>
                <div className="text-sm text-white">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-2 h-2 rounded-full bg-gold-400"></div>
                    <span className="text-dark-600">{t('aiTeam.twoHoursAgo')}</span>
                  </div>
                  <p className="ml-4">{t('aiTeam.systemStartup')}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default AgentTeamPanel

