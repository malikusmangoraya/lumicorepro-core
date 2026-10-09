export const messages = [
  { id: 1, role: 'ai', text: 'Hi — I am Lumicore AI. How can I help you today?', timestamp: new Date(Date.now() - 3600000) },
  { id: 2, role: 'user', text: 'Draft a short product update for our new dashboard feature.', timestamp: new Date(Date.now() - 3500000) },
  { id: 3, role: 'ai', text: 'Sure! Share the feature list and target audience, and I\'ll draft a compelling product update for you.', timestamp: new Date(Date.now() - 3400000) },
];

export const models = [
  { id: 'gpt-4o', name: 'GPT-4o', tier: 'premium', description: 'Most capable model for complex tasks' },
  { id: 'gpt-4', name: 'GPT-4', tier: 'premium', description: 'High-quality reasoning and creativity' },
  { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', tier: 'standard', description: 'Fast and cost-effective' },
  { id: 'claude-3-opus', name: 'Claude 3 Opus', tier: 'premium', description: 'Excellent for analysis and writing' },
  { id: 'claude-3-sonnet', name: 'Claude 3 Sonnet', tier: 'standard', description: 'Balanced performance and speed' },
];