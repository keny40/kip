class EntryModel {
  const EntryModel({
    required this.id,
    required this.entryNumber,
    required this.laneNumber,
    required this.lineupPosition,
    required this.status,
    required this.playerNumber,
    required this.playerName,
    required this.grade,
    required this.region,
  });

  final int id;
  final int entryNumber;
  final int laneNumber;
  final int lineupPosition;
  final String status;
  final int playerNumber;
  final String playerName;
  final String grade;
  final String region;

  factory EntryModel.fromJson(Map<String, dynamic> json) {
    final player = json['player'] as Map<String, dynamic>;
    return EntryModel(
      id: json['id'] as int,
      entryNumber: json['entry_number'] as int,
      laneNumber: json['lane_number'] as int,
      lineupPosition: json['lineup_position'] as int,
      status: json['status'] as String,
      playerNumber: player['player_number'] as int,
      playerName: player['name'] as String,
      grade: player['grade'] as String,
      region: player['region'] as String,
    );
  }
}
