import 'dart:typed_data';

/// Fallback for web or environments where dart:io is unavailable.
Future<Uint8List?> readNativeFileBytes(String path) async {
  return null;
}
