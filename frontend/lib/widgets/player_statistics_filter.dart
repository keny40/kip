import 'package:flutter/material.dart';

import '../models/track.dart';

class PlayerStatisticsFilterSelection {
  const PlayerStatisticsFilterSelection({
    this.trackId,
    this.trackName,
    this.dateFrom,
    this.dateTo,
    this.lastN,
    this.grade,
  });

  final int? trackId;
  final String? trackName;
  final DateTime? dateFrom;
  final DateTime? dateTo;
  final int? lastN;
  final String? grade;

  PlayerStatisticsFilterSelection copyWith({
    int? trackId,
    String? trackName,
    DateTime? dateFrom,
    DateTime? dateTo,
    int? lastN,
    String? grade,
    bool clearTrackId = false,
    bool clearTrackName = false,
    bool clearDateFrom = false,
    bool clearDateTo = false,
    bool clearLastN = false,
    bool clearGrade = false,
  }) {
    return PlayerStatisticsFilterSelection(
      trackId: clearTrackId ? null : (trackId ?? this.trackId),
      trackName: clearTrackName ? null : (trackName ?? this.trackName),
      dateFrom: clearDateFrom ? null : (dateFrom ?? this.dateFrom),
      dateTo: clearDateTo ? null : (dateTo ?? this.dateTo),
      lastN: clearLastN ? null : (lastN ?? this.lastN),
      grade: clearGrade ? null : (grade ?? this.grade),
    );
  }

  Map<String, String> toQueryParameters() {
    final params = <String, String>{};
    if (trackId != null) {
      params['track_id'] = trackId.toString();
    }
    if (dateFrom != null) {
      params['date_from'] = _formatDate(dateFrom!);
    }
    if (dateTo != null) {
      params['date_to'] = _formatDate(dateTo!);
    }
    if (lastN != null) {
      params['last_n'] = lastN.toString();
    }
    if (grade != null && grade!.isNotEmpty) {
      params['grade'] = grade!;
    }
    return params;
  }

  String summaryLabel() {
    final parts = <String>[];
    parts.add(trackName ?? '전체 경기장');
    if (dateFrom != null && dateTo != null) {
      parts.add('${_formatDate(dateFrom!)}~${_formatDate(dateTo!)}');
    } else if (dateFrom != null) {
      parts.add('${_formatDate(dateFrom!)}~');
    } else if (dateTo != null) {
      parts.add('~${_formatDate(dateTo!)}');
    } else {
      parts.add('전체 기간');
    }
    parts.add(lastN == null ? '전체 경기' : '최근 ${lastN}경기');
    if (grade != null && grade!.isNotEmpty) {
      parts.add('등급 ${grade!}');
    }
    return parts.join(' · ');
  }

  bool get hasAnyFilter => trackId != null || dateFrom != null || dateTo != null || lastN != null || grade != null;
}

class PlayerStatisticsFilterHeader extends StatelessWidget {
  const PlayerStatisticsFilterHeader({
    super.key,
    required this.selection,
    required this.onPressed,
  });

  final PlayerStatisticsFilterSelection selection;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: Text(
            selection.summaryLabel(),
            style: Theme.of(context).textTheme.bodyMedium,
          ),
        ),
        const SizedBox(width: 12),
        OutlinedButton.icon(
          key: const Key('player_statistics_filter_button'),
          onPressed: onPressed,
          icon: const Icon(Icons.tune),
          label: const Text('필터'),
        ),
      ],
    );
  }
}

String _formatDate(DateTime value) {
  final year = value.year.toString().padLeft(4, '0');
  final month = value.month.toString().padLeft(2, '0');
  final day = value.day.toString().padLeft(2, '0');
  return '$year-$month-$day';
}

bool isPlayerStatisticsDateRangeValid(DateTime? dateFrom, DateTime? dateTo) {
  if (dateFrom == null || dateTo == null) {
    return true;
  }
  return !dateFrom.isAfter(dateTo);
}

class PlayerStatisticsFilterSheet extends StatefulWidget {
  const PlayerStatisticsFilterSheet({
    super.key,
    required this.tracks,
    required this.initialSelection,
    required this.playerGrade,
  });

  final List<Track> tracks;
  final PlayerStatisticsFilterSelection initialSelection;
  final String playerGrade;

  @override
  State<PlayerStatisticsFilterSheet> createState() => _PlayerStatisticsFilterSheetState();
}

