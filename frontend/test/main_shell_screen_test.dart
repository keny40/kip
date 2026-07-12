import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:kip_frontend/screens/main_shell_screen.dart';

void main() {
  Widget buildTestApp() {
    return MaterialApp(
      home: MainShellScreen(
        tabs: const [
          _TabStub(label: 'RACES_TAB'),
          _TabStub(label: 'PLAYERS_TAB'),
          _TabStub(label: 'TRACKS_TAB'),
          _TabStub(label: 'ANALYTICS_TAB'),
        ],
      ),
    );
  }

  testWidgets('shows races tab by default', (tester) async {
    await tester.pumpWidget(buildTestApp());

    expect(find.text('RACES_TAB'), findsOneWidget);
    expect(find.text('경주'), findsOneWidget);
  });

  testWidgets('switches to players tab', (tester) async {
    await tester.pumpWidget(buildTestApp());

    await tester.tap(find.text('선수'));
    await tester.pumpAndSettle();

    expect(find.text('PLAYERS_TAB'), findsOneWidget);
  });

  testWidgets('switches to tracks tab', (tester) async {
    await tester.pumpWidget(buildTestApp());

    await tester.tap(find.text('경기장'));
    await tester.pumpAndSettle();

    expect(find.text('TRACKS_TAB'), findsOneWidget);
  });

  testWidgets('switches to analytics tab', (tester) async {
    await tester.pumpWidget(buildTestApp());

    await tester.tap(find.text('분석'));
    await tester.pumpAndSettle();

    expect(find.text('ANALYTICS_TAB'), findsOneWidget);
  });
}

class _TabStub extends StatelessWidget {
  const _TabStub({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(child: Text(label)),
    );
  }
}
