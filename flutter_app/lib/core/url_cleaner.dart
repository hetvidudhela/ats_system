import 'url_cleaner_stub.dart'
    if (dart.library.html) 'url_cleaner_web.dart';

/// Cross-platform URL cleaner: on Flutter Web, strips session_id from the browser address bar.
void cleanSessionUrl() {
  cleanSessionUrlImpl();
}
