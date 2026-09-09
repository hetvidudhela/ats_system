import 'package:flutter/foundation.dart'
    show defaultTargetPlatform, kIsWeb, TargetPlatform;

/// Centralized API configuration supporting multi-platform backend resolution.
class ApiConfig {
  /// Default backend port.
  static const int defaultPort = 8000;

  /// Optional override for testing or custom environments.
  static String? _customBaseUrl;

  static void setCustomBaseUrl(String? url) {
    _customBaseUrl = url;
  }

  /// Automatically resolves the correct backend base URL based on runtime platform:
  /// - Android Emulator: http://10.0.2.2:8000
  /// - Web / Windows / macOS / Linux / iOS: http://localhost:8000
  static String get baseUrl {
    if (_customBaseUrl != null && _customBaseUrl!.isNotEmpty) {
      return _customBaseUrl!;
    }

    if (kIsWeb) {
      return 'http://localhost:$defaultPort';
    }

    if (defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:$defaultPort';
    }

    return 'http://localhost:$defaultPort';
  }

  /// Primary ATS analysis endpoint.
  static String get analyzeEndpoint => '$baseUrl/analyze/';

  /// Health check endpoint.
  static String get healthEndpoint => '$baseUrl/health/';

  /// Version check endpoint.
  static String get versionEndpoint => '$baseUrl/version/';
}
