import { createClient } from '@supabase/supabase-js';
import { authConfig } from './authConfig.js';

export const supabase = authConfig.configured
  ? createClient(authConfig.url, authConfig.anonKey, {
      auth: {
        autoRefreshToken: true,
        detectSessionInUrl: true,
        flowType: 'pkce',
        persistSession: true,
      },
    })
  : null;
