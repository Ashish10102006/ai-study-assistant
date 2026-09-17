import React, { createContext, useContext, useState, useEffect } from 'react';
import { supabase, isSupabaseConfigured } from '../services/supabase';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isSupabaseConfigured || !supabase) {
      // Offline / guest fallback session
      const cached = localStorage.getItem('demo_student_user');
      if (cached) {
        setUser(JSON.parse(cached));
      }
      setLoading(false);
      return;
    }

    // Check active session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    });

    // Listen for auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  const signIn = async (email, password) => {
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
    if (!isSupabaseConfigured || !supabase) {
      localStorage.removeItem('demo_student_user');
      setUser(null);
      return { error: null };
    }
    return await supabase.auth.signOut();
  };

  return (
    <AuthContext.Provider value={{ user, session, loading, signIn, signUp, signOut }}>
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
