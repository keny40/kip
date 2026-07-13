import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

import '../config/app_config.dart';
import '../models/admin_import.dart';
import '../models/external_player_admin.dart';
import '../models/analytics.dart';
import '../models/player.dart';
import '../models/player_statistics.dart';
import '../models/race.dart';
import '../models/track.dart';

class ApiException implements Exception {
  ApiException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;

  @override
  String toString() => message;
}

class ApiClient {
  ApiClient({http.Client? client, String? baseUrl, String? bearerToken})
      : _client = client ?? http.Client(),
        _baseUrl = baseUrl ?? AppConfig.apiBaseUrl,
        _bearerToken = bearerToken;

  final http.Client _client;
  final String _baseUrl;
  String? _bearerToken;

  set bearerToken(String? value) {
    _bearerToken = value;
  }

  Uri _uri(String path, [Map<String, String>? query]) {
    return Uri.parse('$_baseUrl$path').replace(queryParameters: query);
  }

  Map<String, String> buildHeaders({bool authenticated = false}) {
    final headers = <String, String>{'Accept': 'application/json'};
    final token = authenticated ? _bearerToken : null;
    if (token != null && token.isNotEmpty) {
      headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }

  Future<List<RaceSummary>> fetchTodayRaces() async {
    final today = DateTime.now().toIso8601String().split('T').first;
    final response = await _client.get(
      _uri('/api/v1/races', {
        'race_date': today,
        'page': '1',
        'page_size': '20',
      }),
      headers: buildHeaders(),
    );
    return _parseRaceList(response);
  }

  Future<List<Track>> fetchTracks() async {
    final response = await _client.get(
      _uri('/api/v1/tracks'),
      headers: buildHeaders(),
    );
    if (response.statusCode == 200) {
      final payload = jsonDecode(response.body) as List<dynamic>;
      return payload
          .map((item) => Track.fromJson(item as Map<String, dynamic>))
          .toList();
    }
    throw ApiException(_messageFromResponse(response));
  }

  Future<Track> fetchTrack(int trackId) async {
    final response = await _client.get(
      _uri('/api/v1/tracks/$trackId'),
      headers: buildHeaders(),
    );
    if (response.statusCode == 200) {
      return Track.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
    }
    throw ApiException(_messageFromResponse(response));
  }

  Future<TrackAnalyticsSummary> fetchTrackSummary(int trackId) async {
    final response = await _client.get(
      _uri('/api/v1/analytics/tracks/$trackId/summary'),
      headers: buildHeaders(),
    );
    if (response.statusCode == 200) {
      return TrackAnalyticsSummary.fromJson(
          jsonDecode(response.body) as Map<String, dynamic>);
    }
    throw ApiException(_messageFromResponse(response));
  }

  Future<List<TrackPlayerStat>> fetchTrackPlayers(int trackId) async {
    final response = await _client.get(
      _uri('/api/v1/analytics/tracks/$trackId/players'),
      headers: buildHeaders(),
    );
    if (response.statusCode == 200) {
      final payload = jsonDecode(response.body) as List<dynamic>;
      return payload
          .map((item) => TrackPlayerStat.fromJson(item as Map<String, dynamic>))
          .toList();
    }
    throw ApiException(_messageFromResponse(response));
  }

  Future<AnalyticsDashboardSummary> fetchAnalyticsDashboard() async {
    final response = await _client.get(
      _uri('/api/v1/analytics/races/summary'),
      headers: buildHeaders(),
    );
    if (response.statusCode == 200) {
      return AnalyticsDashboardSummary.fromJson(
          jsonDecode(response.body) as Map<String, dynamic>);
    }
    throw ApiException(_messageFromResponse(response));
  }

  Future<RaceDetail> fetchRaceDetail(int raceId) async {
    final response = await _client.get(
      _uri('/api/v1/races/$raceId'),
      headers: buildHeaders(),
    );
    if (response.statusCode == 200) {
      return RaceDetail.fromJson(
          jsonDecode(response.body) as Map<String, dynamic>);
    }
    throw ApiException(_messageFromResponse(response));
  }

  Future<List<PlayerSummary>> fetchPlayers() async {
    final response = await _client.get(
      _uri('/api/v1/players', {'page': '1', 'page_size': '100'}),
      headers: buildHeaders(),
    );
    if (response.statusCode == 200) {
      final payload = jsonDecode(response.body) as Map<String, dynamic>;
      final items = payload['items'] as List<dynamic>;
      return items
          .map((item) => PlayerSummary.fromJson(item as Map<String, dynamic>))
          .toList();
    }
    throw ApiException(_messageFromResponse(response));
  }

  Future<PlayerDetail> fetchPlayer(int playerId) async {
    final response = await _client.get(
      _uri('/api/v1/players/$playerId'),
      headers: buildHeaders(),
    );
    if (response.statusCode == 200) {
      return PlayerDetail.fromJson(
          jsonDecode(response.body) as Map<String, dynamic>);
    }
    throw ApiException(_messageFromResponse(response));
  }

  Future<PlayerRaceHistoryResponse> fetchPlayerRaceHistory(int playerId) async {
    final response = await _client.get(
      _uri('/api/v1/players/$playerId/race-history'),
      headers: buildHeaders(),
    );
    if (response.statusCode == 200) {
      return PlayerRaceHistoryResponse.fromJson(
          jsonDecode(response.body) as Map<String, dynamic>);
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
      _uri(
          '/api/v1/players/$playerId/statistics', query.isEmpty ? null : query),
      headers: buildHeaders(),
    );
    if (response.statusCode == 200) {
      return PlayerStatisticsResponse.fromJson(
          jsonDecode(response.body) as Map<String, dynamic>);
    }
    throw ApiException(_messageFromResponse(response));
  }

  Future<AdminImportResult> importAdminCsv({
    required String importType,
    required List<int> bytes,
    required String filename,
    required bool dryRun,
  }) async {
    final request = http.MultipartRequest(
      'POST',
      _uri(
        '/api/v1/admin/imports/$importType',
        dryRun ? {'dry_run': 'true'} : null,
      ),
    );
    request.headers.addAll(buildHeaders(authenticated: true));
    request.files.add(
      http.MultipartFile.fromBytes(
        'file',
        bytes,
        filename: filename,
        contentType: MediaType('text', 'csv'),
      ),
    );

    late final http.StreamedResponse streamedResponse;
    try {
      streamedResponse = await _client.send(request);
    } on http.ClientException {
      throw ApiException('Request failed');
    }

    final response = await http.Response.fromStream(streamedResponse);
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return AdminImportResult.fromJson(
          jsonDecode(response.body) as Map<String, dynamic>);
    }
    throw ApiException(_messageFromResponse(response),
        statusCode: response.statusCode);
  }

