import { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  Globe,
  Brain,
  CreditCard,
  ExternalLink,
  CheckCircle2,
  XCircle,
  ArrowLeft,
  Save,
  Trash2,
  Download,
  Upload,
} from 'lucide-react';
import Card, {
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input from '../components/forms/Input';
import Textarea from '../components/forms/Textarea';
import Alert from '../components/ui/Alert';
import {
  getApiConfig,
  saveApiConfig,
  testGeminiApi,
  testDeepSeekApi,
  testOpenRouterApi,
  testStripeApi,
} from '../services/apiConfig';

const providerConfig = {
  gemini: {
    name: 'Google Gemini',
    icon: Brain,
    color: 'text-yellow-500',
    description: 'AI-powered generation and chat capabilities',
    keyLabel: 'Gemini API Key',
    keyPlaceholder: 'AIzaXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
    helpUrl: 'https://aistudio.google.com/apikey',
    helpText: 'Get free API key from Google AI Studio',
  },
  deepseek: {
    name: 'DeepSeek',
    icon: Brain,
    color: 'text-blue-500',
    description: 'Advanced AI technology and integrations',
    keyLabel: 'DeepSeek API Key',
    keyPlaceholder: 'sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXX',
    helpUrl: 'https://platform.deepseek.com',
    helpText: 'Create account and generate API key',
  },
  openrouter: {
    name: 'OpenRouter',
    icon: Globe,
    color: 'text-purple-500',
    description: 'Unified gateway for multiple AI models',
    keyLabel: 'OpenRouter API Key',
    keyPlaceholder: 'sk-or-XXXXXXXXXXXXXXXXXXXXXXXXXXXX',
    helpUrl: ' https://openrouter.ai/keys',
    helpText: 'Create account and add API key',
  },
  stripe: {
    name: 'Stripe',
    icon: CreditCard,
    color: 'text-indigo-500',
    description: 'Payment processing and billing',
    keyLabel: 'Publishable Key',
    secretLabel: 'Secret Key',
    keyPlaceholder: 'pk_test_xxxxxxxxxxxxxxxxxxxxxxxx',
    secretPlaceholder: 'sk_test_xxxxxxxxxxxxxxxxxxxxxxxx',
    helpUrl: 'https://dashboard.stripe.com/api-keys',
    helpText: 'Get API keys from Stripe Dashboard',
  },
};

function TestResult({ result }) {
  if (!result) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={`mt-3 flex items-start gap-2 rounded-lg p-3 text-sm ${
        result.success ? 'bg-green-500/10 text-green-600' : 'bg-red-500/10 text-red-600'
      }`}
    >
      {result.success ? (
        <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5" />
      ) : (
        <XCircle className="h-4 w-4 shrink-0 mt-0.5" />
      )}
      <div className="flex-1">
        {result.message}
        {result.models !== undefined && (
          <div className="mt-1 text-xs opacity-70">{result.models} models available</div>
        )}
        {result.isTestKey !== undefined && (
          <div className="mt-1 text-xs opacity-70">Mode: {result.isTestKey ? 'Test' : 'Live'}</div>
        )}
      </div>
    </motion.div>
  );
}

