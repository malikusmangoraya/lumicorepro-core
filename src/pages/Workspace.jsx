import { useState, useCallback, useEffect } from 'react';
import {
  Activity,
  Package,
  MonitorPlay,
  CreditCard,
  Wand2,
  RefreshCw,
  Cloud,
  CheckCircle2,
  XCircle,
  Rocket,
  FileCode2,
  FileCheck2,
  Bell,
  Save,
  Send,
} from 'lucide-react';
import { Button, Card, Input, Textarea } from '@/components/ui';
import { extensionsAPI } from '@/services/api';
import { useAppContext } from '@/context/AppContext';
import PageSEO from '@/components/common/PageSEO';
import { cn } from '@/utils';

const RUN_STORAGE_KEY = 'lmc_last_run_id';

const TABS = [
  { id: 'watchtower', label: 'Watchtower', icon: Activity },
  { id: 'marketing', label: 'Marketing Kit', icon: Package },
  { id: 'browserqa', label: 'Browser QA', icon: MonitorPlay },
  { id: 'checkout', label: 'Stripe Checkout', icon: CreditCard },
  { id: 'editor', label: 'Visual Editor', icon: Wand2 },
  { id: 'delivery', label: 'Delivery Reports', icon: FileCheck2 },
  { id: 'webhooks', label: 'Webhooks', icon: Bell },
];

const initialErrors = { watchtower: '', runAction: '', editor: '', deploy: '' };

