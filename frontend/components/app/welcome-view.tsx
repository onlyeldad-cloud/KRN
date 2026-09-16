'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { DEMO_PASSWORD_STORAGE_KEY } from '@/lib/demo-auth';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  const [password, setPassword] = useState('');
  const requiresPassword =
    process.env.NEXT_PUBLIC_KRN_REQUIRES_PASSWORD === 'true';

  const handleStart = () => {
    const trimmed = password.trim();
    if (trimmed) {
      sessionStorage.setItem(DEMO_PASSWORD_STORAGE_KEY, trimmed);
    } else {
      sessionStorage.removeItem(DEMO_PASSWORD_STORAGE_KEY);
    }
    onStartCall();
  };

  return (
    <div ref={ref}>
      <section className="flex flex-col items-center justify-center text-center">
        <div className="mb-6 rounded-2xl bg-white px-8 py-5 shadow-[0_8px_30px_rgba(11,31,77,0.08)]">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/krn-logo.png" alt="KRN" className="h-20 w-auto md:h-24" />
        </div>
        <span className="mb-4 rounded-full border border-[#0B1F4D]/15 bg-white px-4 py-2 text-xs tracking-widest text-[#0B1F4D] uppercase">
          KRN Agent · Persönliche Assistenz
        </span>
        <h1 className="max-w-3xl text-5xl font-semibold tracking-tight text-[#0B1F4D] md:text-7xl">
          Ein Gespräch.
          <br />
          <span className="text-[#D4A017]">Viele Möglichkeiten.</span>
        </h1>

        <p className="text-foreground max-w-prose pt-1 leading-6 font-medium">
          Sprich auf Deutsch mit KRN. Stelle Fragen, teile deine Kamera oder
          lass dir im Alltag helfen.
        </p>

        <label className="mt-6 flex w-64 flex-col gap-2 text-left text-xs font-medium tracking-wide text-[#0B1F4D]">
          Demo-Passwort
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            onKeyDown={(event) => {
              if (
                event.key === 'Enter' &&
                (!requiresPassword || password.trim())
              ) {
                handleStart();
              }
            }}
            placeholder={
              requiresPassword ? 'Von KRN erhalten' : 'Nur für die Online-Demo'
            }
            className="h-11 rounded-full border border-[#0B1F4D]/20 bg-white px-4 text-sm font-normal outline-none focus:border-[#D4A017]"
          />
        </label>

        <Button
          size="lg"
          onClick={handleStart}
          disabled={requiresPassword && !password.trim()}
          className="mt-4 w-64 rounded-full bg-[#D4A017] font-mono text-xs font-bold tracking-wider text-[#0B1F4D] uppercase hover:bg-[#c09112]"
        >
          {startButtonText}
        </Button>
        <div className="mt-10 grid max-w-xl grid-cols-2 gap-3 text-sm md:grid-cols-4">
          {[
            'Sprache & Chat',
            'Kamera & Bildschirm',
            'Suche & Wetter',
            'Browser-Assistent',
          ].map((feature) => (
            <div
              key={feature}
              className="rounded-2xl border border-[#0B1F4D]/12 bg-white px-4 py-3 text-[#0B1F4D] shadow-sm"
            >
              {feature}
            </div>
          ))}
        </div>
        <p className="mt-6 max-w-md text-xs opacity-60">
          Du entscheidest, wann Mikrofon und Kamera aktiv sind. Zum Beenden
          einfach auflegen.
        </p>
      </section>
    </div>
  );
};