function ProviderCard({ provider, config, onChange, onTest }) {
  const { name, icon: Icon, color, description, helpUrl, helpText } = providerConfig[provider];
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);

  const testData = config[provider] || {};

  const handleClickTest = async () => {
    if (provider === 'stripe' && !testData.publishableKey) {
      setTestResult({ success: false, message: 'Please enter publishable key first' });
      return;
    }
    if (provider !== 'stripe' && !testData.apiKey) {
      setTestResult({ success: false, message: 'Please enter API key first' });
      return;
    }

    setTesting(true);
    setTestResult(null);

    try {
      let result;
      switch (provider) {
        case 'gemini':
          result = await testGeminiApi(testData.apiKey);
          break;
        case 'deepseek':
          result = await testDeepSeekApi(testData.apiKey);
          break;
        case 'openrouter':
          result = await testOpenRouterApi(testData.apiKey);
          break;
        case 'stripe':
          result = await testStripeApi(testData.publishableKey);
          break;
        default:
          result = { success: false, message: 'Unknown provider' };
      }
      setTestResult(result);
    } catch (error) {
      setTestResult({ success: false, message: 'Connection failed: ' + error.message });
    } finally {
      setTesting(false);
    }
  };

  const handleKeyChange = (type, value) => {
    const newConfig = { ...config };
    if (!newConfig[provider]) newConfig[provider] = {};

    if (provider === 'stripe') {
      if (type === 'publishableKey') {
        newConfig[provider].publishableKey = value;
      } else {
        newConfig[provider].secretKey = value;
      }
    } else {
      newConfig[provider].apiKey = value;
    }

    onChange(newConfig);
    setTestResult(null);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="border border-border/50 hover:border-border transition-colors">
        <CardHeader>
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className={`p-2 rounded-lg bg-muted ${color}`}>
                <Icon className="h-5 w-5" />
              </div>
              <div>
                <CardTitle className="text-base">{name}</CardTitle>
                <CardDescription className="text-sm mt-1">{description}</CardDescription>
              </div>
            </div>
            <a
              href={helpUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-xs text-primary hover:underline"
            >
              {helpText}
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {provider === 'stripe' ? (
              <>
                <Input
                  label="Publishable Key"
                  type="password"
                  value={testData.publishableKey || ''}
                  onChange={(e) => handleKeyChange('publishableKey', e.target.value)}
                  placeholder={providerConfig.stripe.keyPlaceholder}
                  autoComplete="off"
                />
                <Input
                  label="Secret Key (optional, stored securely)"
                  type="password"
                  value={testData.secretKey || ''}
                  onChange={(e) => handleKeyChange('secretKey', e.target.value)}
                  placeholder={providerConfig.stripe.secretPlaceholder}
                  autoComplete="off"
                />
              </>
            ) : (
              <Input
                label={providerConfig[provider].keyLabel}
                type="password"
                value={testData.apiKey || ''}
                onChange={(e) => handleKeyChange('apiKey', e.target.value)}
                placeholder={providerConfig[provider].keyPlaceholder}
                autoComplete="off"
              />
            )}

            <div className="flex items-center gap-2 mt-4">
              <Button
                onClick={handleClickTest}
                disabled={testing}
                variant="outline"
                size="sm"
                className="flex-1"
                loading={testing}
              >
                Test Connection
              </Button>
            </div>

            <TestResult result={testResult} />
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

const defaultConfig = () => ({
  gemini: { apiKey: '', enabled: false, lastTested: null, testStatus: null },
  deepseek: { apiKey: '', enabled: false, lastTested: null, testStatus: null },
  openrouter: { apiKey: '', enabled: false, lastTested: null, testStatus: null },
  stripe: { publishableKey: '', secretKey: '', enabled: false, lastTested: null, testStatus: null },
});

export default function ApiSettings() {
  const navigate = useNavigate();
  const [config, setConfig] = useState(() => getApiConfig());
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [showImport, setShowImport] = useState(false);
  const [importText, setImportText] = useState('');

  const handleSave = async () => {
    setSaving(true);
    await new Promise((resolve) => setTimeout(resolve, 500));
    const success = saveApiConfig(config);
    if (success) {
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    }
    setSaving(false);
  };

  const handleReset = () => {
    if (
      confirm(
        'Are you sure you want to reset all API configuration? This will clear all saved keys.'
      )
    ) {
      const newConfig = defaultConfig();
      setConfig(newConfig);
      saveApiConfig(newConfig);
    }
  };

  const handleExport = () => {
    const json = JSON.stringify(config, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'lumicorepro-api-config.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleImport = () => {
    try {
      const parsed = JSON.parse(importText);
      const newConfig = { ...defaultConfig(), ...parsed };
      setConfig(newConfig);
      saveApiConfig(newConfig);
      setImportText('');
      setShowImport(false);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (error) {
      alert('Failed to import configuration: Invalid JSON');
    }
  };

  const handleConfigChange = (newConfig) => {
    setConfig(newConfig);
    setSaved(false);
  };

  return (
    <div className="min-h-screen bg-background py-8">
      <div className="container mx-auto px-4 max-w-4xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-8"
        >
          <div className="flex flex-col gap-4">
            <Button
              variant="ghost"
              size="sm"
              leftIcon={ArrowLeft}
              onClick={() => navigate('/templates')}
              className="-ml-2 px-2 text-muted-foreground hover:text-foreground self-start"
            >
              Back to Templates
            </Button>

            <div>
              <h1 className="text-3xl font-bold tracking-tight">API Configuration</h1>
              <p className="text-muted-foreground mt-2">
                Configure API keys for external services. Your keys are stored locally in your
                browser.
              </p>
            </div>
          </div>

          <Alert variant="warning" title="Security Notice">
            API keys are stored in your browser's localStorage. For production use, recommended to
            set up a backend proxy server to keep keys secure. Never share your API keys publicly.
          </Alert>

          <div className="grid gap-6">
            <ProviderCard provider="gemini" config={config} onChange={handleConfigChange} />
            <ProviderCard provider="deepseek" config={config} onChange={handleConfigChange} />
            <ProviderCard provider="openrouter" config={config} onChange={handleConfigChange} />
            <ProviderCard provider="stripe" config={config} onChange={handleConfigChange} />
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Actions</CardTitle>
              <CardDescription>Save or manage your API configuration</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-3">
                <Button
                  onClick={handleSave}
                  disabled={saving || saved}
                  loading={saving}
                  leftIcon={saved ? CheckCircle2 : Save}
                >
                  {saving ? 'Saving...' : saved ? 'Saved!' : 'Save Configuration'}
                </Button>

                <Button onClick={handleExport} variant="outline" leftIcon={Download}>
                  Export Config
                </Button>

                <Button
                  onClick={() => setShowImport(!showImport)}
                  variant="outline"
                  leftIcon={Upload}
                >
                  Import Config
                </Button>

                <Button
                  onClick={handleReset}
                  variant="outline"
                  leftIcon={Trash2}
                  className="text-red-500 hover:text-red-600"
                >
                  Reset All
                </Button>
              </div>

              {showImport && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="mt-4 space-y-3"
                >
                  <Textarea
                    value={importText}
                    onChange={(e) => setImportText(e.target.value)}
                    placeholder="Paste JSON configuration here..."
                    className="w-full h-32 font-mono resize-none"
                    rows={6}
                  />
                  <Button onClick={handleImport} variant="outline" size="sm" leftIcon={Upload}>
                    Import Configuration
                  </Button>
                </motion.div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
