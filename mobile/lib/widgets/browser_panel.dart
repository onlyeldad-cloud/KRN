import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:livekit_client/livekit_client.dart' as sdk;

/// Browser approvals are answered by the person using the app, never by the LLM.
class BrowserPanel extends StatefulWidget {
  final sdk.Room room;
  const BrowserPanel({super.key, required this.room});

  @override
  State<BrowserPanel> createState() => _BrowserPanelState();
}

class _BrowserPanelState extends State<BrowserPanel> {
  Completer<String>? _pending;
  String _action = '';
  String _url = '';
  Uint8List? _preview;

  @override
  void initState() {
    super.initState();
    widget.room.registerRpcMethod('krn.browser.confirm', (data) async {
      if (!mounted || _pending != null ||
          widget.room.remoteParticipants[data.callerIdentity]?.kind != sdk.ParticipantKind.AGENT) {
        return 'denied';
      }
      final payload = jsonDecode(data.payload) as Map<String, dynamic>;
      final pending = Completer<String>();
      setState(() {
        _pending = pending;
        _action = payload['action'].toString();
        _url = payload['url'].toString();
      });
      try {
        return await pending.future.timeout(const Duration(seconds: 25), onTimeout: () => 'denied');
      } finally {
        if (mounted) setState(() => _pending = null);
      }
    });
    widget.room.registerTextStreamHandler('krn.browser.preview', (reader, identity) async {
      if (widget.room.remoteParticipants[identity]?.kind != sdk.ParticipantKind.AGENT) return;
      final value = await reader.readAll();
      const prefix = 'data:image/jpeg;base64,';
      if (mounted && value.startsWith(prefix) && value.length < 4000000) {
        try {
          final bytes = base64Decode(value.substring(prefix.length));
          setState(() => _preview = bytes);
        } on FormatException {
          // Ignore invalid image data.
        }
      }
    });
  }

  void _decide(String value) {
    final pending = _pending;
    if (pending != null && !pending.isCompleted) pending.complete(value);
  }

  @override
  void dispose() {
    _decide('denied');
    widget.room.unregisterRpcMethod('krn.browser.confirm');
    widget.room.unregisterTextStreamHandler('krn.browser.preview');
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_pending != null) {
      return Positioned.fill(
        child: ColoredBox(
          color: Colors.black54,
          child: Center(
            child: AlertDialog(
              title: const Text('Browseraktion freigeben?'),
              content: SingleChildScrollView(child: Text('$_action\n\n$_url')),
              actions: [
                TextButton(onPressed: () => _decide('denied'), child: const Text('Abbrechen')),
                FilledButton(onPressed: () => _decide('approved'), child: const Text('Einmal erlauben')),
              ],
            ),
          ),
        ),
      );
    }
    if (_preview != null) {
      return Positioned(
        left: 16, right: 16, top: 70,
        child: Card(
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            TextButton(onPressed: () => setState(() => _preview = null), child: const Text('Browser-Vorschau schließen')),
            ConstrainedBox(constraints: const BoxConstraints(maxHeight: 260), child: Image.memory(_preview!, fit: BoxFit.contain)),
          ]),
        ),
      );
    }
    return const SizedBox.shrink();
  }
}
