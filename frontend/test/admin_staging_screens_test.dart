import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:kip_frontend/models/current_user.dart';
import 'package:kip_frontend/models/external_player_admin.dart';
import 'package:kip_frontend/screens/admin_external_player_statistics_screen.dart';
import 'package:kip_frontend/screens/admin_external_players_screen.dart';
import 'package:kip_frontend/screens/admin_player_match_candidates_screen.dart';
import 'package:kip_frontend/services/api_client.dart';
import 'package:kip_frontend/services/auth_service.dart';

void main() {
  testWidgets('external player list renders, filters, and opens detail',
      (tester) async {
    ExternalPlayerFilters? captured;
    var openedUrl = '';
    final player = _externalPlayer();
    await tester.pumpWidget(_app(
      AdminExternalPlayersScreen(
        authService: _auth(),
        loader: (filters, page, pageSize) async {
          captured = filters;
          return ExternalPlayerPage(
            items: [player],
            meta: const AdminPaginationMeta(page: 1, pageSize: 20, total: 1),
          );
        },
        detailLoader: (_) async => player,
        linkOpener: (url) => openedUrl = url,
      ),
    ));
    await tester.pumpAndSettle();
    expect(find.text('00120034'), findsOneWidget);
    expect(find.text('테스트 선수'), findsOneWidget);

    final fields = find.byType(TextField);
    await tester.enterText(fields.at(1), '검색명');
    await tester.tap(find.byKey(const Key('admin_filter_search')));
    await tester.pumpAndSettle();
    expect(captured!.name, '검색명');

    await tester.tap(find.text('00120034'));
    await tester.pumpAndSettle();
    expect(find.text('외부 선수 상세'), findsOneWidget);
    await tester.tap(find.byKey(const Key('external_player_detail_link')));
    expect(openedUrl, endsWith('00120034'));
  });

  testWidgets('external player handles empty and API errors', (tester) async {
    await tester.pumpWidget(_app(AdminExternalPlayersScreen(
      authService: _auth(),
      loader: (_, __, ___) async => const ExternalPlayerPage(
        items: [],
        meta: AdminPaginationMeta(page: 1, pageSize: 20, total: 0),
      ),
    )));
    await tester.pumpAndSettle();
    expect(find.text('조건에 맞는 외부 선수가 없습니다.'), findsOneWidget);

    await tester.pumpWidget(_app(AdminExternalPlayersScreen(
      authService: _auth(),
      loader: (_, __, ___) async =>
          throw ApiException('hidden', statusCode: 500),
    )));
    await tester.pumpAndSettle();
    expect(find.textContaining('서버 오류'), findsOneWidget);
    expect(find.textContaining('hidden'), findsNothing);
  });

  testWidgets('statistics shows null as dash, explicit zero, rates, and detail',
      (tester) async {
    final item = _statistic();
    await tester.pumpWidget(_app(AdminExternalPlayerStatisticsScreen(
      authService: _auth(),
      loader: (_, __, ___) async => ExternalPlayerStatisticPage(
        items: [item],
        meta: const AdminPaginationMeta(page: 1, pageSize: 20, total: 1),
      ),
      detailLoader: (_) async => item,
    )));
    await tester.pumpAndSettle();
    expect(find.text('0'), findsWidgets);
    expect(find.text('-'), findsWidgets);
    expect(find.text('25.5'), findsOneWidget);

    await tester.tap(find.text('테스트 통계'));
    await tester.pumpAndSettle();
    expect(find.text('선수 통계 상세'), findsOneWidget);
    expect(find.text('출전일수: -'), findsOneWidget);
    expect(find.text('2위 횟수: 0'), findsOneWidget);
    expect(find.text('연대율: 25.5'), findsOneWidget);
  });

  testWidgets(
      'match candidates render five Korean statuses without action buttons',
      (tester) async {
    const statuses = [
      'UNIQUE_CANDIDATE',
      'NO_CANDIDATE',
      'MULTIPLE_CANDIDATES',
      'MISSING_PERIOD_NUMBER',
      'GRADE_MISMATCH',
    ];
    await tester.pumpWidget(_app(AdminPlayerMatchCandidatesScreen(
      authService: _auth(),
      loader: (_) async => [
        for (var i = 0; i < statuses.length; i++) _candidate(i + 1, statuses[i])
      ],
    )));
    await tester.pumpAndSettle();
    for (final label in ['유일 후보', '후보 없음', '복수 후보', '기수 미확인', '등급 불일치']) {
      expect(find.text(label), findsWidgets);
    }
    expect(find.text('1'), findsWidgets);
    expect(find.text('연결 승인'), findsNothing);
    expect(find.text('자동 매칭'), findsNothing);
    expect(find.text('players 반영'), findsNothing);
  });

  testWidgets('unauthenticated access is blocked and 401 clears session',
      (tester) async {
    final unauthenticated = AuthService(session: AuthSession());
    await tester.pumpWidget(_app(
      AdminExternalPlayersScreen(authService: unauthenticated),
      loginRoute: true,
    ));
    await tester.pumpAndSettle();
    expect(find.text('로그인 화면'), findsOneWidget);

    final authenticated = _auth();
    await tester.pumpWidget(_app(
      AdminPlayerMatchCandidatesScreen(
        authService: authenticated,
        loader: (_) async => throw ApiException('expired', statusCode: 401),
      ),
      loginRoute: true,
    ));
    await tester.pumpAndSettle();
    expect(find.text('로그인 화면'), findsOneWidget);
    expect(authenticated.currentUser, isNull);
  });

  testWidgets('narrow viewport keeps table in horizontal scroll container',
      (tester) async {
    await tester.binding.setSurfaceSize(const Size(390, 800));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(_app(AdminExternalPlayerStatisticsScreen(
      authService: _auth(),
      loader: (_, __, ___) async => ExternalPlayerStatisticPage(
        items: [_statistic()],
        meta: const AdminPaginationMeta(page: 1, pageSize: 20, total: 1),
      ),
    )));
    await tester.pumpAndSettle();
    expect(find.byType(SingleChildScrollView), findsWidgets);
    expect(tester.takeException(), isNull);
  });
}

