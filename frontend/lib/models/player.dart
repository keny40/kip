class PlayerSummary {
  const PlayerSummary({
    required this.id,
    required this.name,
    required this.playerNumber,
    required this.grade,
    required this.region,
    required this.status,
  });

  final int id;
  final String name;
  final int playerNumber;
  final String grade;
  final String region;
  final String status;

  factory PlayerSummary.fromJson(Map<String, dynamic> json) {
    return PlayerSummary(
      id: json['id'] as int,
      name: json['name'] as String,
      playerNumber: json['player_number'] as int,
      grade: json['grade'] as String,
      region: json['region'] as String,
      status: json['status'] as String,
    );
  }
}

class PlayerHistoryItem {
  const PlayerHistoryItem({
    required this.raceId,
    required this.raceDate,
    required this.trackName,
    required this.raceNumber,
    required this.scheduledStartTime,
    required this.resultStatus,
    required this.finishPosition,
    required this.finishTime,
    required this.points,
  });

  final int raceId;
  final String raceDate;
  final String trackName;
  final int raceNumber;
  final String scheduledStartTime;
  final String resultStatus;
  final int? finishPosition;
  final String? finishTime;
  final int? points;

  factory PlayerHistoryItem.fromJson(Map<String, dynamic> json) {
    return PlayerHistoryItem(
      raceId: json['race_id'] as int,
      raceDate: json['race_date'] as String,
      trackName: json['track_name'] as String,
      raceNumber: json['race_number'] as int,
      scheduledStartTime: json['scheduled_start_time'] as String,
      resultStatus: json['result_status'] as String,
      finishPosition: json['finish_position'] as int?,
      finishTime: json['finish_time'] as String?,
      points: json['points'] as int?,
    );
  }
}

class PlayerDetail extends PlayerSummary {
  const PlayerDetail({
    required super.id,
    required super.name,
    required super.playerNumber,
    required super.grade,
    required super.region,
    required super.status,
    required this.history,
  });

  final List<PlayerHistoryItem> history;

  factory PlayerDetail.fromJson(Map<String, dynamic> json) {
    return PlayerDetail(
      id: json['id'] as int,
      name: json['name'] as String,
      playerNumber: json['player_number'] as int,
      grade: json['grade'] as String,
      region: json['region'] as String,
      status: json['status'] as String,
      history: (json['history'] as List<dynamic>)
          .map((item) => PlayerHistoryItem.fromJson(item as Map<String, dynamic>))
          .toList(),
    );
  }
}

class PlayerRaceHistoryResponse {
  const PlayerRaceHistoryResponse({
    required this.playerId,
    required this.playerName,
    required this.playerNumber,
    required this.grade,
    required this.region,
    required this.history,
  });

  final int playerId;
  final String playerName;
  final int playerNumber;
  final String grade;
  final String region;
  final List<PlayerHistoryItem> history;

  factory PlayerRaceHistoryResponse.fromJson(Map<String, dynamic> json) {
    return PlayerRaceHistoryResponse(
      playerId: json['player_id'] as int,
      playerName: json['player_name'] as String,
      playerNumber: json['player_number'] as int,
      grade: json['grade'] as String,
      region: json['region'] as String,
      history: (json['history'] as List<dynamic>)
          .map((item) => PlayerHistoryItem.fromJson(item as Map<String, dynamic>))
          .toList(),
    );
  }
}
