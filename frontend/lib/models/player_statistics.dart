import 'race.dart';

class PlayerStatistics {
  const PlayerStatistics({
    required this.totalRaces,
    required this.finishedCount,
    required this.firstPlaceCount,
    required this.secondPlaceCount,
    required this.thirdPlaceCount,
    required this.winRate,
    required this.placeRate,
    required this.dnfCount,
    required this.currentStreak,
    required this.recentFiveResults,
  });

  final int totalRaces;
  final int finishedCount;
  final int firstPlaceCount;
  final int secondPlaceCount;
  final int thirdPlaceCount;
  final double winRate;
  final double placeRate;
  final int dnfCount;
  final int currentStreak;
  final List<RaceResult> recentFiveResults;

  factory PlayerStatistics.fromJson(Map<String, dynamic> json) {
    return PlayerStatistics(
      totalRaces: json['total_races'] as int,
      finishedCount: json['finished_count'] as int,
      firstPlaceCount: json['first_place_count'] as int,
      secondPlaceCount: json['second_place_count'] as int,
      thirdPlaceCount: json['third_place_count'] as int,
      winRate: (json['win_rate'] as num).toDouble(),
      placeRate: (json['place_rate'] as num).toDouble(),
      dnfCount: json['dnf_count'] as int,
      currentStreak: json['current_streak'] as int,
      recentFiveResults: (json['recent_five_results'] as List<dynamic>)
          .map((item) => RaceResult.fromJson(item as Map<String, dynamic>))
          .toList(),
    );
  }
}

class PlayerStatisticsFilters {
  const PlayerStatisticsFilters({
    required this.trackId,
    required this.dateFrom,
    required this.dateTo,
    required this.lastN,
    required this.grade,
  });

  final int? trackId;
  final String? dateFrom;
  final String? dateTo;
  final int? lastN;
  final String? grade;

  factory PlayerStatisticsFilters.fromJson(Map<String, dynamic> json) {
    return PlayerStatisticsFilters(
      trackId: json['track_id'] as int?,
      dateFrom: json['date_from'] as String?,
      dateTo: json['date_to'] as String?,
      lastN: json['last_n'] as int?,
      grade: json['grade'] as String?,
    );
  }
}

class PlayerStatisticsResponse {
  const PlayerStatisticsResponse({required this.filters, required this.statistics});

  final PlayerStatisticsFilters filters;
  final PlayerStatistics statistics;

  factory PlayerStatisticsResponse.fromJson(Map<String, dynamic> json) {
    return PlayerStatisticsResponse(
      filters: PlayerStatisticsFilters.fromJson(json['filters'] as Map<String, dynamic>),
      statistics: PlayerStatistics.fromJson(json['statistics'] as Map<String, dynamic>),
    );
  }
}
