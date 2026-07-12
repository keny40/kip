class AnalyticsDashboardSummary {
  const AnalyticsDashboardSummary({
    required this.totalRaces,
    required this.scheduledRaces,
    required this.inProgressRaces,
    required this.completedRaces,
    required this.totalPlayers,
    required this.totalResults,
    required this.latestRaceDate,
    required this.trackCount,
  });

  final int totalRaces;
  final int scheduledRaces;
  final int inProgressRaces;
  final int completedRaces;
  final int totalPlayers;
  final int totalResults;
  final String? latestRaceDate;
  final int trackCount;

  factory AnalyticsDashboardSummary.fromJson(Map<String, dynamic> json) {
    return AnalyticsDashboardSummary(
      totalRaces: json['total_races'] as int,
      scheduledRaces: json['scheduled_races'] as int,
      inProgressRaces: json['in_progress_races'] as int,
      completedRaces: json['completed_races'] as int,
      totalPlayers: json['total_players'] as int,
      totalResults: json['total_results'] as int,
      latestRaceDate: json['latest_race_date'] as String?,
      trackCount: json['track_count'] as int,
    );
  }
}
