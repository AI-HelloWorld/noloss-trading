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
    <nav className="bg-dark-50/90 border-b border-gold-400/15 shadow-lg backdrop-blur-sm">
      <div className="container mx-auto px-4">
        <div className="flex space-x-3 py-3">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = currentPage === item.id
            
            return (
              <button
                key={item.id}
                onClick={() => onPageChange(item.id)}
                className={`
                  relative flex items-center space-x-2 px-6 py-3 rounded-lg font-bold transition-all duration-300 overflow-hidden group
                  ${isActive 
                    ? 'bg-gradient-to-r from-gold-400 via-gold-500 to-gold-400 text-dark-50 shadow-lg shadow-gold-400/50 transform scale-105' 
                    : 'bg-dark-100/80 text-dark-700 hover:bg-dark-200 hover:text-gold-400 border border-dark-200/50 hover:border-gold-400/40'
                  }
                `}
              >
                {isActive && (
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer"></div>
                )}
                <Icon className={`w-5 h-5 relative z-10 ${isActive ? 'text-dark-50' : 'text-gold-500 group-hover:text-gold-400'}`} />
                <span className={`text-sm font-semibold relative z-10 ${isActive ? 'text-dark-50' : 'text-dark-700 group-hover:text-gold-400'}`}>{item.name}</span>
              </button>
            )
          })}
        </div>
      </div>
    </nav>
  )
}

export default Navigation

