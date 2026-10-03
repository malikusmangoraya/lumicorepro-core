import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Search, Plus, Trash2, Pencil, Download, Loader2, AlertCircle, X } from 'lucide-react';
import { usersAPI } from '../services/api';
import { toCSV, downloadCSV } from '../utils/csv';

const ROLES = ['user', 'admin', 'editor'];

const fmtDate = (date) => {
  if (!date) return '-';
  return new Intl.DateTimeFormat('en-US', { dateStyle: 'medium' }).format(new Date(date));
};

export default function AdminUsers() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [form, setForm] = useState({ name: '', email: '', role: 'user' });
  const [formError, setFormError] = useState('');
  const [deletingId, setDeletingId] = useState(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ['users'],
    queryFn: () => usersAPI.getAll(),
  });

  const users = data?.data?.data || [];

  const saveMutation = useMutation({
    mutationFn: () =>
      editingUser
        ? usersAPI.update(editingUser.id, form)
        : usersAPI.create(form),
    onSuccess: () => {
      queryClient.invalidateQueries(['users']);
      setShowModal(false);
      setEditingUser(null);
      setForm({ name: '', email: '', role: 'user' });
      setFormError('');
    },
    onError: (err) => {
      setFormError(err?.response?.data?.message || t('adminUsers.saveError', 'Failed to save user'));
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => usersAPI.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries(['users']);
      setDeletingId(null);
    },
  });

  const openCreate = () => {
    setEditingUser(null);
    setForm({ name: '', email: '', role: 'user' });
    setFormError('');
    setShowModal(true);
  };

  const openEdit = (user) => {
    setEditingUser(user);
    setForm({ name: user.name || '', email: user.email || '', role: user.role || 'user' });
    setFormError('');
    setShowModal(true);
  };

  const confirmDelete = (user) => {
    if (window.confirm(t('adminUsers.deleteConfirm', 'Delete this user?'))) {
      setDeletingId(user.id);
      deleteMutation.mutate(user.id);
    }
  };

  const handleExport = () => {
    const columns = [
      { key: 'id', label: t('adminUsers.id', 'ID') },
      { key: 'name', label: t('adminUsers.name', 'Name') },
      { key: 'email', label: t('adminUsers.email', 'Email') },
      { key: 'role', label: t('adminUsers.role', 'Role') },
      { key: 'createdAt', label: t('adminUsers.joined', 'Joined') },
    ];
    downloadCSV(toCSV(users, columns), 'users.csv');
  };

  const filtered = users.filter((u) => {
    const q = search.toLowerCase();
    if (!q) return true;
    return (
      (u.name || '').toLowerCase().includes(q) ||
      (u.email || '').toLowerCase().includes(q)
    );
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-500">
        <AlertCircle className="w-5 h-5 shrink-0" />
        <span>{t('adminUsers.loadError', 'Failed to load users')}</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <h1 className="text-2xl font-bold text-foreground">{t('adminUsers.title', 'Manage Users')}</h1>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleExport}
            className="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg border border-border bg-card text-foreground hover:bg-muted transition-all duration-200"
          >
            <Download className="w-4 h-4" />
            {t('adminUsers.export', 'Export CSV')}
          </button>
          <button
            type="button"
            onClick={openCreate}
            className="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-all duration-200"
          >
            <Plus className="w-4 h-4" />
            {t('adminUsers.addUser', 'Add User')}
          </button>
        </div>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder={t('adminUsers.search', 'Search by name or email...')}
          className="w-full pl-10 pr-4 py-2.5 text-sm rounded-lg border border-border bg-card text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
        />
      </div>

      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">{t('adminUsers.id', 'ID')}</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">{t('adminUsers.name', 'Name')}</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">{t('adminUsers.email', 'Email')}</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">{t('adminUsers.role', 'Role')}</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">{t('adminUsers.joined', 'Joined')}</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">{t('adminUsers.actions', 'Actions')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center">
                    <AlertCircle className="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
                    <p className="text-muted-foreground">{t('adminUsers.noUsers', 'No users found')}</p>
                  </td>
                </tr>
              )}
              {filtered.map((user) => (
                <tr key={user.id} className="hover:bg-muted/30 transition-colors">
                  <td className="px-4 py-3 text-muted-foreground">#{user.id}</td>
                  <td className="px-4 py-3 font-medium text-foreground">{user.name}</td>
                  <td className="px-4 py-3 text-foreground">{user.email}</td>
                  <td className="px-4 py-3">
                    <span className="inline-block text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary font-medium capitalize">
                      {user.role || 'user'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">{fmtDate(user.createdAt)}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        type="button"
                        onClick={() => openEdit(user)}
                        className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-all duration-200"
                        aria-label={t('adminUsers.edit', 'Edit')}
                      >
                        <Pencil className="w-4 h-4" />
                      </button>
                      <button
                        type="button"
                        onClick={() => confirmDelete(user)}
                        disabled={deletingId === user.id}
                        className="p-2 rounded-lg text-muted-foreground hover:text-red-500 hover:bg-red-500/10 transition-all duration-200"
                        aria-label={t('adminUsers.delete', 'Delete')}
                      >
                        {deletingId === user.id ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Trash2 className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" role="dialog" aria-modal="true">
          <div className="w-full max-w-md bg-card border border-border rounded-xl p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-foreground">
                {editingUser ? t('adminUsers.editUser', 'Edit User') : t('adminUsers.addUser', 'Add User')}
              </h2>
              <button
                type="button"
                onClick={() => setShowModal(false)}
                className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-all duration-200"
                aria-label={t('common.close', 'Close')}
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {formError && (
              <div className="flex items-center gap-2 p-3 mb-4 bg-red-500/10 border border-red-500/20 rounded-lg text-sm text-red-500">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1" htmlFor="user-name">
                  {t('adminUsers.name', 'Name')}
                </label>
                <input
                  id="user-name"
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="w-full px-3 py-2.5 text-sm rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1" htmlFor="user-email">
                  {t('adminUsers.email', 'Email')}
                </label>
                <input
                  id="user-email"
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  className="w-full px-3 py-2.5 text-sm rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-1" htmlFor="user-role">
                  {t('adminUsers.role', 'Role')}
                </label>
                <select
                  id="user-role"
                  value={form.role}
                  onChange={(e) => setForm({ ...form, role: e.target.value })}
                  className="w-full px-3 py-2.5 text-sm rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                >
                  {ROLES.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button
                type="button"
                onClick={() => setShowModal(false)}
                className="px-4 py-2.5 text-sm font-medium rounded-lg border border-border bg-card text-foreground hover:bg-muted transition-all duration-200"
              >
                {t('adminUsers.cancel', 'Cancel')}
              </button>
              <button
                type="button"
                onClick={() => saveMutation.mutate()}
                disabled={saveMutation.isPending}
                className="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-60 transition-all duration-200"
              >
                {saveMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
                {t('adminUsers.save', 'Save')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}