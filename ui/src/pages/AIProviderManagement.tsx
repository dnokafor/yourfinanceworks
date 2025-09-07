import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, Bot, Plus, Edit, Trash2, TestTube, CheckCircle, XCircle, Settings, Eye, EyeOff } from 'lucide-react'
import { settingsApi, aiConfigApi, AIConfig, AIConfigCreate, AIProviderInfo, AIConfigTestResponse } from "@/lib/api"
import { useToast } from "@/hooks/use-toast"

interface AIProvider {
  name: string
  display_name: string
  description: string
  website?: string
  models: string[]
  supports_ocr: boolean
  requires_api_key: boolean
  default_model: string
  default_max_tokens: number
}

export default function AIProviderManagement() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const [aiConfigs, setAiConfigs] = useState<AIConfig[]>([])
  const [supportedProviders, setSupportedProviders] = useState<Record<string, AIProvider>>({})
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedConfig, setSelectedConfig] = useState<AIConfig | null>(null)
  const [testingConfig, setTestingConfig] = useState<number | null>(null)

  // Form state for create/edit
  const [formData, setFormData] = useState({
    provider_name: '',
    provider_url: '',
    api_key: '',
    model_name: '',
    is_active: true,
    is_default: false,
    ocr_enabled: false,
    max_tokens: 4096,
    temperature: 0.1
  })

  useEffect(() => {
    fetchAIConfigs()
    fetchSupportedProviders()
  }, [])

  const fetchAIConfigs = async () => {
    try {
      const configs = await aiConfigApi.getAIConfigs()
      setAiConfigs(configs)
    } catch (error) {
      console.error('Failed to fetch AI configurations:', error)
      toast({
        title: "Error",
        description: "Failed to fetch AI configurations",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }

  const fetchSupportedProviders = async () => {
    try {
      const response = await aiConfigApi.getSupportedProviders()
      console.log('Supported providers loaded:', response.providers)
      setSupportedProviders(response.providers)
    } catch (error) {
      console.error('Error fetching supported providers:', error)
    }
  }

  const handleCreateConfig = () => {
    setFormData({
      provider_name: '',
      provider_url: '',
      api_key: '',
      model_name: '',
      is_active: true,
      is_default: false,
      ocr_enabled: false,
      max_tokens: 4096,
      temperature: 0.1
    })
    setShowCreateModal(true)
  }

  const handleEditConfig = (config: AIConfig) => {
    setFormData({
      provider_name: config.provider_name,
      provider_url: config.provider_url || '',
      api_key: config.api_key || '',
      model_name: config.model_name,
      is_active: config.is_active,
      is_default: config.is_default,
      ocr_enabled: config.ocr_enabled,
      max_tokens: config.max_tokens,
      temperature: config.temperature
    })
    setSelectedConfig(config)
    setShowEditModal(true)
  }

  const handleDeleteConfig = async (configId: number) => {
    if (!confirm('Are you sure you want to delete this AI configuration?')) return

    try {
      await aiConfigApi.deleteAIConfig(configId)
      setAiConfigs(prev => prev.filter(config => config.id !== configId))
      toast({
        title: "Success",
        description: "AI configuration deleted successfully"
      })
    } catch (error) {
      console.error('Error deleting AI configuration:', error)
      toast({
        title: "Error",
        description: "Failed to delete AI configuration",
        variant: "destructive"
      })
    }
  }

  const handleTestConfig = async (configId: number) => {
    setTestingConfig(configId)

    try {
      const result: AIConfigTestResponse = await aiConfigApi.testAIConfig(configId)

      if (result.success) {
        toast({
          title: "Test Successful",
          description: `Response time: ${result.response_time_ms?.toFixed(0)}ms\n${result.response}`,
        })
        // Refresh configs to update tested status
        fetchAIConfigs()
      } else {
        toast({
          title: "Test Failed",
          description: result.message,
          variant: "destructive"
        })
      }
    } catch (error) {
      console.error('Error testing AI configuration:', error)
      toast({
        title: "Error",
        description: "Error testing AI configuration",
        variant: "destructive"
      })
    } finally {
      setTestingConfig(null)
    }
  }

  const handleSubmitCreate = async (e: React.FormEvent) => {
    e.preventDefault()

    try {
      const newConfig = await aiConfigApi.createAIConfig(formData)
      setAiConfigs(prev => [...prev, newConfig])
      setShowCreateModal(false)
      toast({
        title: "Success",
        description: "AI configuration created successfully"
      })
    } catch (error) {
      console.error('Error creating AI configuration:', error)
      toast({
        title: "Error",
        description: "Failed to create AI configuration",
        variant: "destructive"
      })
    }
  }

  const handleSubmitEdit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!selectedConfig) return

    try {
      const updatedConfig = await aiConfigApi.updateAIConfig(selectedConfig.id, formData)
      setAiConfigs(prev => prev.map(config =>
        config.id === selectedConfig.id ? updatedConfig : config
      ))
      setShowEditModal(false)
      setSelectedConfig(null)
      toast({
        title: "Success",
        description: "AI configuration updated successfully"
      })
    } catch (error) {
      console.error('Error updating AI configuration:', error)
      toast({
        title: "Error",
        description: "Failed to update AI configuration",
        variant: "destructive"
      })
    }
  }

  const getStatusIcon = (isActive: boolean, tested: boolean) => {
    if (!isActive) return <XCircle className="w-5 h-5 text-gray-400" />
    if (tested) return <CheckCircle className="w-5 h-5 text-green-500" />
    return <XCircle className="w-5 h-5 text-yellow-500" />
  }

  const getProviderInfo = (providerName: string) => {
    return supportedProviders[providerName] || {
      name: providerName,
      display_name: providerName,
      description: 'Unknown provider',
      requires_api_key: true
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate(-1)}
            className="p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center space-x-2">
              <Bot className="w-6 h-6" />
              <span>AI Provider Management</span>
            </h1>
            <p className="text-gray-600">Configure and manage AI providers for document processing</p>
          </div>
        </div>
        <button
          onClick={handleCreateConfig}
          className="btn-primary flex items-center space-x-2"
        >
          <Plus className="w-4 h-4" />
          <span>Add Provider</span>
        </button>
      </div>

      <div className="grid gap-6">
        {/* AI Configurations */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">AI Configurations</h2>

          {aiConfigs.length === 0 ? (
            <div className="text-center py-8">
              <Bot className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No AI configurations found</h3>
              <p className="text-gray-600 mb-4">Add your first AI provider to get started with document processing</p>
              <button
                onClick={handleCreateConfig}
                className="btn-primary"
              >
                Add Your First Provider
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {aiConfigs.map((config) => {
                const providerInfo = getProviderInfo(config.provider_name)
                return (
                  <div
                    key={config.id}
                    className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        {getStatusIcon(config.is_active, config.tested)}
                        <div>
                          <h3 className="font-medium text-gray-900">{providerInfo.display_name}</h3>
                          <p className="text-sm text-gray-600">{config.model_name}</p>
                        </div>
                        {config.is_default && (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            Default
                          </span>
                        )}
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleTestConfig(config.id)}
                          disabled={testingConfig === config.id}
                          className="p-1 text-gray-400 hover:text-blue-600 disabled:opacity-50"
                          title="Test configuration"
                        >
                          {testingConfig === config.id ? (
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                          ) : (
                            <TestTube className="w-4 h-4" />
                          )}
                        </button>
                        <button
                          onClick={() => handleEditConfig(config)}
                          className="p-1 text-gray-400 hover:text-blue-600"
                          title="Edit configuration"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteConfig(config.id)}
                          className="p-1 text-gray-400 hover:text-red-600"
                          title="Delete configuration"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Usage Count:</span>
                        <p className="font-medium">{config.usage_count}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Max Tokens:</span>
                        <p className="font-medium">{config.max_tokens}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Temperature:</span>
                        <p className="font-medium">{config.temperature}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">OCR Enabled:</span>
                        <p className="font-medium">{config.ocr_enabled ? 'Yes' : 'No'}</p>
                      </div>
                    </div>

                    {config.last_used_at && (
                      <div className="mt-2 text-xs text-gray-500">
                        Last used: {new Date(config.last_used_at).toLocaleString()}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* Create AI Configuration Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
                <Plus className="w-5 h-5" />
                <span>Add AI Provider</span>
              </h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-1 text-gray-400 hover:text-gray-600"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmitCreate} className="space-y-6">
              {/* Provider Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  AI Provider
                </label>
                <select
                  value={formData.provider_name}
                  onChange={(e) => {
                    const provider = e.target.value
                    const providerInfo = supportedProviders[provider]
                    setFormData(prev => ({
                      ...prev,
                      provider_name: provider,
                      model_name: providerInfo?.default_model || '',
                      max_tokens: providerInfo?.default_max_tokens || 4096
                    }))
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">Select a provider...</option>
                  {Object.entries(supportedProviders).map(([key, provider]) => (
                    <option key={key} value={key}>
                      {provider.display_name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Provider URL */}
              {formData.provider_name && formData.provider_name === 'custom' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Provider URL
                  </label>
                  <input
                    type="url"
                    value={formData.provider_url}
                    onChange={(e) => setFormData(prev => ({ ...prev, provider_url: e.target.value }))}
                    placeholder="https://api.example.com/v1"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
              )}

              {/* API Key */}
              {formData.provider_name && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    API Key {getProviderInfo(formData.provider_name).requires_api_key ? '' : '(Optional)'}
                    <span className="text-xs text-gray-500 ml-2">
                      (Debug: {formData.provider_name} - requires_api_key: {getProviderInfo(formData.provider_name).requires_api_key ? 'true' : 'false'})
                    </span>
                  </label>
                  <div className="relative">
                  <input
                    type="password"
                    value={formData.api_key}
                    onChange={(e) => setFormData(prev => ({ ...prev, api_key: e.target.value }))}
                    placeholder={getProviderInfo(formData.provider_name).requires_api_key ? "Enter your API key" : "API key (optional)"}
                    className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required={getProviderInfo(formData.provider_name).requires_api_key}
                  />
                    <button
                      type="button"
                      className="absolute inset-y-0 right-0 pr-3 flex items-center"
                      onClick={() => {
                        const input = document.querySelector('input[type="password"]') as HTMLInputElement
                        input.type = input.type === 'password' ? 'text' : 'password'
                      }}
                    >
                      <Eye className="w-4 h-4 text-gray-400" />
                    </button>
                  </div>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Model Name
                </label>
                <input
                  type="text"
                  value={formData.model_name}
                  onChange={(e) => setFormData(prev => ({ ...prev, model_name: e.target.value }))}
                  placeholder="e.g., gpt-4, claude-3-sonnet"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              {/* Configuration Options */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Max Tokens
                  </label>
                  <input
                    type="number"
                    value={formData.max_tokens}
                    onChange={(e) => setFormData(prev => ({ ...prev, max_tokens: parseInt(e.target.value) }))}
                    min="1"
                    max="128000"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Temperature
                  </label>
                  <input
                    type="number"
                    value={formData.temperature}
                    onChange={(e) => setFormData(prev => ({ ...prev, temperature: parseFloat(e.target.value) }))}
                    min="0"
                    max="2"
                    step="0.1"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* Options */}
              <div className="space-y-3">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Active</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.is_default}
                    onChange={(e) => setFormData(prev => ({ ...prev, is_default: e.target.checked }))}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Set as default</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.ocr_enabled}
                    onChange={(e) => setFormData(prev => ({ ...prev, ocr_enabled: e.target.checked }))}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Enable OCR processing</span>
                </label>
              </div>

              <div className="flex justify-end space-x-3 pt-6 border-t">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                >
                  Create Configuration
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit AI Configuration Modal */}
      {showEditModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl mx-4 max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
                <Settings className="w-5 h-5" />
                <span>Edit AI Provider</span>
              </h2>
              <button
                onClick={() => setShowEditModal(false)}
                className="p-1 text-gray-400 hover:text-gray-600"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmitEdit} className="space-y-6">
              {/* Provider Selection (disabled for edit) */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  AI Provider
                </label>
                <input
                  type="text"
                  value={getProviderInfo(formData.provider_name).display_name}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                  disabled
                />
              </div>

              {/* API Key */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  API Key {getProviderInfo(formData.provider_name).requires_api_key ? '' : '(Optional)'}
                </label>
                  <div className="relative">
                    <input
                      type="password"
                      value={formData.api_key}
                      onChange={(e) => setFormData(prev => ({ ...prev, api_key: e.target.value }))}
                      placeholder={getProviderInfo(formData.provider_name).requires_api_key ? "Enter your API key" : "API key (optional)"}
                      className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required={getProviderInfo(formData.provider_name).requires_api_key}
                    />
                    <button
                      type="button"
                      className="absolute inset-y-0 right-0 pr-3 flex items-center"
                      onClick={() => {
                        const inputs = document.querySelectorAll('input[type="password"]')
                        inputs.forEach(input => {
                          const htmlInput = input as HTMLInputElement
                          htmlInput.type = htmlInput.type === 'password' ? 'text' : 'password'
                        })
                      }}
                    >
                      <Eye className="w-4 h-4 text-gray-400" />
                    </button>
                  </div>
                </div>

              {/* Model Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Model Name
                </label>
                <input
                  type="text"
                  value={formData.model_name}
                  onChange={(e) => setFormData(prev => ({ ...prev, model_name: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              {/* Configuration Options */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Max Tokens
                  </label>
                  <input
                    type="number"
                    value={formData.max_tokens}
                    onChange={(e) => setFormData(prev => ({ ...prev, max_tokens: parseInt(e.target.value) }))}
                    min="1"
                    max="128000"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Temperature
                  </label>
                  <input
                    type="number"
                    value={formData.temperature}
                    onChange={(e) => setFormData(prev => ({ ...prev, temperature: parseFloat(e.target.value) }))}
                    min="0"
                    max="2"
                    step="0.1"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* Options */}
              <div className="space-y-3">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Active</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.is_default}
                    onChange={(e) => setFormData(prev => ({ ...prev, is_default: e.target.checked }))}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Set as default</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.ocr_enabled}
                    onChange={(e) => setFormData(prev => ({ ...prev, ocr_enabled: e.target.checked }))}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Enable OCR processing</span>
                </label>
              </div>

              <div className="flex justify-end space-x-3 pt-6 border-t">
                <button
                  type="button"
                  onClick={() => setShowEditModal(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                >
                  Update Configuration
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
