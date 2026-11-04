"""Emit a secure Expo + TypeScript mobile client for generated records APIs."""

import json
import re
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlsplit


MOBILE_DEPENDENCIES = {
    "expo": "~58.0.21",
    "expo-constants": "~58.0.14",
    "expo-crypto": "~58.0.7",
    "expo-linking": "~58.0.15",
    "expo-router": "~58.0.28",
    "expo-secure-store": "~58.0.2",
    "expo-splash-screen": "~58.0.12",
    "expo-status-bar": "~58.0.4",
    "react": "19.3.0",
    "react-dom": "19.3.0",
    "react-native": "0.88.0",
    "react-native-web": "^0.21.4",
    "react-native-safe-area-context": "~5.10.1",
    "react-native-screens": "~4.30.0",
    "react-native-sse": "1.2.1",
    "@react-native-async-storage/async-storage": "2.2.0",
    "@react-native-community/netinfo": "12.0.1",
}

MOBILE_DEV_DEPENDENCIES = {
    "@types/react": "~19.3.0",
    "typescript": "~6.0.3",
}

_PROJECT_FILES = {
    "tsconfig.json": {
        "extends": "expo/tsconfig.base",
        "compilerOptions": {"strict": True, "paths": {"@/*": ["./src/*"]}},
        "include": ["**/*.ts", "**/*.tsx", ".expo/types/**/*.ts", "expo-env.d.ts"],
    },
    "app/_layout.tsx": r"""import { useEffect } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { Stack, useRouter, useSegments } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { AuthProvider, useAuth } from '../src/auth/AuthContext';
import { theme } from '../src/theme';

function RootNavigator() {
  const { ready, isAuthenticated } = useAuth();
  const segments = useSegments();
  const router = useRouter();
  useEffect(() => {
    if (!ready) return;
    const inAuthGroup = segments[0] === '(auth)';
    if (!isAuthenticated && !inAuthGroup) router.replace('/(auth)/sign-in');
    else if (isAuthenticated && inAuthGroup) router.replace('/(tabs)');
  }, [ready, isAuthenticated, segments, router]);
  if (!ready) return <View style={{ flex: 1, justifyContent: 'center', backgroundColor: theme.background }}>
    <ActivityIndicator accessibilityLabel="Loading session" />
  </View>;
  return (
    <>
      <StatusBar style="light" />
      <Stack screenOptions={{ headerStyle: { backgroundColor: theme.surface }, headerTintColor: theme.text }}>
        <Stack.Screen name="(auth)" options={{ headerShown: false }} />
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="record/[id]" options={{ title: 'Record' }} />
        <Stack.Screen name="record/new" options={{ title: 'New record' }} />
      </Stack>
    </>
  );
}

export default function RootLayout() {
  return <AuthProvider><RootNavigator /></AuthProvider>;
}
""",
    "app/(auth)/_layout.tsx": r"""import { Stack } from 'expo-router';

export default function AuthLayout() {
  return <Stack screenOptions={{ headerShown: false }} />;
}
""",
    "app/(auth)/sign-in.tsx": r"""import { useState } from 'react';
import { Link, router } from 'expo-router';
import { ActivityIndicator, Button, Text, TextInput, View } from 'react-native';
import { useAuth } from '../../src/auth/AuthContext';
import { theme } from '../../src/theme';

const BRAND = {{BRAND}};

export default function SignInScreen() {
  const { signIn } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  async function submit() {
    setLoading(true);
    setError('');
    try {
      await signIn(email.trim(), password);
      router.replace('/(tabs)');
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'Unable to sign in. Try again.');
    } finally {
      setLoading(false);
    }
  }
  return (
    <View style={{ flex: 1, justifyContent: 'center', padding: 24, backgroundColor: theme.background }}>
      <Text style={{ color: theme.text, fontSize: 30, fontWeight: '700' }}>{BRAND}</Text>
      <Text style={{ color: theme.muted, marginVertical: 16 }}>Sign in to your workspace</Text>
      <TextInput accessibilityLabel="Email" testID="Email" autoCapitalize="none"
        keyboardType="email-address" value={email} onChangeText={setEmail} placeholder="Email"
        placeholderTextColor={theme.muted}
        style={{ color: theme.text, borderColor: theme.border, borderWidth: 1, padding: 14, marginBottom: 12 }} />
      <TextInput accessibilityLabel="Password" testID="Password" secureTextEntry value={password}
        onChangeText={setPassword} placeholder="Password" placeholderTextColor={theme.muted}
        style={{ color: theme.text, borderColor: theme.border, borderWidth: 1, padding: 14 }} />
      {!!error && <Text accessibilityRole="alert" style={{ color: theme.danger, marginTop: 12 }}>{error}</Text>}
      {loading ? <ActivityIndicator accessibilityLabel="Signing in" /> : <Button title="Sign in" onPress={submit} />}
      <Link href="/(auth)/register" style={{ color: theme.primary, marginTop: 18 }}>Create your account</Link>
    </View>
  );
}
""",
    "app/(auth)/register.tsx": r"""import { useState } from 'react';
import { Link, router } from 'expo-router';
import { Button, Text, TextInput, View } from 'react-native';
import { useAuth } from '../../src/auth/AuthContext';
import { theme } from '../../src/theme';

export default function RegisterScreen() {
  const { register } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  async function submit() {
    setError('');
    try {
      await register(name.trim(), email.trim(), password);
      router.replace('/(tabs)');
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'Unable to register. Try again.');
    }
  }
  return (
    <View style={{ flex: 1, justifyContent: 'center', padding: 24, backgroundColor: theme.background }}>
      <Text accessibilityRole="header" style={{ color: theme.text, fontSize: 28, fontWeight: '700' }}>
        Create your account
      </Text>
      <TextInput accessibilityLabel="Name" testID="Name" value={name} onChangeText={setName}
        placeholder="Name" placeholderTextColor={theme.muted} style={{ color: theme.text, padding: 14 }} />
      <TextInput accessibilityLabel="Email" testID="Email" autoCapitalize="none"
        keyboardType="email-address" value={email} onChangeText={setEmail} placeholder="Email"
        placeholderTextColor={theme.muted} style={{ color: theme.text, padding: 14 }} />
      <TextInput accessibilityLabel="Password" testID="Password" secureTextEntry value={password}
        onChangeText={setPassword} placeholder="Password" placeholderTextColor={theme.muted}
        style={{ color: theme.text, padding: 14 }} />
      {!!error && <Text accessibilityRole="alert" style={{ color: theme.danger }}>{error}</Text>}
      <Button title="Create account" onPress={submit} />
      <Link href="/(auth)/sign-in" style={{ color: theme.primary, marginTop: 18 }}>Sign in</Link>
    </View>
  );
}
""",
    "app/(tabs)/_layout.tsx": r"""import { Tabs } from 'expo-router';
import { theme } from '../../src/theme';

export default function TabsLayout() {
  return <Tabs screenOptions={{
    headerStyle: { backgroundColor: theme.surface }, headerTintColor: theme.text,
    tabBarStyle: { backgroundColor: theme.surface }, tabBarActiveTintColor: theme.primary,
  }}>
    <Tabs.Screen name="index" options={{ title: 'Overview', tabBarLabel: 'Home' }} />
    <Tabs.Screen name="records" options={{ title: 'Records' }} />
    <Tabs.Screen name="settings" options={{ title: 'Settings' }} />
  </Tabs>;
}
""",
    "app/(tabs)/index.tsx": r"""import { Link } from 'expo-router';
import { Text, View } from 'react-native';
import { theme } from '../../src/theme';

export default function OverviewScreen() {
  return <View style={{ flex: 1, padding: 24, backgroundColor: theme.background }}>
    <Text accessibilityRole="header" style={{ color: theme.text, fontSize: 28, fontWeight: '700' }}>
      Your workspace
    </Text>
    <Text style={{ color: theme.muted, marginTop: 10 }}>Manage your records and account.</Text>
    <Link href="/(tabs)/records" style={{ color: theme.primary, marginTop: 24 }}>Browse records</Link>
  </View>;
}
""",
    "app/(tabs)/records.tsx": r"""import { useCallback, useEffect, useState } from 'react';
import { Link, useFocusEffect } from 'expo-router';
import { ActivityIndicator, Button, FlatList, Pressable, Text, View } from 'react-native';
import { listRecords, RecordItem } from '../../src/api/records';
import { useRecordFeed } from '../../src/realtime/useRecordFeed';
import { subscribeQueueCount } from '../../src/offline/queue';
import { theme } from '../../src/theme';

export default function RecordsScreen() {
  const [records, setRecords] = useState<RecordItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [queued, setQueued] = useState(0);
  const load = useCallback(async () => {
    setError('');
    try { setRecords(await listRecords()); }
    catch (failure) { setError(failure instanceof Error ? failure.message : 'Could not load records.'); }
    finally { setLoading(false); }
  }, []);
  useRecordFeed(load);
  useFocusEffect(useCallback(() => { void load(); }, [load]));
  useEffect(() => subscribeQueueCount(setQueued), []);
  return <View style={{ flex: 1, padding: 20, backgroundColor: theme.background }}>
    <Text accessibilityRole="header" style={{ color: theme.text, fontSize: 26, fontWeight: '700' }}>
      All records
    </Text>
    {!!queued && <Text accessibilityLiveRegion="polite" style={{ color: theme.accent, marginVertical: 8 }}>
      {queued} queued — waiting to sync
    </Text>}
    <Link href="/record/new" style={{ color: theme.primary, marginVertical: 14 }}>Create record</Link>
    {loading ? <ActivityIndicator accessibilityLabel="Loading records" /> : error ?
      <View><Text accessibilityRole="alert" style={{ color: theme.danger }}>{error}</Text>
        <Button title="Retry" onPress={() => { setLoading(true); void load(); }} /></View> :
      records.length === 0 ? <Text style={{ color: theme.muted }}>No records yet. Create one to get started.</Text> :
      <FlatList data={records} keyExtractor={(item) => item.id}
        renderItem={({ item }) => <Link href={{ pathname: '/record/[id]', params: { id: item.id } }} asChild>
          <Pressable accessibilityRole="link" style={{ padding: 16, borderBottomWidth: 1, borderColor: theme.border }}>
            <Text style={{ color: theme.text, fontWeight: '600' }}>{item.title}</Text>
          </Pressable>
        </Link>} />}
  </View>;
}
""",
    "app/(tabs)/settings.tsx": r"""import { Button, Text, View } from 'react-native';
import { useAuth } from '../../src/auth/AuthContext';
import { theme } from '../../src/theme';

export default function SettingsScreen() {
  const { signOut, user } = useAuth();
  return <View style={{ flex: 1, padding: 24, backgroundColor: theme.background }}>
    <Text accessibilityRole="header" style={{ color: theme.text, fontSize: 26 }}>Account settings</Text>
    <Text style={{ color: theme.muted, marginVertical: 18 }}>{user?.email || 'Signed in'}</Text>
    <Button title="Sign out" onPress={() => { void signOut(); }} />
  </View>;
}
""",
    "app/record/[id].tsx": r"""import { useCallback, useEffect, useState } from 'react';
import { router, useLocalSearchParams } from 'expo-router';
import { ActivityIndicator, Button, Text, TextInput, View } from 'react-native';
import { deleteRecord, getRecord, RecordItem, updateRecord } from '../../src/api/records';
import { theme } from '../../src/theme';

export default function RecordDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [record, setRecord] = useState<RecordItem | null>(null);
  const [title, setTitle] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const load = useCallback(async () => {
    setError('');
    try {
      const value = await getRecord(id);
      setRecord(value);
      setTitle(value.title);
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'Could not load this record.');
    }
  }, [id]);
  useEffect(() => { void load(); }, [load]);
  async function save() {
    if (!record) return;
    try {
      const result = await updateRecord(id, {
        title, body: record.body, status: record.status,
      });
      if (result.queued) {
        setMessage('Queued offline — waiting for server confirmation.');
        return;
      }
      router.back();
    }
    catch (failure) { setError(failure instanceof Error ? failure.message : 'Could not update record.'); }
  }
  async function remove() {
    try { await deleteRecord(id); router.back(); }
    catch (failure) { setError(failure instanceof Error ? failure.message : 'Could not delete record.'); }
  }
  if (!record) return <View style={{ padding: 24 }}>
    {error ? <>
      <Text accessibilityRole="alert" style={{ color: theme.danger }}>{error}</Text>
      <Button title="Retry" onPress={() => { void load(); }} />
    </> : <ActivityIndicator accessibilityLabel="Loading record" />}
  </View>;
  return <View style={{ flex: 1, padding: 24, backgroundColor: theme.background }}>
    <TextInput accessibilityLabel="Title" testID="Title" value={title} onChangeText={setTitle}
      style={{ color: theme.text, borderWidth: 1, borderColor: theme.border, padding: 14 }} />
    <Text style={{ color: theme.muted, marginVertical: 16 }}>{record.body || 'No description'}</Text>
    {!!message && <Text accessibilityLiveRegion="polite" style={{ color: theme.accent }}>{message}</Text>}
    {!!error && <Text accessibilityRole="alert" style={{ color: theme.danger }}>{error}</Text>}
    <Button title="Save changes" onPress={() => { void save(); }} />
    <Button title="Delete record" color={theme.danger} onPress={() => { void remove(); }} />
  </View>;
}
""",
    "app/record/new.tsx": r"""import { useState } from 'react';
import { router } from 'expo-router';
import { Button, Text, TextInput, View } from 'react-native';
import { createRecord } from '../../src/api/records';
import { theme } from '../../src/theme';

export default function NewRecordScreen() {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  async function submit() {
    setMessage('');
    setError('');
    try {
      const result = await createRecord({ title, body: description });
      if (result.queued) {
        setMessage('Queued offline — this record will appear after the server confirms sync.');
        return;
      }
      router.back();
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'Could not create record.');
    }
  }
  return <View style={{ flex: 1, padding: 24, backgroundColor: theme.background }}>
    <Text accessibilityRole="header" style={{ color: theme.text, fontSize: 26 }}>New record</Text>
    <TextInput accessibilityLabel="Title" testID="Title" value={title} onChangeText={setTitle}
      placeholder="Title" placeholderTextColor={theme.muted} style={{ color: theme.text, padding: 14 }} />
    <TextInput accessibilityLabel="Description" testID="Description" value={description}
      onChangeText={setDescription} placeholder="Description" placeholderTextColor={theme.muted}
      style={{ color: theme.text, padding: 14 }} />
    {!!message && <Text accessibilityLiveRegion="polite" style={{ color: theme.accent }}>{message}</Text>}
    {!!error && <Text accessibilityRole="alert" style={{ color: theme.danger }}>{error}</Text>}
    <Button title="Create record" onPress={() => { void submit(); }} />
  </View>;
}
""",
    "src/api/client.ts": r"""import * as SecureStore from 'expo-secure-store';

const DEFAULT_API_BASE = __DEV__ ? 'http://10.0.2.2:5000/api/v1' : '';
export const API_BASE = (process.env.EXPO_PUBLIC_API_URL || DEFAULT_API_BASE)
  .replace(/\/+$/, '');
let unauthorizedHandler: (() => void) | undefined;

export function setUnauthorizedHandler(handler: () => void) {
  unauthorizedHandler = handler;
}

function assertApiBase() {
  let url: URL;
  try { url = new URL(API_BASE); } catch { throw new Error('Set EXPO_PUBLIC_API_URL to a valid API URL.'); }
  const localHttp = url.protocol === 'http:' &&
    ['10.0.2.2', 'localhost', '127.0.0.1'].includes(url.hostname);
  if (url.username || url.password || url.search || url.hash) {
    throw new Error('API URL must not contain credentials, query parameters, or fragments.');
  }
  if (url.protocol !== 'https:' && !(localHttp && __DEV__)) {
    throw new Error('Release builds require an HTTPS API URL.');
  }
  return url;
}

export async function readAuthToken() {
  return SecureStore.getItemAsync('authToken');
}

export class ApiError extends Error {
  constructor(message: string, public readonly status: number) { super(message); }
}

export async function request<T>(
  path: string,
  init: RequestInit = {},
  expectedOwnerId?: string,
): Promise<T> {
  const base = assertApiBase().toString().replace(/\/$/, '');
  const token = await readAuthToken();
  if (expectedOwnerId) {
    const activeOwnerId = await SecureStore.getItemAsync('authUserId');
    if (!token || activeOwnerId !== expectedOwnerId) {
      throw new Error('The active account changed before queued changes could sync.');
    }
  }
  const response = await fetch(`${base}${path.startsWith('/') ? path : `/${path}`}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  });
  if (response.status === 401) {
    await SecureStore.deleteItemAsync('authToken');
    unauthorizedHandler?.();
  }
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new ApiError(body.message || body.error || 'The request could not be completed.', response.status);
  }
  return (body.data === undefined ? body : body.data) as T;
}
""",
    "src/api/auth.ts": r"""import { request } from './client';

export type AuthResult = { token: string; user: { id: string; name?: string; email: string } };

export function login(email: string, password: string) {
  return request<AuthResult>('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });
}

export function register(name: string, email: string, password: string) {
  return request<AuthResult>('/auth/register', {
    method: 'POST', body: JSON.stringify({ name, email, password }),
  });
}
""",
    "src/api/records.ts": r"""import NetInfo from '@react-native-community/netinfo';
import * as Crypto from 'expo-crypto';
import { enqueueOperation, flushQueue, getQueueScope, QueuedOperation } from '../offline/queue';
import { request } from './client';

export type RecordItem = { id: string; title: string; body?: string; status?: string };
type WriteResult = { queued: boolean; record?: RecordItem };

export async function listRecords() {
  return request<RecordItem[]>('/records');
}

export async function getRecord(id: string) {
  return request<RecordItem>(`/records/${encodeURIComponent(id)}`);
}

async function online() {
  return (await NetInfo.fetch()).isConnected === true;
}

export async function createRecord(input: Pick<RecordItem, 'title' | 'body'>): Promise<WriteResult> {
  const operation: QueuedOperation = {
    clientId: Crypto.randomUUID(), method: 'POST', path: '/records', body: input,
  };
  if (!(await online())) {
    await enqueueOperation(operation);
    return { queued: true };
  }
  try {
    return { queued: false, record: await request<RecordItem>('/records', {
      method: 'POST', body: JSON.stringify({ ...input, id: operation.clientId }),
    }) };
  } catch (error) {
    if (error instanceof TypeError) {
      await enqueueOperation(operation);
      return { queued: true };
    }
    throw error;
  }
}

export async function updateRecord(id: string, input: Partial<RecordItem>) {
  const patch = {
    ...(input.title !== undefined ? { title: input.title } : {}),
    ...(input.body !== undefined ? { body: input.body } : {}),
    ...(input.status !== undefined ? { status: input.status } : {}),
  };
  const operation: QueuedOperation = {
    clientId: id, method: 'PUT', path: `/records/${encodeURIComponent(id)}`, body: patch,
  };
  if (!(await online())) {
    await enqueueOperation(operation);
    return { queued: true };
  }
  try {
    await request<RecordItem>(operation.path, { method: 'PUT', body: JSON.stringify(patch) });
    return { queued: false };
  } catch (error) {
    if (error instanceof TypeError) {
      await enqueueOperation(operation);
      return { queued: true };
    }
    throw error;
  }
}

export function deleteRecord(id: string) {
  return request<void>(`/records/${encodeURIComponent(id)}`, { method: 'DELETE' });
}

export async function flushQueuedRecords() {
  const ownerId = getQueueScope();
  if (!ownerId) return;
  await flushQueue(async (operation) => request(operation.path, {
    method: operation.method,
    body: JSON.stringify(operation.method === 'POST'
      ? { ...operation.body, id: operation.clientId }
      : operation.body),
  }, ownerId));
}
""",
    "src/auth/AuthContext.tsx": r"""import { createContext, PropsWithChildren, useContext, useEffect, useMemo, useState } from 'react';
import * as SecureStore from 'expo-secure-store';
import { AppState } from 'react-native';
import NetInfo from '@react-native-community/netinfo';
import { AuthResult, login, register } from '../api/auth';
import { readAuthToken, setUnauthorizedHandler } from '../api/client';
import { flushQueuedRecords } from '../api/records';
import { setQueueScope } from '../offline/queue';

type User = AuthResult['user'] | null;
type AuthValue = {
  user: User;
  ready: boolean;
  isAuthenticated: boolean;
  signIn(email: string, password: string): Promise<void>;
  register(name: string, email: string, password: string): Promise<void>;
  signOut(): Promise<void>;
};
const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<User>(null);
  const [ready, setReady] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  async function signOut() {
    await SecureStore.deleteItemAsync('authToken');
    await SecureStore.deleteItemAsync('authUserId');
    setQueueScope(null);
    setUser(null);
    setIsAuthenticated(false);
  }
  async function persist(result: AuthResult) {
    await SecureStore.setItemAsync('authToken', result.token);
    await SecureStore.setItemAsync('authUserId', result.user.id);
    setQueueScope(result.user.id);
    setUser(result.user);
    setIsAuthenticated(true);
  }
  useEffect(() => {
    setUnauthorizedHandler(() => { void signOut(); });
    void Promise.all([
      readAuthToken(),
      SecureStore.getItemAsync('authUserId'),
    ]).then(([token, userId]) => {
      if (token) {
        setQueueScope(userId);
        setIsAuthenticated(true);
      }
    }).finally(() => setReady(true));
    const unsubscribe = NetInfo.addEventListener((state) => {
      if (state.isConnected && isAuthenticated) {
        void flushQueuedRecords().catch(() => undefined);
      }
    });
    const app = AppState.addEventListener('change', (state) => {
      if (state === 'active' && isAuthenticated) {
        void flushQueuedRecords().catch(() => undefined);
      }
    });
    return () => { unsubscribe(); app.remove(); };
  }, [isAuthenticated]);
  const value = useMemo<AuthValue>(() => ({
    user,
    ready,
    isAuthenticated,
    signIn: async (email, password) => persist(await login(email, password)),
    register: async (name, email, password) => persist(await register(name, email, password)),
    signOut,
  }), [user, ready, isAuthenticated]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used inside AuthProvider.');
  return value;
}
""",
    "src/realtime/useRecordFeed.ts": r"""import { useEffect, useState } from 'react';
import { AppState } from 'react-native';
import EventSource from 'react-native-sse';
import { API_BASE, readAuthToken } from '../api/client';

export function useRecordFeed(onChange: () => void) {
  const [mode, setMode] = useState<'connecting' | 'live' | 'polling'>('connecting');
  useEffect(() => {
    let active = true;
    let source: EventSource<'record:changed'> | undefined;
    let poll: ReturnType<typeof setInterval> | undefined;
    const close = () => { source?.close(); source = undefined; };
    const startPolling = () => {
      close();
      setMode('polling');
      if (!poll) poll = setInterval(() => { if (active) onChange(); }, 15000);
    };
    const connect = async () => {
      const token = await readAuthToken();
      if (!active || !token) return startPolling();
      close();
      if (poll) { clearInterval(poll); poll = undefined; }
      setMode('connecting');
      source = new EventSource(`${API_BASE}/events?token=${encodeURIComponent(token)}`);
      source.addEventListener('open', () => { if (active) setMode('live'); });
      source.addEventListener('message', () => { if (active) onChange(); });
      source.addEventListener('record:changed', () => { if (active) onChange(); });
      source.addEventListener('error', () => { if (active) startPolling(); });
    };
    void connect();
    const app = AppState.addEventListener('change', (state) => {
      if (state === 'active') void connect();
      else startPolling();
    });
    return () => {
      active = false;
      close();
      if (poll) clearInterval(poll);
      app.remove();
    };
  }, [onChange]);
  return mode;
}
""",
    "src/offline/queue.ts": r"""import AsyncStorage from '@react-native-async-storage/async-storage';

const QUEUE_KEY = 'lumicore:offline-queue';
export const MAX_QUEUE_SIZE = 50;
export type QueuedOperation = {
  clientId: string;
  method: 'POST' | 'PUT';
  path: string;
  body: Record<string, unknown>;
};
const listeners = new Set<(count: number) => void>();
let queueScope = 'anonymous';
let flushing = false;

export function setQueueScope(userId: string | null) {
  queueScope = userId || 'anonymous';
}

export function getQueueScope() {
  return queueScope === 'anonymous' ? null : queueScope;
}

function storageKey(scope = queueScope) {
  return `${QUEUE_KEY}:${scope}`;
}

async function readQueue(key = storageKey()): Promise<QueuedOperation[]> {
  const value = await AsyncStorage.getItem(key);
  return value ? JSON.parse(value) as QueuedOperation[] : [];
}

async function writeQueue(queue: QueuedOperation[], key = storageKey()) {
  await AsyncStorage.setItem(key, JSON.stringify(queue));
  listeners.forEach((listener) => listener(queue.length));
}

export function subscribeQueueCount(listener: (count: number) => void) {
  const key = storageKey();
  listeners.add(listener);
  void readQueue(key).then((items) => listener(items.length));
  return () => { listeners.delete(listener); };
}

export async function enqueueOperation(operation: QueuedOperation) {
  const key = storageKey();
  const queue = await readQueue(key);
  if (queue.length >= MAX_QUEUE_SIZE) throw new Error('Offline queue is full. Connect to sync your changes.');
  queue.push(operation);
  await writeQueue(queue, key);
}

export async function flushQueue(send: (operation: QueuedOperation) => Promise<unknown>) {
  const scope = queueScope;
  const key = storageKey(scope);
  if (scope === 'anonymous' || flushing) return;
  flushing = true;
  try {
    // Sequential flush preserves order; only confirmed writes leave the scoped queue.
    while (scope === queueScope) {
      const current = await readQueue(key);
      const operation = current[0];
      if (!operation) return;
      await send(operation);
      if (scope !== queueScope) return;
      const latest = await readQueue(key);
      const confirmedIndex = latest.findIndex((item) =>
        item.clientId === operation.clientId &&
        item.method === operation.method &&
        item.path === operation.path &&
        JSON.stringify(item.body) === JSON.stringify(operation.body));
      if (confirmedIndex !== -1) latest.splice(confirmedIndex, 1);
      await writeQueue(latest, key);
    }
  } finally {
    flushing = false;
  }
}
""",
    ".maestro/smoke.yaml": r"""appId: {{PACKAGE}}
---
- launchApp:
    clearState: true
- assertVisible: "Sign in"
- tapOn: "Create your account"
- assertVisible: "Create your account"
- takeScreenshot: "register"
""",
    ".maestro/records.yaml": r"""appId: {{PACKAGE}}
---
- launchApp:
    clearState: true
- assertVisible: "Create your account"
- tapOn: "Create your account"
- assertVisible: "Create your account"
- tapOn:
    id: "Name"
- inputText: "Maestro User"
- tapOn:
    id: "Email"
- inputText: "${EMAIL}"
- tapOn:
    id: "Password"
- inputText: "${PASSWORD}"
- tapOn: "Create account"
- assertVisible: "Your workspace"
- takeScreenshot: "registered"
- tapOn: "Records"
- takeScreenshot: "records-list"
- tapOn: "Create record"
- tapOn:
    id: "Title"
- inputText: "Maestro record"
- tapOn: "Create record"
- assertVisible: "Maestro record"
- takeScreenshot: "record-created"
- tapOn: "Maestro record"
- assertVisible: "No description"
- takeScreenshot: "record-detail"
# Edit the title and verify the server-confirmed value.
- tapOn:
    id: "Title"
- eraseText: 30
- inputText: "Updated Maestro record"
- tapOn: "Save changes"
- assertVisible: "Updated Maestro record"
- takeScreenshot: "record-updated"
""",
}


