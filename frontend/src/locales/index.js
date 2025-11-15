// 语言包管理
import { zh } from './zh'
import { en } from './en'

export const languages = {
  zh: {
    name: '中文',
    code: 'zh',
    data: zh
  },
  en: {
    name: 'English',
    code: 'en',
    data: en
  }
}

// 默认语言
export const defaultLanguage = 'zh'

// 获取当前语言
export const getCurrentLanguage = () => {
  const saved = localStorage.getItem('language')
  return saved && languages[saved] ? saved : defaultLanguage
}

// 设置语言
export const setLanguage = (langCode) => {
  if (languages[langCode]) {
    localStorage.setItem('language', langCode)
    return true
  }
  return false
}

// 获取翻译文本
export const t = (key, langCode = null) => {
  const currentLang = langCode || getCurrentLanguage()
  const langData = languages[currentLang]?.data || languages[defaultLanguage].data
  
  const keys = key.split('.')
  let result = langData
  
  for (const k of keys) {
    if (result && typeof result === 'object' && k in result) {
      result = result[k]
    } else {
      // 如果找不到翻译，返回key本身
      return key
    }
  }
  
  return result
}

// 获取所有支持的语言
export const getSupportedLanguages = () => {
  return Object.values(languages).map(lang => ({
    code: lang.code,
    name: lang.name
  }))
}

// 语言切换Hook
export const useLanguage = () => {
  const currentLang = getCurrentLanguage()
  const langData = languages[currentLang].data
  
  const changeLanguage = (langCode) => {
    if (setLanguage(langCode)) {
      // 刷新页面以应用新语言
      window.location.reload()
    }
  }
  
  return {
    currentLang,
    langData,
    changeLanguage,
    t: (key) => t(key, currentLang)
  }
}
