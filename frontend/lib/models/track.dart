class Track {
  const Track({
    required this.id,
    required this.code,
    required this.name,
    required this.region,
    required this.address,
    required this.status,
  });

  final int id;
  final String code;
  final String name;
  final String region;
  final String? address;
  final String status;

  factory Track.fromJson(Map<String, dynamic> json) {
    return Track(
      id: json['id'] as int,
      code: json['code'] as String,
      name: json['name'] as String,
      region: json['region'] as String,
      address: json['address'] as String?,
      status: json['status'] as String,
    );
  }
}

class TrackRaceSummary {
  const TrackRaceSummary({
    required this.raceId,
    required this.raceDate,
    required this.trackName,
    required this.raceNumber,
    required this.status,
  });

  final int raceId;
  final String raceDate;
  final String trackName;
  final int raceNumber;
  final String status;

  factory TrackRaceSummary.fromJson(Map<String, dynamic> json) {
    return TrackRaceSummary(
      raceId: json['race_id'] as int,
      raceDate: json['race_date'] as String,
      trackName: json['track_name'] as String,
      raceNumber: json['race_number'] as int,
      status: json['status'] as String,
    );
  }
}

class TrackAnalyticsSummary {
  const TrackAnalyticsSummary({
    required this.trackId,
    required this.trackName,
    required this.code,
    required this.region,
    required this.totalRaces,
    required this.completedRaces,
    required this.totalEntries,
    required this.uniquePlayers,
    required this.latestRaceDate,
    required this.raceStatusCounts,
    required this.gradeCounts,
    required this.recent30Races,
  });

  final int trackId;
  final String trackName;
  final String code;
  final String region;
  final int totalRaces;
  final int completedRaces;
  final int totalEntries;
  final int uniquePlayers;
  final String? latestRaceDate;
  final Map<String, int> raceStatusCounts;
  final Map<String, int> gradeCounts;
  final List<TrackRaceSummary> recent30Races;

  factory TrackAnalyticsSummary.fromJson(Map<String, dynamic> json) {
    return TrackAnalyticsSummary(
      trackId: json['track_id'] as int,
      trackName: json['track_name'] as String,
      code: json['code'] as String,
      region: json['region'] as String,
      totalRaces: json['total_races'] as int,
      completedRaces: json['completed_races'] as int,
      totalEntries: json['total_entries'] as int,
      uniquePlayers: json['unique_players'] as int,
      latestRaceDate: json['latest_race_date'] as String?,
      raceStatusCounts: Map<String, int>.from(json['race_status_counts'] as Map),
      gradeCounts: Map<String, int>.from(json['grade_counts'] as Map),
      recent30Races: (json['recent_30_races'] as List<dynamic>)
          .map((item) => TrackRaceSummary.fromJson(item as Map<String, dynamic>))
          .toList(),
    );
  }
}

class TrackPlayerStat {
  const TrackPlayerStat({
    required this.playerId,
    required this.playerNumber,
    required this.name,
    required this.grade,
    required this.starts,
    required this.wins,
    required this.top2,
    required this.top3,
    required this.winRate,
    required this.top2Rate,
    required this.top3Rate,
    required this.disqualifiedCount,
    required this.withdrawnCount,
  });

  final int playerId;
  final int playerNumber;
  final String name;
  final String grade;
  final int starts;
  final int wins;
  final int top2;
  final int top3;
  final double winRate;
  final double top2Rate;
  final double top3Rate;
  final int disqualifiedCount;
  final int withdrawnCount;

  factory TrackPlayerStat.fromJson(Map<String, dynamic> json) {
    return TrackPlayerStat(
      playerId: json['player_id'] as int,
      playerNumber: json['player_number'] as int,
      name: json['name'] as String,
      grade: json['grade'] as String,
      starts: json['starts'] as int,
      wins: json['wins'] as int,
      top2: json['top2'] as int,
      top3: json['top3'] as int,
      winRate: (json['win_rate'] as num).toDouble(),
      top2Rate: (json['top2_rate'] as num).toDouble(),
      top3Rate: (json['top3_rate'] as num).toDouble(),
      disqualifiedCount: json['disqualified_count'] as int,
      withdrawnCount: json['withdrawn_count'] as int,
    );
  }
}
