import 'dart:convert';
import 'dart:math' as math;
import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import 'core/url_cleaner.dart';
import 'models/ats_result.dart';
import 'services/ats_api_service.dart';
import 'services/ai_service.dart';
import 'widgets/ai_assistant_panel.dart';

class AtsScreen extends StatefulWidget {
  final AtsApiService? apiService;
  final AiService? aiService;
  final String? initialSessionId;

  const AtsScreen({
    super.key,
    this.apiService,
    this.aiService,
    this.initialSessionId,
  });

  @override
  State<AtsScreen> createState() => _AtsScreenState();
}

class _AtsScreenState extends State<AtsScreen> {
  late final AtsApiService _apiService;
  late final AiService _aiService;
  final TextEditingController _jobDescriptionController = TextEditingController();

  PlatformFile? _selectedResume;
  bool _isAnalyzing = false;
  bool _isLoadingSession = false;
  String? _restoredSessionBanner;
  AtsAnalysisResult? _analysisResult;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _apiService = widget.apiService ?? AtsApiService();
    _aiService = widget.aiService ?? AiService();

    final sessionId = widget.initialSessionId ?? _extractSessionIdFromUrl();
    if (sessionId != null && sessionId.isNotEmpty) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _restoreSession(sessionId);
      });
    }
  }

  /// Extracts the session ID query parameter from the browser URL (supports standard and hash routes).
  String? _extractSessionIdFromUrl() {
    try {
      // 1. Direct query parameter on Uri.base
      if (Uri.base.queryParameters.containsKey('session_id')) {
        final id = Uri.base.queryParameters['session_id'];
        if (id != null && id.trim().isNotEmpty) return id.trim();
      }

      // 2. Fragment query parameter (e.g. #/?session_id=...)
      if (Uri.base.hasFragment) {
        final fragment = Uri.base.fragment;
        final qIndex = fragment.indexOf('?');
        if (qIndex != -1) {
          final queryPart = fragment.substring(qIndex + 1);
          final params = Uri.splitQueryString(queryPart);
          if (params.containsKey('session_id')) {
            final id = params['session_id'];
            if (id != null && id.trim().isNotEmpty) return id.trim();
          }
        }
      }
    } catch (_) {}
    return null;
  }

  /// Fetches the session payload from the backend and restores the resume, JD, and ATS result.
  Future<void> _restoreSession(String sessionId) async {
    setState(() {
      _isLoadingSession = true;
      _errorMessage = null;
    });

    try {
      final sessionData = await _apiService.getSession(sessionId);
      if (!mounted) return;

      if (sessionData == null) {
        cleanSessionUrl();
        setState(() {
          _isLoadingSession = false;
          _errorMessage =
              'The extension analysis session has expired or is invalid. You can upload your resume to start a new analysis.';
        });
        return;
      }

      // 1. Restore Job Description
      final jd = sessionData['job_description'] as String? ?? '';
      _jobDescriptionController.text = jd;

      // 2. Restore Selected Resume File and Raw Bytes
      final filename = sessionData['filename'] as String? ?? 'resume.pdf';
      final fileBytesBase64 = sessionData['file_bytes'] as String?;
      Uint8List? bytes;
      if (fileBytesBase64 != null && fileBytesBase64.isNotEmpty) {
        try {
          bytes = base64Decode(fileBytesBase64);
        } catch (_) {}
      }

      if (bytes != null && bytes.isNotEmpty) {
        _selectedResume = PlatformFile(
          name: filename,
          size: bytes.length,
          bytes: bytes,
        );
      }

      // 3. Restore Completed ATS Analysis Report
      final rawResult = sessionData['analysis_result'];
      if (rawResult != null && rawResult is Map) {
        _analysisResult = AtsAnalysisResult.fromJson(
          Map<String, dynamic>.from(rawResult),
        );
      }

      // Clean up: strip session_id from URL address bar and purge from backend
      cleanSessionUrl();
      _apiService.deleteSession(sessionId);

      setState(() {
        _isLoadingSession = false;
        _restoredSessionBanner = 'Analysis restored from ATS Chrome Extension.';
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _isLoadingSession = false;
        _errorMessage = 'Failed to restore analysis session: $e';
      });
    }
  }


  @override
  void dispose() {
    _jobDescriptionController.dispose();
    super.dispose();
  }

  Future<void> _pickResume() async {
    try {
      final result = await FilePicker.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf', 'docx'],
        withData: true,
      );

      if (result != null && result.files.isNotEmpty) {
        setState(() {
          _selectedResume = result.files.first;
          _errorMessage = null;
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Failed to pick file: $e';
      });
    }
  }

  Future<void> _analyzeResume() async {
    if (_selectedResume == null) {
      setState(() {
        _errorMessage = 'Please select a resume file (.pdf or .docx).';
      });
      return;
    }

    final jd = _jobDescriptionController.text.trim();
    if (jd.isEmpty) {
      setState(() {
        _errorMessage = 'Please paste a target job description.';
      });
      return;
    }

    if (jd.length < 15) {
      setState(() {
        _errorMessage = 'Job description is too short (minimum 15 characters).';
      });
      return;
    }

    setState(() {
      _isAnalyzing = true;
      _errorMessage = null;
    });

    try {
      final result = await _apiService.analyzeResume(
        resumeFile: _selectedResume!,
        jobDescription: jd,
      );

      if (!mounted) return;

      setState(() {
        _analysisResult = result;
        _isAnalyzing = false;
      });
    } on AtsApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _errorMessage = e.message;
        _isAnalyzing = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _errorMessage = 'An unexpected error occurred: $e';
        _isAnalyzing = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final result = _analysisResult;
    final int displayScore = result?.score ?? 0;
    final bool hasAnalyzed = result != null;

    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FB),
      body: SafeArea(
        child: Stack(
          children: [
            SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(20, 24, 20, 110),
              child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // -------------------------------------------------------------
              // Header
              // -------------------------------------------------------------
              const Text(
                'Resume Intelligence',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF111827),
                ),
              ),
              const SizedBox(height: 6),
              const Text(
                'Analyze your resume and compare it against a job description to improve your match.',
                style: TextStyle(
                  fontSize: 14,
                  color: Color(0xFF6B7280),
                  height: 1.5,
                ),
              ),
              const SizedBox(height: 20),

              // -------------------------------------------------------------
              // Session Loading Indicator (Restoring from Chrome Extension)
              // -------------------------------------------------------------
              if (_isLoadingSession) ...[
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  decoration: BoxDecoration(
                    color: const Color(0xFFEFF6FF),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: const Color(0xFFBFDBFE)),
                  ),
                  child: const Row(
                    children: [
                      SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF2563EB)),
                      ),
                      SizedBox(width: 12),
                      Text(
                        'Restoring analysis from ATS Chrome Extension...',
                        style: TextStyle(
                          color: Color(0xFF1D4ED8),
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 18),
              ],

              // -------------------------------------------------------------
              // Restored Session Confirmation Banner
              // -------------------------------------------------------------
              if (_restoredSessionBanner != null) ...[
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  decoration: BoxDecoration(
                    color: const Color(0xFFECFDF5),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: const Color(0xFFA7F3D0)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.check_circle_outline, color: Color(0xFF059669), size: 20),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          _restoredSessionBanner!,
                          style: const TextStyle(
                            color: Color(0xFF065F46),
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                      GestureDetector(
                        onTap: () => setState(() => _restoredSessionBanner = null),
                        child: const Icon(Icons.close, color: Color(0xFF065F46), size: 16),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 18),
              ],

              // -------------------------------------------------------------
              // Error Alert Banner (if error occurred)
              // -------------------------------------------------------------
              if (_errorMessage != null) ...[
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFEF2F2),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: const Color(0xFFFECACA)),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.error_outline, color: Color(0xFFDC2626), size: 22),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          _errorMessage!,
                          style: const TextStyle(
                            color: Color(0xFF991B1B),
                            fontSize: 14,
                            fontWeight: FontWeight.w500,
                            height: 1.4,
                          ),
                        ),
                      ),
                      GestureDetector(
                        onTap: () => setState(() => _errorMessage = null),
                        child: const Icon(Icons.close, color: Color(0xFF991B1B), size: 18),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 18),
              ],

              // -------------------------------------------------------------
              // 1. Upload Resume Card
              // -------------------------------------------------------------
              Container(
                width: double.infinity,
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(color: const Color(0xFFE5E7EB)),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.03),
                      blurRadius: 16,
                      offset: const Offset(0, 8),
                    ),
                  ],
                ),
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Upload Resume',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                        color: Color(0xFF111827),
                      ),
                    ),
                    const SizedBox(height: 14),
                    Container(
                      width: double.infinity,
                      decoration: BoxDecoration(
                        color: const Color(0xFFF8FAFC),
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: const Color(0xFFCBD5E1)),
                      ),
                      padding: const EdgeInsets.symmetric(
                        vertical: 24,
                        horizontal: 18,
                      ),
                      child: Column(
                        children: [
                          Container(
                            width: 58,
                            height: 58,
                            decoration: BoxDecoration(
                              color: const Color(0xFFEFF6FF),
                              borderRadius: BorderRadius.circular(18),
                            ),
                            child: const Icon(
                              Icons.upload_file,
                              size: 30,
                              color: Color(0xFF2563EB),
                            ),
                          ),
                          const SizedBox(height: 14),
                          const Text(
                            'Click to Choose File',
                            style: TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.w600,
                              color: Color(0xFF111827),
                            ),
                          ),
                          const SizedBox(height: 4),
                          const Text(
                            'Supports .PDF or .DOCX format',
                            style: TextStyle(
                              fontSize: 13,
                              color: Color(0xFF6B7280),
                            ),
                            textAlign: TextAlign.center,
                          ),
                          if (_selectedResume != null) ...[
                            const SizedBox(height: 16),
                            Container(
                              width: double.infinity,
                              padding: const EdgeInsets.symmetric(
                                vertical: 12,
                                horizontal: 16,
                              ),
                              decoration: BoxDecoration(
                                color: const Color(0xFFF1F5F9),
                                borderRadius: BorderRadius.circular(16),
                                border: Border.all(
                                  color: const Color(0xFFCBD5E1),
                                ),
                              ),
                              child: Row(
                                children: [
                                  const Icon(
                                    Icons.insert_drive_file,
                                    color: Color(0xFF2563EB),
                                    size: 20,
                                  ),
                                  const SizedBox(width: 10),
                                  Expanded(
                                    child: Text(
                                      _selectedResume!.name,
                                      style: const TextStyle(
                                        fontSize: 13,
                                        fontWeight: FontWeight.w600,
                                        color: Color(0xFF111827),
                                      ),
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                  GestureDetector(
                                    onTap: () {
                                      setState(() {
                                        _selectedResume = null;
                                        _analysisResult = null;
                                      });
                                    },
                                    child: const Icon(
                                      Icons.close,
                                      size: 18,
                                      color: Color(0xFF6B7280),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                          const SizedBox(height: 16),
                          SizedBox(
                            width: double.infinity,
                            height: 46,
                            child: OutlinedButton(
                              onPressed: _isAnalyzing ? null : _pickResume,
                              style: OutlinedButton.styleFrom(
                                side: const BorderSide(color: Color(0xFFCBD5E1)),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(14),
                                ),
                              ),
                              child: const Text(
                                'Choose File',
                                style: TextStyle(
                                  fontSize: 14,
                                  fontWeight: FontWeight.w600,
                                  color: Color(0xFF1D4ED8),
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // -------------------------------------------------------------
              // 2. Job Description Card
              // -------------------------------------------------------------
              Container(
                width: double.infinity,
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(color: const Color(0xFFE5E7EB)),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.03),
                      blurRadius: 16,
                      offset: const Offset(0, 8),
                    ),
                  ],
                ),
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Job Description',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                        color: Color(0xFF111827),
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _jobDescriptionController,
                      maxLines: 4,
                      enabled: !_isAnalyzing,
                      decoration: const InputDecoration(
                        hintText: 'Paste the target job description here (min 15 characters)...',
                        contentPadding: EdgeInsets.all(16),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.all(Radius.circular(16)),
                          borderSide: BorderSide(color: Color(0xFFCBD5E1)),
                        ),
                        filled: true,
                        fillColor: Color(0xFFF8FAFC),
                      ),
                    ),
                    const SizedBox(height: 16),
                    SizedBox(
                      width: double.infinity,
                      height: 50,
                      child: ElevatedButton(
                        onPressed: _selectedResume == null || _isAnalyzing
                            ? null
                            : _analyzeResume,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF0052CC),
                          disabledBackgroundColor: const Color(0xFF9CA3AF),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(16),
                          ),
                        ),
                        child: _isAnalyzing
                            ? const Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  SizedBox(
                                    height: 20,
                                    width: 20,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2.2,
                                      color: Colors.white,
                                    ),
                                  ),
                                  SizedBox(width: 12),
                                  Text(
                                    'Analyzing with ATS Engine...',
                                    style: TextStyle(
                                      fontSize: 15,
                                      fontWeight: FontWeight.w600,
                                      color: Colors.white,
                                    ),
                                  ),
                                ],
                              )
                            : const Text(
                                'Analyze Resume',
                                style: TextStyle(
                                  fontSize: 15,
                                  fontWeight: FontWeight.w600,
                                  color: Colors.white,
                                ),
                              ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // -------------------------------------------------------------
              // 3. Score Circle
              // -------------------------------------------------------------
              Center(
                child: Container(
                  width: 168,
                  height: 168,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: const Color(0xFFEFF6FF),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.blue.withValues(alpha: 0.12),
                        blurRadius: 28,
                        offset: const Offset(0, 14),
                      ),
                    ],
                  ),
                  child: AnimatedSwitcher(
                    duration: const Duration(milliseconds: 500),
                    child: _isAnalyzing
                        ? const SizedBox(
                            key: ValueKey('progress'),
                            width: 168,
                            height: 168,
                            child: Center(
                              child: CircularProgressIndicator(
                                strokeWidth: 3,
                                color: Color(0xFF2563EB),
                              ),
                            ),
                          )
                        : TweenAnimationBuilder<double>(
                            key: ValueKey('score_${displayScore}_$hasAnalyzed'),
                            tween: Tween<double>(
                              begin: 0,
                              end: hasAnalyzed ? displayScore.toDouble() : 0,
                            ),
                            duration: const Duration(milliseconds: 1000),
                            builder: (context, value, child) {
                              return Center(
                                child: Column(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Text(
                                      '${value.toInt()}%',
                                      style: TextStyle(
                                        fontSize: 36,
                                        fontWeight: FontWeight.bold,
                                        color: hasAnalyzed
                                            ? _getScoreColor(displayScore)
                                            : const Color(0xFF024BDB),
                                      ),
                                    ),
                                    const SizedBox(height: 6),
                                    Text(
                                      hasAnalyzed
                                          ? result.matchRatingText
                                          : 'Ready to analyze',
                                      style: TextStyle(
                                        fontSize: 14,
                                        color: hasAnalyzed
                                            ? _getScoreColor(displayScore)
                                            : const Color(0xFF1D4ED8),
                                        fontWeight: FontWeight.w700,
                                      ),
                                    ),
                                  ],
                                ),
                              );
                            },
                          ),
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // -------------------------------------------------------------
              // 4. Real Results Section (Displayed after analysis)
              // -------------------------------------------------------------
              if (result != null) ...[
                // Eligibility Warning Assessment (deterministic ATS rules)
                if (result.eligibility != null && result.eligibility!.warning) ...[
                  _buildEligibilityWarningCard(result.eligibility!),
                  const SizedBox(height: 18),
                ],

                // Score Breakdown
                if (result.scoreBreakdown != null) ...[

                  _buildSectionTitle('Score Breakdown'),
                  const SizedBox(height: 12),
                  _buildScoreBreakdownCard(result.scoreBreakdown!),
                  const SizedBox(height: 20),
                ],

                // Skills Analysis (Matched & Missing)
                _buildSectionTitle('Skills Analysis'),
                const SizedBox(height: 12),
                _buildSkillsCard(result),
                const SizedBox(height: 20),

                // Experience & Education Match
                if (result.experienceAnalysis != null || result.educationAnalysis != null) ...[
                  _buildSectionTitle('Requirements Assessment'),
                  const SizedBox(height: 12),
                  _buildRequirementsCard(result),
                  const SizedBox(height: 20),
                ],

                // Suggestions Card
                if (result.suggestions.isNotEmpty) ...[
                  _buildSectionTitle('ATS Recommendations'),
                  const SizedBox(height: 12),
                  _buildSuggestionsCard(result.suggestions),
                  const SizedBox(height: 20),
                ],

                // Parsed Candidate Summary (if parsed info available)
                if (result.parsedResume != null &&
                    (result.parsedResume!.name.isNotEmpty || result.parsedResume!.email.isNotEmpty)) ...[
                  _buildSectionTitle('Detected Candidate Profile'),
                  const SizedBox(height: 12),
                  _buildCandidateCard(result.parsedResume!),
                  const SizedBox(height: 20),
                ],
              ] else ...[
                // Initial State placeholder
                const Text(
                  'Analysis Overview',
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.w700,
                    color: Color(0xFF111827),
                  ),
                ),
                const SizedBox(height: 10),
                const Text(
                  'Upload your resume (.pdf or .docx) and paste a target job description above to compute a comprehensive ATS compatibility breakdown.',
                  style: TextStyle(
                    fontSize: 14,
                    color: Color(0xFF6B7280),
                    height: 1.6,
                  ),
                ),
                const SizedBox(height: 24),
              ],
            ],
          ),
        ),
        if (hasAnalyzed)
          Positioned(
            bottom: 24,
            right: 24,
            child: _buildAskGeminiButton(context),
          ),
      ],
    ),
  ),
);
  }

  // -------------------------------------------------------------------------
  // Helper UI Builders
  // -------------------------------------------------------------------------

  Widget _buildSectionTitle(String title) {
    return Text(
      title,
      style: const TextStyle(
        fontSize: 18,
        fontWeight: FontWeight.w700,
        color: Color(0xFF111827),
      ),
    );
  }

  Color _getScoreColor(int score) {
    if (score >= 80) return const Color(0xFF059669); // Green
    if (score >= 65) return const Color(0xFF024BDB); // Blue
    if (score >= 50) return const Color(0xFFD97706); // Amber
    return const Color(0xFFDC2626); // Red
  }

  Widget _buildScoreBreakdownCard(ScoreBreakdown breakdown) {
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFFE5E7EB)),
      ),
      padding: const EdgeInsets.all(18),
      child: Column(
        children: [
          _buildBreakdownRow('Keywords & Skills', breakdown.keywordMatch.score, breakdown.keywordMatch.maxScore),
          const Divider(height: 18, color: Color(0xFFF1F5F9)),
          _buildBreakdownRow('Experience Match', breakdown.experienceMatch.score, breakdown.experienceMatch.maxScore),
          const Divider(height: 18, color: Color(0xFFF1F5F9)),
          _buildBreakdownRow('Project Relevance', breakdown.projectRelevance.score, breakdown.projectRelevance.maxScore),
          const Divider(height: 18, color: Color(0xFFF1F5F9)),
          _buildBreakdownRow('Education Match', breakdown.educationMatch.score, breakdown.educationMatch.maxScore),
          const Divider(height: 18, color: Color(0xFFF1F5F9)),
          _buildBreakdownRow('Resume Formatting', breakdown.formatting.score, breakdown.formatting.maxScore),
          const Divider(height: 18, color: Color(0xFFF1F5F9)),
          _buildBreakdownRow('Content Quality', breakdown.quality.score, breakdown.quality.maxScore),
        ],
      ),
    );
  }

  Widget _buildBreakdownRow(String title, double score, double maxScore) {
    final double percent = maxScore > 0 ? (score / maxScore).clamp(0.0, 1.0) : 0.0;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              title,
              style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Color(0xFF374151)),
            ),
            Text(
              '${score.toStringAsFixed(1)} / ${maxScore.toInt()} pts',
              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: Color(0xFF1D4ED8)),
            ),
          ],
        ),
        const SizedBox(height: 6),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: percent,
            minHeight: 6,
            backgroundColor: const Color(0xFFEFF6FF),
            valueColor: AlwaysStoppedAnimation<Color>(
              percent >= 0.7 ? const Color(0xFF2563EB) : const Color(0xFFF59E0B),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildSkillsCard(AtsAnalysisResult result) {
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFFE5E7EB)),
      ),
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Matched Skills
          Row(
            children: [
              const Icon(Icons.check_circle_outline, color: Color(0xFF059669), size: 18),
              const SizedBox(width: 8),
              Text(
                'Matched Skills (${result.matchedSkills.length})',
                style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: Color(0xFF111827)),
              ),
            ],
          ),
          const SizedBox(height: 10),
          if (result.matchedSkills.isEmpty)
            const Text(
              'No required skills matched from the job description.',
              style: TextStyle(fontSize: 13, color: Color(0xFF6B7280), fontStyle: FontStyle.italic),
            )
          else
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: result.matchedSkills.map((skill) => _SkillChip(
                label: skill,
                isMatched: true,
              )).toList(),
            ),

          const SizedBox(height: 18),
          const Divider(color: Color(0xFFF1F5F9)),
          const SizedBox(height: 12),

          // Missing Skills
          Row(
            children: [
              const Icon(Icons.highlight_off, color: Color(0xFFDC2626), size: 18),
              const SizedBox(width: 8),
              Text(
                'Missing Skills (${result.missingSkills.length})',
                style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: Color(0xFF111827)),
              ),
            ],
          ),
          const SizedBox(height: 10),
          if (result.missingSkills.isEmpty)
            const Text(
              'Great job! All extracted job skills are present in your resume.',
              style: TextStyle(fontSize: 13, color: Color(0xFF059669), fontWeight: FontWeight.w500),
            )
          else
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: result.missingSkills.map((skill) => _SkillChip(
                label: skill,
                isMatched: false,
              )).toList(),
            ),
        ],
      ),
    );
  }

  Widget _buildRequirementsCard(AtsAnalysisResult result) {
    final exp = result.experienceAnalysis;
    final edu = result.educationAnalysis;

    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFFE5E7EB)),
      ),
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (exp != null && exp.details.isNotEmpty) ...[
            Row(
              children: [
                Icon(
                  exp.isMet ? Icons.verified : Icons.info_outline,
                  color: exp.isMet ? const Color(0xFF059669) : const Color(0xFFD97706),
                  size: 18,
                ),
                const SizedBox(width: 8),
                const Text('Experience Requirement', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700)),
              ],
            ),
            const SizedBox(height: 4),
            Text(exp.details, style: const TextStyle(fontSize: 13, color: Color(0xFF4B5563), height: 1.4)),
            const SizedBox(height: 14),
          ],
          if (edu != null && edu.details.isNotEmpty) ...[
            Row(
              children: [
                Icon(
                  edu.isMet ? Icons.school : Icons.info_outline,
                  color: edu.isMet ? const Color(0xFF059669) : const Color(0xFFD97706),
                  size: 18,
                ),
                const SizedBox(width: 8),
                const Text('Education Requirement', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700)),
              ],
            ),
            const SizedBox(height: 4),
            Text(edu.details, style: const TextStyle(fontSize: 13, color: Color(0xFF4B5563), height: 1.4)),
          ],
        ],
      ),
    );
  }

  Widget _buildSuggestionsCard(List<String> suggestions) {
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: const Color(0xFFF0FDF4),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFFBBF7D0)),
      ),
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: suggestions.map((s) => Padding(
          padding: const EdgeInsets.only(bottom: 10),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Icon(Icons.lightbulb_outline, color: Color(0xFF16A34A), size: 18),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  s,
                  style: const TextStyle(fontSize: 13, color: Color(0xFF15803D), height: 1.4),
                ),
              ),
            ],
          ),
        )).toList(),
      ),
    );
  }

  Widget _buildCandidateCard(ParsedResume resume) {
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFFE5E7EB)),
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (resume.name.isNotEmpty)
            Text(resume.name, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: Color(0xFF111827))),
          if (resume.email.isNotEmpty) ...[
            const SizedBox(height: 4),
            Text(resume.email, style: const TextStyle(fontSize: 13, color: Color(0xFF6B7280))),
          ],
          if (resume.skills.isNotEmpty) ...[
            const SizedBox(height: 10),
            Text('Detected ${resume.skills.length} skills in resume.', style: const TextStyle(fontSize: 12, color: Color(0xFF4B5563), fontWeight: FontWeight.w500)),
          ],
        ],
      ),
    );
  }

  Widget _buildEligibilityWarningCard(EligibilityAssessment eligibility) {
    final bool isUnverified = eligibility.isRequirementsNotVerified;
    final Color bgColor = isUnverified ? const Color(0xFFFFFBEB) : const Color(0xFFFFF1F2);
    final Color borderColor = isUnverified ? const Color(0xFFFDE68A) : const Color(0xFFFECDD3);
    final Color accentColor = isUnverified ? const Color(0xFFD97706) : const Color(0xFFE11D48);
    final Color iconBg = isUnverified ? const Color(0xFFFEF3C7) : const Color(0xFFFFE4E6);
    final Color titleColor = isUnverified ? const Color(0xFF92400E) : const Color(0xFF9F1239);
    final Color textColor = isUnverified ? const Color(0xFF78350F) : const Color(0xFF881337);

    final String title = isUnverified
        ? 'Eligibility Requirements Need Verification'
        : 'Potential Eligibility Warning';

    final String subtitle = isUnverified
        ? 'Mandatory job requirements could not be confirmed from the resume:'
        : 'Key eligibility conditions or minimum thresholds were not satisfied:';

    return Container(
      key: const Key('eligibilityWarningCard'),
      width: double.infinity,
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: borderColor, width: 1.5),
        boxShadow: [
          BoxShadow(
            color: accentColor.withValues(alpha: 0.06),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: iconBg,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(
                  isUnverified ? Icons.help_outline_rounded : Icons.warning_amber_rounded,
                  color: accentColor,
                  size: 24,
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w700,
                        color: titleColor,
                        letterSpacing: -0.2,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      subtitle,
                      style: TextStyle(
                        fontSize: 13,
                        color: textColor.withValues(alpha: 0.9),
                        height: 1.4,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          if (eligibility.reasons.isNotEmpty) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.only(left: 46),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: eligibility.reasons.map((reason) {
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 6),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          margin: const EdgeInsets.only(top: 6, right: 8),
                          width: 5,
                          height: 5,
                          decoration: BoxDecoration(
                            color: accentColor,
                            shape: BoxShape.circle,
                          ),
                        ),
                        Expanded(
                          child: Text(
                            reason,
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                              color: textColor,
                              height: 1.4,
                            ),
                          ),
                        ),
                      ],
                    ),
                  );
                }).toList(),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildAskGeminiButton(BuildContext context) {
    return ElevatedButton.icon(
      onPressed: () => _openGeminiChat(context),
      icon: const Icon(Icons.auto_awesome, size: 18, color: Colors.white),
      label: const Text(
        'Ask AI',
        style: TextStyle(
          fontSize: 15,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.3,
          color: Colors.white,
        ),
      ),
      style: ElevatedButton.styleFrom(
        backgroundColor: const Color(0xFF0052CC),
        foregroundColor: Colors.white,
        elevation: 8,
        shadowColor: const Color(0xFF0052CC).withValues(alpha: 0.4),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(28),
          side: const BorderSide(color: Color(0xFF3B82F6), width: 1.5),
        ),
      ),
    );
  }

  void _openGeminiChat(BuildContext context) {
    if (_analysisResult == null) return;

    final mediaQuery = MediaQuery.of(context);
    final isDesktop = mediaQuery.size.width > 700;

    if (isDesktop) {
      final dialogWidth = math.min(600.0, mediaQuery.size.width - 48);
      final dialogHeight = math.min(720.0, mediaQuery.size.height - 48);

      showDialog(
        context: context,
        builder: (ctx) => Dialog(
          backgroundColor: Colors.transparent,
          insetPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 24),
          child: SizedBox(
            width: dialogWidth,
            height: dialogHeight,
            child: ClipRRect(
              borderRadius: BorderRadius.circular(24),
              child: AiAssistantPanel(
                analysisResult: _analysisResult!,
                jobDescription: _jobDescriptionController.text.trim(),
                aiService: _aiService,
                isDialog: true,
                onAnalysisUpdated: (updatedResult) {
                  setState(() {
                    _analysisResult = updatedResult;
                  });
                },
              ),
            ),
          ),
        ),
      );
    } else {
      showModalBottomSheet(
        context: context,
        isScrollControlled: true,
        backgroundColor: Colors.transparent,
        builder: (ctx) => Padding(
          padding: EdgeInsets.only(
            bottom: MediaQuery.of(ctx).viewInsets.bottom,
          ),
          child: SizedBox(
            height: mediaQuery.size.height * 0.85,
            child: ClipRRect(
              borderRadius: const BorderRadius.vertical(top: Radius.circular(28)),
              child: AiAssistantPanel(
                analysisResult: _analysisResult!,
                jobDescription: _jobDescriptionController.text.trim(),
                aiService: _aiService,
                isDialog: false,
                onAnalysisUpdated: (updatedResult) {
                  setState(() {
                    _analysisResult = updatedResult;
                  });
                },
              ),
            ),
          ),
        ),
      );
    }
  }
}


class _SkillChip extends StatelessWidget {
  final String label;
  final bool isMatched;

  const _SkillChip({
    required this.label,
    this.isMatched = true,
  });

  @override
  Widget build(BuildContext context) {
    final bgColor = isMatched ? const Color(0xFFF0FDF4) : const Color(0xFFFEF2F2);
    final borderColor = isMatched ? const Color(0xFFBBF7D0) : const Color(0xFFFECACA);
    final textColor = isMatched ? const Color(0xFF15803D) : const Color(0xFFB91C1C);

    return Container(
      padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 12),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: borderColor),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: textColor,
          fontWeight: FontWeight.w600,
          fontSize: 12,
        ),
      ),
    );
  }
}
