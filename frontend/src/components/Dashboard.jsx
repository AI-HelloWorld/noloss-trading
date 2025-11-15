import React from 'react'
import PortfolioCard from './PortfolioCard'
import PortfolioChart from './PortfolioChart'
import TradesTable from './TradesTable'
import AIDecisionsPanel from './AIDecisionsPanel'
import PositionsTable from './PositionsTable'
import AgentTeamPanel from './AgentTeamPanel'
import { useLanguage } from '../locales'

const Dashboard = ({ portfolioData, trades, portfolioHistory, aiDecisions }) => {
  const { t } = useLanguage()
  
  // 添加调试信息
  console.log('Dashboard接收到的portfolioData:', portfolioData)
  console.log('Dashboard中的positions:', portfolioData?.positions)
  
  return (
    <div className="space-y-6">
      {/* 投资组合概览卡片 */}
      <PortfolioCard portfolioData={portfolioData} />
      
      {/* AI分析师团队面板 */}
      <AgentTeamPanel />
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 投资组合历史图表 */}
        <div className="lg:col-span-2">
          <PortfolioChart data={portfolioHistory} />
        </div>
        
        {/* AI决策面板 */}
        <div className="lg:col-span-1">
          <AIDecisionsPanel decisions={aiDecisions} />
        </div>
      </div>
      
      {/* 当前持仓 */}
      <PositionsTable positions={portfolioData?.positions || []} />
      
      {/* 交易历史 */}
      <TradesTable trades={trades} />
    </div>
  )
}

export default Dashboard

