import 'package:flutter/material.dart';

import '../models/track.dart';
import '../services/api_client.dart';
import '../utils/display_labels.dart';
import '../utils/error_messages.dart';

class TrackDetailScreen extends StatefulWidget {
  const TrackDetailScreen({super.key, required this.trackId});

  final int trackId;

  @override
  State<TrackDetailScreen> createState() => _TrackDetailScreenState();
}

class _TrackDetailScreenState extends State<TrackDetailScreen> {
  late Future<_TrackDetailBundle> _future = _load();

  Future<_TrackDetailBundle> _load() async {
    final client = ApiClient();
    final track = await client.fetchTrack(widget.trackId);
    final summary = await client.fetchTrackSummary(widget.trackId);
    final players = await client.fetchTrackPlayers(widget.trackId);
    return _TrackDetailBundle(track: track, summary: summary, players: players);
  }

  void _reload() {
    setState(() {
      _future = _load();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('경기장 상세'),
        actions: [
          IconButton(
            onPressed: _reload,
            icon: const Icon(Icons.refresh_outlined),
            tooltip: '새로고침',
          ),
        ],
      ),
      body: FutureBuilder<_TrackDetailBundle>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return _ErrorState(message: userFacingLoadError, onRetry: _reload);
          }
          final bundle = snapshot.data;
          if (bundle == null) {
            return const _EmptyState(message: '경기장 상세 정보를 찾을 수 없습니다.');
          }
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _TrackHeader(track: bundle.track),
              const SizedBox(height: 16),
              Text('요약', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              Wrap(
                spacing: 12,
                runSpacing: 12,
                children: [
                  _MetricCard(
                      label: '전체 경주',
                      value: '${bundle.summary.totalRaces}'),
                  _MetricCard(
                      label: '완료 경주',
                      value: '${bundle.summary.completedRaces}'),
                  _MetricCard(
                      label: '출전 인원',
                      value: '${bundle.summary.totalEntries}'),
                  _MetricCard(
                      label: '참여 선수',
                      value: '${bundle.summary.uniquePlayers}'),
                ],
              ),
              const SizedBox(height: 16),
              Text('최근 경주',
                  style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              if (bundle.summary.recent30Races.isEmpty)
                const _EmptyState(message: '이 경기장의 최근 경주가 없습니다.')
              else
                ...bundle.summary.recent30Races.map(
                  (race) => Card(
                    elevation: 0,
                    child: ListTile(
                      title: Text('${race.raceDate} · ${race.raceNumber}경주'),
                      subtitle:
                          Text('${race.trackName} · ${statusLabel(race.status)}'),
                    ),
                  ),
                ),
              const SizedBox(height: 16),
              Text('선수 성적',
                  style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              if (bundle.players.isEmpty)
                const _EmptyState(message: '표시할 선수 성적이 없습니다.')
              else
                ...bundle.players.map(
                  (player) => Card(
                    elevation: 0,
                    child: ListTile(
                      title: Text('${player.playerNumber} · ${player.name}'),
                      subtitle: Text(
                        '등급 ${player.grade} · 출전 ${player.starts} · 우승 ${player.wins} · 3위 이내 ${player.top3}',
                      ),
                      trailing:
                          Text('${(player.winRate * 100).toStringAsFixed(1)}%'),
                    ),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}

class _TrackDetailBundle {
  const _TrackDetailBundle({
    required this.track,
    required this.summary,
    required this.players,
  });

  final Track track;
  final TrackAnalyticsSummary summary;
  final List<TrackPlayerStat> players;
}

class _TrackHeader extends StatelessWidget {
  const _TrackHeader({required this.track});

  final Track track;

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(track.name, style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 8),
            Text('코드: ${track.code}'),
            Text('지역: ${track.region}'),
            if (track.address != null) Text('주소: ${track.address}'),
            Text('상태: ${statusLabel(track.status)}'),
          ],
        ),
      ),
    );
  }
}

class _MetricCard extends StatelessWidget {
  const _MetricCard({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 160,
      child: Card(
        elevation: 0,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: Theme.of(context).textTheme.labelLarge),
              const SizedBox(height: 8),
              Text(value, style: Theme.of(context).textTheme.headlineSmall),
            ],
          ),
        ),
      ),
    );
  }
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('경기장 상세를 불러오지 못했습니다',
                style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            FilledButton(onPressed: onRetry, child: const Text('다시 시도')),
          ],
        ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 24),
      child: Text(message, textAlign: TextAlign.center),
    );
  }
}
