class AdminPaginationMeta {
  const AdminPaginationMeta(
      {required this.page, required this.pageSize, required this.total});

  final int page;
  final int pageSize;
  final int total;

  factory AdminPaginationMeta.fromJson(Map<String, dynamic> json) =>
      AdminPaginationMeta(
        page: json['page'] as int,
        pageSize: json['page_size'] as int,
        total: json['total'] as int,
      );
}

class ExternalPlayerAdmin {
  const ExternalPlayerAdmin({
    required this.id,
    required this.source,
    required this.externalId,
    required this.name,
    required this.periodNumber,
    required this.grade,
    required this.region,
    required this.status,
    required this.detailUrl,
    required this.sourceUpdatedAt,
    required this.collectedAt,
    required this.createdAt,
    required this.updatedAt,
  });

  final int id;
  final String source;
  final String externalId;
  final String name;
  final String? periodNumber;
  final String grade;
  final String region;
  final String status;
  final String? detailUrl;
  final DateTime? sourceUpdatedAt;
  final DateTime collectedAt;
  final DateTime createdAt;
  final DateTime updatedAt;

  factory ExternalPlayerAdmin.fromJson(Map<String, dynamic> json) =>
      ExternalPlayerAdmin(
        id: json['id'] as int,
        source: json['source'] as String,
        externalId: json['external_id'] as String,
        name: json['name'] as String,
        periodNumber: json['period_number'] as String?,
        grade: (json['grade'] as String?) ?? 'unknown',
        region: (json['region'] as String?) ?? 'unknown',
        status: (json['status'] as String?) ?? 'unknown',
        detailUrl: json['detail_url'] as String?,
        sourceUpdatedAt: _dateOrNull(json['source_updated_at']),
        collectedAt: DateTime.parse(json['collected_at'] as String),
        createdAt: DateTime.parse(json['created_at'] as String),
        updatedAt: DateTime.parse(json['updated_at'] as String),
      );
}

class ExternalPlayerPage {
  const ExternalPlayerPage({required this.items, required this.meta});

  final List<ExternalPlayerAdmin> items;
  final AdminPaginationMeta meta;

  factory ExternalPlayerPage.fromJson(Map<String, dynamic> json) =>
      ExternalPlayerPage(
        items: (json['items'] as List<dynamic>)
            .map((item) =>
                ExternalPlayerAdmin.fromJson(item as Map<String, dynamic>))
            .toList(),
        meta:
            AdminPaginationMeta.fromJson(json['meta'] as Map<String, dynamic>),
      );
}

class ExternalPlayerFilters {
  const ExternalPlayerFilters({
    this.source,
    this.name,
    this.periodNumber,
    this.grade,
    this.status,
  });

  final String? source;
  final String? name;
  final String? periodNumber;
  final String? grade;
  final String? status;

  Map<String, String> toQuery({required int page, required int pageSize}) =>
      _cleanQuery({
        'page': '$page',
        'page_size': '$pageSize',
        'source': source,
        'name': name,
        'period_number': periodNumber,
        'grade': grade,
        'status': status,
      });
}

class ExternalPlayerStatisticAdmin {
  const ExternalPlayerStatisticAdmin({
    required this.id,
    required this.source,
    required this.standardYear,
    required this.racerName,
    required this.periodNumber,
    required this.grade,
    required this.runCount,
    required this.runDayCount,
    required this.rankCounts,
    required this.eliminatedCount,
    required this.winRate,
    required this.highRate,
    required this.high3Rate,
    required this.collectedAt,
    required this.createdAt,
    required this.updatedAt,
  });

  final int id;
  final String source;
  final String standardYear;
  final String racerName;
  final String? periodNumber;
  final String grade;
  final int? runCount;
  final int? runDayCount;
  final List<int?> rankCounts;
  final int? eliminatedCount;
  final num? winRate;
  final num? highRate;
  final num? high3Rate;
  final DateTime collectedAt;
  final DateTime createdAt;
  final DateTime updatedAt;

  factory ExternalPlayerStatisticAdmin.fromJson(Map<String, dynamic> json) =>
      ExternalPlayerStatisticAdmin(
        id: json['id'] as int,
        source: json['source'] as String,
        standardYear: json['standard_year'] as String,
        racerName: json['racer_name'] as String,
        periodNumber: json['period_number'] as String?,
        grade: (json['grade'] as String?) ?? 'unknown',
        runCount: json['run_count'] as int?,
        runDayCount: json['run_day_count'] as int?,
        rankCounts: List<int?>.generate(
            9, (index) => json['rank${index + 1}_count'] as int?),
        eliminatedCount: json['eliminated_count'] as int?,
        winRate: _numOrNull(json['win_rate']),
        highRate: _numOrNull(json['high_rate']),
        high3Rate: _numOrNull(json['high_3_rate']),
        collectedAt: DateTime.parse(json['collected_at'] as String),
        createdAt: DateTime.parse(json['created_at'] as String),
        updatedAt: DateTime.parse(json['updated_at'] as String),
      );
}

