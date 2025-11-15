import axios from 'axios'

const API_BASE_URL = '/api'

class APIServiceClass {
  async getStatus() {
    const response = await axios.get(`${API_BASE_URL}/status`)
    return response.data
  }

  async getPortfolio() {
    const response = await axios.get(`${API_BASE_URL}/portfolio`)
    return response.data
  }

  async getTrades(limit = 50) {
    const response = await axios.get(`${API_BASE_URL}/trades?limit=${limit}`)
    return response.data
  }

  async getPortfolioHistory(days = 30) {
    const response = await axios.get(`${API_BASE_URL}/portfolio-history?days=${days}`)
    return response.data
  }

  async getAIDecisions(limit = 20) {
    const response = await axios.get(`${API_BASE_URL}/ai-decisions?limit=${limit}`)
    return response.data
  }

  async getMarketData() {
    const response = await axios.get(`${API_BASE_URL}/market-data`)
    return response.data
  }

  async getTeamStatus() {
    const response = await axios.get(`${API_BASE_URL}/team`)
    return response.data
  }
}

export const APIService = new APIServiceClass()

