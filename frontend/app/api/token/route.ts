import { NextResponse } from 'next/server';
import { AccessToken } from 'livekit-server-sdk';
import { randomUUID } from 'node:crypto';
import { RoomConfiguration } from '@livekit/protocol';
import { bearerMatchesSecret } from '@/lib/demo-auth-server';

export const runtime = 'nodejs';
export const revalidate = 0;

function isLocalDevCaller(req: Request): boolean {
  const url = new URL(req.url);
  const origin = req.headers.get('origin');
  if (origin === url.origin) {
    return true;
  }
  if (req.headers.get('sec-fetch-site') === 'same-origin') {
    return true;
  }
  const referer = req.headers.get('referer');
  if (referer) {
    try {
      return new URL(referer).origin === url.origin;
    } catch {
      return false;
    }
  }
  const host = (req.headers.get('host') ?? url.host).split(':')[0];
  return host === '127.0.0.1' || host === 'localhost';
}

function isAuthorized(req: Request): boolean {
  const supplied =
    req.headers.get('authorization')?.replace(/^Bearer /, '') ?? '';
  if (bearerMatchesSecret(supplied, process.env.KRN_DEMO_PASSWORD ?? '')) {
    return true;
  }
  if (bearerMatchesSecret(supplied, process.env.KRN_MOBILE_DEV_TOKEN ?? '')) {
    return true;
  }
  return process.env.NODE_ENV === 'development' && isLocalDevCaller(req);
}

export async function POST(req: Request) {
  if (!isAuthorized(req)) {
    return NextResponse.json(
      { error: 'Bitte das Demo-Passwort eingeben.' },
      { status: 401 }
    );
  }
  const { LIVEKIT_API_KEY, LIVEKIT_API_SECRET, LIVEKIT_URL } = process.env;
  if (!LIVEKIT_API_KEY || !LIVEKIT_API_SECRET || !LIVEKIT_URL) {
    return NextResponse.json(
      { error: 'LiveKit-Konfiguration fehlt auf dem Server.' },
      { status: 503 }
    );
  }
  const roomName = `krn-${randomUUID()}`;
  const token = new AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET, {
    identity: `krn-user-${randomUUID()}`,
    name: 'Du',
    ttl: '10m',
  });
  token.addGrant({
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canSubscribe: true,
    canPublishData: true,
  });
  token.roomConfig = RoomConfiguration.fromJson({
    agents: [{ agentName: 'my-agent' }],
  });
  return NextResponse.json(
    {
      serverUrl: LIVEKIT_URL,
      roomName,
      participantName: 'Du',
      participantToken: await token.toJwt(),
    },
    { headers: { 'Cache-Control': 'no-store' } }
  );
}
