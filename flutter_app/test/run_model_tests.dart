// ignore_for_file: avoid_print
// run_model_tests.dart
// ====================
// Pure Dart verification runner for models and business logic.

import 'package:flutter_app/models/ats_result.dart';
import 'package:flutter_app/models/ai_models.dart';


void main() {
  print('Running ATS and AI model verification tests...');

  // 1. Test AtsAnalysisResult deserialization and serialization
  final mockJson = <String, dynamic>{
    'success': true,
    'score': 82,
    'ats_score': 82,
    'matched_skills': ['Python', 'Docker'],
    'missing_skills': ['AWS'],
    'suggestions': ['Add cloud experience.'],
    'parsed_resume': {
      'name': 'Alice Smith',
      'email': 'alice@example.com',
      'skills': ['Python', 'Docker'],
      'raw_text': 'Alice Smith Python Docker',
    },
  };

  final result = AtsAnalysisResult.fromJson(mockJson);
  assert(result.success == true, 'Success should be true');
  assert(result.score == 82, 'Score should be 82');
  assert(result.matchedSkills.length == 2, 'Matched skills length should be 2');
  assert(result.missingSkills.contains('AWS'), 'Missing skills should have AWS');
  assert(result.parsedResume != null, 'Parsed resume should not be null');
  assert(result.parsedResume!.name == 'Alice Smith', 'Name should match');
  print('✓ AtsAnalysisResult deserialization verified.');

  // Test toJson()
  final serialized = result.toJson();
  assert(serialized['score'] == 82, 'Serialized score should be 82');
  print('✓ AtsAnalysisResult toJson verified.');

  // 2. Test Zero-Match Warning condition logic
  // Zero matched skills with identifiable requirements -> warning shown
  final zeroMatchResult = AtsAnalysisResult.fromJson({
    'success': true,
    'score': 15,
    'matched_skills': <String>[],
    'missing_skills': ['Docker', 'Kubernetes'],
    'match_details': [
      {'skill': 'Docker', 'status': 'missing'}
    ],
  });
  final showWarning1 = zeroMatchResult.matchedSkills.isEmpty &&
      (zeroMatchResult.matchDetails.isNotEmpty ||
          zeroMatchResult.missingSkills.isNotEmpty ||
          zeroMatchResult.requiredMissing.isNotEmpty);
  assert(showWarning1 == true, 'Zero match warning should trigger when no skills match and requirements exist');

  // At least 1 matched skill -> warning NOT shown
  final normalMatchResult = AtsAnalysisResult.fromJson({
    'success': true,
    'score': 75,
    'matched_skills': ['Docker'],
    'missing_skills': ['Kubernetes'],
  });
  final showWarning2 = normalMatchResult.matchedSkills.isEmpty &&
      (normalMatchResult.matchDetails.isNotEmpty ||
          normalMatchResult.missingSkills.isNotEmpty ||
          normalMatchResult.requiredMissing.isNotEmpty);
  assert(showWarning2 == false, 'Zero match warning must NOT trigger when at least 1 skill matches');
  print('✓ Deterministic Zero-Match Warning condition verified.');

  // 3. Test ProposedChange serialization and state
  final change = ProposedChange(
    type: 'add_skill',
    section: 'skills',
    value: 'Docker',
    reason: 'User stated Docker experience.',
  );
  assert(change.isApproved == null, 'New proposal should be pending approval');
  assert(change.type == 'add_skill');
  assert(change.value == 'Docker');

  change.isApproved = true;
  assert(change.isApproved == true, 'Proposal marked approved');
  final changeJson = change.toJson();
  assert(changeJson['value'] == 'Docker');
  assert(changeJson['is_approved'] == true);
  print('✓ ProposedChange model verified.');

  // 4. Test AiChatResponse deserialization
  final chatRespJson = {
    'success': true,
    'message': 'You indicated Docker experience. Would you like to add it?',
    'proposed_changes': [
      {
        'type': 'add_skill',
        'section': 'skills',
        'value': 'Docker',
        'reason': 'User confirmed Docker knowledge.',
      }
    ],
  };
  final chatResp = AiChatResponse.fromJson(chatRespJson);
  assert(chatResp.success == true);
  assert(chatResp.proposedChanges.length == 1);
  assert(chatResp.proposedChanges.first.value == 'Docker');
  print('✓ AiChatResponse deserialization verified.');

  // 5. Test AiApplyChangesResponse deserialization
  final applyRespJson = {
    'success': true,
    'updated_resume': {
      'skills': ['Python', 'Docker'],
      'raw_text': 'Skills: Python, Docker',
    },
    'analysis_result': {
      'success': true,
      'score': 88,
      'ats_score': 88,
      'matched_skills': ['Python', 'Docker'],
      'missing_skills': <String>[],
    },
  };
  final applyResp = AiApplyChangesResponse.fromJson(applyRespJson);
  assert(applyResp.success == true);
  assert(applyResp.analysisResult.score == 88);
  assert(applyResp.analysisResult.matchedSkills.contains('Docker'));
  print('✓ AiApplyChangesResponse deserialization verified.');

  print('ALL MODEL AND BUSINESS LOGIC TESTS PASSED SUCCESSFULLY!');
}
