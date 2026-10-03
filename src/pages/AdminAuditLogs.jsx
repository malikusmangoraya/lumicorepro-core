import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Search, Download, Loader2, AlertCircle, ChevronLeft, ChevronRight } from 'lucide-react';
import { auditAPI } from '../services/api';
import { downloadBlob } from '../utils/csv';

const fmtDate = (date) => {
  if (!date) return '-';
  return new Intl.DateTimeFormat('en-US', { dateStyle: 'medium' }).format(new Date(date));
};

export default function AdminAuditLogs() {
  const { t } = useTranslation();
  const [page, setPage] = useState(1);
  const [actionFilter, setActionFilter] = useState('');
  const [userIdFilter, setUserIdFilter] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [applied, setApplied] = useState({});
  const [limit] = useState(20);
  const [exporting, setExporting] = useState(false);

  const { data, isLoading, error } = useQuery({
    queryKey: ['audit', { page, limit, ...applied }],
    queryFn: () =>
      auditAPI.list({
        page,
        limit,
        action: applied.action || undefined,
        userId: applied.userId || undefined,
        from: applied.from || undefined,
        to: applied.to || undefined,
      }),
  });

  const rows = data?.data?.data || [];
  const pagination = data?.data?.pagination || { page: 1, totalPages: 1, total: 0 };

  const applyFilters = () => {
    setPage(1);
    setApplied({
      action: actionFilter.trim(),
      userId: userIdFilter.trim(),
      from: dateFrom,
      to: dateTo,
    });
  };

  const resetFilters = () => {
    setActionFilter('');
    setUserIdFilter('');
    setDateFrom('');
    setDateTo('');
    setApplied({});
    setPage(1);
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const res = await auditAPI.exportCSV({
        action: applied.action || undefined,
        userId: applied.userId || undefined,
        from: applied.from || undefined,
        to: applied.to || undefined,
      });
      downloadBlob(res.data, 'audit-logs.csv');
    } finally {
      setExporting(false);
    }
  };

  const inputClass = 'px-3 py-2 text-sm rounded-lg border border-border bg-card text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50';

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h1 className="text-2xl font-bold text-foreground">{t('adminAudit.title', 'Audit Logs')}</h1>
        <button
          type="button"
          onClick={handleExport}
          disabled={exporting}
          className="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg border border-border bg-card text-foreground hover:bg-muted disabled:opacity-60 transition-all duration-200"
        >
          {exporting ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Download className="w-4 h-4" />
          )}
          {t('adminAudit.export', 'Export CSV')}
        </button>
      </div>

      <div className="bg-card border border-border rounded-lg p-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          <input
            type="text"
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            placeholder={t('adminAudit.actionFilter', 'Action...')}
            className={inputClass}
          />
          <input
            type="text"
            value={userIdFilter}
            onChange={(e) => setUserIdFilter(e.target.value)}
            placeholder={t('adminAudit.userIdFilter', 'User ID...')}
            className={inputClass}
          />
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className={inputClass}
            aria-label={t('adminAudit.from', 'From date')}
          />
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className={inputClass}
            aria-label={t('adminAudit.to', 'To date')}
          />
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={applyFilters}
              className="inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-all duration-200"
            >
              <Search className="w-4 h-4" />
              {t('adminAudit.search', 'Search')}
            </button>
            <button
              type="button"
              onClick={resetFilters}
              className="px-4 py-2 text-sm font-medium rounded-lg border border-border bg-card text-foreground hover:bg-muted transition-all duration-200"
            >
              {t('adminAudit.reset', 'Reset')}
            </button>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <div className="flex items-center gap-2 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-500">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{t('adminAudit.loadError', 'Failed to load audit logs')}</span>
        </div>
      ) : (
        <div className="bg-card border border-border rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">{t('adminAudit.id', 'ID')}</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">{t('adminAudit.action', 'Action')}</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">{t('adminAudit.email', 'Email')}</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">{t('adminAudit.ip', 'IP')}</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">{t('adminAudit.userAgent', 'User Agent')}</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">{t('adminAudit.timestamp', 'Timestamp')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {rows.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-4 py-12 text-center">
                      <AlertCircle className="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
                      <p className="text-muted-foreground">{t('adminAudit.empty', 'No audit logs found')}</p>
                    </td>
                  </tr>
                )}
                {rows.map((log) => (
                  <tr key={log.id} className="hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-3 text-muted-foreground">#{log.id}</td>
                    <td className="px-4 py-3">
                      <span className="inline-block text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary font-medium">
                        {log.action}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-foreground">{log.email || '-'}</td>
                    <td className="px-4 py-3 text-muted-foreground">{log.ip || '-'}</td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {log.userAgent
                        ? `${log.userAgent.slice(0, 40)}${log.userAgent.length > 40 ? '...' : ''}`
                        : '-'}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{fmtDate(log.timestamp)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {rows.length > 0 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-border">
              <p className="text-sm text-muted-foreground">
                {t('adminAudit.pageInfo', 'Page {{page}} of {{totalPages}}', {
                  page: pagination.page,
                  totalPages: pagination.totalPages,
                })}
              </p>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={pagination.page <= 1}
                  className="inline-flex items-center gap-1 px-3 py-2 text-sm font-medium rounded-lg border border-border bg-card text-foreground hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                >
                  <ChevronLeft className="w-4 h-4" />
                  {t('adminAudit.prev', 'Prev')}
                </button>
                <button
                  type="button"
                  onClick={() => setPage((p) => p + 1)}
                  disabled={pagination.page >= pagination.totalPages}
                  className="inline-flex items-center gap-1 px-3 py-2 text-sm font-medium rounded-lg border border-border bg-card text-foreground hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                >
                  {t('adminAudit.next', 'Next')}
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}