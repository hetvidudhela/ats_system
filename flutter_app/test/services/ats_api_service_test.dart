import 'dart:convert';
import 'dart:typed_data';
import 'package:file_picker/file_picker.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:flutter_app/services/ats_api_service.dart';

void main() {
  final sampleBytes = Uint8List.fromList([1, 2, 3]);

  group('AtsApiService Unit Tests', () {
    const validJd = 'Software Engineer. Requirements: Python, FastAPI, Docker, SQL. 2+ years experience.';

    test('validates empty job description', () async {
      final service = AtsApiService();
      final file = PlatformFile(name: 'resume.pdf', size: 100, bytes: sampleBytes);


      expect(
        () => service.analyzeResume(resumeFile: file, jobDescription: ''),
        throwsA(isA<AtsApiException>().having(
          (e) => e.message,
          'message',
          contains('cannot be empty'),
        )),
      );
    });

    test('validates too short job description', () async {
      final service = AtsApiService();
      final file = PlatformFile(name: 'resume.pdf', size: 100, bytes: sampleBytes);

      expect(
        () => service.analyzeResume(resumeFile: file, jobDescription: 'Short JD'),
        throwsA(isA<AtsApiException>().having(
          (e) => e.message,
          'message',
          contains('too short'),
        )),
      );
    });

    test('validates unsupported file format', () async {
      final service = AtsApiService();
      final file = PlatformFile(name: 'resume.txt', size: 100, bytes: sampleBytes);

      expect(
        () => service.analyzeResume(resumeFile: file, jobDescription: validJd),
        throwsA(isA<AtsApiException>().having(
          (e) => e.message,
          'message',
          contains('Unsupported file format'),
        )),
      );
    });

    test('successful 200 response parses into AtsAnalysisResult', () async {
      final mockClient = MockClient((request) async {
        expect(request.method, 'POST');
        expect(request.url.path, contains('/analyze/'));

        // Verify that the request is sent as multipart/form-data
        expect(request.headers['content-type'], contains('multipart/form-data'));

        // Verify that the multipart body contains the resume file field and job_description field
        final bodyString = request.body;
        expect(bodyString, contains('name="job_description"'));
        expect(bodyString, contains(validJd));
        expect(bodyString, contains('name="resume"'));
        expect(bodyString, contains('filename="resume.pdf"'));
        expect(bodyString, contains('application/pdf'));

        final responseBody = jsonEncode({
          "success": true,
          "score": 85,
          "ats_score": 85,
          "matched_skills": ["Python", "FastAPI"],
          "missing_skills": ["Docker"],
          "suggestions": ["Add Docker to skills"],
        });

        return http.Response(responseBody, 200, headers: {
          'content-type': 'application/json; charset=utf-8',
        });
      });

      final service = AtsApiService(client: mockClient);
      final file = PlatformFile(name: 'resume.pdf', size: 100, bytes: sampleBytes);

      final result = await service.analyzeResume(
        resumeFile: file,
        jobDescription: validJd,
      );

      expect(result.success, isTrue);
      expect(result.score, 85);
      expect(result.matchedSkills, ['Python', 'FastAPI']);
      expect(result.missingSkills, ['Docker']);
    });

    test('supports reading bytes from readStream when bytes is null', () async {
      final mockClient = MockClient((request) async {
        expect(request.headers['content-type'], contains('multipart/form-data'));
        expect(request.body, contains('name="resume"'));

        final responseBody = jsonEncode({
          "success": true,
          "score": 90,
          "ats_score": 90,
          "matched_skills": ["Python"],
          "missing_skills": [],
          "suggestions": [],
        });

        return http.Response(responseBody, 200, headers: {
          'content-type': 'application/json; charset=utf-8',
        });
      });

      final service = AtsApiService(client: mockClient);
      final file = PlatformFile(
        name: 'resume.pdf',
        size: 3,
        bytes: null,
        readStream: Stream.value([1, 2, 3]),
      );

      final result = await service.analyzeResume(
        resumeFile: file,
        jobDescription: validJd,
      );

      expect(result.success, isTrue);
      expect(result.score, 90);
    });

    test('validates when file bytes cannot be resolved', () async {
      final service = AtsApiService();
      final file = PlatformFile(
        name: 'resume.pdf',
        size: 0,
        bytes: null,
        readStream: null,
        path: null,
      );

      expect(
        () => service.analyzeResume(resumeFile: file, jobDescription: validJd),
        throwsA(isA<AtsApiException>().having(
          (e) => e.message,
          'message',
          contains('Unable to read resume file bytes'),
        )),
      );
    });

    test('handles 400 Bad Request error response from backend', () async {
      final mockClient = MockClient((request) async {
        return http.Response(
          jsonEncode({"detail": "Job description is required and cannot be empty."}),
          400,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      });

      final service = AtsApiService(client: mockClient);
      final file = PlatformFile(name: 'resume.pdf', size: 100, bytes: sampleBytes);

      expect(
        () => service.analyzeResume(resumeFile: file, jobDescription: validJd),
        throwsA(isA<AtsApiException>().having(
          (e) => e.message,
          'message',
          contains('Job description is required'),
        )),
      );
    });

    test('handles 500 Server Error response', () async {
      final mockClient = MockClient((request) async {
        return http.Response('Internal Server Error', 500);
      });

      final service = AtsApiService(client: mockClient);
      final file = PlatformFile(name: 'resume.docx', size: 100, bytes: sampleBytes);

      expect(
        () => service.analyzeResume(resumeFile: file, jobDescription: validJd),
        throwsA(isA<AtsApiException>().having(
          (e) => e.statusCode,
          'statusCode',
          500,
        )),
      );
    });

    test('health check returns true on 200', () async {
      final mockClient = MockClient((request) async {
        return http.Response('{"status": "healthy"}', 200);
      });

      final service = AtsApiService(client: mockClient);
      final healthy = await service.checkHealth();
      expect(healthy, isTrue);
    });

    test('health check returns false on server error', () async {
      final mockClient = MockClient((request) async {
        return http.Response('Error', 500);
      });

      final service = AtsApiService(client: mockClient);
      final healthy = await service.checkHealth();
      expect(healthy, isFalse);
    });
  });
}
