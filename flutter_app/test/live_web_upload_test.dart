import 'dart:convert';
import 'dart:typed_data';
import 'package:file_picker/file_picker.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_app/core/api_config.dart';
import 'package:flutter_app/services/ats_api_service.dart';

void main() {
  test('Live Web Upload in Chrome to FastAPI backend', () async {
    ApiConfig.setCustomBaseUrl('http://127.0.0.1:8000');
    final service = AtsApiService();

    // 1. Verify backend health
    final isHealthy = await service.checkHealth();
    expect(isHealthy, isTrue, reason: 'FastAPI health check failed from Chrome');

    // 2. Load exact sample_resume.pdf bytes
    const pdfBase64 = 'JVBERi0xLjcKJcK1wrYKCjEgMCBvYmoKPDwvVHlwZS9DYXRhbG9nL1BhZ2VzIDIgMCBSPj4KZW5kb2JqCgoyIDAgb2JqCjw8L1R5cGUvUGFnZXMvQ291bnQgMS9LaWRzWzQgMCBSXT4+CmVuZG9iagoKMyAwIG9iago8PC9Gb250PDwvaGVsdiA1IDAgUj4+Pj4KZW5kb2JqCgo0IDAgb2JqCjw8L1R5cGUvUGFnZS9NZWRpYUJveFswIDAgNTk1IDg0Ml0vUm90YXRlIDAvUmVzb3VyY2VzIDMgMCBSL1BhcmVudCAyIDAgUi9Db250ZW50c1s2IDAgUl0+PgplbmRvYmoKCjUgMCBvYmoKPDwvVHlwZS9Gb250L1N1YnR5cGUvVHlwZTEvQmFzZUZvbnQvSGVsdmV0aWNhL0VuY29kaW5nL1dpbkFuc2lFbmNvZGluZz4+CmVuZG9iagoKNiAwIG9iago8PC9MZW5ndGggNjg4L0ZpbHRlci9GbGF0ZURlY29kZT4+CnN0cmVhbQp42oVUu47UQBDM/RWOkYB59MMjnQgQJGRIzk4Ed36IAAISvp/qHts7PltCq7vdmenprq6q6e5P93nsYh/wiT2HXofUj7+7jz+XX3/7GPtx7Z+f6EVWGWRJgQi/+NOP8VsX+veRP8RI/file36SPWYRj6EgrINEmTXIJIz9jP05BZ1SSK85pjmzffAdc8oZ34S1ZK0xuFVkkVdhZCyeuWZYfbXuFWu97Y5KUZJBWVITf4p09OM79PX4xRk3ZnyiJi3NfsBO1oyKK+5H5EYltryipGrxtkOMU3W8jL4T0GxIUsi2Kti33BkYcTc5O2r/k9iZYUUe7yxIAm/ZOwdmrFFVBatJVtyZbV9tP27n2U/YfxuijG6tOoNMUnaMy33fqFJwe9Lcdq2O3XpOYJXEWSCKHKj4jjHpCNHrZIxwpMlPvG/fS8TYB6bmnmsKRINHgAvLK2oIa447lGAXXaCe8e9KNGeVq2FjJ+38mpGuzJI7QgMQUNXpHHdyBB1622kxBUxB66/1CLwb7A+unlPYVnTfx1Xzkxb/cVWTyXqeHZur7O5ejQGP51bNHVHFB22TnVcPNRnPHqtegouQb0jzhlqMYXslO6tvNTZ/K/t7AfKLcw7Hnhy2vEGRveqyYViOmvCOvtTdzW9B86a9vdy8q3znq1OV6Pqvfou2Osb+YppXvt1JhiY4I2V/dZcO25dw9FdfAdU5FEyt3bm4f/8STRebVPXNNvpR87rZPIlqyFlViGDq7IyESLzoOh/wN2M9WXWoSO66WKeHHrmkyfWYLmqrdJ1Gj8l2nQu3zE8NLy1brSLFuWe/d2hy5649kzs419nm+jk6tddfDp0eSF9YuU5Hdt95j4hsZsq9LmDfXr3FyDn+pFFE/uzzpY12ZCf9TOXNDXueQ7+vY/e9+wfk1L2jCmVuZHN0cmVhbQplbmRvYmoKCnhyZWYKMCA3CjAwMDAwMDAwMDAgNjU1MzUgZiAKMDAwMDAwMDAxNiAwMDAwMCBuIAowMDAwMDAwMDYyIDAwMDAwIG4gCjAwMDAwMDAxMTQgMDAwMDAgbiAKMDAwMDAwMDE1NSAwMDAwMCBuIAowMDAwMDAwMjYyIDAwMDAwIG4gCjAwMDAwMDAzNTEgMDAwMDAgbiAKCnRyYWlsZXIKPDwvU2l6ZSA3L1Jvb3QgMSAwIFIvSURbPEMyQjE3RUMyQkE0QUMzOEMwOEMyOTFDMjgwQzNBRUMyPjxBNzlFNTgyRTJEMkYzMUFGNEVDQjVBOUUyRUNGMDIwMD5dPj4Kc3RhcnR4cmVmCjExMDgKJSVFT0YK';
    final bytes = base64Decode(pdfBase64);
    final platformFile = PlatformFile(
      name: 'sample_resume.pdf',
      size: bytes.length,
      bytes: Uint8List.fromList(bytes),
    );

    const jd = 'Senior Full Stack Engineer\n'
        'Requirements:\n'
        '- Python\n'
        '- FastAPI\n'
        '- Docker\n'
        '- PostgreSQL\n'
        '- REST API\n'
        '- React\n'
        '- 2+ years experience\n'
        '- Bachelor degree in Computer Science';

    // 3. Live analysis request from Chrome
    final result = await service.analyzeResume(
      resumeFile: platformFile,
      jobDescription: jd,
    );

    // ignore: avoid_print
    print('REAL_ATS_SCORE: ${result.score}');
    // ignore: avoid_print
    print('REAL_MATCHED_SKILLS: ${result.matchedSkills.join(", ")}');
    // ignore: avoid_print
    print('REAL_MISSING_SKILLS: ${result.missingSkills.join(", ")}');
    // ignore: avoid_print
    print('REAL_RATING: ${result.matchRatingText}');

    // 4. Assert response attributes
    expect(result.success, isTrue);
    expect(result.score, greaterThan(60));
    expect(result.score, lessThanOrEqualTo(100));
    expect(result.matchedSkills, contains('Python'));
    expect(result.matchedSkills, contains('Docker'));
    expect(result.matchedSkills, contains('PostgreSQL'));
    expect(result.missingSkills, contains('React'));
    expect(result.scoreBreakdown, isNotNull);
    expect(result.experienceAnalysis, isNotNull);
    expect(result.educationAnalysis, isNotNull);
    expect(result.suggestions, isNotEmpty);
    expect(result.parsedResume, isNotNull);
    expect(result.parsedResume!.name, 'John Doe');
  });
}
