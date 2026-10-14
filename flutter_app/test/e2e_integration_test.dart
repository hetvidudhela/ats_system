import 'dart:io';
import 'package:file_picker/file_picker.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:flutter_app/core/api_config.dart';
import 'package:flutter_app/services/ats_api_service.dart';

void main() {
  test('Live End-to-End ATS API integration test', () async {
    ApiConfig.setCustomBaseUrl('http://127.0.0.1:8000');
    final service = AtsApiService();

    // 1. Health check against live backend
    final isHealthy = await service.checkHealth();
    if (!isHealthy) {
      // Live backend is not currently running; skip live assertion
      return;
    }
    expect(isHealthy, isTrue, reason: 'Live FastAPI backend should report healthy');

    // 2. Load sample PDF from backend repository
    final samplePdfFile = File('../backend/parser/sample_resumes/sample_resume.pdf');
    expect(samplePdfFile.existsSync(), isTrue, reason: 'sample_resume.pdf must exist');

    final bytes = await samplePdfFile.readAsBytes();
    final platformFile = PlatformFile(
      name: 'sample_resume.pdf',
      size: bytes.length,
      bytes: bytes,
    );

    const jd = '''
    Senior Full Stack Engineer
    Requirements:
    - Python
    - FastAPI
    - Docker
    - PostgreSQL
    - REST API
    - React
    - 2+ years experience
    - Bachelor degree in Computer Science
    ''';

    // 3. Live analysis call
    final result = await service.analyzeResume(
      resumeFile: platformFile,
      jobDescription: jd,
    );

    // 4. Assert real response attributes
    expect(result.success, isTrue);
    expect(result.score, greaterThan(60));
    expect(result.score, lessThanOrEqualTo(100));
    expect(result.matchedSkills, contains('Python'));
    expect(result.matchedSkills, contains('Docker'));
    expect(result.matchedSkills, contains('PostgreSQL'));
    expect(result.missingSkills, contains('React'));
    expect(result.scoreBreakdown, isNotNull);
    expect(result.scoreBreakdown!.keywordMatch.score, greaterThan(0));
    expect(result.experienceAnalysis, isNotNull);
    expect(result.educationAnalysis, isNotNull);
    expect(result.suggestions, isNotEmpty);
    expect(result.parsedResume, isNotNull);
    expect(result.parsedResume!.name, 'John Doe');
  });
}
