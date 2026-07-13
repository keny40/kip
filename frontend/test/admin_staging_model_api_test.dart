import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

import 'package:kip_frontend/models/external_player_admin.dart';
import 'package:kip_frontend/services/api_client.dart';

void main() {
  test('external player JSON preserves string IDs and nullable fields', () {
    final player = ExternalPlayerAdmin.fromJson(_externalPlayerJson());
    expect(player.externalId, '00120034');
    expect(player.externalId, isA<String>());
    expect(player.periodNumber, '06');
    expect(player.sourceUpdatedAt, isNull);
  });

  test('statistics JSON preserves null, explicit zero, and rate values', () {
    final statistic = ExternalPlayerStatisticAdmin.fromJson(_statisticJson());
    expect(statistic.runCount, 0);
    expect(statistic.runDayCount, isNull);
    expect(statistic.rankCounts[0], isNull);
    expect(statistic.rankCounts[1], 0);
    expect(statistic.winRate, 0);
    expect(statistic.highRate, 25.5);
  });

  test('statistics JSON parses decimal strings returned by the API', () {
    final payload = _statisticJson()
      ..['win_rate'] = '2.000'
      ..['high_rate'] = '11.000'
      ..['high_3_rate'] = '26.000';

    final statistic = ExternalPlayerStatisticAdmin.fromJson(payload);

    expect(statistic.winRate, 2);
    expect(statistic.highRate, 11);
    expect(statistic.high3Rate, 26);
  });

  test('all match statuses have Korean labels', () {
    const expected = {
      'UNIQUE_CANDIDATE': '유일 후보',
      'NO_CANDIDATE': '후보 없음',
      'MULTIPLE_CANDIDATES': '복수 후보',
      'MISSING_PERIOD_NUMBER': '기수 미확인',
      'GRADE_MISMATCH': '등급 불일치',
    };
    for (final entry in expected.entries) {
      final item =
          PlayerMatchCandidateAdmin.fromJson(_candidateJson(entry.key));
      expect(item.statusLabel, entry.value);
      expect(item.candidateCount, 1);
    }
  });

  test('filter query builders omit blanks and preserve strings', () {
    final external = const ExternalPlayerFilters(
      source: 'kcycle',
      name: '홍',
      periodNumber: '06',
      grade: '',
      status: 'active',
    ).toQuery(page: 2, pageSize: 50);
    expect(external, {
      'page': '2',
      'page_size': '50',
      'source': 'kcycle',
      'name': '홍',
      'period_number': '06',
      'status': 'active',
    });

    final stats = const ExternalPlayerStatisticFilters(
      year: '2025',
      racerName: '김',
      periodNumber: '0',
      grade: 'A1',
    ).toQuery(page: 1, pageSize: 20);
    expect(stats['period_number'], '0');

    final matches = const PlayerMatchCandidateFilters(
      year: '2025',
      racerName: '박',
      periodNumber: '29',
      grade: 'S1',
      matchStatus: 'UNIQUE_CANDIDATE',
    ).toQuery(limit: 10);
    expect(matches['match_status'], 'UNIQUE_CANDIDATE');
    expect(matches['limit'], '10');
  });

  test('admin API requests include JWT and map actual response shapes',
      () async {
    final client = _RecordingClient((request) async {
      expect(request.headers['Authorization'], 'Bearer admin-token');
      if (request.url.path.endsWith('/external-players')) {
        expect(request.url.queryParameters['source'], 'kcycle');
        return _jsonResponse({
          'items': [_externalPlayerJson()],
          'meta': _metaJson()
        });
      }
      if (request.url.path.endsWith('/external-player-statistics')) {
        expect(request.url.queryParameters['year'], '2025');
        return _jsonResponse({
          'items': [_statisticJson()],
          'meta': _metaJson()
        });
      }
      expect(request.url.path.endsWith('/player-match-candidates'), isTrue);
      expect(request.url.queryParameters['match_status'], 'NO_CANDIDATE');
      return _jsonResponse([_candidateJson('NO_CANDIDATE')]);
    });
    final api = ApiClient(
      client: client,
      baseUrl: 'http://localhost:8000',
      bearerToken: 'admin-token',
    );
    final players = await api.fetchAdminExternalPlayers(
      filters: const ExternalPlayerFilters(source: 'kcycle'),
    );
    final stats = await api.fetchAdminExternalPlayerStatistics(
      filters: const ExternalPlayerStatisticFilters(year: '2025'),
    );
    final candidates = await api.fetchAdminPlayerMatchCandidates(
      filters: const PlayerMatchCandidateFilters(matchStatus: 'NO_CANDIDATE'),
    );
    expect(players.meta.total, 1);
    expect(stats.items.single.runCount, 0);
    expect(candidates.single.statusLabel, '후보 없음');
  });
}

Map<String, dynamic> _externalPlayerJson() => {
      'id': 1,
      'source': 'kcycle',
      'external_id': '00120034',
      'name': '테스트 선수',
      'period_number': '06',
      'grade': 'A1',
      'region': 'unknown',
      'status': 'active',
      'detail_url': 'https://www.kcycle.or.kr/racer/info/00120034',
      'source_updated_at': null,
      'collected_at': '2026-07-13T00:00:00Z',
      'created_at': '2026-07-13T00:00:00Z',
      'updated_at': '2026-07-13T00:00:00Z',
    };

Map<String, dynamic> _statisticJson() => {
      'id': 1,
      'source': 'data_go',
      'standard_year': '2025',
      'racer_name': '테스트 선수',
      'period_number': '06',
      'grade': 'A1',
      'run_count': 0,
      'run_day_count': null,
      'rank1_count': null,
      'rank2_count': 0,
      'rank3_count': 3,
      'rank4_count': null,
      'rank5_count': null,
      'rank6_count': null,
      'rank7_count': null,
      'rank8_count': null,
      'rank9_count': null,
      'eliminated_count': null,
      'win_rate': 0,
      'high_rate': 25.5,
      'high_3_rate': null,
      'collected_at': '2026-07-13T00:00:00Z',
      'created_at': '2026-07-13T00:00:00Z',
      'updated_at': '2026-07-13T00:00:00Z',
    };

Map<String, dynamic> _candidateJson(String status) => {
      'statistic_id': 1,
      'standard_year': '2025',
      'masked_racer_name': '테***',
      'period_number': '06',
      'statistic_grade': 'A1',
      'candidate_count': 1,
      'match_status': status,
      'masked_external_id': '0012****',
      'external_grade': 'A1',
      'grade_matches': true,
    };

Map<String, dynamic> _metaJson() => {'page': 1, 'page_size': 20, 'total': 1};

http.StreamedResponse _jsonResponse(Object body, {int status = 200}) =>
    http.StreamedResponse(
      Stream.value(utf8.encode(jsonEncode(body))),
      status,
      headers: {'content-type': 'application/json'},
    );

class _RecordingClient extends http.BaseClient {
  _RecordingClient(this.onSend);
  final Future<http.StreamedResponse> Function(http.BaseRequest request) onSend;
  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) =>
      onSend(request);
}
