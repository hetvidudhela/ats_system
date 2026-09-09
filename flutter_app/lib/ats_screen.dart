import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import 'models/ats_result.dart';
import 'services/ats_api_service.dart';

class AtsScreen extends StatefulWidget {
  final AtsApiService? apiService;

  const AtsScreen({super.key, this.apiService});

  @override
  State<AtsScreen> createState() => _AtsScreenState();
}

class _AtsScreenState extends State<AtsScreen> {
  late final AtsApiService _apiService;
  final TextEditingController _jobDescriptionController = TextEditingController();

  PlatformFile? _selectedResume;
  bool _isAnalyzing = false;
  AtsAnalysisResult? _analysisResult;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _apiService = widget.apiService ?? AtsApiService();
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
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
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
