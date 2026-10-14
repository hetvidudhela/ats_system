// ai_models.dart
// =============
// Data models for the Gemini AI Assistant in Flutter.

import 'ats_result.dart';

class ProposedChange {
  final String type;
  final String section;
  final String value;
  final String reason;
  bool? isApproved; // null: pending, true: approved, false: rejected

  ProposedChange({
    required this.type,
    required this.section,
    required this.value,
    required this.reason,
    this.isApproved,
  });

  factory ProposedChange.fromJson(Map<String, dynamic> json) {
    return ProposedChange(
      type: json['type'] as String? ?? 'add_skill',
      section: json['section'] as String? ?? 'skills',
      value: json['value'] as String? ?? '',
      reason: json['reason'] as String? ?? '',
      isApproved: json['is_approved'] as bool?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'type': type,
      'section': section,
      'value': value,
      'reason': reason,
      if (isApproved != null) 'is_approved': isApproved,
    };
  }
}

class ChatMessage {
  final String role; // 'user', 'assistant', 'system'
  final String content;
  final DateTime timestamp;
  final List<ProposedChange> proposedChanges;

  ChatMessage({
    required this.role,
    required this.content,
    DateTime? timestamp,
    this.proposedChanges = const [],
  }) : timestamp = timestamp ?? DateTime.now();

  bool get isUser => role == 'user';
  bool get isAssistant => role == 'assistant';
  bool get isSystem => role == 'system';

  Map<String, dynamic> toJson() {
    return {
      'role': role,
      'content': content,
    };
  }
}

class AiChatResponse {
  final bool success;
  final String message;
  final List<ProposedChange> proposedChanges;
  final String? error;

  const AiChatResponse({
    required this.success,
    required this.message,
    this.proposedChanges = const [],
    this.error,
  });

  factory AiChatResponse.fromJson(Map<String, dynamic> json) {
    final rawChanges = json['proposed_changes'] as List<dynamic>? ?? const [];
    return AiChatResponse(
      success: json['success'] as bool? ?? false,
      message: json['message'] as String? ?? '',
      proposedChanges: rawChanges
          .map((item) => ProposedChange.fromJson(Map<String, dynamic>.from(item as Map)))
          .toList(),
      error: json['error'] as String?,
    );
  }
}

class AiApplyChangesResponse {
  final bool success;
  final Map<String, dynamic> updatedResume;
  final AtsAnalysisResult analysisResult;
  final String? error;

  const AiApplyChangesResponse({
    required this.success,
    required this.updatedResume,
    required this.analysisResult,
    this.error,
  });

  factory AiApplyChangesResponse.fromJson(Map<String, dynamic> json) {
    return AiApplyChangesResponse(
      success: json['success'] as bool? ?? false,
      updatedResume: Map<String, dynamic>.from(json['updated_resume'] as Map? ?? {}),
      analysisResult: AtsAnalysisResult.fromJson(
        Map<String, dynamic>.from(json['analysis_result'] as Map? ?? {}),
      ),
      error: json['error'] as String?,
    );
  }
}
