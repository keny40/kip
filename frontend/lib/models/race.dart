import 'entry.dart';

class ResultPlayer {
  const ResultPlayer({
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

  factory ResultPlayer.fromJson(Map<String, dynamic> json) {
    return ResultPlayer(
      id: json['id'] as int,
      name: json['name'] as String,
      playerNumber: json['player_number'] as int,
      grade: json['grade'] as String,
      region: json['region'] as String,
      status: json['status'] as String,
    );
  }
}

class RaceResult {
  const RaceResult({
    required this.id,
    required this.raceId,
    required this.playerId,
    required this.raceDate,
    required this.trackName,
    required this.raceNumber,
    required this.scheduledStartTime,
    required this.raceStatus,
    required this.finishPosition,
    required this.finishTime,
    required this.resultStatus,
    required this.points,
    required this.player,
  });

  final int id;
  final int raceId;
  final int playerId;
  final String raceDate;
  final String trackName;
  final int raceNumber;
  final String scheduledStartTime;
  final String raceStatus;
  final int finishPosition;
  final String? finishTime;
  final String resultStatus;
  final int? points;
  final ResultPlayer player;

  factory RaceResult.fromJson(Map<String, dynamic> json) {
    return RaceResult(
      id: json['id'] as int,
      raceId: json['race_id'] as int,
      playerId: json['player_id'] as int,
      raceDate: (json['race'] as Map<String, dynamic>)['race_date'] as String,
      trackName: (json['race'] as Map<String, dynamic>)['track_name'] as String,
      raceNumber: (json['race'] as Map<String, dynamic>)['race_number'] as int,
      scheduledStartTime: (json['race'] as Map<String, dynamic>)['scheduled_start_time'] as String,
      raceStatus: (json['race'] as Map<String, dynamic>)['status'] as String,
      finishPosition: json['finish_position'] as int,
      finishTime: json['finish_time'] as String?,
      resultStatus: json['result_status'] as String,
      points: json['points'] as int?,
      player: ResultPlayer.fromJson(json['player'] as Map<String, dynamic>),
    );
  }
}

class RaceSummary {
  const RaceSummary({
    required this.id,
    required this.raceDate,
    required this.trackName,
    required this.raceNumber,
    required this.scheduledStartTime,
    required this.status,
  });

  final int id;
  final String raceDate;
  final String trackName;
  final int raceNumber;
  final String scheduledStartTime;
  final String status;

  factory RaceSummary.fromJson(Map<String, dynamic> json) {
    return RaceSummary(
      id: json['id'] as int,
      raceDate: json['race_date'] as String,
      trackName: json['track_name'] as String,
      raceNumber: json['race_number'] as int,
      scheduledStartTime: json['scheduled_start_time'] as String,
      status: json['status'] as String,
    );
  }
}

class RaceDetail extends RaceSummary {
  const RaceDetail({
    required super.id,
    required super.raceDate,
    required super.trackName,
    required super.raceNumber,
    required super.scheduledStartTime,
    required super.status,
    required this.entries,
    required this.results,
  });

  final List<EntryModel> entries;
  final List<RaceResult> results;

  factory RaceDetail.fromJson(Map<String, dynamic> json) {
    return RaceDetail(
      id: json['id'] as int,
      raceDate: json['race_date'] as String,
      trackName: json['track_name'] as String,
      raceNumber: json['race_number'] as int,
      scheduledStartTime: json['scheduled_start_time'] as String,
      status: json['status'] as String,
      entries: (json['entries'] as List<dynamic>)
          .map((item) => EntryModel.fromJson(item as Map<String, dynamic>))
          .toList(),
      results: (json['results'] as List<dynamic>)
          .map((item) => RaceResult.fromJson(item as Map<String, dynamic>))
          .toList(),
    );
  }
}
