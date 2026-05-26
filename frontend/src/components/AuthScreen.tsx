'use client';

import { useState } from 'react';

interface Props {
  onAuthenticated: (email: string) => void;
}

type Mode = 'login' | 'register';

export default function AuthScreen({ onAuthenticated }: Props) {
  const [mode, setMode] = useState<Mode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const trimmedEmail = email.trim();
    if (!trimmedEmail) return setError('Email is required');
    if (!password) return setError('Password is required');
    if (password.length < 6) return setError('Password must be at least 6 characters');

    setSubmitting(true);
    try {
      const path = mode === 'login' ? '/proxy/v1/auth/login' : '/proxy/v1/auth/register';
      const body =
        mode === 'login'
          ? { email: trimmedEmail, password }
          : { email: trimmedEmail, password, full_name: fullName.trim() || undefined };

      const res = await fetch(path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        if (res.status === 401) throw new Error('Wrong email or password.');
        if (res.status === 400) throw new Error('Email already registered.');
        throw new Error(`Request failed (${res.status}).`);
      }
      onAuthenticated(trimmedEmail);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex h-screen items-center justify-center bg-[#212121]">
      <div className="w-full max-w-sm rounded-2xl border border-[#3f3f3f] bg-[#2a2a2a] p-8 shadow-2xl">
        <div className="mb-6 flex flex-col items-center gap-3">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/15">
            <AirIcon />
          </div>
          <h1 className="text-xl font-semibold text-[#ececec]">
            {mode === 'login' ? 'Welcome back' : 'Create an account'}
          </h1>
          <p className="text-center text-sm text-[#8e8ea0]">
            AQI Agent — Hanoi air quality assistant
          </p>
        </div>

        <div className="mb-5 flex rounded-xl bg-[#171717] p-1">
          <button
            type="button"
            onClick={() => setMode('login')}
            className={`flex-1 rounded-lg py-2 text-sm font-medium transition ${
              mode === 'login' ? 'bg-[#2f2f2f] text-[#ececec]' : 'text-[#8e8ea0] hover:text-[#ececec]'
            }`}
          >
            Sign in
          </button>
          <button
            type="button"
            onClick={() => setMode('register')}
            className={`flex-1 rounded-lg py-2 text-sm font-medium transition ${
              mode === 'register' ? 'bg-[#2f2f2f] text-[#ececec]' : 'text-[#8e8ea0] hover:text-[#ececec]'
            }`}
          >
            Sign up
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === 'register' && (
            <div>
              <label className="mb-1.5 block text-sm font-medium text-[#c5c5c5]">Full name</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="optional"
                className="w-full rounded-xl border border-[#3f3f3f] bg-[#171717] px-4 py-2.5 text-sm text-[#ececec] placeholder:text-[#5a5a5a] transition focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              />
            </div>
          )}

          <div>
            <label className="mb-1.5 block text-sm font-medium text-[#c5c5c5]">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              autoFocus
              className="w-full rounded-xl border border-[#3f3f3f] bg-[#171717] px-4 py-2.5 text-sm text-[#ececec] placeholder:text-[#5a5a5a] transition focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-[#c5c5c5]">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="at least 6 characters"
              className="w-full rounded-xl border border-[#3f3f3f] bg-[#171717] px-4 py-2.5 text-sm text-[#ececec] placeholder:text-[#5a5a5a] transition focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
          </div>

          {error && <p className="text-xs text-red-400">{error}</p>}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-xl bg-emerald-600 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-500 active:bg-emerald-700 disabled:opacity-60"
          >
            {submitting ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}
          </button>
        </form>
      </div>
    </div>
  );
}

function AirIcon() {
  return (
    <svg width="30" height="30" viewBox="0 0 24 24" fill="none">
      <path
        d="M9.59 4.59A2 2 0 1111 8H2m10.59 11.41A2 2 0 1014 16H2m15.73-8.27A2.5 2.5 0 1119.5 12H2"
        stroke="#34d399"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
