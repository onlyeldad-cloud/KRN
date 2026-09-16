'use client';

import { TokenSource } from 'livekit-client';
import { DEMO_PASSWORD_STORAGE_KEY } from '@/lib/demo-auth';

export function getKrnTokenSource() {
  return TokenSource.custom(async () => {
    const password =
      typeof window === 'undefined'
        ? ''
        : (sessionStorage.getItem(DEMO_PASSWORD_STORAGE_KEY) ?? '');
    const res = await fetch('/api/token', {
      method: 'POST',
      headers: password ? { Authorization: `Bearer ${password}` } : {},
    });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(
        typeof body.error === 'string'
          ? body.error
          : 'Verbindung zum Agenten fehlgeschlagen.'
      );
    }
    return body;
  });
}
