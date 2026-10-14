import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_app/models/ats_result.dart';

void main() {
  group('AtsAnalysisResult JSON Deserialization', () {
    test('parses complete realistic backend response successfully', () {
      final json = {
        "success": true,
        "score": 78,
        "ats_score": 78,
        "matched_skills": ["Docker", "PostgreSQL", "Python", "REST API"],
        "missing_skills": ["React"],
        "matched_keywords": ["REST API"],
        "missing_keywords": <String>[],
        "required_matched": ["Docker", "PostgreSQL", "Python", "REST API"],
        "required_missing": ["React"],
        "preferred_matched": <String>[],
        "preferred_missing": <String>[],
        "score_breakdown": {
          "keyword_match": {"score": 33.0, "max_score": 40.0},
          "experience_match": {"score": 12.0, "max_score": 20.0},
          "education_match": {"score": 10.0, "max_score": 10.0},
          "project_relevance": {"score": 9.0, "max_score": 15.0},
          "formatting": {"score": 10.0, "max_score": 10.0},
          "quality": {"score": 4.0, "max_score": 5.0}
        },
        "experience_analysis": {
          "status": "partially_meets",
          "required_years": 3.0,
          "estimated_years": 2.0,
          "details": "Candidate has 2.0 years of experience."
        },
        "education_analysis": {
          "status": "meets",
          "required_level": "Bachelor's Degree",
          "detected_education": "Bachelor's Degree",
          "details": "Education meets requirements."
        },
        "project_relevance": {
          "score": 9.0,
          "max_score": 15.0,
          "matched_technologies": ["Docker", "PostgreSQL", "REST API"],
          "details": "Projects demonstrate 3 technologies."
        },
        "match_details": [
          {
            "skill": "Docker",
            "status": "matched",
            "match_type": "canonical",
            "is_required": true,
            "evidence": "Skills: Docker"
          },
          {
            "skill": "React",
            "status": "missing",
            "match_type": "none",
            "is_required": true,
            "evidence": "Not found"
          }
        ],
        "suggestions": [
          "Highlight React prominently.",
          "Quantify project achievements."
        ],
        "parsed_resume": {
          "name": "John Doe",
          "email": "john@example.com",
          "phone": "+1-555-123-4567",
          "skills": ["Python", "Docker", "PostgreSQL"]
        }
      };

      final result = AtsAnalysisResult.fromJson(json);

      expect(result.success, isTrue);
      expect(result.score, 78);
      expect(result.atsScore, 78);
      expect(result.matchRatingText, 'Strong Match');

      expect(result.matchedSkills, ['Docker', 'PostgreSQL', 'Python', 'REST API']);
      expect(result.missingSkills, ['React']);

      // Breakdown
      expect(result.scoreBreakdown, isNotNull);
      expect(result.scoreBreakdown!.keywordMatch.score, 33.0);
      expect(result.scoreBreakdown!.keywordMatch.maxScore, 40.0);
      expect(result.scoreBreakdown!.experienceMatch.score, 12.0);

      // Experience & Education
      expect(result.experienceAnalysis, isNotNull);
      expect(result.experienceAnalysis!.isPartiallyMet, isTrue);
      expect(result.experienceAnalysis!.requiredYears, 3.0);

      expect(result.educationAnalysis, isNotNull);
      expect(result.educationAnalysis!.isMet, isTrue);

      // Project Relevance
      expect(result.projectRelevance, isNotNull);
      expect(result.projectRelevance!.matchedTechnologies, ['Docker', 'PostgreSQL', 'REST API']);

      // Match Details
      expect(result.matchDetails.length, 2);
      expect(result.matchDetails[0].isMatched, isTrue);
      expect(result.matchDetails[1].isMatched, isFalse);

      // Suggestions
      expect(result.suggestions.length, 2);

      // Parsed Resume
      expect(result.parsedResume, isNotNull);
      expect(result.parsedResume!.name, 'John Doe');
      expect(result.parsedResume!.email, 'john@example.com');
    });

    test('handles missing or null optional fields gracefully without throwing', () {
      final json = <String, dynamic>{
        "score": 62,
      };

      final result = AtsAnalysisResult.fromJson(json);

      expect(result.success, isTrue);
      expect(result.score, 62);
      expect(result.atsScore, 62);
      expect(result.matchRatingText, 'Good Match');
      expect(result.matchedSkills, isEmpty);
      expect(result.missingSkills, isEmpty);
      expect(result.suggestions, isEmpty);
      expect(result.scoreBreakdown, isNotNull);
      expect(result.experienceAnalysis, isNotNull);
      expect(result.educationAnalysis, isNotNull);
    });

    test('clamps score within 0 to 100', () {
      final overJson = {"score": 150};
      final underJson = {"score": -20};

      expect(AtsAnalysisResult.fromJson(overJson).score, 100);
      expect(AtsAnalysisResult.fromJson(underJson).score, 0);
    });

    test('matchRatingText evaluates ranges correctly', () {
      expect(AtsAnalysisResult.fromJson({"score": 95}).matchRatingText, 'Excellent Match');
      expect(AtsAnalysisResult.fromJson({"score": 75}).matchRatingText, 'Strong Match');
      expect(AtsAnalysisResult.fromJson({"score": 58}).matchRatingText, 'Good Match');
      expect(AtsAnalysisResult.fromJson({"score": 42}).matchRatingText, 'Moderate Match');
      expect(AtsAnalysisResult.fromJson({"score": 25}).matchRatingText, 'Low Match');
    });

    test('parses eligibility assessment correctly from JSON', () {
      final json = {
        "score": 35,
        "eligibility": {
          "eligible": false,
          "warning": true,
          "status": "potentially_ineligible",
          "reasons": [
            "Overall ATS score is 35%, which is below the 40% threshold.",
            "Only 1 of 8 required skills matched."
          ]
        }
      };

      final result = AtsAnalysisResult.fromJson(json);

      expect(result.eligibility, isNotNull);
      expect(result.eligibility!.eligible, isFalse);
      expect(result.eligibility!.warning, isTrue);
      expect(result.eligibility!.status, 'potentially_ineligible');
      expect(result.eligibility!.isPotentiallyIneligible, isTrue);
      expect(result.eligibility!.isRequirementsNotVerified, isFalse);
      expect(result.eligibility!.reasons.length, 2);
      expect(result.eligibility!.reasons[0], contains('below the 40% threshold'));

      // Test toJson roundtrip
      final serialized = result.toJson();
      expect(serialized['eligibility'], isNotNull);
      expect(serialized['eligibility']['warning'], isTrue);
      expect(serialized['eligibility']['reasons'].length, 2);
    });

    test('handles unverified eligibility requirements', () {
      final json = {
        "score": 65,
        "eligibility": {
          "eligible": null,
          "warning": true,
          "status": "requirements_not_verified",
          "reasons": [
            "Required Bachelor's Degree could not be verified from the resume."
          ]
        }
      };

      final result = AtsAnalysisResult.fromJson(json);

      expect(result.eligibility, isNotNull);
      expect(result.eligibility!.eligible, isNull);
      expect(result.eligibility!.warning, isTrue);
      expect(result.eligibility!.isRequirementsNotVerified, isTrue);
      expect(result.eligibility!.isPotentiallyIneligible, isFalse);
      expect(result.eligibility!.reasons.single, contains('could not be verified'));
    });
  });
}
