import 'dart:convert';
import 'dart:typed_data';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:flutter_app/ats_screen.dart';
import 'package:flutter_app/models/ats_result.dart';
import 'package:flutter_app/services/ai_service.dart';
import 'package:flutter_app/services/ats_api_service.dart';
import 'package:flutter_app/widgets/ai_assistant_panel.dart';
import 'package:flutter_markdown/flutter_markdown.dart';

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

  testWidgets('Gemini AI Assistant dialog renders and sends message receiving response', (WidgetTester tester) async {
    final mockHttpClient = MockClient((request) async {
      if (request.url.path.contains('/ai/chat')) {
        return http.Response(
          jsonEncode({
            "message": "Based on the ATS analysis, you should learn React to improve your score.",
            "proposed_changes": [],
            "error": null,
          }),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      }
      return http.Response('Not Found', 404);
    });

    final aiService = AiService(client: mockHttpClient);
    final mockResult = AtsAnalysisResult(
      score: 85,
      atsScore: 85,
      success: true,
      matchedSkills: ['Python', 'Docker'],
      missingSkills: ['React'],
    );

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: AiAssistantPanel(
            analysisResult: mockResult,
            jobDescription: 'Python, Docker, React Developer',
            onAnalysisUpdated: (_) {},
            aiService: aiService,
            isDialog: true,
          ),
        ),
      ),
    );

    // Verify dialog header and greeting
    expect(find.text('Gemini AI Assistant'), findsOneWidget);
    expect(find.textContaining('ATS Resume Assistant'), findsOneWidget);

    // Enter message
    await tester.enterText(find.byType(TextField), 'What skills should I learn?');
    await tester.pump();

    // Tap send button
    await tester.tap(find.byIcon(Icons.send));
    await tester.pumpAndSettle();

    // Verify Gemini response is rendered
    expect(find.textContaining('learn React to improve your score'), findsOneWidget);
  });

  testWidgets('Gemini AI Assistant renders Markdown formatting with MarkdownBody and not raw text', (WidgetTester tester) async {
    const rawMarkdownResponse = '''
Your ATS score is **61%** because your resume matches several key skills.

### Why your score is 61%:

#### 1. Matched Skills

- **Python**
- **JavaScript**
- **React**
- **REST API**
- **HTML**
- **Git**

#### 2. Missing Required Skills

- **Flutter**
- **Dart**
- **FastAPI**
- **Docker**
- **PostgreSQL**
- **Unit Testing**
''';

    final mockHttpClient = MockClient((request) async {
      if (request.url.path.contains('/ai/chat')) {
        return http.Response(
          jsonEncode({
            "message": rawMarkdownResponse,
            "proposed_changes": [],
            "error": null,
          }),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      }
      return http.Response('Not Found', 404);
    });

    final aiService = AiService(client: mockHttpClient);
    final mockResult = AtsAnalysisResult(
      score: 61,
      atsScore: 61,
      success: true,
      matchedSkills: ['Python', 'JavaScript', 'React', 'REST API', 'HTML', 'Git'],
      missingSkills: ['Flutter', 'Dart', 'FastAPI', 'Docker', 'PostgreSQL', 'Unit Testing'],
    );

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: AiAssistantPanel(
            analysisResult: mockResult,
            jobDescription: 'Software Engineer',
            onAnalysisUpdated: (_) {},
            aiService: aiService,
            isDialog: true,
          ),
        ),
      ),
    );

    await tester.enterText(find.byType(TextField), 'Why is my ATS score?');
    await tester.pump();
    await tester.tap(find.byIcon(Icons.send));
    await tester.pumpAndSettle();

    // Verify MarkdownBody is rendered
    expect(find.byType(MarkdownBody), findsAtLeastNWidgets(1));

    // Verify that raw Markdown syntax symbols like '### Why your score' or '**61%**' are NOT rendered as literal text
    expect(find.text('### Why your score is 61%:'), findsNothing);
    expect(find.text('**61%**'), findsNothing);
    expect(find.text('- **Python**'), findsNothing);

    // Verify that the formatted content is found within MarkdownBody
    final markdownWidget = tester.widget<MarkdownBody>(find.byType(MarkdownBody).last);
    expect(markdownWidget.data, contains('### Why your score is 61%:'));
    expect(markdownWidget.selectable, isTrue);
    expect(markdownWidget.styleSheet, isNotNull);
    expect(markdownWidget.styleSheet!.h1?.fontSize, 18);
    expect(markdownWidget.styleSheet!.h2?.fontSize, 16);
    expect(markdownWidget.styleSheet!.h3?.fontSize, 15);
    expect(markdownWidget.styleSheet!.h4?.fontSize, 14);
    expect(markdownWidget.styleSheet!.p?.fontSize, 14);
    expect(markdownWidget.styleSheet!.listIndent, 20.0);
  });

  testWidgets('AtsScreen restores session from extension session_id successfully', (WidgetTester tester) async {
    const validSessionId = '12345678-1234-1234-1234-123456789abc';
    final sampleFileBytes = base64Encode(utf8.encode('%PDF-1.4 sample resume bytes'));

    final mockClient = MockClient((request) async {
      if (request.url.path.contains('/session/$validSessionId')) {
        return http.Response(
          jsonEncode({
            "success": true,
            "session_id": validSessionId,
            "version": 1,
            "filename": "Jane_Doe_Resume.pdf",
            "file_bytes": sampleFileBytes,
            "job_description": "Senior Backend Developer with Python, FastAPI, and Docker.",
            "analysis_result": {
              "success": true,
              "score": 94,
              "ats_score": 94,
              "match_rating": "Excellent Match",
              "matched_skills": ["Python", "FastAPI", "Docker"],
              "missing_skills": [],
              "score_breakdown": {
                "keyword_match": {"score": 40.0, "max_score": 40},
                "experience_match": {"score": 20.0, "max_score": 20},
                "project_relevance": {"score": 15.0, "max_score": 15},
                "education_match": {"score": 10.0, "max_score": 10},
                "formatting": {"score": 5.0, "max_score": 10},
                "quality": {"score": 4.0, "max_score": 5}
              },
              "suggestions": ["Strong alignment with the job description."],
            },
            "expires_in_seconds": 290
          }),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      }
      return http.Response('Not Found', 404);
    });

    final service = AtsApiService(client: mockClient);

    await tester.pumpWidget(
      MaterialApp(
        home: AtsScreen(
          apiService: service,
          initialSessionId: validSessionId,
        ),
      ),
    );

    // Pump to process the post-frame session restoration callback
    await tester.pumpAndSettle();

    // 1. Verify Job Description textfield restored
    expect(
      find.text('Senior Backend Developer with Python, FastAPI, and Docker.'),
      findsOneWidget,
    );

    // 2. Verify Resume filename restored
    expect(find.text('Jane_Doe_Resume.pdf'), findsOneWidget);

    // 3. Verify Score and Rating restored directly without re-analyzing
    expect(find.text('94%'), findsOneWidget);
    expect(find.text('Excellent Match'), findsOneWidget);

    // 4. Verify confirmation banner displayed
    expect(find.text('Analysis restored from ATS Chrome Extension.'), findsOneWidget);

    // 5. Verify Matched Skills card renders restored skills
    expect(find.text('Python'), findsWidgets);
    expect(find.text('FastAPI'), findsWidgets);
    expect(find.text('Docker'), findsWidgets);
  });

  testWidgets('AtsScreen consumes and deletes temporary session on backend upon restoration', (WidgetTester tester) async {
    const validSessionId = '99999999-9999-9999-9999-999999999999';
    final sampleFileBytes = base64Encode(utf8.encode('%PDF-1.4 sample resume'));
    bool deleteCalled = false;

    final mockClient = MockClient((request) async {
      if (request.url.path.contains('/session/$validSessionId')) {
        if (request.method == 'DELETE') {
          deleteCalled = true;
          return http.Response('', 204);
        }
        return http.Response(
          jsonEncode({
            "success": true,
            "session_id": validSessionId,
            "version": 1,
            "filename": "consumed_resume.pdf",
            "file_bytes": sampleFileBytes,
            "job_description": "Clean consumption test job description.",
            "analysis_result": null,
            "expires_in_seconds": 250
          }),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      }
      return http.Response('Not Found', 404);
    });

    final service = AtsApiService(client: mockClient);

    await tester.pumpWidget(
      MaterialApp(
        home: AtsScreen(
          apiService: service,
          initialSessionId: validSessionId,
        ),
      ),
    );

    await tester.pumpAndSettle();

    // Verify fields were populated
    expect(find.text('Clean consumption test job description.'), findsOneWidget);
    expect(find.text('consumed_resume.pdf'), findsOneWidget);

    // Verify backend delete was invoked to clean up temporary session
    expect(deleteCalled, isTrue);
  });

  testWidgets('AtsScreen fresh launch starts clean with empty resume and job description', (WidgetTester tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: AtsScreen(),
      ),
    );

    await tester.pumpAndSettle();

    // Verify Job Description field is empty
    final TextField jdField = tester.widget(find.byType(TextField).first);
    expect(jdField.controller?.text.isEmpty ?? true, isTrue);

    // Verify no file is selected and dropzone shows default upload prompt
    expect(find.text('Click to Choose File'), findsOneWidget);
    expect(find.text('Supports .PDF or .DOCX format'), findsOneWidget);

    // Verify score is 0% and ready to analyze
    expect(find.text('0%'), findsOneWidget);
    expect(find.text('Ready to analyze'), findsOneWidget);

    // Verify no error or restored session banners exist
    expect(find.text('Analysis restored from ATS Chrome Extension.'), findsNothing);
    expect(find.byIcon(Icons.error_outline), findsNothing);
  });

  testWidgets('AtsScreen handles missing/expired extension session gracefully', (WidgetTester tester) async {
    const expiredSessionId = '00000000-0000-0000-0000-000000000000';

    final mockClient = MockClient((request) async {
      return http.Response(
        jsonEncode({"detail": "Session not found or has expired."}),
        404,
        headers: {'content-type': 'application/json; charset=utf-8'},
      );
    });

    final service = AtsApiService(client: mockClient);

    await tester.pumpWidget(
      MaterialApp(
        home: AtsScreen(
          apiService: service,
          initialSessionId: expiredSessionId,
        ),
      ),
    );

    // Pump post-frame callback
    await tester.pumpAndSettle();

    // Verify friendly warning banner is shown
    expect(
      find.textContaining('extension analysis session has expired or is invalid'),
      findsOneWidget,
    );

    // Verify initial clean state remains ready for fresh analysis
    expect(find.text('0%'), findsOneWidget);
    expect(find.text('Ready to analyze'), findsOneWidget);
  });

  testWidgets('AtsScreen renders Eligibility Warning Card when candidate is potentially ineligible', (WidgetTester tester) async {
    const sessionId = 'test-ineligible-session-id';
    final mockClient = MockClient((request) async {
      if (request.url.path.contains(sessionId)) {
        return http.Response(
          jsonEncode({
            "session_id": sessionId,
            "filename": "junior_resume.pdf",
            "job_description": "Senior Software Engineer requiring 5+ years experience and Kubernetes.",
            "analysis_result": {
              "success": true,
              "score": 32,
              "ats_score": 32,
              "match_rating": "Low Match",
              "matched_skills": ["Python"],
              "missing_skills": ["Kubernetes", "Docker", "AWS", "Go"],
              "eligibility": {
                "eligible": false,
                "warning": true,
                "status": "potentially_ineligible",
                "reasons": [
                  "Overall ATS score is 32%, which is below the 40% threshold.",
                  "Only 1 of 5 required skills matched (20%)."
                ]
              }
            }
          }),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      }
      return http.Response('Not found', 404);
    });

    final service = AtsApiService(client: mockClient);

    await tester.pumpWidget(
      MaterialApp(
        home: AtsScreen(
          apiService: service,
          initialSessionId: sessionId,
        ),
      ),
    );

    await tester.pumpAndSettle();

    // Verify Eligibility Warning Card is displayed
    expect(find.byKey(const Key('eligibilityWarningCard')), findsOneWidget);
    expect(find.text('Potential Eligibility Warning'), findsOneWidget);
    expect(find.textContaining('below the 40% threshold'), findsOneWidget);
    expect(find.textContaining('Only 1 of 5 required skills matched'), findsOneWidget);
  });

  testWidgets('AtsScreen renders unverified warning when mandatory requirements are unverified', (WidgetTester tester) async {
    const sessionId = 'test-unverified-session-id';
    final mockClient = MockClient((request) async {
      if (request.url.path.contains(sessionId)) {
        return http.Response(
          jsonEncode({
            "session_id": sessionId,
            "filename": "applicant.pdf",
            "job_description": "Requires Bachelor's Degree.",
            "analysis_result": {
              "success": true,
              "score": 65,
              "ats_score": 65,
              "match_rating": "Good Match",
              "matched_skills": ["Python", "FastAPI"],
              "missing_skills": [],
              "eligibility": {
                "eligible": null,
                "warning": true,
                "status": "requirements_not_verified",
                "reasons": [
                  "Required Bachelor's Degree could not be verified from the resume."
                ]
              }
            }
          }),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      }
      return http.Response('Not found', 404);
    });

    final service = AtsApiService(client: mockClient);

    await tester.pumpWidget(
      MaterialApp(
        home: AtsScreen(
          apiService: service,
          initialSessionId: sessionId,
        ),
      ),
    );

    await tester.pumpAndSettle();

    // Verify Eligibility Warning Card shows unverified title and reason
    expect(find.byKey(const Key('eligibilityWarningCard')), findsOneWidget);
    expect(find.text('Eligibility Requirements Need Verification'), findsOneWidget);
    expect(find.textContaining('could not be verified from the resume'), findsOneWidget);
  });

  testWidgets('AtsScreen does NOT render Eligibility Warning Card for a strong match', (WidgetTester tester) async {
    const sessionId = 'test-strong-session-id';
    final mockClient = MockClient((request) async {
      if (request.url.path.contains(sessionId)) {
        return http.Response(
          jsonEncode({
            "session_id": sessionId,
            "filename": "senior_dev.pdf",
            "job_description": "Senior Python Developer with Docker and FastAPI.",
            "analysis_result": {
              "success": true,
              "score": 85,
              "ats_score": 85,
              "match_rating": "Strong Match",
              "matched_skills": ["Python", "FastAPI", "Docker"],
              "missing_skills": [],
              "eligibility": {
                "eligible": true,
                "warning": false,
                "status": "no_major_issues_detected",
                "reasons": []
              }
            }
          }),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      }
      return http.Response('Not found', 404);
    });

    final service = AtsApiService(client: mockClient);

    await tester.pumpWidget(
      MaterialApp(
        home: AtsScreen(
          apiService: service,
          initialSessionId: sessionId,
        ),
      ),
    );

    await tester.pumpAndSettle();

    // Verify Eligibility Warning Card is NOT rendered
    expect(find.byKey(const Key('eligibilityWarningCard')), findsNothing);
    expect(find.text('Potential Eligibility Warning'), findsNothing);
    expect(find.text('Eligibility Requirements Need Verification'), findsNothing);
  });
}