def _brand_slug(brand: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(brand).strip().lower()).strip("-")
    slug = slug[:40].strip("-")
    if not slug:
        raise ValueError("Brand must contain letters or numbers.")
    return slug


def _validate_api_base(api_base: str) -> str:
    if not api_base:
        return ""
    try:
        parsed = urlsplit(api_base)
        hostname = (parsed.hostname or "").lower()
        _ = parsed.port
        valid = (
            parsed.scheme == "https"
            or (parsed.scheme == "http" and hostname in {"10.0.2.2", "localhost"})
        )
        if (not valid or not hostname or parsed.username or parsed.password
                or parsed.query or parsed.fragment):
            raise ValueError
    except (TypeError, ValueError):
        raise ValueError("Mobile release API base must use HTTPS.") from None
    return api_base.rstrip("/")


def _theme_source(design: Dict[str, Any]) -> str:
    colors = {
        "primary": design.get("primary", "#2563eb"),
        "accent": design.get("accent", "#0d9488"),
        "background": design.get("slate", {}).get("950", "#0f172a"),
        "surface": design.get("slate", {}).get("900", "#1e293b"),
        "text": design.get("ink", "#f8fafc"),
        "muted": design.get("muted", "#94a3b8"),
        "border": design.get("slate", {}).get("700", "#334155"),
        "danger": "#ef4444",
    }
    return "export const theme = " + json.dumps(colors, indent=2) + " as const;\n"


