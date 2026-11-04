/** prompts — reusable prompt template engine.
 * Templates are {{var}}-substituted system+user pairs, versioned in code so
 * every generated artifact is reproducible. render() throws on missing vars
 * (fail loud, never ship a half-filled prompt to a paid API).
 */
const TEMPLATES = {
  summarize: {
    system: 'You are an expert summarizer. Output concise, factual, structured summaries in markdown.',
    user: 'Summarize the following {{kind}} in under {{maxWords}} words:\n\n{{content}}',
  },
  rewrite: {
    system: 'You are a senior editor. Improve clarity and tone without changing meaning.',
    user: 'Rewrite this {{kind}} in a {{tone}} tone:\n\n{{content}}',
  },
  chat: {
    system: 'You are {{brand}} support. Answer only from the provided context. If unsure, say so.',
    user: 'Context:\n{{context}}\n\nQuestion: {{question}}',
  },
  seoArticle: {
    system: 'You are an SEO content strategist writing for humans first.',
    user: 'Write a {{maxWords}}-word article on "{{topic}}" targeting the keyword "{{keyword}}". Include H2 headings and a meta description.',
  },
  email: {
    system: 'You are a conversion copywriter. Short paragraphs, one clear CTA.',
    user: 'Write a {{tone}} email to {{audience}} about {{subject}}. Goal: {{goal}}.',
  },
};

function render(name, vars = {}) {
  const tpl = TEMPLATES[name];
  if (!tpl) throw new Error(`Unknown prompt template: ${name}`);
  const fill = (s) => s.replace(/{{\s*(\w+)\s*}}/g, (_, k) => {
    if (vars[k] === undefined || vars[k] === null || vars[k] === '') {
      throw new Error(`Prompt "${name}" missing variable: ${k}`);
    }
    return String(vars[k]);
  });
  return { system: fill(tpl.system), user: fill(tpl.user) };
}

function list() {
  return Object.keys(TEMPLATES);
}

module.exports = { render, list, TEMPLATES };
