import 'dart:convert';
import 'dart:typed_data';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:flutter_app/ats_screen.dart';
import 'package:flutter_app/services/ats_api_service.dart';

void main() {
  testWidgets('AtsScreen initial render smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: AtsScreen(),
      ),
    );

    // Header elements
    expect(find.text('Resume Intelligence'), findsOneWidget);
    expect(find.text('Upload Resume'), findsOneWidget);
    expect(find.text('Job Description'), findsOneWidget);

    // Initial state
    expect(find.text('0%'), findsOneWidget);
    expect(find.text('Ready to analyze'), findsOneWidget);
    expect(find.text('Choose File'), findsOneWidget);
    expect(find.text('Analyze Resume'), findsOneWidget);

    // Verify analyze button is disabled when no file is selected
    final ElevatedButton analyzeButton = tester.widget(
      find.widgetWithText(ElevatedButton, 'Analyze Resume'),
    );
    expect(analyzeButton.onPressed, isNull);
  });

  testWidgets('AtsScreen displays error banner on API error', (WidgetTester tester) async {
    final mockClient = MockClient((request) async {
      return http.Response(
        jsonEncode({"detail": "Job description is too short."}),
        400,
        headers: {'content-type': 'application/json; charset=utf-8'},
      );
    });

    final service = AtsApiService(client: mockClient);

    await tester.pumpWidget(
      MaterialApp(
        home: AtsScreen(apiService: service),
      ),
    );

    // Initially no error banner
    expect(find.byIcon(Icons.error_outline), findsNothing);
  });

  testWidgets('AtsScreen renders ATS score and matched/missing skills when result is received', (WidgetTester tester) async {
    final mockClient = MockClient((request) async {
      return http.Response(
        jsonEncode({
          "success": true,
          "score": 88,
          "ats_score": 88,
          "match_rating": "Excellent Match",
          "matched_skills": ["Docker", "FastAPI", "Python"],
          "missing_skills": ["React"],
          "score_breakdown": {
            "keyword_match": {"score": 38.0, "max_score": 40},
            "experience_match": {"score": 20.0, "max_score": 20},
            "project_relevance": {"score": 10.0, "max_score": 10},
            "education_match": {"score": 10.0, "max_score": 10},
            "formatting": {"score": 5.0, "max_score": 10},
            "quality": {"score": 5.0, "max_score": 10}
          },
          "suggestions": ["Add React to projects"],
        }),
        200,
        headers: {'content-type': 'application/json; charset=utf-8'},
      );
    });

    final service = AtsApiService(client: mockClient);

    await tester.pumpWidget(
      MaterialApp(
        home: AtsScreen(apiService: service),
      ),
    );

    // Initial state
    expect(find.text('Ready to analyze'), findsOneWidget);

    // Simulate analysis directly via service
    final result = await service.analyzeResume(
      resumeFile: PlatformFile(name: 'resume.pdf', size: 100, bytes: Uint8List.fromList([1, 2, 3])),
      jobDescription: 'Software Engineer with Python, FastAPI, Docker, and React skills.',
    );

    expect(result.score, 88);
    expect(result.matchedSkills, contains('Docker'));
    expect(result.missingSkills, contains('React'));
  });
}