def _render_assets(asset_dir: Path, brand: str, design: Dict[str, Any]) -> None:
    from PIL import Image, ImageDraw, ImageFont

    primary = design.get("primary", "#2563eb")
    accent = design.get("accent", "#0d9488")
    background = design.get("slate", {}).get("950", "#0f172a")

    def color(value: str):
        value = value.lstrip("#")
        if len(value) != 6 or not re.fullmatch(r"[0-9a-fA-F]{6}", value):
            value = "2563eb"
        return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))

    asset_dir.mkdir(parents=True, exist_ok=True)
    mark = color(primary)
    secondary = color(accent)
    bg = color(background)
    for filename, size, is_splash in (
        ("icon.png", (1024, 1024), False),
        ("adaptive-icon.png", (1024, 1024), False),
        ("splash.png", (1284, 2778), True),
    ):
        image = Image.new("RGB", size, bg)
        draw = ImageDraw.Draw(image)
        width, height = size
        scale = min(width, height)
        radius = int(scale * (0.25 if is_splash else 0.3))
        cx, cy = width // 2, int(height * 0.43 if is_splash else height // 2)
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=mark)
        inner = int(radius * 0.58)
        points = [
            (cx, cy - inner), (cx + inner, cy - inner // 3),
            (cx + inner * 2 // 3, cy + inner), (cx - inner * 2 // 3, cy + inner),
            (cx - inner, cy - inner // 3),
        ]
        draw.polygon(points, fill=secondary)
        if is_splash:
            label = brand[:28]
            font = _splash_font(max(36, int(width * 0.065)))
            box = draw.textbbox((0, 0), label, font=font)
            draw.text(((width - box[2]) / 2, cy + radius + 72), label, fill=(248, 250, 252),
                      font=font)
        image.save(asset_dir / filename, format="PNG", optimize=True)


_SPLASH_FONT_NAMES = (
    "arial.ttf", "Arial.ttf", "Arial-Bold.ttf", "Helvetica.ttc",
    "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf", "Roboto-Bold.ttf",
)


def _splash_font(size: int):
    """Pick a real scalable font on any OS; arial alone only exists on Windows."""
    from PIL import ImageFont

    for name in _SPLASH_FONT_NAMES:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()


def generate_mobile_app(
    project_dir: str,
    brand: str,
    industry: str,
    design: Dict[str, Any],
    app: Dict[str, Any],
    *,
    api_base: str = "",
) -> Dict[str, Any]:
    """Generate an Expo project and return its project-relative file inventory."""
    del industry
    try:
        base = _validate_api_base(api_base)
        slug = _brand_slug(brand)
    except ValueError:
        raise

    mobile_root = Path(project_dir) / "mobile"
    package_id = f"com.lumicore.{slug.replace('-', '')}"
    if not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)+", package_id):
        raise ValueError("Brand cannot form a valid Android package identifier.")
    contract = app if isinstance(app, dict) else {}
    mobile_contract = contract.get("mobile")
    platforms = (
        mobile_contract.get("platforms", ["android"])
        if isinstance(mobile_contract, dict) else ["android"]
    )
    verification = (
        str(mobile_contract.get("verification") or "apk_emulator")
        if isinstance(mobile_contract, dict) else "apk_emulator"
    )
    if not isinstance(platforms, list) or not platforms or any(
        platform not in {"android", "ios"} for platform in platforms
    ):
        return {"success": False, "files": [], "errors": ["Unsupported mobile platform."],
                "mobile": {}}
    expo_config = {
        "expo": {
            "name": brand,
            "slug": slug,
            "scheme": slug,
            "version": "1.0.0",
            "orientation": "portrait",
            "userInterfaceStyle": "dark",
            "plugins": [
                "expo-router",
                "expo-secure-store",
                "expo-status-bar",
                ["expo-splash-screen", {
                    "image": "./assets/splash.png",
                    "imageWidth": 200,
                    "resizeMode": "contain",
                    "backgroundColor": design.get("slate", {}).get("950", "#0f172a"),
                }],
            ],
            "experiments": {"typedRoutes": True},
            "icon": "./assets/icon.png",
            "android": {
                "package": package_id,
                "adaptiveIcon": {
                    "foregroundImage": "./assets/adaptive-icon.png",
                    "backgroundColor": design.get("slate", {}).get("950", "#0f172a"),
                },
            },
            "ios": {"supportsTablet": True, "bundleIdentifier": package_id},
        }
    }
    package = {
        "name": slug,
        "version": "1.0.0",
        "private": True,
        "main": "expo-router/entry",
        "scripts": {
            "start": "expo start",
            "android": "expo start --android",
            "ios": "expo start --ios",
            "web": "expo start --web",
            "typecheck": "tsc --noEmit",
        },
        "dependencies": MOBILE_DEPENDENCIES,
        "devDependencies": MOBILE_DEV_DEPENDENCIES,
    }
    files: Dict[str, Any] = {
        "mobile/app.json": json.dumps(expo_config, indent=2) + "\n",
        "mobile/package.json": json.dumps(package, indent=2) + "\n",
        "mobile/src/theme.ts": _theme_source(design),
        # `expo prebuild` regenerates the native projects and `expo export`
        # writes bundles inside this folder; `maestro test` records its results
        # under .maestro/. Committing any of it ships a customer's download full
        # of toolchain output.
        "mobile/.gitignore": (
            "node_modules/\n"
            ".expo/\n"
            "dist/\n"
            "web-build/\n"
            "/android/\n"
            "/ios/\n"
            ".maestro/test-results/\n"
            ".env*\n"
            "*.jks\n"
            "*.keystore\n"
            "*.p8\n"
            "*.p12\n"
            "*.mobileprovision\n"
            ".DS_Store\n"
            "npm-debug.*\n"
        ),
    }
    substitutions = {
        "{{BRAND}}": json.dumps(brand),
        "{{PACKAGE}}": json.dumps(package_id),
    }
    for relative, content in _PROJECT_FILES.items():
        if isinstance(content, dict):
            rendered = json.dumps(content, indent=2) + "\n"
        else:
            rendered = content
            for token, value in substitutions.items():
                rendered = rendered.replace(token, value)
        files[f"mobile/{relative}"] = rendered
    client_source = _PROJECT_FILES["src/api/client.ts"]
    if base:
        # A supplied origin is the bundled default for release builds too; the
        # emulator loopback is only the fallback when no origin was supplied.
        client_source = client_source.replace(
            "const DEFAULT_API_BASE = __DEV__ ? 'http://10.0.2.2:5000/api/v1' : '';",
            f"const DEFAULT_API_BASE = {json.dumps(base)};",
        )
    files["mobile/src/api/client.ts"] = client_source
    release_base = (
        f"The release API base is bundled as {base}."
        if base else
        "No release API base was supplied; set EXPO_PUBLIC_API_URL at build time."
    )
    readme = f"""# {brand} mobile app

Expo + TypeScript client for the generated records API.

## Start locally

1. Install Node.js 20 or newer and run `npm install` in `mobile/`.
2. Start the API and database from the project root using its README instructions.
3. Run `npx expo start` and open the project on an Android emulator or device.
4. For Android emulator access to the host machine, use `http://10.0.2.2:5000/api/v1`.

`EXPO_PUBLIC_API_URL` overrides the API origin. The debug build defaults to
`http://10.0.2.2:5000/api/v1`. {release_base} Do not put API keys, passwords, or
other secrets in Expo public variables.

## Commands

- `npm run start` — start Expo.
- `npm run android` — launch the Android development target.
- `npm run ios` — launch the iOS development target (requires macOS tooling).
- `npm run typecheck` — run TypeScript checks.
- `npx expo export --platform all` — produce Android, iOS and web bundles.

## Maestro flows

Run the smoke flow after a build is installed:

```bash
maestro test .maestro/smoke.yaml
```

The records journey registers a real account, so pass per-run credentials as
environment variables instead of editing the flow:

```bash
maestro test -e EMAIL=you@example.test -e PASSWORD='per-run-secret' .maestro/records.yaml
```

The account created by that flow remains in the database; note or remove it after
the run.

Sign-in tokens are held in platform secure storage. Offline create/update actions
are queued locally (up to 50) and only leave the queue after server confirmation.
"""
    files["mobile/README.md"] = readme

    written: List[str] = []
    try:
        for relative, content in files.items():
            target = Path(project_dir) / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            written.append(relative.replace("\\", "/"))
        _render_assets(mobile_root / "assets", brand, design)
        written.extend([
            "mobile/assets/icon.png",
            "mobile/assets/adaptive-icon.png",
            "mobile/assets/splash.png",
        ])
    except Exception as exc:
        return {
            "success": False,
            "files": written,
            "errors": [f"Mobile generation failed: {type(exc).__name__}"],
            "mobile": {"platforms": platforms, "verification": verification,
                       "package": package_id},
        }
    return {
        "success": True,
        "files": written,
        "errors": [],
        "mobile": {
            "platforms": platforms,
            "verification": verification,
            "package": package_id,
            "api_base": base or "http://10.0.2.2:5000/api/v1",
        },
    }
