// ai_assistant_panel.dart
// ======================
// Clean, modern slide-up panel / modal for the Gemini AI Assistant.
// Strictly advisory; proposals require explicit user approval,
// and approved changes trigger deterministic ATS re-scoring on the backend.

import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';

import '../models/ai_models.dart';
import '../models/ats_result.dart';
import '../services/ai_service.dart';

class AiAssistantPanel extends StatefulWidget {
  final AtsAnalysisResult analysisResult;
  final String jobDescription;
  final ValueChanged<AtsAnalysisResult> onAnalysisUpdated;
  final AiService? aiService;
  final bool isDialog;

  const AiAssistantPanel({
    super.key,
    required this.analysisResult,
    required this.jobDescription,
    required this.onAnalysisUpdated,
    this.aiService,
    this.isDialog = false,
  });

  @override
  State<AiAssistantPanel> createState() => _AiAssistantPanelState();
}

class _AiAssistantPanelState extends State<AiAssistantPanel> {
  late final AiService _aiService;
  final TextEditingController _inputController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  final List<ChatMessage> _messages = [];
  bool _isLoading = false;
  late AtsAnalysisResult _currentResult;
  Map<String, dynamic> _currentResumeMap = {};

  @override
  void initState() {
    super.initState();
    _aiService = widget.aiService ?? AiService();
    _currentResult = widget.analysisResult;
    _currentResumeMap = _currentResult.parsedResume?.toJson() ?? {};

    // Initial greeting message with analysis context
    _messages.add(
      ChatMessage(
        role: 'assistant',
        content:
            'Hello! I am your ATS Resume Assistant. I can help explain your ATS score (${_currentResult.score}%), review missing skills, and suggest improvements based on the job description.\n\n'
            'If you possess a required skill that was omitted from your resume, let me know and I will propose adding it for your explicit approval.',
      ),
    );
  }

