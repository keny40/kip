import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:kip_frontend/models/current_user.dart';
import 'package:kip_frontend/models/data_quality_summary.dart';
import 'package:kip_frontend/screens/admin_data_quality_screen.dart';
import 'package:kip_frontend/services/api_client.dart';
import 'package:kip_frontend/services/auth_service.dart';

void main() {
  test('summary parses nullable dates, zeroes, rate and filter query', () {
    final summary = DataQualitySummary.fromJson(_json());
    expect(summary.externalPlayersQuality.latestCollectedAt, isNull);
    expect(summary.counts.externalPlayers, 0);
    expect(summary.coverage.rate, 30.0);
    expect(
        const DataQualityFilters(year: ' 2025 ', source: 'data_go').toQuery(),
        {'year': '2025', 'source': 'data_go'});
  });

  testWidgets('renders zeroes, rate, five statuses and no write actions',
      (tester) async {
    await tester.pumpWidget(_app(AdminDataQualityScreen(
      authService: _auth(),
      loader: (_) async => DataQualitySummary.fromJson(_json()),
    )));
    await tester.pumpAndSettle();
    expect(find.text('30.0%'), findsOneWidget);
    expect(find.text('미수집'), findsNothing);
    await tester.scrollUntilVisible(find.text('기수 미확인'), 300,
        scrollable: find.byType(Scrollable).first);
    for (final label in ['유일 후보', '후보 없음', '복수 후보', '기수 미확인', '등급 불일치']) {
      expect(find.text(label), findsWidgets);
    }
    expect(find.text('0'), findsWidgets);
    expect(find.text('수정'), findsNothing);
    expect(find.text('승인'), findsNothing);
    expect(find.text('재수집'), findsNothing);
  });

  testWidgets('shows uncollected date, handles errors and 401', (tester) async {
    final empty = _json()
      ..['external_players_quality'] = {
        ...(_json()['external_players_quality'] as Map<String, dynamic>),
        'latest_collected_at': null,
      }
      ..['statistics_quality'] = {
        ...(_json()['statistics_quality'] as Map<String, dynamic>),
        'latest_collected_at': null,
      };
    await tester.pumpWidget(_app(AdminDataQualityScreen(
        authService: _auth(),
        loader: (_) async => DataQualitySummary.fromJson(empty))));
    await tester.pumpAndSettle();
    expect(find.textContaining('미수집'), findsOneWidget);

    await tester.pumpWidget(_app(AdminDataQualityScreen(
        authService: _auth(),
        loader: (_) async => throw ApiException('hidden', statusCode: 500))));
    await tester.pumpAndSettle();
    expect(find.textContaining('서버 오류'), findsOneWidget);
    expect(find.textContaining('hidden'), findsNothing);

    final auth = _auth();
    await tester.pumpWidget(_app(
        AdminDataQualityScreen(
            authService: auth,
            loader: (_) async =>
                throw ApiException('expired', statusCode: 401)),
        login: true));
    await tester.pumpAndSettle();
    expect(find.text('로그인 화면'), findsOneWidget);
    expect(auth.currentUser, isNull);
  });

  testWidgets('card navigates and narrow screen has no overflow',
      (tester) async {
    await tester.binding.setSurfaceSize(const Size(390, 800));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(_app(
        AdminDataQualityScreen(
            authService: _auth(),
            loader: (_) async => DataQualitySummary.fromJson(_json())),
        routes: true));
    await tester.pumpAndSettle();
    await tester.tap(find.text('외부 선수').first);
    await tester.pumpAndSettle();
    expect(find.text('외부 선수 화면'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}

Widget _app(Widget home, {bool login = false, bool routes = false}) =>
    MaterialApp(
      key: UniqueKey(),
      home: home,
      routes: {
        if (login) '/admin/login': (_) => const Scaffold(body: Text('로그인 화면')),
        if (routes)
          '/admin/external-players': (_) =>
              const Scaffold(body: Text('외부 선수 화면')),
      },
    );

AuthService _auth() {
  final session = AuthSession()
    ..accessToken = 'token'
    ..currentUser = CurrentUser(
        id: 1,
        email: 'a@b.c',
        username: 'admin',
        role: 'admin',
        status: 'active',
        createdAt: DateTime(2026),
        updatedAt: DateTime(2026));
  return AuthService(session: session);
}

Map<String, dynamic> _json() => {
      'counts': {
        'players_count': 13,
        'external_players_count': 0,
        'external_player_statistics_count': 10
      },
      'external_players_quality': {
        'missing_name_count': 0,
        'missing_period_number_count': 0,
        'unknown_grade_count': 0,
        'unknown_region_count': 2,
        'unknown_status_count': 3,
        'duplicate_source_external_id_count': 0,
        'latest_collected_at': null
      },
      'statistics_quality': {
        'missing_name_count': 0,
        'missing_period_number_count': 1,
        'unknown_grade_count': 1,
        'provisional_duplicate_count': 0,
        'invalid_or_null_run_count': 1,
        'null_win_rate_count': 1,
        'null_high_rate_count': 0,
        'null_high_3_rate_count': 0,
        'latest_collected_at': '2026-07-13T00:00:00Z'
      },
      'match_status_counts': {
        'UNIQUE_CANDIDATE': 3,
        'NO_CANDIDATE': 4,
        'MULTIPLE_CANDIDATES': 1,
        'MISSING_PERIOD_NUMBER': 1,
        'GRADE_MISMATCH': 1
      },
      'coverage': {
        'total_statistics': 10,
        'unique_candidate_count': 3,
        'unmatched_count': 6,
        'multiple_candidate_count': 1,
        'unique_candidate_rate': 30.0
      },
    };
