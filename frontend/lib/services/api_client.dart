import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../models/analytics.dart';
import '../models/player.dart';
import '../models/player_statistics.dart';
import '../models/race.dart';
import '../models/track.dart';

class ApiException implements Exception {
  ApiException(this.message);

  final String message;

  @override
  String toString() => message;
}

class ApiClient {
  ApiClient({http.Client? client, String? baseUrl})
      : _client = client ?? http.Client(),
        _baseUrl = baseUrl ?? AppConfig.apiBaseUrl;

  final http.Client _client;
  final String _baseUrl;

  Uri _uri(String path, [Map<String, String>? query]) {
    return Uri.parse('$_baseUrl$path').replace(queryParameters: query);
  }

  Future<List<RaceSummary>> fetchTodayRaces() async {
    final today = DateTime.now().toIso8601String().split('T').first;
    final response = await _client.get(
      _uri('/api/v1/races', {
        'race_date': today,
        'page': '1',
        'page_size': '20',
      }),
      headers: {'Accept': 'application/json'},
    );
    return _parseRaceList(response);
  }

  Future<List<Track>> fetchTracks() async {
    final response = await _client.get(
      _uri('/api/v1/tracks'),
      headers: {'Accept': 'application/json'},
    );
    if (response.statusCode == 200) {
      final payload = jsonDecode(response.body) as List<dynamic>;
      return payload.map((item) => Track.fromJson(item as Map<String, dynamic>)).toList();
    }
    throw ApiException(_messageFromResponse(response));
  }

  Future<Track> fetchTrack(int trackId) async {
    final response = await _client.get(
      _uri('/api/v1/tracks/$trackId'),
      headers: {'Accept': 'application/json'},
    );
    if (response.statusCode == 200) {
      return Track.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
    }
    throw ApiException(_messageFromResponse(response));
  }

  Future<TrackAnalyticsSummary> fetchTrackSummary(int trackId) async {
    final response = await _client.get(
      _uri('/api/v1/analytics/tracks/$trackId/summary'),
      headers: {'Accept': 'application/json'},
    );
    if (response.statusCode == 200) {
      return TrackAnalyticsSummary.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
    }
    throw ApiException(_messageFromResponse(response));
  }

  Future<List<TrackPlayerStat>> fetchTrackPlayers(int trackId) async {
    final response = await _client.get(
      _uri('/api/v1/analytics/tracks/$trackId/players'),
      headers: {'Accept': 'application/json'},
    );
    if (response.statusCode == 200) {
      final payload = jsonDecode(response.body) as List<dynamic>;
      return payload.map((item) => TrackPlayerStat.fromJson(item as Map<String, dynamic>)).toList();
    }
    throw ApiException(_messageFromResponse(response));
  }

  Future<AnalyticsDashboardSummary> fetchAnalyticsDashboard() async {
    final response = await _client.get(
      _uri('/api/v1/analytics/races/summary'),
      headers: {'Accept': 'application/json'},
    );
    if (response.statusCode == 200) {
      return AnalyticsDashboardSummary.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
    }
    throw ApiException(_messageFromResponse(response));
  }

  Future<RaceDetail> fetchRaceDetail(int raceId) async {
    final response = await _client.get(
      _uri('/api/v1/races/$raceId'),
      headers: {'Accept': 'application/json'},
    );
    if (response.statusCode == 200) {
      return RaceDetail.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
    }
    throw ApiException(_messageFromResponse(response));
  }

  Future<List<PlayerSummary>> fetchPlayers() async {
    final response = await _client.get(
      _uri('/api/v1/players', {'page': '1', 'page_size': '100'}),
      headers: {'Accept': 'application/json'},
    );
    if (response.statusCode == 200) {
      final payload = jsonDecode(response.body) as Map<String, dynamic>;
      final items = payload['items'] as List<dynamic>;
      return items.map((item) => PlayerSummary.fromJson(item as Map<String, dynamic>)).toList();
    }
    throw ApiException(_messageFromResponse(response));
  }

  Future<PlayerDetail> fetchPlayer(int playerId) async {
    final response = await _client.get(
      _uri('/api/v1/players/$playerId'),
      headers: {'Accept': 'application/json'},
    );
    if (response.statusCode == 200) {
      return PlayerDetail.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
    }
    throw ApiException(_messageFromResponse(response));
  }

  Future<PlayerRaceHistoryResponse> fetchPlayerRaceHistory(int playerId) async {
    final response = await _client.get(
      _uri('/api/v1/players/$playerId/race-history'),
      headers: {'Accept': 'application/json'},
    );
    if (response.statusCode == 200) {
      return PlayerRaceHistoryResponse.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
    }
    throw ApiException(_messageFromResponse(response));
  }

  Future<PlayerStatisticsResponse> fetchPlayerStatistics(
    int playerId, {
    int? trackId,
    DateTime? dateFrom,
    DateTime? dateTo,
    int? lastN,
    String? grade,
  }) async {
    final query = <String, String>{};
    if (trackId != null) {
      query['track_id'] = trackId.toString();
    }
    if (dateFrom != null) {
      query['date_from'] = dateFrom.toIso8601String().split('T').first;
    }
    if (dateTo != null) {
      query['date_to'] = dateTo.toIso8601String().split('T').first;
    }
    if (lastN != null) {
      query['last_n'] = lastN.toString();
    }
    if (grade != null && grade.isNotEmpty) {
      query['grade'] = grade;
    }
    final response = await _client.get(
      _uri('/api/v1/players/$playerId/statistics', query.isEmpty ? null : query),
      headers: {'Accept': 'application/json'},
    );
    if (response.statusCode == 200) {
      return PlayerStatisticsResponse.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
    }
    throw ApiException(_messageFromResponse(response));
  }

  List<RaceSummary> _parseRaceList(http.Response response) {
    if (response.statusCode == 200) {
      final payload = jsonDecode(response.body) as Map<String, dynamic>;
      final items = payload['items'] as List<dynamic>;
      return items.map((item) => RaceSummary.fromJson(item as Map<String, dynamic>)).toList();
    }
    throw ApiException(_messageFromResponse(response));
  }

  String _messageFromResponse(http.Response response) {
    try {
      final payload = jsonDecode(response.body) as Map<String, dynamic>;
      final detail = payload['detail'];
      if (detail is String) {
        return detail;
      }
    } catch (_) {
      // Fall back to raw status text below.
    }
    return 'Request failed with status ${response.statusCode}';
  }
}