  @override
  void dispose() {
    _inputController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _handleSendMessage([String? prefilledText]) async {
    final text = (prefilledText ?? _inputController.text).trim();
    if (text.isEmpty || _isLoading) return;

    if (prefilledText == null) {
      _inputController.clear();
    }

    setState(() {
      _messages.add(ChatMessage(role: 'user', content: text));
      _isLoading = true;
    });
    _scrollToBottom();

    try {
      final response = await _aiService.sendMessage(
        message: text,
        resumeContext: _currentResumeMap,
        jobDescription: widget.jobDescription,
        analysisContext: _currentResult.toJson(),
        conversationHistory: _messages,
      );

      if (!mounted) return;

      setState(() {
        _isLoading = false;
        _messages.add(
          ChatMessage(
            role: 'assistant',
            content: response.message,
            proposedChanges: response.proposedChanges,
          ),
        );
      });
      _scrollToBottom();
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _isLoading = false;
        _messages.add(
          ChatMessage(
            role: 'assistant',
            content: 'Sorry, I encountered an error: $e',
          ),
        );
      });
      _scrollToBottom();
    }
  }

  Future<void> _handleApproveChange(ProposedChange change) async {
    setState(() {
      change.isApproved = true;
      _isLoading = true;
    });

    try {
      final response = await _aiService.applyApprovedChanges(
        originalResume: _currentResumeMap,
        approvedChanges: [change],
        jobDescription: widget.jobDescription,
      );

      if (!mounted) return;

      final previousScore = _currentResult.score;
      final newScore = response.analysisResult.score;

      setState(() {
        _isLoading = false;
        _currentResumeMap = response.updatedResume;
        _currentResult = response.analysisResult;

        _messages.add(
          ChatMessage(
            role: 'system',
            content:
                '✓ Skill "${change.value}" added to resume while preserving structure and formatting.\n'
                'ATS Score recalculated by deterministic engine: $previousScore% → $newScore%.',
          ),
        );
      });

      // Update parent screen
      widget.onAnalysisUpdated(response.analysisResult);
      _scrollToBottom();
    } catch (e) {
      if (!mounted) return;
      setState(() {
        change.isApproved = null; // reset to allow retry
        _isLoading = false;
        _messages.add(
          ChatMessage(
            role: 'system',
            content: 'Error applying change: $e',
          ),
        );
      });
      _scrollToBottom();
    }
  }

  Future<void> _handleReAnalyze() async {
    if (_isLoading) return;

    setState(() {
      _isLoading = true;
    });

    try {
      final response = await _aiService.applyApprovedChanges(
        originalResume: _currentResumeMap,
        approvedChanges: [],
        jobDescription: widget.jobDescription,
      );

      if (!mounted) return;

      setState(() {
        _isLoading = false;
        _currentResult = response.analysisResult;
        _messages.add(
          ChatMessage(
            role: 'system',
            content:
                '✓ Deterministic ATS analysis recalculated.\n'
                'Current ATS Score: ${_currentResult.score}%.',
          ),
        );
      });

      widget.onAnalysisUpdated(response.analysisResult);
      _scrollToBottom();
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _isLoading = false;
        _messages.add(
          ChatMessage(
            role: 'system',
            content: 'Error re-running ATS analysis: $e',
          ),
        );
      });
      _scrollToBottom();
    }
  }

  void _handleRejectChange(ProposedChange change) {
    setState(() {
      change.isApproved = false;
      _messages.add(
        ChatMessage(
          role: 'system',
          content: 'Proposal to add "${change.value}" was rejected. No changes made.',
        ),
      );
    });
    _scrollToBottom();
  }

  @override
  Widget build(BuildContext context) {
    final mediaQuery = MediaQuery.of(context);
    final isDesktop = mediaQuery.size.width > 700;


    return Container(
      height: widget.isDialog ? 720 : mediaQuery.size.height * 0.85,
      width: isDesktop ? 600 : double.infinity,
      decoration: BoxDecoration(
        color: const Color(0xFFF8FAFC),
        borderRadius: widget.isDialog
            ? BorderRadius.circular(24)
            : const BorderRadius.vertical(top: Radius.circular(28)),
      ),
      child: Column(
        children: [
          // -------------------------------------------------------------
          // Top Header
          // -------------------------------------------------------------
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: widget.isDialog
                  ? const BorderRadius.vertical(top: Radius.circular(24))
                  : const BorderRadius.vertical(top: Radius.circular(28)),
              border: const Border(bottom: BorderSide(color: Color(0xFFE2E8F0))),
            ),
            child: Row(
              children: [
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    color: const Color(0xFFEFF6FF),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Center(
                    child: Text('✨', style: TextStyle(fontSize: 20)),
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Gemini AI Assistant',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                          color: Color(0xFF0F172A),
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        'ATS Score: ${_currentResult.score}% • ${_currentResult.missingSkills.length} Missing Skills',
                        style: const TextStyle(
                          fontSize: 12,
                          color: Color(0xFF64748B),
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.refresh, color: Color(0xFF0052CC)),
                  tooltip: 'Re-Analyze with ATS Engine',
                  onPressed: _isLoading ? null : _handleReAnalyze,
                ),
                IconButton(
                  icon: const Icon(Icons.close, color: Color(0xFF64748B)),
                  onPressed: () => Navigator.of(context).pop(),
                  tooltip: 'Close Assistant',
                ),
              ],
            ),
          ),

          // -------------------------------------------------------------
          // Quick Suggestion Chips (when only initial message)
          // -------------------------------------------------------------
          if (_messages.length <= 1)
            Container(
              color: Colors.white,
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    _buildQuickChip('Why is my ATS score ${_currentResult.score}%?'),
                    const SizedBox(width: 8),
                    _buildQuickChip('What skills am I missing?'),
                    const SizedBox(width: 8),
                    _buildQuickChip('Which skills matched successfully?'),
                    const SizedBox(width: 8),
                    _buildQuickChip('Review experience & education match'),
                    const SizedBox(width: 8),
                    _buildQuickChip('What should I improve in my resume?'),
                  ],
                ),
              ),
            ),

          // -------------------------------------------------------------
          // Message History List
          // -------------------------------------------------------------
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final message = _messages[index];
                return _buildMessageItem(message);
              },
            ),
          ),

          // -------------------------------------------------------------
          // Loading Indicator
          // -------------------------------------------------------------
          if (_isLoading)
            Container(
              padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 20),
              alignment: Alignment.centerLeft,
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF2563EB)),
                  ),
                  const SizedBox(width: 10),
                  Text(
                    'AI Assistant is thinking...',
                    style: TextStyle(
                      fontSize: 13,
                      color: Colors.grey.shade600,
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                ],
              ),
            ),

          // -------------------------------------------------------------
          // Input Field & Send Button
          // -------------------------------------------------------------
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: const BoxDecoration(
              color: Colors.white,
              border: Border(top: BorderSide(color: Color(0xFFE2E8F0))),
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _inputController,
                    onSubmitted: (_) => _handleSendMessage(),
                    enabled: !_isLoading,
                    decoration: InputDecoration(
                      hintText: 'Ask about your score, missing skills, or add experience...',
                      hintStyle: TextStyle(fontSize: 13, color: Colors.grey.shade500),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(24),
                        borderSide: const BorderSide(color: Color(0xFFCBD5E1)),
                      ),
                      filled: true,
                      fillColor: const Color(0xFFF8FAFC),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Material(
                  color: const Color(0xFF0052CC),
                  borderRadius: BorderRadius.circular(24),
                  child: InkWell(
                    borderRadius: BorderRadius.circular(24),
                    onTap: _isLoading ? null : () => _handleSendMessage(),
                    child: const Padding(
                      padding: EdgeInsets.all(12),
                      child: Icon(Icons.send, color: Colors.white, size: 20),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildQuickChip(String label) {
    return ActionChip(
      label: Text(
        label,
        style: const TextStyle(fontSize: 12, color: Color(0xFF1D4ED8), fontWeight: FontWeight.w500),
      ),
      backgroundColor: const Color(0xFFEFF6FF),
      side: const BorderSide(color: Color(0xFFBFDBFE)),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      onPressed: () => _handleSendMessage(label),
    );
  }

  Widget _buildMessageItem(ChatMessage message) {
    if (message.isSystem) {
      return Container(
        margin: const EdgeInsets.symmetric(vertical: 8),
        alignment: Alignment.center,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          decoration: BoxDecoration(
            color: const Color(0xFFF1F5F9),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: const Color(0xFFCBD5E1)),
          ),
          child: Text(
            message.content,
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Color(0xFF334155)),
          ),
        ),
      );
    }

    final isUser = message.isUser;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Column(
        crossAxisAlignment: isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (!isUser) ...[
                Container(
                  width: 32,
                  height: 32,
                  decoration: BoxDecoration(
                    color: const Color(0xFFEFF6FF),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: const Color(0xFFBFDBFE)),
                  ),
                  child: const Center(
                    child: Text('✨', style: TextStyle(fontSize: 15)),
                  ),
                ),
                const SizedBox(width: 8),
              ],
              Flexible(
                child: Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: isUser ? const Color(0xFF0052CC) : Colors.white,
                    borderRadius: BorderRadius.circular(18).copyWith(
                      bottomRight: isUser ? const Radius.circular(4) : const Radius.circular(18),
                      bottomLeft: !isUser ? const Radius.circular(4) : const Radius.circular(18),
                    ),
                    border: isUser ? null : Border.all(color: const Color(0xFFE2E8F0)),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withValues(alpha: 0.03),
                        blurRadius: 8,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                  child: isUser
                      ? Text(
                          message.content,
                          style: const TextStyle(
                            fontSize: 14,
                            height: 1.45,
                            color: Colors.white,
                          ),
                        )
                      : MarkdownBody(
                          data: message.content,
                          selectable: true,
                          styleSheet: MarkdownStyleSheet.fromTheme(Theme.of(context)).copyWith(
                            p: const TextStyle(
                              fontSize: 14,
                              height: 1.5,
                              color: Color(0xFF1E293B),
                            ),
                            h1: const TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.w700,
                              color: Color(0xFF0F172A),
                              height: 1.4,
                            ),
                            h2: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w700,
                              color: Color(0xFF0F172A),
                              height: 1.4,
                            ),
                            h3: const TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.w700,
                              color: Color(0xFF1E293B),
                              height: 1.35,
                            ),
                            h4: const TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w700,
                              color: Color(0xFF334155),
                              height: 1.35,
                            ),
                            strong: const TextStyle(
                              fontWeight: FontWeight.w700,
                              color: Color(0xFF0F172A),
                            ),
                            em: const TextStyle(
                              fontStyle: FontStyle.italic,
                              color: Color(0xFF334155),
                            ),
                            listBullet: const TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w600,
                              color: Color(0xFF2563EB),
                            ),
                            listIndent: 20.0,
                            blockSpacing: 10.0,
                            code: const TextStyle(
                              fontSize: 13,
                              fontFamily: 'monospace',
                              backgroundColor: Color(0xFFF1F5F9),
                              color: Color(0xFF0F172A),
                            ),
                            codeblockDecoration: BoxDecoration(
                              color: const Color(0xFFF1F5F9),
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: const Color(0xFFCBD5E1)),
                            ),
                            codeblockPadding: const EdgeInsets.all(10),
                            blockquote: const TextStyle(
                              fontSize: 13.5,
                              fontStyle: FontStyle.italic,
                              color: Color(0xFF475569),
                            ),
                            blockquoteDecoration: const BoxDecoration(
                              color: Color(0xFFF8FAFC),
                              borderRadius: BorderRadius.all(Radius.circular(4)),
                              border: Border(
                                left: BorderSide(color: Color(0xFF3B82F6), width: 3),
                              ),
                            ),
                            blockquotePadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                            a: const TextStyle(
                              color: Color(0xFF2563EB),
                              decoration: TextDecoration.underline,
                            ),
                          ),
                        ),
                ),
              ),
            ],
          ),

          // Render Proposed Changes (Approval Cards)
          if (message.proposedChanges.isNotEmpty) ...[
            const SizedBox(height: 8),
            ...message.proposedChanges.map((change) => _buildProposalCard(change)),
          ],
        ],
      ),
    );
  }

  Widget _buildProposalCard(ProposedChange change) {
    return Container(
      margin: const EdgeInsets.only(left: 40, top: 6, bottom: 6),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFFF8FAFC),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFF93C5FD), width: 1.5),
        boxShadow: [
          BoxShadow(
            color: Colors.blue.withValues(alpha: 0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: const [
              Icon(Icons.edit_note, color: Color(0xFF1D4ED8), size: 18),
              SizedBox(width: 8),
              Text(
                'AI Proposes a Resume Update',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: Color(0xFF1D4ED8),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Add skill: ',
                style: TextStyle(fontSize: 13, color: Color(0xFF64748B), fontWeight: FontWeight.w500),
              ),
              Expanded(
                child: Text(
                  change.value,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: Color(0xFF0F172A),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            'Reason: ${change.reason}',
            style: const TextStyle(
              fontSize: 12,
              color: Color(0xFF475569),
              fontStyle: FontStyle.italic,
            ),
          ),
          const SizedBox(height: 14),

          // Actions
          if (change.isApproved == null)
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    icon: const Icon(Icons.check, size: 16, color: Colors.white),
                    label: const Text('Approve', style: TextStyle(fontWeight: FontWeight.w600)),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF059669),
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      padding: const EdgeInsets.symmetric(vertical: 10),
                    ),
                    onPressed: _isLoading ? null : () => _handleApproveChange(change),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: OutlinedButton.icon(
                    icon: const Icon(Icons.close, size: 16, color: Color(0xFFDC2626)),
                    label: const Text('Reject', style: TextStyle(color: Color(0xFFDC2626), fontWeight: FontWeight.w600)),
                    style: OutlinedButton.styleFrom(
                      side: const BorderSide(color: Color(0xFFFECACA)),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      padding: const EdgeInsets.symmetric(vertical: 10),
                    ),
                    onPressed: _isLoading ? null : () => _handleRejectChange(change),
                  ),
                ),
              ],
            )
          else if (change.isApproved == true)
            Wrap(
              spacing: 8,
              runSpacing: 6,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 12),
                  decoration: BoxDecoration(
                    color: const Color(0xFFDCFCE7),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: const Color(0xFF86EFAC)),
                  ),
                  child: const Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.check_circle, size: 16, color: Color(0xFF15803D)),
                      SizedBox(width: 6),
                      Text(
                        'Approved & Re-analyzed by ATS Engine',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: Color(0xFF15803D),
                        ),
                      ),
                    ],
                  ),
                ),
                OutlinedButton.icon(
                  icon: const Icon(Icons.refresh, size: 14, color: Color(0xFF0052CC)),
                  label: const Text(
                    'Re-Analyze ATS',
                    style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Color(0xFF0052CC)),
                  ),
                  style: OutlinedButton.styleFrom(
                    side: const BorderSide(color: Color(0xFFBFDBFE)),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  ),
                  onPressed: _isLoading ? null : _handleReAnalyze,
                ),
              ],
            )
          else
            Container(
              padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 12),
              decoration: BoxDecoration(
                color: const Color(0xFFFEE2E2),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: const Color(0xFFFCA5A5)),
              ),
              child: const Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.cancel, size: 16, color: Color(0xFFB91C1C)),
                  SizedBox(width: 6),
                  Text(
                    'Rejected - No changes applied',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: Color(0xFFB91C1C),
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}
