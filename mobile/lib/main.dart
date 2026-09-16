import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'app.dart';

// Load environment variables before starting the app
// Contains only the KRN token endpoint and personal development access token.
// Provider credentials remain on the Python/Next.js servers.
void main() async {
  await dotenv.load(fileName: 'assets/.env', isOptional: true);
  runApp(const VoiceAssistantApp());
}
