class DataQualitySummary {
  const DataQualitySummary({
    required this.counts,
    required this.externalPlayersQuality,
    required this.statisticsQuality,
    required this.matchStatusCounts,
    required this.coverage,
  });

  final DataQualityCounts counts;
  final ExternalPlayersQuality externalPlayersQuality;
  final StatisticsQuality statisticsQuality;
  final Map<String, int> matchStatusCounts;
  final MatchCoverage coverage;

  factory DataQualitySummary.fromJson(Map<String, dynamic> json) {
    final statuses = json['match_status_counts'] as Map<String, dynamic>;
    return DataQualitySummary(
      counts:
          DataQualityCounts.fromJson(json['counts'] as Map<String, dynamic>),
      externalPlayersQuality: ExternalPlayersQuality.fromJson(
          json['external_players_quality'] as Map<String, dynamic>),
      statisticsQuality: StatisticsQuality.fromJson(
          json['statistics_quality'] as Map<String, dynamic>),
      matchStatusCounts:
          statuses.map((key, value) => MapEntry(key, value as int)),
      coverage:
          MatchCoverage.fromJson(json['coverage'] as Map<String, dynamic>),
    );
  }

  DateTime? get latestCollectedAt {
    final values = [
      externalPlayersQuality.latestCollectedAt,
      statisticsQuality.latestCollectedAt
    ].whereType<DateTime>().toList();
    if (values.isEmpty) return null;
    values.sort();
    return values.last;
  }
}

class DataQualityCounts {
  const DataQualityCounts(this.players, this.externalPlayers, this.statistics);
  final int players;
  final int externalPlayers;
  final int statistics;
  factory DataQualityCounts.fromJson(Map<String, dynamic> json) =>
      DataQualityCounts(
          json['players_count'] as int,
          json['external_players_count'] as int,
          json['external_player_statistics_count'] as int);
}

class ExternalPlayersQuality {
  const ExternalPlayersQuality(
      {required this.missingName,
      required this.missingPeriod,
      required this.unknownGrade,
      required this.unknownRegion,
      required this.unknownStatus,
      required this.duplicates,
      required this.latestCollectedAt});
  final int missingName,
      missingPeriod,
      unknownGrade,
      unknownRegion,
      unknownStatus,
      duplicates;
  final DateTime? latestCollectedAt;
  factory ExternalPlayersQuality.fromJson(Map<String, dynamic> json) =>
      ExternalPlayersQuality(
        missingName: json['missing_name_count'] as int,
        missingPeriod: json['missing_period_number_count'] as int,
        unknownGrade: json['unknown_grade_count'] as int,
        unknownRegion: json['unknown_region_count'] as int,
        unknownStatus: json['unknown_status_count'] as int,
        duplicates: json['duplicate_source_external_id_count'] as int,
        latestCollectedAt: _date(json['latest_collected_at']),
      );
}

class StatisticsQuality {
  const StatisticsQuality(
      {required this.missingName,
      required this.missingPeriod,
      required this.unknownGrade,
      required this.duplicates,
      required this.invalidRunCount,
      required this.nullWinRate,
      required this.nullHighRate,
      required this.nullHigh3Rate,
      required this.latestCollectedAt});
  final int missingName,
      missingPeriod,
      unknownGrade,
      duplicates,
      invalidRunCount;
  final int nullWinRate, nullHighRate, nullHigh3Rate;
  final DateTime? latestCollectedAt;
  int get nullRateTotal => nullWinRate + nullHighRate + nullHigh3Rate;
  factory StatisticsQuality.fromJson(Map<String, dynamic> json) =>
      StatisticsQuality(
        missingName: json['missing_name_count'] as int,
        missingPeriod: json['missing_period_number_count'] as int,
        unknownGrade: json['unknown_grade_count'] as int,
        duplicates: json['provisional_duplicate_count'] as int,
        invalidRunCount: json['invalid_or_null_run_count'] as int,
        nullWinRate: json['null_win_rate_count'] as int,
        nullHighRate: json['null_high_rate_count'] as int,
        nullHigh3Rate: json['null_high_3_rate_count'] as int,
        latestCollectedAt: _date(json['latest_collected_at']),
      );
}

class MatchCoverage {
  const MatchCoverage(
      this.total, this.unique, this.unmatched, this.multiple, this.rate);
  final int total, unique, unmatched, multiple;
  final double rate;
  factory MatchCoverage.fromJson(Map<String, dynamic> json) => MatchCoverage(
      json['total_statistics'] as int,
      json['unique_candidate_count'] as int,
      json['unmatched_count'] as int,
      json['multiple_candidate_count'] as int,
      (json['unique_candidate_rate'] as num).toDouble());
}

class DataQualityFilters {
  const DataQualityFilters({this.year, this.source});
  final String? year;
  final String? source;
  Map<String, String> toQuery() => {
        if (year != null && year!.trim().isNotEmpty) 'year': year!.trim(),
        if (source != null && source!.trim().isNotEmpty)
          'source': source!.trim(),
      };
}

DateTime? _date(dynamic value) =>
    value is String && value.isNotEmpty ? DateTime.parse(value) : null;
