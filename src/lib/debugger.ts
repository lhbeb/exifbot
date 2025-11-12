/**
 * MAAW Development Debugger
 * A comprehensive debugging tool for browser-based error tracking and API testing
 */

interface DebugConfig {
  enabled: boolean;
  logLevel: 'error' | 'warn' | 'info' | 'debug';
  showInConsole: boolean;
  showInUI: boolean;
  apiEndpoint: string;
}

interface ErrorLog {
  timestamp: string;
  level: 'error' | 'warn' | 'info' | 'debug';
  message: string;
  stack?: string;
  context?: any;
  userAgent: string;
  url: string;
}

interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

class MAAWDebugger {
  private config: DebugConfig;
  private errorLogs: ErrorLog[] = [];
  private isInitialized = false;

  constructor(config: Partial<DebugConfig> = {}) {
    this.config = {
      enabled: true,
      logLevel: 'debug',
      showInConsole: true,
      showInUI: true,
      apiEndpoint: '/api/debug',
      ...config
    };

    this.initialize();
  }

  private initialize() {
    if (this.isInitialized) return;

    // Override console methods
    this.overrideConsole();
    
    // Add global error handlers
    this.addGlobalErrorHandlers();
    
    // Add network monitoring
    this.monitorNetworkRequests();
    
    // Add UI debug panel
    if (this.config.showInUI) {
      this.createDebugPanel();
    }

    this.isInitialized = true;
    this.log('info', 'MAAW Debugger initialized');
  }

  private overrideConsole() {
    if (typeof window === 'undefined') return; // Skip in SSR
    
    const originalConsole = { ...console };
    
    console.error = (...args) => {
      this.log('error', args.join(' '), { originalArgs: args });
      originalConsole.error(...args);
    };

    console.warn = (...args) => {
      this.log('warn', args.join(' '), { originalArgs: args });
      originalConsole.warn(...args);
    };

    console.info = (...args) => {
      this.log('info', args.join(' '), { originalArgs: args });
      originalConsole.info(...args);
    };

    console.debug = (...args) => {
      this.log('debug', args.join(' '), { originalArgs: args });
      originalConsole.debug(...args);
    };
  }

