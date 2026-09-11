/**
 * API Configuration Management Service
 * Manages API keys, configuration, and testing for all external providers
 */

// Storage key for API configuration
const STORAGE_KEY = 'lumicorepro_api_config';

// Default API configuration structure
const defaultConfig = {
  gemini: {
    apiKey: '',
    enabled: false,
    lastTested: null,
    testStatus: null, // 'success', 'error', null
  },
  deepseek: {
    apiKey: '',
    enabled: false,
    lastTested: null,
    testStatus: null,
  },
  openrouter: {
    apiKey: '',
    enabled: false,
    lastTested: null,
    testStatus: null,
  },
  stripe: {
    publishableKey: '',
    secretKey: '',
    enabled: false,
    lastTested: null,
    testStatus: null,
  },
};

/**
 * Get current API configuration from localStorage
 */
export function getApiConfig() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      return { ...defaultConfig, ...parsed };
    }
  } catch {
    // Invalid stored config — reset to defaults
  }
  return { ...defaultConfig };
}

/**
 * Save API configuration to localStorage
 */
export function saveApiConfig(config) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
    return true;
  } catch {
    return false;
  }
}

/**
 * Update specific provider configuration
 */
export function updateProviderConfig(provider, updates) {
  const config = getApiConfig();
  if (config[provider]) {
    config[provider] = { ...config[provider], ...updates };
    return saveApiConfig(config);
  }
  return false;
}

/**
 * Test Gemini API connectivity
 */
export async function testGeminiApi(apiKey) {
  try {
    const response = await fetch(
      'https://generativelanguage.googleapis.com/v1beta/models?key=' + apiKey,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (response.ok) {
      const data = await response.json();
      return {
        success: true,
        message: 'Gemini API connection successful!',
        models: data.models?.length || 0,
      };
    } else {
      const error = await response.json();
      return {
        success: false,
        message: error.error?.message || 'Invalid API key',
      };
    }
  } catch (error) {
    return {
      success: false,
      message: 'Connection failed: ' + error.message,
    };
  }
}

/**
 * Test DeepSeek API connectivity
 */
export async function testDeepSeekApi(apiKey) {
  try {
    const response = await fetch('https://api.deepseek.com/v1/models', {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
    });

    if (response.ok) {
      const data = await response.json();
      return {
        success: true,
        message: 'DeepSeek API connection successful!',
        models: data.data?.length || 0,
      };
    } else {
      const error = await response.json();
      return {
        success: false,
        message: error.error?.message || 'Invalid API key',
      };
    }
  } catch (error) {
    return {
      success: false,
      message: 'Connection failed: ' + error.message,
    };
  }
}

/**
 * Test OpenRouter API connectivity
 */
export async function testOpenRouterApi(apiKey) {
  try {
    const response = await fetch('https://openrouter.ai/api/v1/auth/key', {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
        'HTTP-Referer': window.location.origin,
        'X-Title': 'LumiCorePro',
      },
    });

    if (response.ok) {
      const data = await response.json();
      return {
        success: true,
        message: 'OpenRouter API connection successful!',
        keyInfo: data.data?.label || 'Valid key',
      };
    } else {
      return {
        success: false,
        message: 'Invalid API key or unauthorized',
      };
    }
  } catch (error) {
    return {
      success: false,
      message: 'Connection failed: ' + error.message,
    };
  }
}

/**
 * Test Stripe API connectivity (publishable key validation)
 */
export async function testStripeApi(publishableKey) {
  try {
    // Stripe doesn't have a direct test endpoint for publishable keys,
    // but we can validate the format
    const isValidFormat = /^pk_(test|live)_/.test(publishableKey);

    if (!isValidFormat) {
      return {
        success: false,
        message: 'Invalid Stripe publishable key format',
      };
    }

    return {
      success: true,
      message: 'Stripe key format is valid! (Full test requires backend)',
      isTestKey: publishableKey.startsWith('pk_test_'),
    };
  } catch (error) {
    return {
      success: false,
      message: 'Validation failed: ' + error.message,
    };
  }
}

/**
 * Get API key for a specific provider
 */
export function getApiKey(provider) {
  const config = getApiConfig();
  const providerConfig = config[provider];

  if (!providerConfig) return null;

  // Return appropriate key based on provider
  if (provider === 'stripe') {
    return providerConfig.publishableKey || providerConfig.secretKey;
  }

  return providerConfig.apiKey || null;
}

/**
 * Check if a provider is enabled and has API key
 */
export function isProviderEnabled(provider) {
  const config = getApiConfig();
  const providerConfig = config[provider];

  if (!providerConfig) return false;

  if (provider === 'stripe') {
    return !!(providerConfig.publishableKey || providerConfig.secretKey);
  }

  return !!providerConfig.apiKey;
}

/**
 * Reset all API configuration
 */
export function resetApiConfig() {
  localStorage.removeItem(STORAGE_KEY);
  return true;
}

/**
 * Export configuration for backup
 */
export function exportApiConfig() {
  const config = getApiConfig();
  return JSON.stringify(config, null, 2);
}

/**
 * Import configuration from backup
 */
export function importApiConfig(jsonString) {
  try {
    const config = JSON.parse(jsonString);
    return saveApiConfig(config);
  } catch {
    return false;
  }
}

export default {
  getApiConfig,
  saveApiConfig,
  updateProviderConfig,
  testGeminiApi,
  testDeepSeekApi,
  testOpenRouterApi,
  testStripeApi,
  getApiKey,
  isProviderEnabled,
  resetApiConfig,
  exportApiConfig,
  importApiConfig,
};
