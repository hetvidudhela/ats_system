import 'dart:io';
import 'dart:typed_data';

/// Safe native file reader fallback for IO platforms (Windows, macOS, Linux, Android, iOS).
Future<Uint8List?> readNativeFileBytes(String path) async {
  try {
    final file = File(path);
    if (await file.exists()) {
      return await file.readAsBytes();
    }
  } catch (_) {}
  return null;
}
