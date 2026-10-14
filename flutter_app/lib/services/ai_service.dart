// ai_service.dart
// ==============
// Service for communicating with the FastAPI backend Gemini AI Assistant endpoints.
// The Gemini API key remains strictly on the backend.

import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;

import '../core/api_config.dart';
import '../models/ai_models.dart';

class AiServiceException implements Exception {
  final String message;
  final int? statusCode;

  const AiServiceException(this.message, {this.statusCode});

  @override
  String toString() => message;
}

class AiService {
  final http.Client _client;

  AiService({http.Client? client}) : _client = client ?? http.Client();

  /// Sends a query to the Gemini Assistant along with current resume and ATS context.
  Future<AiChatResponse> sendMessage({
    required String message,
    required Map<String, dynamic> resumeContext,
    required String jobDescription,
    required Map<String, dynamic> analysisContext,
    required List<ChatMessage> conversationHistory,
  }) async {
    final cleanMessage = message.trim();
    if (cleanMessage.isEmpty) {
      throw const AiServiceException('Message cannot be empty.');
    }

    try {
      final uri = Uri.parse('${ApiConfig.baseUrl}/api/ai/chat');

      // Keep recent conversation history (last 6 messages)
      final recentHistory = conversationHistory
          .where((m) => !m.isSystem)
          .toList();
      final historyPayload = (recentHistory.length > 6
              ? recentHistory.sublist(recentHistory.length - 6)
              : recentHistory)
          .map((m) => m.toJson())
          .toList();

      final body = jsonEncode({
        'message': cleanMessage,
        'resume_context': resumeContext,
        'job_description': jobDescription,
        'analysis_context': analysisContext,
        'conversation_history': historyPayload,
      });

      final response = await _client.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: body,
      ).timeout(
        const Duration(seconds: 40),
        onTimeout: () {
          throw TimeoutException('AI Assistant took too long to respond.');
        },
      );

      if (response.statusCode == 200) {
        final dynamic decoded = jsonDecode(utf8.decode(response.bodyBytes));
        if (decoded is Map<String, dynamic>) {
          return AiChatResponse.fromJson(decoded);
        }
        throw const AiServiceException('Unexpected response format from AI service.');
      }

      String errorMsg = 'Failed to communicate with AI Assistant (${response.statusCode})';
      try {
        final dynamic errJson = jsonDecode(utf8.decode(response.bodyBytes));
        if (errJson is Map && errJson.containsKey('detail')) {
          errorMsg = errJson['detail'].toString();
        }
      } catch (_) {}

      throw AiServiceException(errorMsg, statusCode: response.statusCode);
    } on TimeoutException {
      return const AiChatResponse(
        success: false,
        message: 'The AI Assistant request timed out. Please try asking again.',
        error: 'Timeout',
      );
    } on AiServiceException {
      rethrow;
    } catch (e) {
      return AiChatResponse(
        success: false,
        message: 'Unable to reach the AI Assistant. Please ensure the backend is running.',
        error: e.toString(),
      );
    }
  }

  /// Sends user-approved resume modifications to the backend for validation
  /// and deterministic re-scoring by the ATS Engine.
  Future<AiApplyChangesResponse> applyApprovedChanges({
    required Map<String, dynamic> originalResume,
    required List<ProposedChange> approvedChanges,
    required String jobDescription,
  }) async {
    try {
      final uri = Uri.parse('${ApiConfig.baseUrl}/api/ai/apply-changes');

      final body = jsonEncode({
        'original_resume': originalResume,
        'approved_changes': approvedChanges.map((c) => c.toJson()).toList(),
        'job_description': jobDescription,
      });

      final response = await _client.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: body,
      ).timeout(
        const Duration(seconds: 30),
        onTimeout: () {
          throw TimeoutException('Request to update resume timed out.');
        },
      );

      if (response.statusCode == 200) {
        final dynamic decoded = jsonDecode(utf8.decode(response.bodyBytes));
        if (decoded is Map<String, dynamic>) {
          return AiApplyChangesResponse.fromJson(decoded);
        }
        throw const AiServiceException('Unexpected response format from resume update.');
      }

      String errorMsg = 'Failed to apply changes (${response.statusCode})';
      try {
        final dynamic errJson = jsonDecode(utf8.decode(response.bodyBytes));
        if (errJson is Map && errJson.containsKey('detail')) {
          errorMsg = errJson['detail'].toString();
        }
      } catch (_) {}

      throw AiServiceException(errorMsg, statusCode: response.statusCode);
    } on AiServiceException {
      rethrow;
    } catch (e) {
      throw AiServiceException('Failed to apply resume updates: $e');
    }
  }

  /// Checks if AI Assistant is configured on backend.
  Future<bool> isAiAvailable() async {
    try {
      final response = await _client
          .get(Uri.parse('${ApiConfig.baseUrl}/api/ai/status'))
          .timeout(const Duration(seconds: 4));
      if (response.statusCode == 200) {
        final dynamic decoded = jsonDecode(response.body);
        return decoded is Map && decoded['available'] == true;
      }
      return false;
    } catch (_) {
      return false;
    }
  }
}
