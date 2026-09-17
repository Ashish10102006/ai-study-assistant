import React, { createContext, useContext, useState, useEffect } from 'react';
import { supabase, isSupabaseConfigured } from '../services/supabase';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [oauthError, setOauthError] = useState(null);

  useEffect(() => {
    // 1. Check for OAuth errors in URL hash or query parameters (e.g. user cancelled)
    if (typeof window !== 'undefined') {
      try {
        const hash = window.location.hash ? window.location.hash.substring(1) : '';
        const search = window.location.search ? window.location.search.substring(1) : '';
        const combined = hash || search;
        if (combined) {
          const params = new URLSearchParams(combined);
          const errCode = params.get('error_code') || params.get('error');
          const errDesc = params.get('error_description');

          if (errCode || errDesc) {
            let friendlyMsg = 'Google authentication was not completed.';
            if (errCode === 'access_denied' || (errDesc && errDesc.toLowerCase().includes('access_denied'))) {
              friendlyMsg = 'Google sign-in was cancelled or access was denied. Please try again.';
            } else if (errDesc) {
              friendlyMsg = decodeURIComponent(errDesc.replace(/\+/g, ' '));
            }
            setOauthError(friendlyMsg);

            // Clean up error params from browser URL bar cleanly
            if (window.history && window.history.replaceState) {
              window.history.replaceState(null, '', window.location.pathname);
            }
          }
        }
      } catch (e) {
        console.warn('URL parameter parsing notice:', e);
      }
    }

    // 2. Handle unconfigured / offline development fallback
    if (!isSupabaseConfigured || !supabase) {
      const cached = localStorage.getItem('demo_student_user');
      if (cached) {
        try {
          setUser(JSON.parse(cached));
        } catch (e) {
          localStorage.removeItem('demo_student_user');
        }
      }
      setLoading(false);
      return;
    }

    // 3. Check active session on mount
    supabase.auth.getSession().then(({ data: { session }, error }) => {
      if (error) {
        console.warn('Supabase getSession notice:', error.message);
      }
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    }).catch((err) => {
      console.error('Session retrieval error:', err);
      setLoading(false);
    });

    // 4. Centralized listener for auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, currentSession) => {
      setSession(currentSession);
      setUser(currentSession?.user ?? null);
      setLoading(false);

      if (event === 'SIGNED_IN') {
        setOauthError(null);
        localStorage.removeItem('demo_student_user');
      } else if (event === 'SIGNED_OUT') {
        localStorage.removeItem('demo_student_user');
        setUser(null);
        setSession(null);
      } else if (event === 'TOKEN_REFRESHED') {
        // Updated session applied above
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  // Continue with Google OAuth
  const signInWithGoogle = async () => {
    setOauthError(null);

    if (!isSupabaseConfigured || !supabase) {
      const err = new Error('Supabase authentication is not configured. Please set VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY in your frontend environment.');
      setOauthError(err.message);
      return { data: null, error: err };
    }

    try {
      const isBrowser = typeof window !== 'undefined';
      const isLocalHost = isBrowser && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

      // Use actual deployed Vercel domain for production, or current window origin locally
      const redirectUrl = isLocalHost
        ? `${window.location.origin}/dashboard`
        : 'https://ai-study-assistant-five-tau.vercel.app/dashboard';

      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: redirectUrl,
          queryParams: {
            access_type: 'offline',
            prompt: 'select_account'
          }
        }
      });

      if (error) {
        setOauthError(error.message || 'Google authentication could not be initiated.');
        return { data: null, error };
      }

      return { data, error: null };
    } catch (err) {
      const msg = err.message || 'Google authentication failed';
      setOauthError(msg);
      return { data: null, error: err };
    }
  };

  const signIn = async (email, password) => {
    setOauthError(null);
    if (!isSupabaseConfigured || !supabase) {
      const demoUser = {
        id: 'student_' + Math.random().toString(36).substring(2, 9),
        email,
        user_metadata: { full_name: email.split('@')[0] }
      };
      localStorage.setItem('demo_student_user', JSON.stringify(demoUser));
      setUser(demoUser);
      return { data: { user: demoUser }, error: null };
    }
    return await supabase.auth.signInWithPassword({ email, password });
  };

  const signUp = async (email, password, fullName) => {
    setOauthError(null);
    if (!isSupabaseConfigured || !supabase) {
      const demoUser = {
        id: 'student_' + Math.random().toString(36).substring(2, 9),
        email,
        user_metadata: { full_name: fullName || email.split('@')[0] }
      };
      localStorage.setItem('demo_student_user', JSON.stringify(demoUser));
      setUser(demoUser);
      return { data: { user: demoUser }, error: null };
    }
    return await supabase.auth.signUp({
      email,
      password,
      options: {
        data: { full_name: fullName }
      }
    });
  };

  const signOut = async () => {
    setOauthError(null);
    if (!isSupabaseConfigured || !supabase) {
      localStorage.removeItem('demo_student_user');
      setUser(null);
      return { error: null };
    }
    return await supabase.auth.signOut();
  };

  const clearOAuthError = () => setOauthError(null);

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        loading,
        oauthError,
        clearOAuthError,
        signInWithGoogle,
        signIn,
        signUp,
        signOut
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
