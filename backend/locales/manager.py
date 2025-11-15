"""
多语言管理器
"""
from typing import Dict, Optional
from .zh import ZH_MESSAGES
from .en import EN_MESSAGES

# 支持的语言
SUPPORTED_LANGUAGES = {
    'zh': ZH_MESSAGES,
    'en': EN_MESSAGES
}

DEFAULT_LANGUAGE = 'zh'

def get_message(key: str, language: str = DEFAULT_LANGUAGE) -> str:
    """
    获取翻译消息
    
    Args:
        key: 消息键，格式为 "category.subkey"
        language: 语言代码 (zh/en)
    
    Returns:
        翻译后的消息
    """
    if language not in SUPPORTED_LANGUAGES:
        language = DEFAULT_LANGUAGE
    
    messages = SUPPORTED_LANGUAGES[language]
    keys = key.split('.')
    
    result = messages
    for k in keys:
        if isinstance(result, dict) and k in result:
            result = result[k]
        else:
            # 如果找不到翻译，返回key本身
            return key
    
    return result

def get_supported_languages() -> Dict[str, str]:
    """
    获取支持的语言列表
    
    Returns:
        语言代码到语言名称的映射
    """
    return {
        'zh': '中文',
        'en': 'English'
    }

def is_language_supported(language: str) -> bool:
    """
    检查语言是否支持
    
    Args:
        language: 语言代码
    
    Returns:
        是否支持该语言
    """
    return language in SUPPORTED_LANGUAGES
