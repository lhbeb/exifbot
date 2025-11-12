"use client";

import { useState, useEffect } from 'react';
import maawDebugger from '../lib/debugger';

interface DebugDashboardProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function DebugDashboard({ isOpen, onClose }: DebugDashboardProps) {
  const [logs, setLogs] = useState<any[]>([]);
  const [apiStatus, setApiStatus] = useState<any>(null);
  const [systemHealth, setSystemHealth] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'logs' | 'api' | 'health' | 'network'>('logs');

  useEffect(() => {
    if (isOpen) {
      refreshLogs();
      checkAPIStatus();
      checkSystemHealth();
    }
  }, [isOpen]);

  const refreshLogs = () => {
    setLogs(maawDebugger.getLogs());
  };

  const checkAPIStatus = async () => {
    try {
      const response = await fetch('/api/debug', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'test_api',
          data: { test: true },
          timestamp: new Date().toISOString()
        })
      });
      const result = await response.json();
      setApiStatus(result);
    } catch (error) {
      setApiStatus({ error: 'Failed to check API status' });
    }
  };

  const checkSystemHealth = async () => {
    try {
      const response = await fetch('/api/debug', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'check_health',
          data: {},
          timestamp: new Date().toISOString()
        })
      });
      const result = await response.json();
      setSystemHealth(result);
    } catch (error) {
      setSystemHealth({ error: 'Failed to check system health' });
    }
  };

  const clearLogs = () => {
    maawDebugger.clearLogs();
    setLogs([]);
  };

  const testFormValidation = async () => {
    const testData = {
      text: 'Test product description',
      team_member_token: 'mehdi',
      images: ['mock_image']
    };

    try {
      const response = await fetch('/api/debug', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'validate_form',
          data: testData,
          timestamp: new Date().toISOString()
        })
      });
      const result = await response.json();
      maawDebugger.log('info', 'Form validation test completed', result);
      refreshLogs();
    } catch (error) {
      maawDebugger.log('error', 'Form validation test failed', { error });
      refreshLogs();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-gray-900 text-white rounded-lg w-full max-w-6xl h-5/6 overflow-hidden">
        {/* Header */}
        <div className="flex justify-between items-center p-4 border-b border-gray-700">
          <h2 className="text-xl font-bold">🐛 MAAW Debug Dashboard</h2>
          <button
            onClick={onClose}
            className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded"
          >
            Close
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-700">
          {[
            { id: 'logs', label: 'Logs', icon: '📝' },
            { id: 'api', label: 'API Status', icon: '🔌' },
            { id: 'health', label: 'System Health', icon: '💚' },
            { id: 'network', label: 'Network', icon: '🌐' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-2 border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-teal-400 text-teal-400'
                  : 'border-transparent text-gray-400 hover:text-white'
              }`}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="p-4 h-full overflow-auto">
          {activeTab === 'logs' && (
            <div>
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">Application Logs</h3>
                <div className="space-x-2">
                  <button
                    onClick={refreshLogs}
                    className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-sm"
                  >
                    Refresh
                  </button>
                  <button
                    onClick={clearLogs}
                    className="bg-red-600 hover:bg-red-700 px-3 py-1 rounded text-sm"
                  >
                    Clear
                  </button>
                </div>
              </div>
              <div className="space-y-2 max-h-96 overflow-auto">
                {logs.length === 0 ? (
                  <p className="text-gray-400">No logs available</p>
                ) : (
                  logs.map((log, index) => (
                    <div
                      key={index}
                      className={`p-3 rounded text-sm ${
                        log.level === 'error' ? 'bg-red-900 border-l-4 border-red-400' :
                        log.level === 'warn' ? 'bg-yellow-900 border-l-4 border-yellow-400' :
                        log.level === 'info' ? 'bg-blue-900 border-l-4 border-blue-400' :
                        'bg-gray-800 border-l-4 border-gray-400'
                      }`}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <span className="font-mono text-xs text-gray-400">
                            {new Date(log.timestamp).toLocaleTimeString()}
                          </span>
                          <span className={`ml-2 px-2 py-1 rounded text-xs font-bold ${
                            log.level === 'error' ? 'bg-red-600' :
                            log.level === 'warn' ? 'bg-yellow-600' :
                            log.level === 'info' ? 'bg-blue-600' :
                            'bg-gray-600'
                          }`}>
                            {log.level.toUpperCase()}
                          </span>
                        </div>
                      </div>
                      <div className="mt-1">{log.message}</div>
                      {log.context && (
                        <details className="mt-2">
                          <summary className="cursor-pointer text-xs text-gray-400">
                            Context
                          </summary>
                          <pre className="mt-1 text-xs bg-gray-800 p-2 rounded overflow-auto">
                            {JSON.stringify(log.context, null, 2)}
                          </pre>
                        </details>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {activeTab === 'api' && (
            <div>
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">API Status</h3>
                <button
                  onClick={checkAPIStatus}
                  className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-sm"
                >
                  Refresh
                </button>
              </div>
              <div className="space-y-4">
                <div className="bg-gray-800 p-4 rounded">
                  <h4 className="font-semibold mb-2">API Connectivity</h4>
                  {apiStatus ? (
                    <pre className="text-sm overflow-auto">
                      {JSON.stringify(apiStatus, null, 2)}
                    </pre>
                  ) : (
                    <p className="text-gray-400">Loading...</p>
                  )}
                </div>
                <div className="bg-gray-800 p-4 rounded">
                  <h4 className="font-semibold mb-2">Form Validation Test</h4>
                  <button
                    onClick={testFormValidation}
                    className="bg-green-600 hover:bg-green-700 px-3 py-1 rounded text-sm"
                  >
                    Test Form Validation
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'health' && (
            <div>
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">System Health</h3>
                <button
                  onClick={checkSystemHealth}
                  className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-sm"
                >
                  Refresh
                </button>
              </div>
              <div className="bg-gray-800 p-4 rounded">
                {systemHealth ? (
                  <pre className="text-sm overflow-auto">
                    {JSON.stringify(systemHealth, null, 2)}
                  </pre>
                ) : (
                  <p className="text-gray-400">Loading...</p>
                )}
              </div>
            </div>
          )}

          {activeTab === 'network' && (
            <div>
              <h3 className="text-lg font-semibold mb-4">Network Monitoring</h3>
              <div className="bg-gray-800 p-4 rounded">
                <p className="text-gray-400">
                  Network requests are automatically logged. Check the Logs tab for network activity.
                </p>
                <div className="mt-4 space-y-2">
                  <div className="flex justify-between">
                    <span>API Endpoint:</span>
                    <span className="font-mono">/api/process_product</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Debug Endpoint:</span>
                    <span className="font-mono">/api/debug</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Health Endpoint:</span>
                    <span className="font-mono">/api/health</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
