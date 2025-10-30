import React from 'react'
import { LayoutDashboard, TrendingUp, Activity } from 'lucide-react'
import { useLanguage } from '../locales'

const Navigation = ({ currentPage, onPageChange }) => {
  const { t } = useLanguage()
  
  const navItems = [
    { id: 'dashboard', name: t('navigation.dashboard'), icon: LayoutDashboard },
    { id: 'market', name: t('navigation.marketPrices'), icon: TrendingUp },
  ]

  return (
    <nav className="bg-dark-50 border-b-2 border-gold-400/30 shadow-xl">
      <div className="container mx-auto px-4">
        <div className="flex space-x-2 py-3">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = currentPage === item.id
            
            return (
              <button
                key={item.id}
                onClick={() => onPageChange(item.id)}
                className={`
                  flex items-center space-x-2 px-6 py-3 rounded-lg font-bold transition-all duration-300
                  ${isActive 
                    ? 'bg-gradient-to-r from-gold-400 to-gold-500 text-dark-50 shadow-lg shadow-gold-400/50 transform scale-105' 
                    : 'bg-dark-100 text-white hover:bg-dark-200 hover:text-gold-400 border border-dark-200 hover:border-gold-400/50'
                  }
                `}
              >
                <Icon className={`w-5 h-5 ${isActive ? '' : 'text-gold-400'}`} />
                <span className="text-sm font-display">{item.name}</span>
              </button>
            )
          })}
        </div>
      </div>
    </nav>
  )
}

export default Navigation