function WorkspacePage() {
  const { addNotification } = useAppContext();
  const [tab, setTab] = useState('watchtower');
  const [runId, setRunId] = useState('');
  const [watch, setWatch] = useState(null);
  const [action, setAction] = useState({ status: '', message: '', data: null });
  const [editor, setEditor] = useState({
    targetFile: 'frontend/src/pages/LandingPage.jsx',
    instruction: '',
    selectorHint: '',
  });
  const [loading, setLoading] = useState({ watchtower: false, runAction: false, editor: false, deploy: false });
  const [errors, setErrors] = useState(initialErrors);
  const [hooks, setHooks] = useState([]);
  const [hooksDraft, setHooksDraft] = useState('');
  const [hooksBusy, setHooksBusy] = useState({ load: false, save: false, test: false });

  useEffect(() => {
    const saved = localStorage.getItem(RUN_STORAGE_KEY) || '';
    setRunId(saved);
  }, []);

  const refreshWatch = useCallback(async () => {
    setLoading((p) => ({ ...p, watchtower: true }));
    setErrors((p) => ({ ...p, watchtower: '' }));
    try {
      const { data } = await extensionsAPI.watchtower();
      setWatch(data.data);
    } catch (err) {
      setErrors((p) => ({ ...p, watchtower: err.message }));
    } finally {
      setLoading((p) => ({ ...p, watchtower: false }));
    }
  }, []);

  useEffect(() => {
    if (tab === 'watchtower' && !watch) refreshWatch();
  }, [tab, watch, refreshWatch]);

  const persistRun = (id) => {
    localStorage.setItem(RUN_STORAGE_KEY, id);
  };

  const runAction = async (kind, payload) => {
    if (!runId) return setErrors((p) => ({ ...p, runAction: 'Run ID required first — generate a project.' }));
    persistRun(runId);
    setLoading((p) => ({ ...p, runAction: true }));
    setErrors((p) => ({ ...p, runAction: '' }));
    setAction({ status: '', message: '', data: null });
    try {
      const { data } = await payload();
      setAction({
        status: data.success ? 'ok' : 'failed',
        message: data.data?.message || (data.success ? 'Done.' : 'Unexpected failure.'),
        data: data.data,
      });
      if (data.success) addNotification?.(`${kind} finished — see extension output below.`);
    } catch (err) {
      setErrors((p) => ({ ...p, runAction: err.message }));
    } finally {
      setLoading((p) => ({ ...p, runAction: false }));
    }
  };

  const runEditor = async () => {
    if (!runId) return setErrors((p) => ({ ...p, editor: 'Run ID required first.' }));
    if (!editor.targetFile || !editor.instruction)
      return setErrors((p) => ({ ...p, editor: 'File path and instruction required.' }));
    persistRun(runId);
    setLoading((p) => ({ ...p, editor: true }));
    setErrors((p) => ({ ...p, editor: '' }));
    setAction({ status: '', message: '', data: null });
    try {
      const { data } = await extensionsAPI.editElement({
        run_id: runId,
        target_file: editor.targetFile,
        instruction: editor.instruction,
        selector_hint: editor.selectorHint,
      });
      setAction({
        status: data.success ? 'ok' : 'failed',
        message: data.data?.message || (data.success ? 'Saved.' : 'Edit rejected.'),
        data: data.data,
      });
      if (data.success) addNotification?.('Visual edit applied.');
    } catch (err) {
      setErrors((p) => ({ ...p, editor: err.message }));
    } finally {
      setLoading((p) => ({ ...p, editor: false }));
    }
  };

  const deployPages = async () => {
    if (!runId) return setErrors((p) => ({ ...p, deploy: 'Run ID required first.' }));
    persistRun(runId);
    setLoading((p) => ({ ...p, deploy: true }));
    setErrors((p) => ({ ...p, deploy: '' }));
    setAction({ status: '', message: '', data: null });
    try {
      const { data } = await extensionsAPI.githubPagesDeploy(runId);
      setAction({
        status: data.success ? 'ok' : 'failed',
        message: data.data?.message || (data.success ? 'Deploy prepared.' : 'Deploy failed.'),
        data: data.data,
      });
      if (data.success) addNotification?.('GitHub Pages deploy prepared.');
    } catch (err) {
      setErrors((p) => ({ ...p, deploy: err.message }));
    } finally {
      setLoading((p) => ({ ...p, deploy: false }));
    }
  };

  const loadHooks = async () => {
    setHooksBusy((p) => ({ ...p, load: true }));
    try {
      const { data } = await extensionsAPI.getWebhooks();
      const urls = data.data?.webhooks || [];
      setHooks(urls);
      setHooksDraft(urls.join('\n'));
    } catch (err) {
      setErrors((p) => ({ ...p, runAction: `Webhooks: ${err.message}` }));
    } finally {
      setHooksBusy((p) => ({ ...p, load: false }));
    }
  };

  const saveHooks = async () => {
    const urls = hooksDraft.split('\n').map((s) => s.trim()).filter(Boolean);
    setHooksBusy((p) => ({ ...p, save: true }));
    try {
      const { data } = await extensionsAPI.updateWebhooks(urls);
      setHooks(urls);
      setAction({ status: 'ok', message: `Saved ${urls.length} webhook endpoint(s).`, data: data.data });
      addNotification?.('Webhooks saved.');
    } catch (err) {
      setErrors((p) => ({ ...p, runAction: `Webhooks: ${err.message}` }));
    } finally {
      setHooksBusy((p) => ({ ...p, save: false }));
    }
  };

  const testHooks = async () => {
    setHooksBusy((p) => ({ ...p, test: true }));
    try {
      const { data } = await extensionsAPI.testWebhook(hooksDraft.split('\n').map((s) => s.trim()).filter(Boolean)[0]);
      setAction({
        status: data.success ? 'ok' : 'failed',
        message: data.success ? 'Test ping delivered.' : 'Test ping failed.',
        data: data.data,
      });
    } catch (err) {
      setErrors((p) => ({ ...p, runAction: `Webhooks: ${err.message}` }));
    } finally {
      setHooksBusy((p) => ({ ...p, test: false }));
    }
  };

  useEffect(() => {
    if (tab === 'webhooks' && !hooks.length) loadHooks();
  }, [tab]);

  const runIdField = (
    <div className="w-full">
      <label htmlFor="run-id" className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
        Project Run ID
      </label>
      <Input
        id="run-id"
        value={runId}
        onChange={(e) => setRunId(e.target.value)}
        placeholder="e.g. generated-website-023"
      />
    </div>
  );

  const actionButtons = (
    <div className="mt-4 flex flex-wrap items-center gap-3">
      <Button
        onClick={() => runAction('marketing', () => extensionsAPI.marketingKit(runId))}
        disabled={loading.runAction}
        loading={loading.runAction}
      >
        Generate Marketing Kit
      </Button>
      <Button
        variant="outline"
        onClick={() => runAction('browserqa', () => extensionsAPI.browserQA(runId))}
        disabled={loading.runAction}
        loading={loading.runAction}
      >
        Run Browser QA
      </Button>
      {tab === 'checkout' && (
        <Button
          variant="outline"
          onClick={() => runAction('checkout', () => extensionsAPI.checkoutStripe(runId))}
          disabled={loading.runAction}
          loading={loading.runAction}
        >
          Scaffold Stripe Checkout
        </Button>
      )}
      {tab === 'delivery' && (
        <Button
          variant="outline"
          onClick={() => runAction('delivery', () => extensionsAPI.deliveryReport(runId))}
          disabled={loading.runAction}
          loading={loading.runAction}
        >
          Write Delivery Reports
        </Button>
      )}
    </div>
  );

  const statusBanner = action.status ? (
    <div
      className={cn(
        'mt-4 flex items-start gap-2 rounded-lg border p-3 text-sm',
        action.status === 'ok'
          ? 'border-emerald-300 bg-emerald-50 text-emerald-800 dark:border-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-200'
          : 'border-rose-300 bg-rose-50 text-rose-800 dark:border-rose-700 dark:bg-rose-900/20 dark:text-rose-200'
      )}
    >
      {action.status === 'ok' ? (
        <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
      ) : (
        <XCircle className="mt-0.5 h-4 w-4 shrink-0" />
      )}
      <div className="min-w-0">
        <div className="font-medium">{action.message}</div>
        {action.data && (
          <pre className="mt-2 max-h-64 overflow-auto rounded bg-black/5 p-2 text-xs dark:bg-black/30">
            {JSON.stringify(action.data, null, 2)}
          </pre>
        )}
      </div>
    </div>
  ) : null;

  const errorLine = (key) =>
    errors[key] ? (
      <p className="mt-2 flex items-center gap-1.5 text-sm text-rose-600 dark:text-rose-400">
        <XCircle className="h-4 w-4" /> {errors[key]}
      </p>
    ) : null;

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-10 dark:bg-slate-950">
      <PageSEO title="Workspace — Agent Extensions" description="Power tools for your generated projects." />
      <div className="mx-auto w-full max-w-6xl">
        <header className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            Agent Extensions Workspace
          </h1>
          <p className="mt-1 text-slate-600 dark:text-slate-400">
            Marketing kit, real-browser QA, Stripe checkout, visual edits and live analytics — built-in.
          </p>
        </header>

        <div className="mb-6 flex flex-wrap gap-2">
          {TABS.map((t) => {
            const Icon = t.icon;
            return (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={cn(
                  'flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all duration-200',
                  tab === t.id
                    ? 'bg-slate-900 text-white shadow dark:bg-white dark:text-slate-900'
                    : 'bg-white text-slate-600 hover:bg-slate-100 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800'
                )}
              >
                <Icon className="h-4 w-4" /> {t.label}
              </button>
            );
          })}
        </div>

        <Card className="p-6">
          {tab === 'watchtower' && (
            <div>
              <div className="mb-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-indigo-500" />
                  <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Watchtower</h2>
                </div>
                <Button variant="ghost" size="sm" onClick={refreshWatch} disabled={loading.watchtower}>
                  <RefreshCw className={cn('h-4 w-4', loading.watchtower && 'animate-spin')} />
                  Refresh
                </Button>
              </div>
              {errorLine('watchtower')}
              {watch ? (
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="grid grid-cols-2 gap-3">
                    <Stat label="Provider Pool" value={`${watch.pool?.available_count ?? 0}/${watch.pool?.loaded_count ?? 0}`} />
                    <Stat label="Calls Tracked" value={watch.usage?.total_calls ?? 0} />
                    <Stat label="Avg Latency" value={`${watch.usage?.avg_latency_ms ?? 0}ms`} />
                    <Stat label="Health" value={`${Math.round((watch.health?.success_rate ?? 0) * 100)}%`} />
                  </div>
                  <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-800">
                    <table className="w-full text-sm">
                      <thead className="bg-slate-100 text-left text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-900 dark:text-slate-400">
                        <tr>
                          <th className="px-3 py-2">Provider</th>
                          <th className="px-3 py-2">Calls</th>
                          <th className="px-3 py-2">Success</th>
                          <th className="px-3 py-2">Latency</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                        {(watch.per_provider || []).map((p) => (
                          <tr key={p.provider}>
                            <td className="px-3 py-2 font-medium dark:text-slate-200">{p.provider}</td>
                            <td className="px-3 py-2">{p.calls}</td>
                            <td className="px-3 py-2">{p.success}</td>
                            <td className="px-3 py-2">{p.avg_latency_ms ?? '-'}ms</td>
                          </tr>
                        ))}
                        {!(watch.per_provider || []).length && (
                          <tr>
                            <td className="px-3 py-2 text-slate-500" colSpan={4}>
                              No provider calls recorded yet.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-slate-500 dark:text-slate-400">Loading analytics…</p>
              )}
            </div>
          )}

          {(tab === 'marketing' || tab === 'browserqa' || tab === 'checkout' || tab === 'delivery') && (
            <div className="max-w-xl">
              <h2 className="mb-1 text-lg font-semibold text-slate-900 dark:text-white">
                {TABS.find((t) => t.id === tab)?.label}
              </h2>
              <p className="mb-4 text-sm text-slate-600 dark:text-slate-400">
                {tab === 'marketing' && 'Logo pack, favicon, OG image, seller README and a zipped seller kit for your generated project.'}
                {tab === 'browserqa' && 'Screenshots + collapse detection + console/LCP evidence from a real browser.'}
                {tab === 'checkout' && 'Working Stripe checkout scaffold for commerce projects (safe no-op otherwise).'}
                {tab === 'delivery' && 'QA, Performance and Accessibility reports written into the project — required for the purchase package.'}
              </p>
              {runIdField}
              {actionButtons}
              {errorLine('runAction')}
              {statusBanner}
            </div>
          )}

          {tab === 'editor' && (
            <div className="max-w-xl">
              <h2 className="mb-1 text-lg font-semibold text-slate-900 dark:text-white">Visual Editor</h2>
              <p className="mb-4 text-sm text-slate-600 dark:text-slate-400">
                AI-edits one project file (safely, with provider pool rotation). Path must stay inside the project.
              </p>
              <div className="space-y-3">
                {runIdField}
                <div>
                  <label htmlFor="target" className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
                    Target file (project-relative)
                  </label>
                  <Input
                    id="target"
                    value={editor.targetFile}
                    onChange={(e) => setEditor((s) => ({ ...s, targetFile: e.target.value }))}
                  />
                </div>
                <div>
                  <label htmlFor="instruction" className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
                    Instruction
                  </label>
                  <Textarea
                    id="instruction"
                    rows={3}
                    value={editor.instruction}
                    onChange={(e) => setEditor((s) => ({ ...s, instruction: e.target.value }))}
                    placeholder="e.g. Swap the hero headline for a punchier one and make the CTA glow."
                  />
                </div>
                <div>
                  <label htmlFor="selector" className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
                    Selector hint (optional)
                  </label>
                  <Input
                    id="selector"
                    value={editor.selectorHint}
                    onChange={(e) => setEditor((s) => ({ ...s, selectorHint: e.target.value }))}
                    placeholder="e.g. .hero-badge or h1"
                  />
                </div>
                <Button onClick={runEditor} disabled={loading.editor} loading={loading.editor}>
                  <FileCode2 className="mr-2 h-4 w-4" /> Apply AI Edit
                </Button>
                {errorLine('editor')}
                {statusBanner}
              </div>
            </div>
          )}

          {tab === 'webhooks' && (
            <div className="max-w-xl">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <h2 className="mb-1 text-lg font-semibold text-slate-900 dark:text-white">Outbound Webhooks</h2>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    Fire events to Zapier / Make / n8n / Slack when builds finish. One URL per line.
                  </p>
                </div>
                <Button variant="ghost" size="sm" onClick={loadHooks} disabled={hooksBusy.load}>
                  <RefreshCw className={cn('h-4 w-4', hooksBusy.load && 'animate-spin')} />
                  Reload
                </Button>
              </div>
              {errorLine('runAction')}
              {statusBanner}
              {hooksBusy.load ? (
                <p className="text-sm text-slate-500 dark:text-slate-400">Loading webhooks…</p>
              ) : (
                <div className="space-y-3">
                  <Textarea
                    rows={4}
                    value={hooksDraft}
                    onChange={(e) => setHooksDraft(e.target.value)}
                    placeholder={'https://hooks.zapier.com/hooks/catch/...\nhttps://discord.com/api/webhooks/...'}
                  />
                  <div className="flex flex-wrap items-center gap-3">
                    <Button onClick={saveHooks} disabled={hooksBusy.save} loading={hooksBusy.save}>
                      <Save className="mr-2 h-4 w-4" /> Save Webhooks
                    </Button>
                    <Button variant="outline" onClick={testHooks} disabled={hooksBusy.test} loading={hooksBusy.test}>
                      <Send className="mr-2 h-4 w-4" /> Send Test Ping
                    </Button>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Events fired: <code className="rounded bg-black/5 px-1 dark:bg-black/30">run.completed</code>,{' '}
                    <code className="rounded bg-black/5 px-1 dark:bg-black/30">deploy.completed</code>,{' '}
                    <code className="rounded bg-black/5 px-1 dark:bg-black/30">qa.completed</code>. Bodies are
                    HMAC-SHA256 signed.
                  </p>
                </div>
              )}
            </div>
          )}

          <div className="mt-6 flex items-center justify-between border-t border-slate-100 pt-4 dark:border-slate-800">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                <Cloud className="mr-1 inline h-4 w-4" />
                Deploy this project free to GitHub Pages.
              </p>
              {errorLine('deploy')}
            </div>
            <Button onClick={deployPages} disabled={loading.deploy} loading={loading.deploy}>
              <Rocket className="mr-2 h-4 w-4" /> Deploy to GitHub Pages
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
      <div className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">{label}</div>
      <div className="text-xl font-bold text-slate-900 dark:text-white">{value}</div>
    </div>
  );
}

export default WorkspacePage;