  Future<ExternalPlayerPage> fetchAdminExternalPlayers({
    required ExternalPlayerFilters filters,
    int page = 1,
    int pageSize = 20,
  }) async {
    final response = await _client.get(
      _uri('/api/v1/admin/external-players',
          filters.toQuery(page: page, pageSize: pageSize)),
      headers: buildHeaders(authenticated: true),
    );
    if (response.statusCode == 200) {
      return ExternalPlayerPage.fromJson(
          jsonDecode(response.body) as Map<String, dynamic>);
    }
    throw ApiException(_messageFromResponse(response),
        statusCode: response.statusCode);
  }

  Future<ExternalPlayerAdmin> fetchAdminExternalPlayer(int id) async {
    final response = await _client.get(
      _uri('/api/v1/admin/external-players/$id'),
      headers: buildHeaders(authenticated: true),
    );
    if (response.statusCode == 200) {
      return ExternalPlayerAdmin.fromJson(
          jsonDecode(response.body) as Map<String, dynamic>);
    }
    throw ApiException(_messageFromResponse(response),
        statusCode: response.statusCode);
  }

  Future<ExternalPlayerStatisticPage> fetchAdminExternalPlayerStatistics({
    required ExternalPlayerStatisticFilters filters,
    int page = 1,
    int pageSize = 20,
  }) async {
    final response = await _client.get(
      _uri('/api/v1/admin/external-player-statistics',
          filters.toQuery(page: page, pageSize: pageSize)),
      headers: buildHeaders(authenticated: true),
    );
    if (response.statusCode == 200) {
      return ExternalPlayerStatisticPage.fromJson(
          jsonDecode(response.body) as Map<String, dynamic>);
    }
    throw ApiException(_messageFromResponse(response),
        statusCode: response.statusCode);
  }

  Future<ExternalPlayerStatisticAdmin> fetchAdminExternalPlayerStatistic(
      int id) async {
    final response = await _client.get(
      _uri('/api/v1/admin/external-player-statistics/$id'),
      headers: buildHeaders(authenticated: true),
    );
    if (response.statusCode == 200) {
      return ExternalPlayerStatisticAdmin.fromJson(
          jsonDecode(response.body) as Map<String, dynamic>);
    }
    throw ApiException(_messageFromResponse(response),
        statusCode: response.statusCode);
  }

  Future<List<PlayerMatchCandidateAdmin>> fetchAdminPlayerMatchCandidates({
    required PlayerMatchCandidateFilters filters,
    int limit = 100,
  }) async {
    final response = await _client.get(
      _uri('/api/v1/admin/player-match-candidates',
          filters.toQuery(limit: limit)),
      headers: buildHeaders(authenticated: true),
    );
    if (response.statusCode == 200) {
      final payload = jsonDecode(response.body) as List<dynamic>;
      return payload
          .map((item) =>
              PlayerMatchCandidateAdmin.fromJson(item as Map<String, dynamic>))
          .toList();
    }
    throw ApiException(_messageFromResponse(response),
        statusCode: response.statusCode);
  }

  List<RaceSummary> _parseRaceList(http.Response response) {
    if (response.statusCode == 200) {
      final payload = jsonDecode(response.body) as Map<String, dynamic>;
      final items = payload['items'] as List<dynamic>;
      return items
          .map((item) => RaceSummary.fromJson(item as Map<String, dynamic>))
          .toList();
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
