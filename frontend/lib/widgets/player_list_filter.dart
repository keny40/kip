import 'package:flutter/material.dart';

import '../models/player.dart';
import '../utils/display_labels.dart';

class PlayerListFilterSelection {
  const PlayerListFilterSelection({
    this.grade,
    this.region,
    this.status,
  });

  final String? grade;
  final String? region;
  final String? status;

  PlayerListFilterSelection copyWith({
    String? grade,
    String? region,
    String? status,
    bool clearGrade = false,
    bool clearRegion = false,
    bool clearStatus = false,
  }) {
    return PlayerListFilterSelection(
      grade: clearGrade ? null : (grade ?? this.grade),
      region: clearRegion ? null : (region ?? this.region),
      status: clearStatus ? null : (status ?? this.status),
    );
  }

  bool get hasAnyFilter => grade != null || region != null || status != null;

  List<String> chipLabels() {
    final chips = <String>[];
    if (grade != null) {
      chips.add('등급 $grade');
    }
    if (region != null) {
      chips.add('지역 $region');
    }
    if (status != null) {
      chips.add('상태 ${statusLabel(status)}');
    }
    return chips;
  }
}

List<PlayerSummary> filterPlayers(
  List<PlayerSummary> players, {
  String query = '',
  String? grade,
  String? region,
  String? status,
}) {
  final normalizedQuery = query.trim().toLowerCase();
  return players.where((player) {
    final matchesQuery = normalizedQuery.isEmpty ||
        player.name.toLowerCase().contains(normalizedQuery) ||
        player.playerNumber.toString().contains(normalizedQuery) ||
        player.grade.toLowerCase().contains(normalizedQuery) ||
        player.region.toLowerCase().contains(normalizedQuery);
    final matchesGrade = grade == null || player.grade == grade;
    final matchesRegion = region == null || player.region == region;
    final matchesStatus = status == null || player.status == status;
    return matchesQuery && matchesGrade && matchesRegion && matchesStatus;
  }).toList();
}

List<String> extractPlayerGrades(List<PlayerSummary> players) {
  final values = players.map((player) => player.grade).toSet().toList()..sort();
  return values;
}

List<String> extractPlayerRegions(List<PlayerSummary> players) {
  final values = players.map((player) => player.region).toSet().toList()..sort();
  return values;
}

List<String> extractPlayerStatuses(List<PlayerSummary> players) {
  final values = players.map((player) => player.status).toSet().toList()..sort();
  return values;
}

class PlayerListFilterBottomSheet extends StatefulWidget {
  const PlayerListFilterBottomSheet({
    super.key,
    required this.players,
    required this.initialSelection,
  });

  final List<PlayerSummary> players;
  final PlayerListFilterSelection initialSelection;

  @override
  State<PlayerListFilterBottomSheet> createState() => _PlayerListFilterBottomSheetState();
}

class _PlayerListFilterBottomSheetState extends State<PlayerListFilterBottomSheet> {
  late PlayerListFilterSelection _selection = widget.initialSelection;

  List<String> get _grades => extractPlayerGrades(widget.players);
  List<String> get _regions => extractPlayerRegions(widget.players);
  List<String> get _statuses => extractPlayerStatuses(widget.players);

  void _apply() {
    Navigator.of(context).pop(_selection);
  }

  void _reset() {
    Navigator.of(context).pop(const PlayerListFilterSelection());
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text('필터', style: Theme.of(context).textTheme.titleLarge),
                    TextButton(onPressed: _reset, child: const Text('초기화')),
                  ],
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String?>(
                  initialValue: _selection.grade,
                  decoration: const InputDecoration(labelText: '등급'),
                  items: [
                    const DropdownMenuItem<String?>(value: null, child: Text('전체')),
                    ..._grades.map((value) => DropdownMenuItem<String?>(value: value, child: Text(value))),
                  ],
                  onChanged: (value) {
                    setState(() {
                      _selection = value == null
                          ? _selection.copyWith(clearGrade: true)
                          : _selection.copyWith(grade: value);
                    });
                  },
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String?>(
                  initialValue: _selection.region,
                  decoration: const InputDecoration(labelText: '지역'),
                  items: [
                    const DropdownMenuItem<String?>(value: null, child: Text('전체')),
                    ..._regions.map((value) => DropdownMenuItem<String?>(value: value, child: Text(value))),
                  ],
                  onChanged: (value) {
                    setState(() {
                      _selection = value == null
                          ? _selection.copyWith(clearRegion: true)
                          : _selection.copyWith(region: value);
                    });
                  },
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String?>(
                  initialValue: _selection.status,
                  decoration: const InputDecoration(labelText: '상태'),
                  items: [
                    const DropdownMenuItem<String?>(value: null, child: Text('전체')),
                    ..._statuses.map((value) => DropdownMenuItem<String?>(
                        value: value, child: Text(statusLabel(value)))),
                  ],
                  onChanged: (value) {
                    setState(() {
                      _selection = value == null
                          ? _selection.copyWith(clearStatus: true)
                          : _selection.copyWith(status: value);
                    });
                  },
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(child: OutlinedButton(onPressed: _reset, child: const Text('초기화'))),
                    const SizedBox(width: 12),
                    Expanded(child: FilledButton(onPressed: _apply, child: const Text('적용'))),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class PlayerListFilterSummary extends StatelessWidget {
  const PlayerListFilterSummary({
    super.key,
    required this.totalCount,
    required this.filteredCount,
    required this.selection,
  });

  final int totalCount;
  final int filteredCount;
  final PlayerListFilterSelection selection;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('전체 $totalCount명 중 $filteredCount명'),
        if (selection.hasAnyFilter) ...[
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: selection.chipLabels().map((label) => Chip(label: Text(label))).toList(),
          ),
        ],
      ],
    );
  }
}
