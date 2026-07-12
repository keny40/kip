import 'package:flutter/material.dart';

import '../models/track.dart';
import '../services/api_client.dart';

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
        title: const Text('Track Detail'),
        actions: [
          IconButton(
            onPressed: _reload,
            icon: const Icon(Icons.refresh_outlined),
            tooltip: 'Refresh',
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
            return _ErrorState(message: snapshot.error.toString(), onRetry: _reload);
          }
          final bundle = snapshot.data;
          if (bundle == null) {
            return const _EmptyState(message: 'Track details are unavailable.');
          }
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _TrackHeader(track: bundle.track),
              const SizedBox(height: 16),
              Text('Summary', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              Wrap(
                spacing: 12,
                runSpacing: 12,
                children: [
                  _MetricCard(label: 'Total races', value: '${bundle.summary.totalRaces}'),
                  _MetricCard(label: 'Completed', value: '${bundle.summary.completedRaces}'),
                  _MetricCard(label: 'Entries', value: '${bundle.summary.totalEntries}'),
                  _MetricCard(label: 'Unique players', value: '${bundle.summary.uniquePlayers}'),
                ],
              ),
              const SizedBox(height: 16),
              Text('Recent races', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              if (bundle.summary.recent30Races.isEmpty)
                const _EmptyState(message: 'No races found for this track.')
              else
                ...bundle.summary.recent30Races.map(
                  (race) => Card(
                    elevation: 0,
                    child: ListTile(
                      title: Text('${race.raceDate} · Race ${race.raceNumber}'),
                      subtitle: Text('${race.trackName} · ${race.status}'),
                    ),
                  ),
                ),
              const SizedBox(height: 16),
              Text('Player performance', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              if (bundle.players.isEmpty)
                const _EmptyState(message: 'No player analytics available.')
              else
                ...bundle.players.map(
                  (player) => Card(
                    elevation: 0,
                    child: ListTile(
                      title: Text('${player.playerNumber} · ${player.name}'),
                      subtitle: Text(
                        'Grade ${player.grade} · Starts ${player.starts} · Wins ${player.wins} · Top3 ${player.top3}',
                      ),
                      trailing: Text('${(player.winRate * 100).toStringAsFixed(1)}%'),
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
            Text('Code: ${track.code}'),
            Text('Region: ${track.region}'),
            if (track.address != null) Text('Address: ${track.address}'),
            Text('Status: ${track.status}'),
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
            Text('Failed to load track detail', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            FilledButton(onPressed: onRetry, child: const Text('Retry')),
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