  private addGlobalErrorHandlers() {
    // Only add handlers in browser environment
    if (typeof window === 'undefined') return;

    // Unhandled errors
    window.addEventListener('error', (event) => {
      this.log('error', `Unhandled error: ${event.message}`, {
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        error: event.error
      });
    });

    // Unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.log('error', `Unhandled promise rejection: ${event.reason}`, {
        reason: event.reason,
        promise: event.promise
      });
    });
  }

  private monitorNetworkRequests() {
    // Only monitor in browser environment
    if (typeof window === 'undefined') return;

    const originalFetch = window.fetch;
    
    window.fetch = async (...args) => {
      const startTime = Date.now();
      const url = args[0] as string;
      
      try {
        const response = await originalFetch(...args);
        const duration = Date.now() - startTime;
        
        this.log('info', `Network request: ${url}`, {
          method: args[1]?.method || 'GET',
          status: response.status,
          duration: `${duration}ms`,
          url
        });
        
        return response;
      } catch (error) {
        const duration = Date.now() - startTime;
        
        this.log('error', `Network request failed: ${url}`, {
          method: args[1]?.method || 'GET',
          duration: `${duration}ms`,
          error: error instanceof Error ? error.message : 'Unknown error',
          url
        });
        
        throw error;
      }
    };
  }

  private createDebugPanel() {
    // Only create panel in browser environment
    if (typeof document === 'undefined') return;

    const panel = document.createElement('div');
    panel.id = 'maaw-debug-panel';
    panel.style.cssText = `
      position: fixed;
      top: 10px;
      right: 10px;
      width: 300px;
      max-height: 400px;
      background: #1a1a1a;
      color: #fff;
      border: 1px solid #333;
      border-radius: 8px;
      padding: 10px;
      font-family: monospace;
      font-size: 12px;
      z-index: 10000;
      overflow-y: auto;
      display: none;
    `;

    const header = document.createElement('div');
    header.style.cssText = `
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
      padding-bottom: 5px;
      border-bottom: 1px solid #333;
    `;

    const title = document.createElement('div');
    title.textContent = '🐛 MAAW Debugger';
    title.style.fontWeight = 'bold';

    const toggle = document.createElement('button');
    toggle.textContent = '×';
    toggle.style.cssText = `
      background: #ff4444;
      color: white;
      border: none;
      border-radius: 3px;
      padding: 2px 6px;
      cursor: pointer;
    `;
    toggle.onclick = () => panel.style.display = 'none';

    header.appendChild(title);
    header.appendChild(toggle);
    panel.appendChild(header);

    const logsContainer = document.createElement('div');
    logsContainer.id = 'maaw-debug-logs';
    panel.appendChild(logsContainer);

    document.body.appendChild(panel);

    // Add toggle button
    const toggleButton = document.createElement('button');
    toggleButton.textContent = '🐛';
    toggleButton.style.cssText = `
      position: fixed;
      top: 10px;
      right: 320px;
      width: 40px;
      height: 40px;
      background: #007acc;
      color: white;
      border: none;
      border-radius: 50%;
      cursor: pointer;
      z-index: 10001;
      font-size: 16px;
    `;
    toggleButton.onclick = () => {
      const panel = document.getElementById('maaw-debug-panel');
      if (panel) {
        panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
      }
    };
    document.body.appendChild(toggleButton);
  }

  public log(level: 'error' | 'warn' | 'info' | 'debug', message: string, context?: any) {
    if (!this.config.enabled) return;

    const logEntry: ErrorLog = {
      timestamp: new Date().toISOString(),
      level,
      message,
      context,
      userAgent: typeof window !== 'undefined' && typeof navigator !== 'undefined' ? navigator.userAgent : 'Server',
      url: typeof window !== 'undefined' ? window.location.href : 'Server'
    };

    this.errorLogs.push(logEntry);

    // Show in console
    if (this.config.showInConsole) {
      const consoleMethod = console[level] || console.log;
      consoleMethod(`[MAAW Debugger] ${message}`, context);
    }

    // Show in UI
    if (this.config.showInUI) {
      this.updateDebugPanel(logEntry);
    }

    // Send to API if it's an error
    if (level === 'error') {
      this.sendToAPI('log_error', logEntry);
    }
  }

  private updateDebugPanel(logEntry: ErrorLog) {
    // Only update panel in browser environment
    if (typeof document === 'undefined') return;

    const logsContainer = document.getElementById('maaw-debug-logs');
    if (!logsContainer) return;

    const logElement = document.createElement('div');
    logElement.style.cssText = `
      margin-bottom: 5px;
      padding: 5px;
      border-radius: 3px;
      font-size: 11px;
      ${this.getLogStyle(logEntry.level)}
    `;

    const timestamp = new Date(logEntry.timestamp).toLocaleTimeString();
    logElement.innerHTML = `
      <div style="display: flex; justify-content: space-between;">
        <span>[${timestamp}]</span>
        <span style="color: ${this.getLogColor(logEntry.level)}">${logEntry.level.toUpperCase()}</span>
      </div>
      <div>${logEntry.message}</div>
      ${logEntry.context ? `<div style="color: #888; font-size: 10px;">${JSON.stringify(logEntry.context, null, 2)}</div>` : ''}
    `;

    logsContainer.appendChild(logElement);
    logsContainer.scrollTop = logsContainer.scrollHeight;

    // Keep only last 50 logs
    while (logsContainer.children.length > 50) {
      logsContainer.removeChild(logsContainer.firstChild!);
    }
  }

  private getLogStyle(level: string): string {
    const styles = {
      error: 'background: #4a1a1a; border-left: 3px solid #ff4444;',
      warn: 'background: #4a3a1a; border-left: 3px solid #ffaa00;',
      info: 'background: #1a3a4a; border-left: 3px solid #00aaff;',
      debug: 'background: #1a1a1a; border-left: 3px solid #888;'
    };
    return styles[level as keyof typeof styles] || styles.debug;
  }

  private getLogColor(level: string): string {
    const colors = {
      error: '#ff4444',
      warn: '#ffaa00',
      info: '#00aaff',
      debug: '#888'
    };
    return colors[level as keyof typeof colors] || '#888';
  }

  private async sendToAPI(action: string, data: any) {
    try {
      await fetch(this.config.apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action,
          data,
          timestamp: new Date().toISOString()
        })
      });
    } catch (error) {
      console.error('Failed to send debug data to API:', error);
    }
  }

  // Public methods for manual debugging
  public async testAPI() {
    try {
      const response = await fetch(this.config.apiEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'test_api',
          data: { test: true },
          timestamp: new Date().toISOString()
        })
      });
      
      const result = await response.json();
      this.log('info', 'API test successful', result);
      return result;
    } catch (error) {
      this.log('error', 'API test failed', { error });
      throw error;
    }
  }

  public async validateForm(formData: any) {
    try {
      const response = await fetch(this.config.apiEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'validate_form',
          data: formData,
          timestamp: new Date().toISOString()
        })
      });
      
      const result = await response.json();
      this.log('info', 'Form validation complete', result);
      return result;
    } catch (error) {
      this.log('error', 'Form validation failed', { error });
      throw error;
    }
  }

  public async checkHealth() {
    try {
      const response = await fetch(this.config.apiEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'check_health',
          data: {},
          timestamp: new Date().toISOString()
        })
      });
      
      const result = await response.json();
      this.log('info', 'Health check complete', result);
      return result;
    } catch (error) {
      this.log('error', 'Health check failed', { error });
      throw error;
    }
  }

  public getLogs() {
    return this.errorLogs;
  }

  public clearLogs() {
    this.errorLogs = [];
    if (typeof document !== 'undefined') {
      const logsContainer = document.getElementById('maaw-debug-logs');
      if (logsContainer) {
        logsContainer.innerHTML = '';
      }
    }
  }
}

// Create global instance only in browser environment
let maawDebugger: MAAWDebugger | null = null;

// Lazy initialization
function getDebugger(): MAAWDebugger {
  if (!maawDebugger && typeof window !== 'undefined') {
    maawDebugger = new MAAWDebugger();
    (window as any).maawDebugger = maawDebugger;
  }
  return maawDebugger!;
}

// Export a safe wrapper
export default {
  log: (level: any, message: string, context?: any) => {
    if (typeof window !== 'undefined') {
      getDebugger().log(level, message, context);
    }
  },
  getLogs: () => {
    if (typeof window !== 'undefined') {
      return getDebugger().getLogs();
    }
    return [];
  },
  clearLogs: () => {
    if (typeof window !== 'undefined') {
      getDebugger().clearLogs();
    }
  }
};
