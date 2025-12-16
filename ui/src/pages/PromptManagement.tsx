import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { api } from '@/lib/api';

interface PromptTemplate {
  id: number;
  name: string;
  description: string;
  category: string;
  template_content: string;
  template_variables: string[];
  default_values: Record<string, any>;
  provider_overrides: Record<string, string>;
  version: number;
  is_active: boolean;
  is_default?: boolean;
  created_at: string;
  updated_at: string;
  created_by: number | null;
  updated_by: number | null;
}

interface PromptVersion extends PromptTemplate {
  is_current: boolean;
}

interface PromptUsageStats {
  total_usage: number;
  successful_usage: number;
  success_rate: number;
  avg_processing_time_ms: number;
  total_tokens: number;
  provider_stats: Record<string, any>;
  days_analyzed: number;
}

const PromptManagement = () => {
  const [prompts, setPrompts] = useState<PromptTemplate[]>([]);
  const [defaultPrompts, setDefaultPrompts] = useState<PromptTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingPrompt, setEditingPrompt] = useState<PromptTemplate | null>(null);
  const [selectedPrompt, setSelectedPrompt] = useState<PromptTemplate | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [testVariables, setTestVariables] = useState('{}');
  const [testResult, setTestResult] = useState<string>('');
  const [usageStats, setUsageStats] = useState<PromptUsageStats | null>(null);
  const [showUsageModal, setShowUsageModal] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [showVersions, setShowVersions] = useState(false);
  const [promptVersions, setPromptVersions] = useState<PromptVersion[]>([]);

  // Helper function to format category names
  const formatCategoryName = (category: string) => {
    const categoryMap: { [key: string]: string } = {
      'invoice_processing': 'Invoice Processing',
      'statement_processing': 'Statement Processing',
      'email_classification': 'Email Classification',
      'ocr_conversion': 'OCR Conversion',
      'expense_processing': 'Expense Processing',
      'general': 'General'
    };
    return categoryMap[category] || category;
  };

  useEffect(() => {
    loadPrompts();
    loadDefaultPrompts();
    loadUsageStats();
  }, []);

  const loadPrompts = async () => {
    try {
      setLoading(true);
      const response = await api.get<PromptTemplate[]>('/prompts/');
      setPrompts(response);
    } catch (error) {
      toast.error('Failed to load prompts');
      console.error('Error loading prompts:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadDefaultPrompts = async () => {
    try {
      const response = await api.get<PromptTemplate[]>('/prompts/defaults/list');
      setDefaultPrompts(response);
    } catch (error) {
      console.error('Error loading default prompts:', error);
    }
  };

  const loadPromptVersions = async (promptName: string) => {
    try {
      const response = await api.get<PromptTemplate[]>(`/prompts/${promptName}/versions`);
      const currentVersion = prompts.find(p => p.name === promptName)?.version || 0;
      const versionsWithCurrent = response.map(v => ({
        ...v,
        is_current: v.version === currentVersion
      }));
      setPromptVersions(versionsWithCurrent);
    } catch (error) {
      console.error('Error loading prompt versions:', error);
    }
  };

  const handleResetPrompt = async (promptName: string) => {
    if (!window.confirm('Are you sure you want to reset this prompt to its default version? This will create a new version with the default content.')) {
      return;
    }
    
    try {
      setLoading(true);
      await api.post(`/prompts/${promptName}/reset`);
      toast.success('Prompt reset to default successfully');
      await loadPrompts();
    } catch (error) {
      toast.error('Failed to reset prompt');
      console.error('Error resetting prompt:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRestoreVersion = async (promptName: string, version: number) => {
    if (!window.confirm(`Are you sure you want to restore version ${version}? This will create a new version with the restored content.`)) {
      return;
    }
    
    try {
      setLoading(true);
      await api.post(`/prompts/${promptName}/versions/${version}/restore`);
      toast.success(`Prompt version ${version} restored successfully`);
      await loadPrompts();
      await loadPromptVersions(promptName);
    } catch (error) {
      toast.error('Failed to restore version');
      console.error('Error restoring version:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadUsageStats = async () => {
    try {
      const response = await api.get<PromptUsageStats>('/prompts/usage-stats?days=30');
      setUsageStats(response);
    } catch (error) {
      console.error('Error loading usage stats:', error);
    }
  };

  const handleSavePrompt = async (prompt: PromptTemplate) => {
    try {
      setLoading(true);
      if (prompt.id) {
        await api.put(`/prompts/${prompt.name}`, prompt);
        toast.success('Prompt updated successfully');
      } else {
        await api.post('/prompts/', prompt);
        toast.success('Prompt created successfully');
      }
      await loadPrompts();
      setIsEditing(false);
      setSelectedPrompt(null);
    } catch (error) {
      toast.error('Failed to save prompt');
      console.error('Error saving prompt:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeletePrompt = async (promptName: string) => {
    if (!window.confirm('Are you sure you want to delete this prompt?')) {
      return;
    }
    
    try {
      await api.delete(`/prompts/${promptName}`);
      toast.success('Prompt deleted successfully');
      await loadPrompts();
    } catch (error) {
      toast.error('Failed to delete prompt');
      console.error('Error deleting prompt:', error);
    }
  };

  const handleTestPrompt = async (prompt: PromptTemplate) => {
    try {
      setIsTesting(true);
      const response = await api.post<{result: string}>(`/prompts/${prompt.name}/test`, {
        variables: testVariables
      });
      setTestResult(response.result);
      toast.success('Prompt tested successfully');
    } catch (error) {
      toast.error('Failed to test prompt');
      console.error('Error testing prompt:', error);
    } finally {
      setIsTesting(false);
    }
  };

  const renderPromptEditor = () => {
    if (!selectedPrompt) return null;

    return (
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4">
          {isEditing ? 'Edit Prompt' : 'Create New Prompt'}
        </h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Prompt Name
            </label>
            <input
              type="text"
              value={selectedPrompt.name}
              onChange={(e) => setSelectedPrompt({...selectedPrompt, name: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., invoice_data_extraction"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              value={selectedPrompt.description}
              onChange={(e) => setSelectedPrompt({...selectedPrompt, description: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
              placeholder="Describe what this prompt does..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Category
            </label>
            <select
              value={selectedPrompt.category}
              onChange={(e) => setSelectedPrompt({...selectedPrompt, category: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="invoice_processing">Invoice Processing</option>
              <option value="statement_processing">Statement Processing</option>
              <option value="email_classification">Email Classification</option>
              <option value="ocr_conversion">OCR Conversion</option>
              <option value="expense_processing">Expense Processing</option>
              <option value="general">General</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Template Content
            </label>
            <textarea
              value={selectedPrompt.template_content}
              onChange={(e) => setSelectedPrompt({...selectedPrompt, template_content: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
              rows={12}
              placeholder="Enter your prompt template using Jinja2 syntax: {{variable_name}}"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Template Variables (comma-separated)
            </label>
            <input
              type="text"
              value={selectedPrompt.template_variables?.join(', ') || ''}
              onChange={(e) => setSelectedPrompt({
                ...selectedPrompt, 
                template_variables: e.target.value.split(',').map(v => v.trim()).filter(v => v)
              })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., file_path, text, raw_content"
            />
          </div>

          <div className="flex space-x-4">
            <button
              onClick={() => handleSavePrompt(selectedPrompt)}
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Saving...' : 'Save Prompt'}
            </button>
            <button
              onClick={() => {
                setIsEditing(false);
                setSelectedPrompt(null);
              }}
              className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderPromptList = () => (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold">Prompt Templates</h2>
        <div className="flex space-x-4">
          <button
            onClick={() => {
              setSelectedPrompt({
                id: 0,
                name: '',
                description: '',
                category: 'general',
                template_content: '',
                template_variables: [],
                default_values: {},
                provider_overrides: {},
                version: 1,
                is_active: true,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
                created_by: null,
                updated_by: null
              });
              setIsEditing(true);
            }}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
          >
            Create New Prompt
          </button>
        </div>
      </div>

      {/* Default Prompts Section */}
      {defaultPrompts.length > 0 && (
        <div className="mb-8">
          <h3 className="text-lg font-semibold mb-4 text-gray-700">Default Prompts</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Category
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Description
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {defaultPrompts.map((prompt) => {
                  const isCustomized = prompts.some(p => p.name === prompt.name && p.created_by !== null);
                  return (
                    <tr key={prompt.id} className="bg-blue-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {prompt.name}
                        {isCustomized && <span className="ml-2 text-xs text-gray-500">(customized)</span>}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatCategoryName(prompt.category)}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {prompt.description || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => {
                            setSelectedPrompt(prompt);
                            setIsEditing(true);
                          }}
                          className="text-indigo-600 hover:text-indigo-900 mr-4"
                        >
                          View
                        </button>
                        {isCustomized && (
                          <button
                            onClick={() => handleResetPrompt(prompt.name)}
                            className="text-orange-600 hover:text-orange-900 mr-4"
                          >
                            Reset
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Custom Prompts Section */}
      <div>
        <h3 className="text-lg font-semibold mb-4 text-gray-700">Custom Prompts</h3>
        {loading ? (
          <div className="text-center py-8">Loading prompts...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Category
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Version
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Active
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {prompts.filter(p => p.created_by !== null).map((prompt) => (
                  <tr key={prompt.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {prompt.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {prompt.category}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      v{prompt.version}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        prompt.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {prompt.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => {
                          setSelectedPrompt(prompt);
                          setIsEditing(true);
                        }}
                        className="text-indigo-600 hover:text-indigo-900 mr-4"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => {
                          loadPromptVersions(prompt.name);
                          setShowVersions(true);
                        }}
                        className="text-purple-600 hover:text-purple-900 mr-4"
                      >
                        Versions
                      </button>
                      <button
                        onClick={() => handleTestPrompt(prompt)}
                        className="text-green-600 hover:text-green-900 mr-4"
                      >
                        Test
                      </button>
                      <button
                        onClick={() => handleDeletePrompt(prompt.name)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );

  const renderTestInterface = () => {
    if (!selectedPrompt || !isEditing) return null;

    return (
      <div className="bg-white rounded-lg shadow-md p-6 mt-6">
        <h3 className="text-lg font-semibold mb-4">Test Prompt</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Test Variables (JSON)
            </label>
            <textarea
              value={JSON.stringify(testVariables, null, 2)}
              onChange={(e) => {
                try {
                  setTestVariables(JSON.parse(e.target.value));
                } catch {
                  // Invalid JSON, ignore
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
              rows={6}
              placeholder='{"file_path": "/path/to/file.pdf", "text": "sample text"}'
            />
          </div>

          <div className="flex space-x-4">
            <button
              onClick={() => handleTestPrompt(selectedPrompt)}
              disabled={isTesting}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
            >
              {isTesting ? 'Testing...' : 'Test Prompt'}
            </button>
          </div>

          {testResult && (
            <div className="mt-4">
              <h4 className="font-semibold mb-2">Test Result:</h4>
              <pre className="bg-gray-100 p-4 rounded-md overflow-x-auto text-sm">
                {testResult}
              </pre>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderUsageStats = () => (
    <div className="bg-white rounded-lg shadow-md p-6 mt-6">
      <h3 className="text-lg font-semibold mb-4">Usage Statistics (Last 30 Days)</h3>
      
      {usageStats ? (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{usageStats.total_usage}</div>
            <div className="text-sm text-gray-600">Total Usage</div>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{usageStats.successful_usage}</div>
            <div className="text-sm text-gray-600">Successful Usage</div>
          </div>
          <div className="bg-yellow-50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-yellow-600">{(usageStats.success_rate * 100).toFixed(1)}%</div>
            <div className="text-sm text-gray-600">Success Rate</div>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">{usageStats.avg_processing_time_ms.toFixed(1)}ms</div>
            <div className="text-sm text-gray-600">Avg Processing Time</div>
          </div>
          <div className="bg-indigo-50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-indigo-600">{usageStats.total_tokens}</div>
            <div className="text-sm text-gray-600">Total Tokens</div>
          </div>
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="text-2xl font-bold text-gray-600">{usageStats.days_analyzed}</div>
            <div className="text-sm text-gray-600">Days Analyzed</div>
          </div>
        </div>
      ) : (
        <div className="text-center py-4 text-gray-500">
          No usage statistics available
        </div>
      )}
    </div>
  );

  const renderVersionModal = () => {
    if (!showVersions) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl p-6 max-w-4xl w-full max-h-[80vh] overflow-y-auto">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-bold">Version History</h3>
            <button
              onClick={() => setShowVersions(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {promptVersions.length > 0 ? (
            <div className="space-y-4">
              {promptVersions.map((version) => (
                <div key={version.id} className={`border rounded-lg p-4 ${version.is_current ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}`}>
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h4 className="font-semibold text-lg">
                        Version {version.version}
                        {version.is_current && <span className="ml-2 text-sm text-blue-600 font-normal">(Current)</span>}
                      </h4>
                      <p className="text-sm text-gray-600">
                        Created: {new Date(version.created_at).toLocaleString()}
                      </p>
                      {version.updated_at && (
                        <p className="text-sm text-gray-600">
                          Updated: {new Date(version.updated_at).toLocaleString()}
                        </p>
                      )}
                    </div>
                    <div className="flex space-x-2">
                      {!version.is_current && (
                        <button
                          onClick={() => handleRestoreVersion(version.name, version.version)}
                          className="px-3 py-1 bg-purple-600 text-white rounded text-sm hover:bg-purple-700"
                        >
                          Restore
                        </button>
                      )}
                      <button
                        onClick={() => {
                          setSelectedPrompt(version);
                          setIsEditing(true);
                          setShowVersions(false);
                        }}
                        className="px-3 py-1 bg-gray-600 text-white rounded text-sm hover:bg-gray-700"
                      >
                        View
                      </button>
                    </div>
                  </div>
                  
                  <div className="mb-3">
                    <p className="text-sm text-gray-700 mb-2">
                      <strong>Description:</strong> {version.description || 'No description'}
                    </p>
                    <p className="text-sm text-gray-700">
                      <strong>Category:</strong> {version.category}
                    </p>
                  </div>

                  <div className="mb-3">
                    <p className="text-sm font-medium text-gray-700 mb-2">Template Content:</p>
                    <div className="bg-gray-50 p-3 rounded text-sm font-mono max-h-32 overflow-y-auto">
                      {version.template_content.substring(0, 500)}
                      {version.template_content.length > 500 && '...'}
                    </div>
                  </div>

                  {version.template_variables && version.template_variables.length > 0 && (
                    <div>
                      <p className="text-sm font-medium text-gray-700 mb-1">Variables:</p>
                      <div className="flex flex-wrap gap-1">
                        {version.template_variables.map((variable, index) => (
                          <span key={index} className="px-2 py-1 bg-gray-200 text-xs rounded">
                            {variable}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              No versions available
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Prompt Management</h1>
          <p className="mt-2 text-gray-600">
            Manage and customize AI prompt templates for different processing tasks. 
            Update prompts to improve AI performance and accuracy.
          </p>
        </div>

        {isEditing ? (
          <>
            {renderPromptEditor()}
            {renderTestInterface()}
          </>
        ) : (
          <>
            {renderPromptList()}
            {renderUsageStats()}
          </>
        )}
        
        {renderVersionModal()}
      </div>
    </div>
  );
};

export default PromptManagement;
