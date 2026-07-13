import 'package:flutter/material.dart';

import '../models/player.dart';
import '../services/api_client.dart';
import '../utils/error_messages.dart';
import '../widgets/player_list_filter.dart';
import 'player_detail_screen.dart';

class PlayersScreen extends StatefulWidget {
  const PlayersScreen({super.key, this.playersLoader});

  final Future<List<PlayerSummary>> Function()? playersLoader;

  @override
  State<PlayersScreen> createState() => _PlayersScreenState();
}

class _PlayersScreenState extends State<PlayersScreen> {
  final TextEditingController _searchController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final ApiClient _client = ApiClient();

  List<PlayerSummary> _players = const [];
  bool _loading = true;
  String? _errorMessage;
  String _query = '';
  PlayerListFilterSelection _selection = const PlayerListFilterSelection();

  @override
  void initState() {
    super.initState();
    _searchController.addListener(_handleSearchChanged);
    _loadPlayers();
  }

  @override
  void dispose() {
    _searchController.removeListener(_handleSearchChanged);
    _searchController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<List<PlayerSummary>> _fetchPlayers() {
    return widget.playersLoader?.call() ?? _client.fetchPlayers();
  }

  Future<void> _loadPlayers() async {
    setState(() {
      _loading = true;
      _errorMessage = null;
    });
    try {
      final players = await _fetchPlayers();
      if (!mounted) {
        return;
      }
      final sanitizedSelection = _sanitizeSelection(players, _selection);
      setState(() {
        _players = players;
        _selection = sanitizedSelection;
        _loading = false;
      });
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _loading = false;
        _errorMessage = userFacingLoadError;
      });
    }
  }

  PlayerListFilterSelection _sanitizeSelection(
      List<PlayerSummary> players, PlayerListFilterSelection selection) {
    final grades = extractPlayerGrades(players);
    final regions = extractPlayerRegions(players);
    final statuses = extractPlayerStatuses(players);
    return selection.copyWith(
      clearGrade: selection.grade != null && !grades.contains(selection.grade),
      clearRegion:
          selection.region != null && !regions.contains(selection.region),
      clearStatus:
          selection.status != null && !statuses.contains(selection.status),
    );
  }

  void _handleSearchChanged() {
    final nextQuery = _searchController.text.trim();
    if (nextQuery == _query) {
      return;
    }
    setState(() {
      _query = nextQuery;
    });
  }

  Future<void> _openFilterSheet() async {
    final result = await showModalBottomSheet<PlayerListFilterSelection>(
      context: context,
      isScrollControlled: true,
      builder: (context) {
        return PlayerListFilterBottomSheet(
          players: _players,
          initialSelection: _selection,
        );
      },
    );
    if (result == null) {
      return;
    }
    setState(() {
      _selection = _sanitizeSelection(_players, result);
    });
  }

  void _resetFilters() {
    setState(() {
      _query = '';
      _searchController.clear();
      _selection = const PlayerListFilterSelection();
    });
  }

  List<PlayerSummary> get _filteredPlayers {
    return filterPlayers(
      _players,
      query: _query,
      grade: _selection.grade,
      region: _selection.region,
      status: _selection.status,
    );
  }

  @override
  Widget build(BuildContext context) {
    final filteredPlayers = _filteredPlayers;
    final totalCount = _players.length;
    final hasResults = filteredPlayers.isNotEmpty;

    return Scaffold(
      appBar: AppBar(
        title: const Text('선수'),
        actions: [
          IconButton(
            onPressed: _loadPlayers,
            icon: const Icon(Icons.refresh_outlined),
            tooltip: '새로고침',
          ),
        ],
      ),
      body: _loading && _players.isEmpty
          ? const Center(child: CircularProgressIndicator())
          : _errorMessage != null && _players.isEmpty
              ? Center(child: Text(_errorMessage!))
              : RefreshIndicator(
                  onRefresh: _loadPlayers,
                  child: ListView(
                    key: const PageStorageKey<String>('players-list'),
                    controller: _scrollController,
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.all(16),
                    children: [
                      TextField(
                        key: const Key('players_search_field'),
                        controller: _searchController,
                        decoration: InputDecoration(
                          labelText: '검색',
                          hintText: '선수명, 선수번호, 등급, 지역',
                          prefixIcon: const Icon(Icons.search),
                          suffixIcon: _query.isEmpty
                              ? null
                              : IconButton(
                                  onPressed: () {
                                    _searchController.clear();
                                  },
                                  icon: const Icon(Icons.clear),
                                ),
                          border: const OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: PlayerListFilterSummary(
                              key: const Key('players_result_summary'),
                              totalCount: totalCount,
                              filteredCount: filteredPlayers.length,
                              selection: _selection,
                            ),
                          ),
                          const SizedBox(width: 12),
                          OutlinedButton.icon(
                            key: const Key('players_filter_button'),
                            onPressed: _openFilterSheet,
                            icon: const Icon(Icons.tune),
                            label: const Text('필터'),
                          ),
                        ],
                      ),
                      if (_loading && _players.isNotEmpty) ...[
                        const SizedBox(height: 12),
                        const LinearProgressIndicator(minHeight: 2),
                      ],
                      if (_errorMessage != null && _players.isNotEmpty) ...[
                        const SizedBox(height: 12),
                        Text(_errorMessage!,
                            style: TextStyle(
                                color: Theme.of(context).colorScheme.error)),
                      ],
                      const SizedBox(height: 12),
                      if (_players.isEmpty)
                        const Padding(
                          padding: EdgeInsets.only(top: 64),
                          child: Center(child: Text('표시할 선수가 없습니다.')),
                        )
                      else if (!hasResults)
                        Padding(
                          padding: const EdgeInsets.only(top: 64),
                          child: Column(
                            children: [
                              const Text('검색 조건에 맞는 선수가 없습니다.'),
                              const SizedBox(height: 8),
                              const Text('검색어나 필터를 초기화해 주세요.',
                                  textAlign: TextAlign.center),
                              const SizedBox(height: 12),
                              FilledButton(
                                key: const Key('players_reset_button'),
                                onPressed: _resetFilters,
                                child: const Text('필터 초기화'),
                              ),
                            ],
                          ),
                        )
                      else
                        ListView.separated(
                          shrinkWrap: true,
                          physics: const NeverScrollableScrollPhysics(),
                          itemCount: filteredPlayers.length,
                          separatorBuilder: (context, index) =>
                              const SizedBox(height: 12),
                          itemBuilder: (context, index) {
                            final player = filteredPlayers[index];
                            return Card(
                              elevation: 0,
                              child: ListTile(
                                title: Text(
                                    '${player.playerNumber} · ${player.name}'),
                                subtitle: Text(
                                    '등급 ${player.grade} · 지역 ${player.region}'),
                                trailing: Text(player.status),
                                onTap: () {
                                  Navigator.of(context).push(
                                    MaterialPageRoute(
                                      builder: (_) => PlayerDetailScreen(
                                          playerId: player.id),
                                    ),
                                  );
                                },
                              ),
                            );
                          },
                        ),
                    ],
                  ),
                ),
    );
  }
}
