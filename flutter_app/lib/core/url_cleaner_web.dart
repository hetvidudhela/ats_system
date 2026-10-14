// ignore_for_file: avoid_web_libraries_in_flutter, deprecated_member_use
import 'dart:html' as html;

/// Web implementation using window.history.replaceState to remove session_id parameter.
void cleanSessionUrlImpl() {
  try {
    final currentHref = html.window.location.href;
    final uri = Uri.parse(currentHref);
    if (uri.queryParameters.containsKey('session_id')) {
      final newParams = Map<String, String>.from(uri.queryParameters)..remove('session_id');
      final cleanUri = uri.replace(queryParameters: newParams.isEmpty ? null : newParams);
      html.window.history.replaceState(null, '', cleanUri.toString());
    } else if (uri.hasFragment && uri.fragment.contains('session_id')) {
      // Also handle fragment query parameter e.g. #/?session_id=...
      final fragment = uri.fragment;
      final qIndex = fragment.indexOf('?');
      if (qIndex != -1) {
        final pathPart = fragment.substring(0, qIndex);
        final queryPart = fragment.substring(qIndex + 1);
        final params = Uri.splitQueryString(queryPart);
        if (params.containsKey('session_id')) {
          final newParams = Map<String, String>.from(params)..remove('session_id');
          final newFragment = newParams.isEmpty ? pathPart : '$pathPart?${Uri(queryParameters: newParams).query}';
          final cleanUri = uri.replace(fragment: newFragment);
          html.window.history.replaceState(null, '', cleanUri.toString());
        }
      }
    }
  } catch (_) {}
}
