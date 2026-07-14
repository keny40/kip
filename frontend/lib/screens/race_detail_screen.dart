import 'package:flutter/material.dart';

import '../models/race.dart';
import '../services/api_client.dart';
import '../utils/display_labels.dart';
import '../utils/error_messages.dart';

class RaceDetailScreen extends StatefulWidget {
  const RaceDetailScreen({super.key, required this.raceId});

  final int raceId;

  @override
  State<RaceDetailScreen> createState() => _RaceDetailScreenState();
}

class _RaceDetailScreenState extends State<RaceDetailScreen> {
  late final Future<RaceDetail> _future =
      ApiClient().fetchRaceDetail(widget.raceId);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('경주 상세')),
      body: FutureBuilder<RaceDetail>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return const Center(child: Text(userFacingLoadError));
          }
          final race = snapshot.data;
          if (race == null) {
            return const Center(child: Text('경주 정보를 찾을 수 없습니다.'));
          }
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Card(
                elevation: 0,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('${race.trackName} · ${race.raceNumber}경주',
                          style: Theme.of(context).textTheme.titleLarge),
                      const SizedBox(height: 8),
                      Text('경기일: ${race.raceDate}'),
                      Text('시작 예정: ${race.scheduledStartTime}'),
                      Text('상태: ${statusLabel(race.status)}'),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Text('출전 선수', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              ...race.entries.map(
                (entry) => Card(
                  elevation: 0,
                  child: ListTile(
                    title: Text('${entry.playerNumber}번 · ${entry.playerName}'),
                    subtitle: Text('등급 ${entry.grade} · 지역 ${entry.region}'),
                    trailing: Text('라인 ${entry.laneNumber}'),
                  ),
                ),
              ),
              if (race.results.isNotEmpty) ...[
                const SizedBox(height: 16),
                Text('결과', style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 8),
                ...race.results.map(
                  (result) => Card(
                    elevation: 0,
                    child: ListTile(
                      title: Text(
                          '${result.player.playerNumber}번 · ${result.player.name}'),
                      subtitle: Text(
                          '순위 ${result.finishPosition} · 상태 ${statusLabel(result.resultStatus)}'),
                      trailing: Text(result.points?.toString() ?? '-'),
                    ),
                  ),
                ),
              ],
            ],
          );
        },
      ),
    );
  }
}
