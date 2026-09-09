// ats_result.dart
// =================
// Comprehensive, null-safe Dart models for deserializing the FastAPI ATS Engine response.


class ScoreComponent {
  final double score;
  final double maxScore;

  const ScoreComponent({
    required this.score,
    required this.maxScore,
  });

  factory ScoreComponent.fromJson(Map<String, dynamic>? json) {
    if (json == null) {
      return const ScoreComponent(score: 0.0, maxScore: 0.0);
    }
    return ScoreComponent(
      score: (json['score'] as num?)?.toDouble() ?? 0.0,
      maxScore: (json['max_score'] as num?)?.toDouble() ?? 0.0,
    );
  }

  double get percentage => maxScore > 0 ? (score / maxScore).clamp(0.0, 1.0) : 0.0;
}

class ScoreBreakdown {
  final ScoreComponent keywordMatch;
  final ScoreComponent experienceMatch;
  final ScoreComponent educationMatch;
  final ScoreComponent projectRelevance;
  final ScoreComponent formatting;
  final ScoreComponent quality;

  const ScoreBreakdown({
    required this.keywordMatch,
    required this.experienceMatch,
    required this.educationMatch,
    required this.projectRelevance,
    required this.formatting,
    required this.quality,
  });

  factory ScoreBreakdown.fromJson(Map<String, dynamic>? json) {
    if (json == null) {
      return const ScoreBreakdown(
        keywordMatch: ScoreComponent(score: 0, maxScore: 40),
        experienceMatch: ScoreComponent(score: 0, maxScore: 20),
        educationMatch: ScoreComponent(score: 0, maxScore: 10),
        projectRelevance: ScoreComponent(score: 0, maxScore: 15),
        formatting: ScoreComponent(score: 0, maxScore: 10),
        quality: ScoreComponent(score: 0, maxScore: 5),
      );
    }
    return ScoreBreakdown(
      keywordMatch: ScoreComponent.fromJson(json['keyword_match'] as Map<String, dynamic>?),
      experienceMatch: ScoreComponent.fromJson(json['experience_match'] as Map<String, dynamic>?),
      educationMatch: ScoreComponent.fromJson(json['education_match'] as Map<String, dynamic>?),
      projectRelevance: ScoreComponent.fromJson(json['project_relevance'] as Map<String, dynamic>?),
      formatting: ScoreComponent.fromJson(json['formatting'] as Map<String, dynamic>?),
      quality: ScoreComponent.fromJson(json['quality'] as Map<String, dynamic>?),
    );
  }
}

class ExperienceAnalysis {
  final String status;
  final double? requiredYears;
  final double? estimatedYears;
  final String details;

  const ExperienceAnalysis({
    this.status = 'not_specified',
    this.requiredYears,
    this.estimatedYears,
    this.details = '',
  });

  factory ExperienceAnalysis.fromJson(Map<String, dynamic>? json) {
    if (json == null) return const ExperienceAnalysis();
    return ExperienceAnalysis(
      status: json['status'] as String? ?? 'not_specified',
      requiredYears: (json['required_years'] as num?)?.toDouble(),
      estimatedYears: (json['estimated_years'] as num?)?.toDouble(),
      details: json['details'] as String? ?? '',
    );
  }

  bool get isMet => status == 'meets';
  bool get isPartiallyMet => status == 'partially_meets';
}

class EducationAnalysis {
  final String status;
  final String requiredLevel;
  final String detectedEducation;
  final String details;

  const EducationAnalysis({
    this.status = 'not_specified',
    this.requiredLevel = '',
    this.detectedEducation = '',
    this.details = '',
  });

  factory EducationAnalysis.fromJson(Map<String, dynamic>? json) {
    if (json == null) return const EducationAnalysis();
    return EducationAnalysis(
      status: json['status'] as String? ?? 'not_specified',
      requiredLevel: json['required_level'] as String? ?? '',
      detectedEducation: json['detected_education'] as String? ?? '',
      details: json['details'] as String? ?? '',
    );
  }

  bool get isMet => status == 'meets';
}

class ProjectRelevance {
  final double score;
  final double maxScore;
  final List<String> matchedTechnologies;
  final String details;

  const ProjectRelevance({
    this.score = 0.0,
    this.maxScore = 15.0,
    this.matchedTechnologies = const [],
    this.details = '',
  });

