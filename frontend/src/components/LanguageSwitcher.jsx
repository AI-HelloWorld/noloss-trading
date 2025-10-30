import React from 'react'
import { Globe } from 'lucide-react'
import { useLanguage } from '../locales'

const LanguageSwitcher = () => {
  const { currentLang, changeLanguage } = useLanguage()

  const languages = [
    { code: 'zh', name: '中文', flag: '🇨🇳' },
    { code: 'en', name: 'English', flag: '🇺🇸' }
  ]

  return (
    <div className="relative group">
      <button className="flex items-center space-x-2 bg-dark-100 px-4 py-2 rounded-lg border border-dark-200 hover:border-gold-400/50 transition-all duration-300">
        <Globe className="w-5 h-5 text-gold-400" />
        <span className="text-sm font-semibold text-dark-700">
          {languages.find(lang => lang.code === currentLang)?.flag} {languages.find(lang => lang.code === currentLang)?.name}
        </span>
        <svg className="w-4 h-4 text-dark-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      
      <div className="absolute top-full left-0 mt-2 w-48 bg-dark-100 border border-dark-200 rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300 z-50">
        <div className="py-2">
          {languages.map((lang) => (
            <button
              key={lang.code}
              onClick={() => changeLanguage(lang.code)}
              className={`w-full flex items-center space-x-3 px-4 py-3 text-left hover:bg-dark-200 transition-colors duration-200 ${
                currentLang === lang.code ? 'bg-gold-400/20 text-gold-400' : 'text-dark-700'
              }`}
            >
              <span className="text-lg">{lang.flag}</span>
              <span className="font-medium">{lang.name}</span>
              {currentLang === lang.code && (
                <svg className="w-4 h-4 ml-auto text-gold-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              )}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

export default LanguageSwitcher