Widget _app(Widget home, {bool loginRoute = false}) => MaterialApp(
      key: UniqueKey(),
      routes: loginRoute
          ? {'/admin/login': (_) => const Scaffold(body: Text('로그인 화면'))}
          : const {},
      home: home,
    );

AuthService _auth() {
  final session = AuthSession()
    ..accessToken = 'admin-token'
    ..currentUser = CurrentUser(
      id: 1,
      email: 'admin@example.com',
      username: 'admin',
      role: 'admin',
      status: 'active',
      createdAt: DateTime.parse('2026-07-13T00:00:00Z'),
      updatedAt: DateTime.parse('2026-07-13T00:00:00Z'),
    );
  return AuthService(session: session);
}

ExternalPlayerAdmin _externalPlayer() => ExternalPlayerAdmin(
      id: 1,
      source: 'kcycle',
      externalId: '00120034',
      name: '테스트 선수',
      periodNumber: '06',
      grade: 'A1',
      region: 'unknown',
      status: 'active',
      detailUrl: 'https://www.kcycle.or.kr/racer/info/00120034',
      sourceUpdatedAt: null,
      collectedAt: DateTime.parse('2026-07-13T00:00:00Z'),
      createdAt: DateTime.parse('2026-07-13T00:00:00Z'),
      updatedAt: DateTime.parse('2026-07-13T00:00:00Z'),
    );

ExternalPlayerStatisticAdmin _statistic() => ExternalPlayerStatisticAdmin(
      id: 1,
      source: 'data_go',
      standardYear: '2025',
      racerName: '테스트 통계',
      periodNumber: '06',
      grade: 'A1',
      runCount: 0,
      runDayCount: null,
      rankCounts: const [null, 0, 3, null, null, null, null, null, null],
      eliminatedCount: null,
      winRate: 0,
      highRate: 25.5,
      high3Rate: null,
      collectedAt: DateTime.parse('2026-07-13T00:00:00Z'),
      createdAt: DateTime.parse('2026-07-13T00:00:00Z'),
      updatedAt: DateTime.parse('2026-07-13T00:00:00Z'),
    );

PlayerMatchCandidateAdmin _candidate(int id, String status) =>
    PlayerMatchCandidateAdmin(
      statisticId: id,
      standardYear: '2025',
      maskedRacerName: '테***',
      periodNumber: '06',
      statisticGrade: 'A1',
      candidateCount: 1,
      matchStatus: status,
      maskedExternalId: '0012****',
      externalGrade: 'A1',
      gradeMatches: true,
    );
