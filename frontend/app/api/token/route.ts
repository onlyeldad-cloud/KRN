import { NextResponse } from 'next/server';
import { AccessToken } from 'livekit-server-sdk';
import { randomUUID, timingSafeEqual } from 'node:crypto';
import { RoomConfiguration } from '@livekit/protocol';

export const runtime = 'nodejs';
export const revalidate = 0;

export async function POST(req: Request) {
  if (process.env.NODE_ENV !== 'development') {
    return NextResponse.json(
      { error: 'Für Produktion ist eine Benutzeranmeldung erforderlich.' },
      { status: 403 }
    );
  }
  const origin = req.headers.get('origin');
  const sameOrigin = origin === new URL(req.url).origin;
  const supplied = req.headers.get('authorization')?.replace(/^Bearer /, '') ?? '';
  const expected = process.env.KRN_MOBILE_DEV_TOKEN ?? '';
  const mobileAllowed =
    expected.length >= 32 &&
    Buffer.byteLength(supplied) === Buffer.byteLength(expected) &&
    timingSafeEqual(Buffer.from(supplied), Buffer.from(expected));
  if (!sameOrigin && !mobileAllowed) {
    return NextResponse.json({ error: 'Zugriff nicht erlaubt.' }, { status: 403 });
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
  token.roomConfig = RoomConfiguration.fromJson({ agents: [{ agentName: 'my-agent' }] });
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
