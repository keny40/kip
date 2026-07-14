import 'package:flutter/material.dart';

import '../models/data_quality_summary.dart';
import '../routes/app_router.dart';
import '../services/api_client.dart';
import '../services/auth_service.dart';
import '../widgets/admin_readonly_widgets.dart';

typedef DataQualityLoader = Future<DataQualitySummary> Function(
    DataQualityFilters filters);

class AdminDataQualityScreen extends StatefulWidget {
  AdminDataQualityScreen(
      {super.key, AuthService? authService, ApiClient? apiClient, this.loader})
      : authService = authService ?? AuthService(),
        apiClient = apiClient;
  final AuthService authService;
  final ApiClient? apiClient;
  final DataQualityLoader? loader;
  @override
  State<AdminDataQualityScreen> createState() => _AdminDataQualityScreenState();
}

class _AdminDataQualityScreenState extends State<AdminDataQualityScreen> {
  final _year = TextEditingController(text: '2025');
  final _source = TextEditingController();
  DataQualitySummary? _summary;
  bool _loading = false;
  String? _error;
  late final ApiClient _api = widget.apiClient ??
      ApiClient(bearerToken: widget.authService.accessToken);
  late final DataQualityLoader _loader = widget.loader ??
      (filters) => _api.fetchAdminDataQualitySummary(filters: filters);

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      if (widget.authService.currentUser == null) {
        Navigator.of(context).pushReplacementNamed(AppRouter.adminLogin);
      } else {
        _load();
      }
    });
  }

  @override
  void dispose() {
    _year.dispose();
    _source.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final value = await _loader(
          DataQualityFilters(year: _year.text, source: _source.text));
      if (mounted) setState(() => _summary = value);
    } on ApiException catch (error) {
      if (!mounted) return;
      if (error.statusCode == 401) {
        widget.authService.logout();
        Navigator.of(context).pushReplacementNamed(AppRouter.adminLogin);
      } else if (error.statusCode == 403) {
        setState(() => _error = '관리자 권한이 없습니다.');
      } else {
        setState(() => _error = '서버 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.');
      }
    } catch (_) {
      if (mounted) setState(() => _error = '네트워크 오류가 발생했습니다.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  String _date(DateTime? value) => value == null ? '미수집' : adminDate(value);
  void _go(String route) => Navigator.of(context).pushNamed(route);

  @override
  Widget build(BuildContext context) {
    final data = _summary;
    return Scaffold(
      appBar: AppBar(title: const Text('데이터 품질')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        AdminFilterPanel(
            onSearch: _load,
            onReset: () {
              _year.text = '2025';
              _source.clear();
              _load();
            },
            children: [
              SizedBox(
                  width: 180,
                  child: TextField(
                      key: const Key('quality_year'),
                      controller: _year,
                      decoration: const InputDecoration(
                          labelText: '연도', border: OutlineInputBorder()))),
              SizedBox(
                  width: 180,
                  child: TextField(
                      key: const Key('quality_source'),
                      controller: _source,
                      decoration: const InputDecoration(
                          labelText: 'source', border: OutlineInputBorder()))),
              FilledButton.icon(
                  key: const Key('quality_refresh'),
                  onPressed: _load,
                  icon: const Icon(Icons.refresh),
                  label: const Text('새로고침')),
            ]),
        if (_loading)
          const Padding(
              padding: EdgeInsets.all(32),
              child: Center(child: CircularProgressIndicator())),
        if (_error != null) adminMessageCard(context, _error!, error: true),
        if (!_loading && _error == null && data != null) ...[
          Text('마지막 수집 시각: ${_date(data.latestCollectedAt)}'),
          const SizedBox(height: 12),
          LayoutBuilder(builder: (context, constraints) {
            final width = constraints.maxWidth < 560
                ? constraints.maxWidth
                : (constraints.maxWidth - 24) / 3;
            return Wrap(spacing: 12, runSpacing: 12, children: [
              _card('기존 선수', data.counts.players, width, AppRouter.adminHome),
              _card('외부 선수', data.counts.externalPlayers, width,
                  AppRouter.adminExternalPlayers),
              _card('선수 통계', data.counts.statistics, width,
                  AppRouter.adminExternalPlayerStatistics),
              _card('유일 후보', data.matchStatusCounts['UNIQUE_CANDIDATE'] ?? 0,
                  width, AppRouter.adminPlayerMatchCandidates),
              _card('후보 없음', data.matchStatusCounts['NO_CANDIDATE'] ?? 0, width,
                  AppRouter.adminPlayerMatchCandidates),
              _card('복수 후보', data.matchStatusCounts['MULTIPLE_CANDIDATES'] ?? 0,
                  width, AppRouter.adminPlayerMatchCandidates),
              _card('연결 가능률', '${data.coverage.rate.toStringAsFixed(1)}%',
                  width, AppRouter.adminPlayerMatchCandidates),
            ]);
          }),
          const SizedBox(height: 16),
          _panel('품질 항목', [
            (
              '기수 누락',
              data.externalPlayersQuality.missingPeriod +
                  data.statisticsQuality.missingPeriod
            ),
            (
              '등급 미확인',
              data.externalPlayersQuality.unknownGrade +
                  data.statisticsQuality.unknownGrade
            ),
            ('지역 미확인', data.externalPlayersQuality.unknownRegion),
            ('상태 미확인', data.externalPlayersQuality.unknownStatus),
            (
              '통계값 NULL',
              data.statisticsQuality.invalidRunCount +
                  data.statisticsQuality.nullRateTotal
            ),
            ('잠정키 중복', data.statisticsQuality.duplicates),
          ]),
          _panel('매칭 상태', [
            ('유일 후보', data.matchStatusCounts['UNIQUE_CANDIDATE'] ?? 0),
            ('후보 없음', data.matchStatusCounts['NO_CANDIDATE'] ?? 0),
            ('복수 후보', data.matchStatusCounts['MULTIPLE_CANDIDATES'] ?? 0),
            ('기수 미확인', data.matchStatusCounts['MISSING_PERIOD_NUMBER'] ?? 0),
            ('등급 불일치', data.matchStatusCounts['GRADE_MISMATCH'] ?? 0),
          ]),
        ],
      ]),
    );
  }

  Widget _card(String label, Object value, double width, String route) =>
      SizedBox(
          width: width,
          child: Card(
              elevation: 0,
              child: InkWell(
                  onTap: () => _go(route),
                  child: Padding(
                      padding: const EdgeInsets.all(18),
                      child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(label),
                            const SizedBox(height: 8),
                            Text('$value',
                                style:
                                    Theme.of(context).textTheme.headlineSmall)
                          ])))));
  Widget _panel(String title, List<(String, int)> rows) => Card(
      elevation: 0,
      child: Padding(
          padding: const EdgeInsets.all(16),
          child:
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(title, style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            ...rows.map((row) => Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(children: [
                  Expanded(child: Text(row.$1)),
                  Chip(label: Text('${row.$2}'))
                ])))
          ])));
}
