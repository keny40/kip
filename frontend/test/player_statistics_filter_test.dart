import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:kip_frontend/models/track.dart';
import 'package:kip_frontend/widgets/player_statistics_filter.dart';

void main() {
  testWidgets('shows filter button and current filter summary', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: PlayerStatisticsFilterHeader(
            selection: const PlayerStatisticsFilterSelection(),
            onPressed: () {},
          ),
        ),
      ),
    );

    expect(find.byKey(const Key('player_statistics_filter_button')), findsOneWidget);
    expect(find.text('전체 경기장 · 전체 기간 · 전체 경기'), findsOneWidget);
  });

  test('summary label includes recent 10 races', () {
    final selection = const PlayerStatisticsFilterSelection(lastN: 10);

    expect(selection.summaryLabel(), contains('최근 10경기'));
  });

  test('query parameters omit null values', () {
    final selection = PlayerStatisticsFilterSelection(
      trackId: 3,
      dateFrom: DateTime(2026, 7, 1),
      dateTo: DateTime(2026, 7, 12),
      lastN: 10,
      grade: 'A1',
    );

    expect(selection.toQueryParameters(), {
      'track_id': '3',
      'date_from': '2026-07-01',
      'date_to': '2026-07-12',
      'last_n': '10',
      'grade': 'A1',
    });
  });

  test('validates date range', () {
    expect(
      isPlayerStatisticsDateRangeValid(DateTime(2026, 7, 12), DateTime(2026, 7, 13)),
      isTrue,
    );
    expect(
      isPlayerStatisticsDateRangeValid(DateTime(2026, 7, 13), DateTime(2026, 7, 12)),
      isFalse,
    );
  });

  testWidgets('recent 10 selection and reset work in filter sheet', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: PlayerStatisticsFilterSheet(
            tracks: const [Track(id: 1, code: 'SEOUL', name: 'Seoul Velodrome', region: 'Seoul', address: null, status: 'active')],
            initialSelection: const PlayerStatisticsFilterSelection(),
            playerGrade: 'A1',
          ),
        ),
      ),
    );

    await tester.tap(find.byType(DropdownButtonFormField<int?>).at(1));
    await tester.pumpAndSettle();
    await tester.tap(find.text('최근 10경기').last);
    await tester.pumpAndSettle();
    expect(find.text('최근 10경기'), findsWidgets);

    await tester.tap(find.text('초기화').last);
    await tester.pumpAndSettle();
    expect(find.byType(PlayerStatisticsFilterSheet), findsNothing);
    expect(find.text('최근 10경기'), findsNothing);
  });
}
