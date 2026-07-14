import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:kip_frontend/models/player.dart';
import 'package:kip_frontend/screens/players_screen.dart';
import 'package:kip_frontend/widgets/player_list_filter.dart';

List<PlayerSummary> _samplePlayers = const [
  PlayerSummary(id: 1, name: '홍길동', playerNumber: 101, grade: 'A1', region: '광명', status: 'active'),
  PlayerSummary(id: 2, name: '김철수', playerNumber: 102, grade: 'B1', region: '서울', status: 'active'),
  PlayerSummary(id: 3, name: '이영희', playerNumber: 123, grade: 'A1', region: '광명', status: 'inactive'),
  PlayerSummary(id: 4, name: '박민수', playerNumber: 204, grade: 'C1', region: '부산', status: 'retired'),
];

void main() {
  test('searches by name, player number, grade, and region', () {
    expect(filterPlayers(_samplePlayers, query: '홍길동').single.name, '홍길동');
    expect(filterPlayers(_samplePlayers, query: '123').single.playerNumber, 123);
    expect(filterPlayers(_samplePlayers, query: 'a1').length, 2);
    expect(filterPlayers(_samplePlayers, query: '광명').length, 2);
  });

  test('applies filters together', () {
    final result = filterPlayers(
      _samplePlayers,
      query: '1',
      grade: 'A1',
      region: '광명',
      status: 'active',
    );

    expect(result.length, 1);
    expect(result.single.name, '홍길동');
  });

  testWidgets('shows count, supports search, and zero-state reset', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: PlayersScreen(
          playersLoader: () async => _samplePlayers,
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('전체 4명 중 4명'), findsOneWidget);
    expect(find.byKey(const Key('players_filter_button')), findsOneWidget);

    await tester.enterText(find.byKey(const Key('players_search_field')), '광명');
    await tester.pumpAndSettle();
    expect(find.text('전체 4명 중 2명'), findsOneWidget);

    await tester.enterText(find.byKey(const Key('players_search_field')), '없는값');
    await tester.pumpAndSettle();
    expect(find.text('검색 조건에 맞는 선수가 없습니다.'), findsOneWidget);
    expect(find.text('필터 초기화'), findsOneWidget);

    await tester.tap(find.byKey(const Key('players_reset_button')));
    await tester.pumpAndSettle();
    expect(find.text('전체 4명 중 4명'), findsOneWidget);
  });

  testWidgets('shows filter chips for active selection', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: PlayerListFilterSummary(
            totalCount: 4,
            filteredCount: 1,
            selection: PlayerListFilterSelection(
              grade: 'A1',
              region: '광명',
              status: 'active',
            ),
          ),
        ),
      ),
    );

    expect(find.text('등급 A1'), findsOneWidget);
    expect(find.text('지역 광명'), findsOneWidget);
    expect(find.text('상태 활성'), findsOneWidget);
  });
}
