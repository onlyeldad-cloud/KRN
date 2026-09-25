'use client';

import { useEffect, useState } from 'react';
import { ParticipantKind } from 'livekit-client';
import { useRoomContext } from '@livekit/components-react';

export function BrowserPanel() {
  const room = useRoomContext();
  const [preview, setPreview] = useState('');
  const [request, setRequest] = useState<{
    action: string;
    url: string;
    decide: (value: string) => void;
  } | null>(null);
  useEffect(() => {
    let pending: ((value: string) => void) | undefined;
    room.localParticipant.registerRpcMethod(
      'krn.browser.confirm',
      async (data) => {
        if (
          room.remoteParticipants.get(data.callerIdentity)?.kind !==
          ParticipantKind.AGENT
        )
          return 'denied';
        if (pending) return 'denied';
        const payload = JSON.parse(data.payload);
        return new Promise<string>((resolve) => {
          const timer = setTimeout(() => finish('denied'), 25000);
          const finish = (value: string) => {
            clearTimeout(timer);
            pending = undefined;
            setRequest(null);
            resolve(value);
          };
          pending = finish;
          setRequest({
            action: String(payload.action),
            url: String(payload.url),
            decide: finish,
          });
        });
      }
    );
    room.registerTextStreamHandler(
      'krn.browser.preview',
      async (reader, participant) => {
        if (
          room.remoteParticipants.get(participant.identity)?.kind !==
          ParticipantKind.AGENT
        )
          return;
        const image = await reader.readAll();
        if (
          image.startsWith('data:image/jpeg;base64,') &&
          image.length < 4000000
        )
          setPreview(image);
      }
    );
    return () => {
      pending?.('denied');
      room.localParticipant.unregisterRpcMethod('krn.browser.confirm');
      room.unregisterTextStreamHandler('krn.browser.preview');
    };
  }, [room]);
  return (
    <>
      {preview && (
        <aside className="fixed top-20 right-4 z-40 max-w-sm rounded-2xl border border-[#D4A017]/40 bg-[#0B1F4D] p-3 shadow-xl">
          <button
            className="mb-2 text-sm text-white"
            onClick={() => setPreview('')}
          >
            Browser-Vorschau schließen ×
          </button>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={preview}
            alt="Aktuelle KRN-Browseransicht"
            className="rounded-xl"
          />
        </aside>
      )}
      {request && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Browseraktion bestätigen"
          className="fixed inset-0 z-[100] grid place-items-center bg-black/70 p-6"
        >
          <div className="w-full max-w-lg rounded-3xl border border-[#D4A017]/40 bg-[#0B1F4D] p-6 text-white">
            <h2 className="text-xl font-semibold">Browseraktion freigeben?</h2>
            <p className="my-4 break-words">{request.action}</p>
            <p className="mb-6 text-xs break-all text-slate-400">
              {request.url}
            </p>
            <div className="flex gap-3">
              <button
                autoFocus
                className="rounded-xl border px-5 py-3"
                onClick={() => request.decide('denied')}
              >
                Abbrechen
              </button>
              <button
                className="rounded-xl bg-[#D4A017] px-5 py-3 text-[#0B1F4D]"
                onClick={() => request.decide('approved')}
              >
                Einmal erlauben
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
