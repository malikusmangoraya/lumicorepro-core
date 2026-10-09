import express from 'express';

const router = express.Router();

router.get('/', (req, res) => {
  res.send(`<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI-Generated Code Disclosure</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #1a1a2e; background: #f8f9fa; line-height: 1.7; }
    .container { max-width: 720px; margin: 40px auto; padding: 0 24px; }
    h1 { font-size: 2rem; margin-bottom: 8px; }
    .meta { color: #6b7280; margin-bottom: 32px; font-size: 0.9rem; }
    h2 { font-size: 1.25rem; margin: 28px 0 12px; color: #1a1a2e; }
    p, li { font-size: 1rem; color: #374151; margin-bottom: 12px; }
    ul { padding-left: 20px; margin-bottom: 12px; }
    li { margin-bottom: 6px; }
    .notice { background: #fef3c7; border-left: 4px solid #f59e0b; padding: 16px 20px; border-radius: 0 8px 8px 0; margin: 20px 0; }
    .notice strong { color: #b45309; }
    .tech { background: #eef2ff; border-left: 4px solid #6366f1; padding: 16px 20px; border-radius: 0 8px 8px 0; margin: 20px 0; }
    code { background: #e5e7eb; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }
  </style>
</head>
<body>
  <div class="container">
    <h1>AI-Generated Code Disclosure</h1>
    <p class="meta">Transparency Notice | Last updated: ${new Date().toISOString().split('T')[0]}</p>

    <div class="notice">
      <strong>Transparency Notice:</strong> Portions of the codebase for this website were generated or assisted by artificial intelligence tools.
    </div>

    <h2>1. What Was AI-Generated</h2>
    <p>This project was built using <strong>LumiCorePro</strong>, an AI-powered full-stack website generator. The following components may contain AI-generated code:</p>
    <ul>
      <li>Frontend React components and page layouts</li>
      <li>Backend Express.js API routes and middleware</li>
      <li>Database schemas and migration scripts</li>
      <li>Configuration files (Tailwind, Vite, etc.)</li>
      <li>Styling and responsive design patterns</li>
    </ul>

    <h2>2. AI Provider</h2>
    <p>The code generation was powered by large language models (LLMs) from one or more of the following providers:</p>
    <ul>
      <li>Google Gemini</li>
      <li>DeepSeek</li>
      <li>OpenRouter (multi-model gateway)</li>
    </ul>

    <h2>3. Human Oversight</h2>
    <p>All AI-generated code was reviewed and validated before deployment:</p>
    <ul>
      <li>Automated quality gates evaluated structure and completeness</li>
      <li>Code security scanning was performed to block dangerous patterns</li>
      <li>A human developer reviewed and approved the final output</li>
    </ul>

    <h2>4. Limitations</h2>
    <p>AI-generated code is provided <strong>as-is</strong>. While it follows established patterns and best practices, it may contain:</p>
    <ul>
      <li>Edge cases not covered in the initial generation</li>
      <li>Dependencies on specific AI-generated project structure</li>
      <li>Code that benefits from human review for domain-specific logic</li>
    </ul>

    <h2>5. Open Source</h2>
    <p>This project is built on open-source technologies: <code>React</code>, <code>Vite</code>, <code>Tailwind CSS</code>, <code>Express.js</code>, <code>Node.js</code>. The AI-generated code follows standard conventions for these frameworks.</p>

    <h2>6. Questions</h2>
    <p>If you have questions about AI-generated portions of this codebase, please contact the project maintainer.</p>
  </div>
</body>
</html>`);
});

export default router;
