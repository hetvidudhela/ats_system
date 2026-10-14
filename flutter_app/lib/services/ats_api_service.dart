import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:file_picker/file_picker.dart';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

import '../core/api_config.dart';
import '../models/ats_result.dart';
import 'platform_file_reader/platform_file_reader.dart';

/// Exception thrown when an ATS API request fails.
class AtsApiException implements Exception {
  final String message;
  final int? statusCode;

  const AtsApiException(this.message, {this.statusCode});

  @override
  String toString() => message;
}

/// Service responsible for communicating with the ATS backend API.
class AtsApiService {
  final http.Client _client;

  AtsApiService({http.Client? client}) : _client = client ?? http.Client();

  /// Analyzes a resume file against a job description.
  Future<AtsAnalysisResult> analyzeResume({
    required PlatformFile resumeFile,
    required String jobDescription,
  }) async {
    final cleanJd = jobDescription.trim();
    if (cleanJd.isEmpty) {
      throw const AtsApiException('Job description cannot be empty.');
    }
    if (cleanJd.length < 15) {
      throw const AtsApiException(
        'Job description is too short. Please provide at least 15 characters.',
      );
    }

    final filename = resumeFile.name.toLowerCase();
    if (!filename.endsWith('.pdf') && !filename.endsWith('.docx')) {
      throw const AtsApiException(
        'Unsupported file format. Please upload a .pdf or .docx resume.',
      );
    }

    try {
      final uri = Uri.parse(ApiConfig.analyzeEndpoint);
      final request = http.MultipartRequest('POST', uri);

      // 1. Attach Job Description
      request.fields['job_description'] = cleanJd;

      // 2. Attach Resume File (Web & Native compatible: always uses MultipartFile.fromBytes)
      final mediaType = filename.endsWith('.pdf')
          ? MediaType('application', 'pdf')
          : MediaType('application', 'vnd.openxmlformats-officedocument.wordprocessingml.document');

      Uint8List? bytes = resumeFile.bytes;

      // Safe fallback 1: read from readStream if bytes not populated in memory
      if (bytes == null && resumeFile.readStream != null) {
        try {
          final chunks = await resumeFile.readStream!.toList();
          final totalLength = chunks.fold<int>(0, (sum, chunk) => sum + chunk.length);
          final result = Uint8List(totalLength);
          int offset = 0;
          for (final chunk in chunks) {
            result.setRange(offset, offset + chunk.length, chunk);
            offset += chunk.length;
          }
          bytes = result;
        } catch (_) {}
      }

      // Safe fallback 2: read from native filesystem on IO platforms without breaking Web compilation
      if (bytes == null && resumeFile.path != null && resumeFile.path!.isNotEmpty) {
        bytes = await readNativeFileBytes(resumeFile.path!);
      }

      if (bytes == null || bytes.isEmpty) {
        throw const AtsApiException(
          'Unable to read resume file bytes. Please select the file again.',
        );
      }

      request.files.add(
        http.MultipartFile.fromBytes(
          'resume',
          bytes,
          filename: resumeFile.name,
          contentType: mediaType,
        ),
      );

      // 3. Send request with timeout
      final streamedResponse = await _client.send(request).timeout(
        const Duration(seconds: 45),
        onTimeout: () {
          throw TimeoutException(
            'The ATS server took too long to respond. Please try again.',
          );
        },
      );

      final response = await http.Response.fromStream(streamedResponse);

      // 4. Handle Response
      if (response.statusCode == 200) {
        final dynamic decoded = jsonDecode(utf8.decode(response.bodyBytes));
        if (decoded is Map<String, dynamic>) {
          return AtsAnalysisResult.fromJson(decoded);
        }
        throw const AtsApiException('Unexpected response format from server.');
      }

      // Parse error details from server response
      String errorMessage = 'Server error (${response.statusCode})';
      try {
        final dynamic errorJson = jsonDecode(utf8.decode(response.bodyBytes));
        if (errorJson is Map && errorJson.containsKey('detail')) {
          final detail = errorJson['detail'];
          if (detail is String) {
            errorMessage = detail;
          } else if (detail is List) {
            errorMessage = detail.map((e) => e['msg'] ?? e.toString()).join('\n');
          }
        }
      } catch (_) {
        if (response.body.isNotEmpty) {
          errorMessage = response.body;
        }
      }

      throw AtsApiException(errorMessage, statusCode: response.statusCode);
    } on AtsApiException {
      rethrow;
    } on TimeoutException catch (e) {
      throw AtsApiException(e.message ?? 'Request timed out.');
    } on http.ClientException catch (e) {
      throw AtsApiException(
        'Unable to reach ATS server at ${ApiConfig.baseUrl}. Please check that the backend is running. (${e.message})',
      );
    } catch (e) {
      final errStr = e.toString();
      if (errStr.contains('SocketException') || errStr.contains('Connection refused')) {
        throw AtsApiException(
          'Unable to reach ATS server at ${ApiConfig.baseUrl}. Please check that the backend is running.',
        );
      }
      throw AtsApiException('Failed to analyze resume: $errStr');
    }
  }

  /// Checks backend connectivity and health.
  Future<bool> checkHealth() async {
    try {
      final response = await _client
          .get(Uri.parse(ApiConfig.healthEndpoint))
          .timeout(const Duration(seconds: 5));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  /// Retrieves a temporary session created by the Chrome Extension.
  Future<Map<String, dynamic>?> getSession(String sessionId) async {
    final cleanId = sessionId.trim();
    if (cleanId.isEmpty) return null;

    try {
      final uri = Uri.parse(ApiConfig.sessionEndpoint(cleanId));
      final response = await _client.get(uri).timeout(
        const Duration(seconds: 10),
        onTimeout: () => throw TimeoutException('Session request timed out.'),
      );

      if (response.statusCode == 200) {
        final dynamic decoded = jsonDecode(utf8.decode(response.bodyBytes));
        if (decoded is Map<String, dynamic>) {
          return decoded;
        }
      }
      return null;
    } catch (_) {
      return null;
    }
  }

  /// Explicitly deletes a consumed temporary session from the backend.
  Future<bool> deleteSession(String sessionId) async {
    final cleanId = sessionId.trim();
    if (cleanId.isEmpty) return false;

    try {
      final uri = Uri.parse(ApiConfig.sessionEndpoint(cleanId));
      final response = await _client.delete(uri).timeout(
        const Duration(seconds: 5),
      );
      return response.statusCode == 204;
    } catch (_) {
      return false;
    }
  }
}