  factory ProjectRelevance.fromJson(Map<String, dynamic>? json) {
    if (json == null) return const ProjectRelevance();
    return ProjectRelevance(
      score: (json['score'] as num?)?.toDouble() ?? 0.0,
      maxScore: (json['max_score'] as num?)?.toDouble() ?? 15.0,
      matchedTechnologies: (json['matched_technologies'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          const [],
      details: json['details'] as String? ?? '',
    );
  }
}

class SkillMatchDetail {
  final String skill;
  final String status;
  final String matchType;
  final bool isRequired;
  final String evidence;

  const SkillMatchDetail({
    required this.skill,
    this.status = 'missing',
    this.matchType = 'none',
    this.isRequired = false,
    this.evidence = '',
  });

  factory SkillMatchDetail.fromJson(Map<String, dynamic> json) {
    return SkillMatchDetail(
      skill: json['skill'] as String? ?? '',
      status: json['status'] as String? ?? 'missing',
      matchType: json['match_type'] as String? ?? 'none',
      isRequired: json['is_required'] as bool? ?? false,
      evidence: json['evidence'] as String? ?? '',
    );
  }

  bool get isMatched => status == 'matched';
}

class ParsedResume {
  final String name;
  final String email;
  final String phone;
  final String linkedin;
  final String github;
  final List<String> skills;
  final String education;
  final String experience;
  final String projects;

  const ParsedResume({
    this.name = '',
    this.email = '',
    this.phone = '',
    this.linkedin = '',
    this.github = '',
    this.skills = const [],
    this.education = '',
    this.experience = '',
    this.projects = '',
  });

  factory ParsedResume.fromJson(Map<String, dynamic>? json) {
    if (json == null) return const ParsedResume();
    return ParsedResume(
      name: json['name'] as String? ?? '',
      email: json['email'] as String? ?? '',
      phone: json['phone'] as String? ?? '',
      linkedin: json['linkedin'] as String? ?? '',
      github: json['github'] as String? ?? '',
      skills: (json['skills'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          const [],
      education: json['education'] as String? ?? '',
      experience: json['experience'] as String? ?? '',
      projects: json['projects'] as String? ?? '',
    );
  }
}

class AtsAnalysisResult {
  final bool success;
  final int score;
  final int atsScore;
  final List<String> matchedSkills;
  final List<String> missingSkills;
  final List<String> matchedKeywords;
  final List<String> missingKeywords;
  final List<String> requiredMatched;
  final List<String> requiredMissing;
  final List<String> preferredMatched;
  final List<String> preferredMissing;
  final ScoreBreakdown? scoreBreakdown;
  final ExperienceAnalysis? experienceAnalysis;
  final EducationAnalysis? educationAnalysis;
  final ProjectRelevance? projectRelevance;
  final List<SkillMatchDetail> matchDetails;
  final List<String> suggestions;
  final ParsedResume? parsedResume;

  const AtsAnalysisResult({
    this.success = true,
    required this.score,
    required this.atsScore,
    this.matchedSkills = const [],
    this.missingSkills = const [],
    this.matchedKeywords = const [],
    this.missingKeywords = const [],
    this.requiredMatched = const [],
    this.requiredMissing = const [],
    this.preferredMatched = const [],
    this.preferredMissing = const [],
    this.scoreBreakdown,
    this.experienceAnalysis,
    this.educationAnalysis,
    this.projectRelevance,
    this.matchDetails = const [],
    this.suggestions = const [],
    this.parsedResume,
  });

  factory AtsAnalysisResult.fromJson(Map<String, dynamic> json) {
    final rawScore = (json['score'] as num?)?.toInt() ??
        (json['ats_score'] as num?)?.toInt() ??
        0;
    final rawAtsScore = (json['ats_score'] as num?)?.toInt() ?? rawScore;

    List<String> parseStringList(String key) {
      return (json[key] as List<dynamic>?)
              ?.map((e) => e.toString())
              .where((s) => s.isNotEmpty)
              .toList() ??
          const [];
    }

    return AtsAnalysisResult(
      success: json['success'] as bool? ?? true,
      score: rawScore.clamp(0, 100),
      atsScore: rawAtsScore.clamp(0, 100),
      matchedSkills: parseStringList('matched_skills'),
      missingSkills: parseStringList('missing_skills'),
      matchedKeywords: parseStringList('matched_keywords'),
      missingKeywords: parseStringList('missing_keywords'),
      requiredMatched: parseStringList('required_matched'),
      requiredMissing: parseStringList('required_missing'),
      preferredMatched: parseStringList('preferred_matched'),
      preferredMissing: parseStringList('preferred_missing'),
      scoreBreakdown: ScoreBreakdown.fromJson(
        json['score_breakdown'] as Map<String, dynamic>?,
      ),
      experienceAnalysis: ExperienceAnalysis.fromJson(
        json['experience_analysis'] as Map<String, dynamic>?,
      ),
      educationAnalysis: EducationAnalysis.fromJson(
        json['education_analysis'] as Map<String, dynamic>?,
      ),
      projectRelevance: ProjectRelevance.fromJson(
        json['project_relevance'] as Map<String, dynamic>?,
      ),
      matchDetails: (json['match_details'] as List<dynamic>?)
              ?.filterJsonMaps()
              .map((item) => SkillMatchDetail.fromJson(item))
              .toList() ??
          const [],
      suggestions: parseStringList('suggestions'),
      parsedResume: ParsedResume.fromJson(
        json['parsed_resume'] as Map<String, dynamic>?,
      ),
    );
  }

  String get matchRatingText {
    if (score >= 85) return 'Excellent Match';
    if (score >= 70) return 'Strong Match';
    if (score >= 55) return 'Good Match';
    if (score >= 40) return 'Moderate Match';
    return 'Low Match';
  }
}

extension _ListMapFilter on List<dynamic> {
  Iterable<Map<String, dynamic>> filterJsonMaps() sync* {
    for (final item in this) {
      if (item is Map<String, dynamic>) {
        yield item;
      } else if (item is Map) {
        yield Map<String, dynamic>.from(item);
      }
    }
  }
}