class _PlayerStatisticsFilterSheetState extends State<PlayerStatisticsFilterSheet> {
  late PlayerStatisticsFilterSelection _selection = widget.initialSelection;
  String? _errorMessage;

  List<String> get _gradeOptions {
    final grades = <String>{widget.playerGrade};
    grades.addAll(['A1', 'A2', 'B1', 'B2', 'C1', 'C2']);
    grades.removeWhere((grade) => grade.isEmpty);
    return grades.toList();
  }

  Future<void> _pickDate({required bool isFrom}) async {
    final now = DateTime.now();
    final initialDate = (isFrom ? _selection.dateFrom : _selection.dateTo) ?? now;
    final picked = await showDatePicker(
      context: context,
      initialDate: initialDate,
      firstDate: DateTime(now.year - 5),
      lastDate: DateTime(now.year + 1),
    );
    if (picked == null) {
      return;
    }
    setState(() {
      _errorMessage = null;
      _selection = isFrom
          ? _selection.copyWith(dateFrom: picked, clearDateFrom: false)
          : _selection.copyWith(dateTo: picked, clearDateTo: false);
    });
  }

  void _apply() {
    if (!isPlayerStatisticsDateRangeValid(_selection.dateFrom, _selection.dateTo)) {
      setState(() {
        _errorMessage = '시작일은 종료일보다 늦을 수 없습니다.';
      });
      return;
    }
    Navigator.of(context).pop(_selection);
  }

  void _reset() {
    Navigator.of(context).pop(const PlayerStatisticsFilterSelection());
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
                    Text('통계 필터', style: Theme.of(context).textTheme.titleLarge),
                    TextButton(onPressed: _reset, child: const Text('초기화')),
                  ],
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<int?>(
                  initialValue: _selection.trackId,
                  decoration: const InputDecoration(labelText: '경기장'),
                  items: [
                    const DropdownMenuItem<int?>(
                      value: null,
                      child: Text('전체 경기장'),
                    ),
                    ...widget.tracks.map(
                      (track) => DropdownMenuItem<int?>(
                        value: track.id,
                        child: Text(track.name),
                      ),
                    ),
                  ],
                  onChanged: (value) {
                    final selectedTrack = value == null
                        ? null
                        : widget.tracks.where((track) => track.id == value).isEmpty
                            ? null
                            : widget.tracks.firstWhere((track) => track.id == value);
                    setState(() {
                      _selection = value == null
                          ? _selection.copyWith(
                              clearTrackId: true,
                              clearTrackName: true,
                            )
                          : _selection.copyWith(
                              trackId: value,
                              trackName: selectedTrack?.name,
                              clearTrackId: false,
                              clearTrackName: false,
                            );
                    });
                  },
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton(
                        onPressed: () => _pickDate(isFrom: true),
                        child: Text(_selection.dateFrom == null ? '시작일 선택' : _formatDate(_selection.dateFrom!)),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: OutlinedButton(
                        onPressed: () => _pickDate(isFrom: false),
                        child: Text(_selection.dateTo == null ? '종료일 선택' : _formatDate(_selection.dateTo!)),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<int?>(
                  initialValue: _selection.lastN,
                  decoration: const InputDecoration(labelText: '최근 경기 수'),
                  items: const [
                    DropdownMenuItem<int?>(value: null, child: Text('전체')),
                    DropdownMenuItem<int?>(value: 5, child: Text('최근 5경기')),
                    DropdownMenuItem<int?>(value: 10, child: Text('최근 10경기')),
                    DropdownMenuItem<int?>(value: 20, child: Text('최근 20경기')),
                    DropdownMenuItem<int?>(value: 50, child: Text('최근 50경기')),
                  ],
                  onChanged: (value) {
                    setState(() {
                      _selection = _selection.copyWith(lastN: value);
                    });
                  },
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String?>(
                  initialValue: _selection.grade,
                  decoration: const InputDecoration(labelText: '등급'),
                  items: [
                    const DropdownMenuItem<String?>(value: null, child: Text('전체')),
                    ..._gradeOptions.map(
                      (grade) => DropdownMenuItem<String?>(
                        value: grade,
                        child: Text(grade),
                      ),
                    ),
                  ],
                  onChanged: (value) {
                    setState(() {
                      _selection = _selection.copyWith(grade: value);
                    });
                  },
                ),
                if (_errorMessage != null) ...[
                  const SizedBox(height: 12),
                  Text(_errorMessage!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
                ],
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
