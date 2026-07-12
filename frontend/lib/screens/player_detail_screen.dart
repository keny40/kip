import 'package:flutter/material.dart';

import '../models/player.dart';
import '../models/player_statistics.dart';
import '../models/race.dart';
import '../models/track.dart';
import '../services/api_client.dart';
import '../widgets/player_statistics_filter.dart';

class PlayerDetailScreen extends StatefulWidget {
  const PlayerDetailScreen({super.key, required this.playerId});

  final int playerId;

  @override
  State<PlayerDetailScreen> createState() => _PlayerDetailScreenState();
}

class _PlayerDetailScreenState extends State<PlayerDetailScreen> {
  final ApiClient _client = ApiClient();
  late final Future<PlayerRaceHistoryResponse> _playerFuture = _client.fetchPlayerRaceHistory(widget.playerId);

  PlayerRaceHistoryResponse? _player;
  List<Track> _tracks = const [];
  String? _trackLoadError;

  PlayerStatisticsResponse? _statistics;
  bool _statsLoading = true;
  String? _statsError;
  PlayerStatisticsFilterSelection _selection = const PlayerStatisticsFilterSelection();

  @override
  void initState() {
    super.initState();
    _playerFuture.then((player) {
      if (!mounted) {
        return;
      }
      setState(() {
        _player = player;
      });
      _loadTracks();
      _reloadStatistics();
    }).catchError((_) {
      // Handled by FutureBuilder when the player bundle is unavailable.
    });
  }

  Future<void> _loadTracks() async {
    try {
      final tracks = await _client.fetchTracks();
      if (!mounted) {
        return;
      }
      setState(() {
        _tracks = tracks;
        _trackLoadError = null;
      });
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _tracks = const [];
        _trackLoadError = error.toString();
      });
    }
  }

  Future<void> _reloadStatistics({PlayerStatisticsFilterSelection? selection}) async {
    final player = _player;
    if (player == null) {
      return;
    }
    final nextSelection = selection ?? _selection;
    setState(() {
      _selection = nextSelection;
      _statsLoading = true;
      _statsError = null;
    });
    try {
      final response = await _client.fetchPlayerStatistics(
        widget.playerId,
        trackId: nextSelection.trackId,
        dateFrom: nextSelection.dateFrom,
        dateTo: nextSelection.dateTo,
        lastN: nextSelection.lastN,
        grade: nextSelection.grade,
      );
      if (!mounted) {
        return;
      }
      setState(() {
        _statistics = response;
        _statsLoading = false;
        _statsError = null;
      });
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _statsLoading = false;
        _statsError = error.toString();
      });
    }
  }

  Future<void> _openFilterSheet() async {
    final player = _player;
    if (player == null) {
      return;
    }
    final result = await showModalBottomSheet<PlayerStatisticsFilterSelection>(
      context: context,
      isScrollControlled: true,
      builder: (context) {
        return PlayerStatisticsFilterSheet(
          tracks: _tracks,
          initialSelection: _selection,
          playerGrade: player.grade,
        );
      },
    );
    if (result != null) {
      await _reloadStatistics(selection: result);
    }
  }

  Future<void> _retryStatistics() async {
    await _reloadStatistics();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('선수 상세')),
      body: FutureBuilder<PlayerRaceHistoryResponse>(
        future: _playerFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting && _player == null) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError && _player == null) {
            return Center(child: Text(snapshot.error.toString()));
          }
          final player = _player ?? snapshot.data;
          if (player == null) {
            return const Center(child: Text('선수 정보를 불러올 수 없습니다.'));
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
                      Text(
                        '${player.playerNumber} - ${player.playerName}',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 8),
                      Text('등급: ${player.grade}'),
                      Text('지역: ${player.region}'),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Text('통계', style: Theme.of(context).textTheme.titleMedium),
                ],
              ),
              const SizedBox(height: 8),
              PlayerStatisticsFilterHeader(
                selection: _selection,
                onPressed: _openFilterSheet,
              ),
              const SizedBox(height: 12),
              if (_statsLoading && _statistics == null)
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 24),
                  child: Center(child: CircularProgressIndicator()),
                )
              else ...[
                if (_statsLoading && _statistics != null)
                  const LinearProgressIndicator(minHeight: 2),
                if (_statsError != null) ...[
                  const SizedBox(height: 8),
                  Card(
                    elevation: 0,
                    color: Theme.of(context).colorScheme.errorContainer,
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '통계를 불러오지 못했습니다',
                            style: TextStyle(color: Theme.of(context).colorScheme.onErrorContainer),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            _statsError!,
                            style: TextStyle(color: Theme.of(context).colorScheme.onErrorContainer),
                          ),
                          const SizedBox(height: 12),
                          FilledButton(
                            onPressed: _retryStatistics,
                            child: const Text('다시 시도'),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
                if (_statistics != null) ...[
                  _StatCard(label: '총 경기', value: '${_statistics!.statistics.totalRaces}'),
                  _StatCard(label: '1위', value: '${_statistics!.statistics.firstPlaceCount}'),
                  _StatCard(label: '2위', value: '${_statistics!.statistics.secondPlaceCount}'),
                  _StatCard(label: '3위', value: '${_statistics!.statistics.thirdPlaceCount}'),
                  _StatCard(label: '최근 결과 수', value: '${_statistics!.statistics.recentFiveResults.length}'),
                ],
              ],
              const SizedBox(height: 16),
              Text('최근 5경주', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              ...(_statistics?.statistics.recentFiveResults ?? const <RaceResult>[]).map(
                (result) => Card(
                  elevation: 0,
                  child: ListTile(
                    title: Text('${result.raceDate} - ${result.trackName} ${result.raceNumber}경주'),
                    subtitle: Text(
                      '시작 ${result.scheduledStartTime} / 순위 ${result.finishPosition} / 상태 ${result.resultStatus}',
                    ),
                    trailing: Text(result.points?.toString() ?? '-'),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Text('경기 이력', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              ...player.history.map(
                (item) => Card(
                  elevation: 0,
                  child: ListTile(
                    title: Text('${item.raceDate} - ${item.trackName} ${item.raceNumber}경주'),
                    subtitle: Text('결과 ${item.resultStatus} / 순위 ${item.finishPosition ?? "-"}'),
                    trailing: Text('점수 ${item.points ?? 0}'),
                  ),
                ),
              ),
              if (_trackLoadError != null) ...[
                const SizedBox(height: 8),
                Text(
                  '경기장 목록을 불러오지 못했습니다. 전체 경기장만 사용할 수 있습니다.',
                  style: TextStyle(color: Theme.of(context).colorScheme.error),
                ),
              ],
            ],
          );
        },
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  const _StatCard({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      child: ListTile(
        title: Text(label),
        trailing: Text(value),
      ),
    );
  }
}
