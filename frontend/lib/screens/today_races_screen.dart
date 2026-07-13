import 'package:flutter/material.dart';

import '../models/race.dart';
import '../services/api_client.dart';
import '../utils/error_messages.dart';
import 'race_detail_screen.dart';

class TodayRacesScreen extends StatefulWidget {
  const TodayRacesScreen({super.key});

  @override
  State<TodayRacesScreen> createState() => _TodayRacesScreenState();
}

class _TodayRacesScreenState extends State<TodayRacesScreen> {
  late final Future<List<RaceSummary>> _future = ApiClient().fetchTodayRaces();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('오늘의 경주')),
      body: FutureBuilder<List<RaceSummary>>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return _StateMessage(
              title: '네트워크 오류',
              message: userFacingLoadError,
            );
          }
          final races = snapshot.data ?? const [];
          if (races.isEmpty) {
            return const _StateMessage(
              title: '표시할 경주가 없습니다',
              message: '오늘 일정에 등록된 경주가 아직 없습니다.',
            );
          }
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: races.length,
            separatorBuilder: (context, index) => const SizedBox(height: 12),
            itemBuilder: (context, index) {
              final race = races[index];
              return _RaceCard(
                race: race,
                onTap: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => RaceDetailScreen(raceId: race.id),
                    ),
                  );
                },
              );
            },
          );
        },
      ),
    );
  }
}

class _RaceCard extends StatelessWidget {
  const _RaceCard({required this.race, required this.onTap});

  final RaceSummary race;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      elevation: 0,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('${race.trackName} · ${race.raceNumber}경주',
                  style: theme.textTheme.titleMedium),
              const SizedBox(height: 4),
              Text('${race.raceDate} · ${race.scheduledStartTime}'),
              const SizedBox(height: 8),
              Chip(label: Text(race.status)),
            ],
          ),
        ),
      ),
    );
  }
}

class _StateMessage extends StatelessWidget {
  const _StateMessage({required this.title, required this.message});

  final String title;
  final String message;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(title, style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            Text(message, textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }
}