class ExternalPlayerStatisticPage {
  const ExternalPlayerStatisticPage({required this.items, required this.meta});

  final List<ExternalPlayerStatisticAdmin> items;
  final AdminPaginationMeta meta;

  factory ExternalPlayerStatisticPage.fromJson(Map<String, dynamic> json) =>
      ExternalPlayerStatisticPage(
        items: (json['items'] as List<dynamic>)
            .map((item) => ExternalPlayerStatisticAdmin.fromJson(
                item as Map<String, dynamic>))
            .toList(),
        meta:
            AdminPaginationMeta.fromJson(json['meta'] as Map<String, dynamic>),
      );
}

class ExternalPlayerStatisticFilters {
  const ExternalPlayerStatisticFilters(
      {this.year, this.racerName, this.periodNumber, this.grade});

  final String? year;
  final String? racerName;
  final String? periodNumber;
  final String? grade;

  Map<String, String> toQuery({required int page, required int pageSize}) =>
      _cleanQuery({
        'page': '$page',
        'page_size': '$pageSize',
        'year': year,
        'racer_name': racerName,
        'period_number': periodNumber,
        'grade': grade,
      });
}

class PlayerMatchCandidateAdmin {
  const PlayerMatchCandidateAdmin({
    required this.statisticId,
    required this.standardYear,
    required this.maskedRacerName,
    required this.periodNumber,
    required this.statisticGrade,
    required this.candidateCount,
    required this.matchStatus,
    required this.maskedExternalId,
    required this.externalGrade,
    required this.gradeMatches,
  });

  final int statisticId;
  final String standardYear;
  final String maskedRacerName;
  final String? periodNumber;
  final String statisticGrade;
  final int candidateCount;
  final String matchStatus;
  final String? maskedExternalId;
  final String? externalGrade;
  final bool? gradeMatches;

  factory PlayerMatchCandidateAdmin.fromJson(Map<String, dynamic> json) =>
      PlayerMatchCandidateAdmin(
        statisticId: json['statistic_id'] as int,
        standardYear: json['standard_year'] as String,
        maskedRacerName: json['masked_racer_name'] as String,
        periodNumber: json['period_number'] as String?,
        statisticGrade: json['statistic_grade'] as String,
        candidateCount: json['candidate_count'] as int,
        matchStatus: json['match_status'] as String,
        maskedExternalId: json['masked_external_id'] as String?,
        externalGrade: json['external_grade'] as String?,
        gradeMatches: json['grade_matches'] as bool?,
      );

  String get statusLabel =>
      const {
        'UNIQUE_CANDIDATE': '유일 후보',
        'NO_CANDIDATE': '후보 없음',
        'MULTIPLE_CANDIDATES': '복수 후보',
        'MISSING_PERIOD_NUMBER': '기수 미확인',
        'GRADE_MISMATCH': '등급 불일치',
      }[matchStatus] ??
      matchStatus;
}

class PlayerMatchCandidateFilters {
  const PlayerMatchCandidateFilters(
      {this.year,
      this.racerName,
      this.periodNumber,
      this.grade,
      this.matchStatus});

  final String? year;
  final String? racerName;
  final String? periodNumber;
  final String? grade;
  final String? matchStatus;

  Map<String, String> toQuery({int limit = 100}) => _cleanQuery({
        'year': year,
        'racer_name': racerName,
        'period_number': periodNumber,
        'grade': grade,
        'match_status': matchStatus,
        'limit': '$limit',
      });
}

DateTime? _dateOrNull(dynamic value) =>
    value is String && value.isNotEmpty ? DateTime.parse(value) : null;

num? _numOrNull(dynamic value) {
  if (value == null) return null;
  if (value is num) return value;
  if (value is String) return num.tryParse(value);
  return null;
}

Map<String, String> _cleanQuery(Map<String, String?> values) => {
      for (final entry in values.entries)
        if (entry.value != null && entry.value!.trim().isNotEmpty)
          entry.key: entry.value!.trim(),
    };
