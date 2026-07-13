import 'package:flutter/material.dart';

import '../models/external_player_admin.dart';
import '../routes/app_router.dart';
import '../services/api_client.dart';
import '../services/auth_service.dart';
import '../widgets/admin_readonly_widgets.dart';

typedef PlayerMatchCandidatesLoader = Future<List<PlayerMatchCandidateAdmin>>
    Function(
  PlayerMatchCandidateFilters filters,
);

class AdminPlayerMatchCandidatesScreen extends StatefulWidget {
  AdminPlayerMatchCandidatesScreen({
    super.key,
    AuthService? authService,
    ApiClient? apiClient,
    this.loader,
  })  : authService = authService ?? AuthService(),
        apiClient = apiClient;

  final AuthService authService;
  final ApiClient? apiClient;
  final PlayerMatchCandidatesLoader? loader;

  @override
  State<AdminPlayerMatchCandidatesScreen> createState() =>
      _AdminPlayerMatchCandidatesScreenState();
}

class _AdminPlayerMatchCandidatesScreenState
    extends State<AdminPlayerMatchCandidatesScreen> {
  final _year = TextEditingController(text: '2025');
  final _name = TextEditingController();
  final _period = TextEditingController();
  final _grade = TextEditingController();
  String? _status;
  List<PlayerMatchCandidateAdmin>? _items;
  bool _loading = false;
  String? _error;

  late final ApiClient _api = widget.apiClient ??
      ApiClient(bearerToken: widget.authService.accessToken);
  late final PlayerMatchCandidatesLoader _loader = widget.loader ??
      (filters) => _api.fetchAdminPlayerMatchCandidates(filters: filters);

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
    for (final controller in [_year, _name, _period, _grade]) {
      controller.dispose();
    }
    super.dispose();
  }

  PlayerMatchCandidateFilters get _filters => PlayerMatchCandidateFilters(
        year: _year.text,
        racerName: _name.text,
        periodNumber: _period.text,
        grade: _grade.text,
        matchStatus: _status,
      );

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final items = await _loader(_filters);
      if (mounted) setState(() => _items = items);
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

  void _reset() {
    _year.text = '2025';
    _name.clear();
    _period.clear();
    _grade.clear();
    _status = null;
    _load();
  }

  Widget _field(String label, TextEditingController controller) => SizedBox(
        width: 180,
        child: TextField(
            controller: controller,
            decoration: InputDecoration(
                labelText: label, border: const OutlineInputBorder())),
      );

  @override
  Widget build(BuildContext context) {
    final items = _items;
    return Scaffold(
      appBar: AppBar(title: const Text('매칭 후보 검토')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          AdminFilterPanel(
            onSearch: _load,
            onReset: _reset,
            children: [
              _field('연도', _year),
              _field('선수명', _name),
              _field('기수', _period),
              _field('등급', _grade),
              SizedBox(
                width: 200,
                child: DropdownButtonFormField<String?>(
                  key: const Key('match_status_filter'),
                  initialValue: _status,
                  decoration: const InputDecoration(
                      labelText: '매칭 상태', border: OutlineInputBorder()),
                  items: const [
                    DropdownMenuItem<String?>(value: null, child: Text('전체')),
                    DropdownMenuItem(
                        value: 'UNIQUE_CANDIDATE', child: Text('유일 후보')),
                    DropdownMenuItem(
                        value: 'NO_CANDIDATE', child: Text('후보 없음')),
                    DropdownMenuItem(
                        value: 'MULTIPLE_CANDIDATES', child: Text('복수 후보')),
                    DropdownMenuItem(
                        value: 'MISSING_PERIOD_NUMBER', child: Text('기수 미확인')),
                    DropdownMenuItem(
                        value: 'GRADE_MISMATCH', child: Text('등급 불일치')),
                  ],
                  onChanged: (value) => setState(() => _status = value),
                ),
              ),
            ],
          ),
          const Card(
            elevation: 0,
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Text('읽기 전용 후보 검토 화면입니다. 자동 연결이나 승인 저장 기능은 제공하지 않습니다.'),
            ),
          ),
          if (_loading)
            const Padding(
                padding: EdgeInsets.all(32),
                child: Center(child: CircularProgressIndicator())),
          if (_error != null) adminMessageCard(context, _error!, error: true),
          if (!_loading && _error == null && items != null && items.isEmpty)
            adminMessageCard(context, '조건에 맞는 매칭 후보가 없습니다.'),
          if (!_loading && _error == null && items != null && items.isNotEmpty)
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: DataTable(
                columns: const [
                  DataColumn(label: Text('통계 ID')),
                  DataColumn(label: Text('연도')),
                  DataColumn(label: Text('선수명')),
                  DataColumn(label: Text('기수')),
                  DataColumn(label: Text('통계 등급')),
                  DataColumn(label: Text('후보 수')),
                  DataColumn(label: Text('상태')),
                  DataColumn(label: Text('External ID')),
                  DataColumn(label: Text('외부 등급')),
                  DataColumn(label: Text('등급 일치')),
                ],
                rows: items
                    .map((item) => DataRow(cells: [
                          DataCell(Text('${item.statisticId}')),
                          DataCell(Text(item.standardYear)),
                          DataCell(Text(item.maskedRacerName)),
                          DataCell(Text(adminValue(item.periodNumber))),
                          DataCell(Text(item.statisticGrade)),
                          DataCell(Text('${item.candidateCount}')),
                          DataCell(Chip(label: Text(item.statusLabel))),
                          DataCell(Text(adminValue(item.maskedExternalId))),
                          DataCell(Text(adminValue(item.externalGrade))),
                          DataCell(Text(item.gradeMatches == null
                              ? '-'
                              : (item.gradeMatches! ? '일치' : '불일치'))),
                        ]))
                    .toList(),
              ),
            ),
        ],
      ),
    );
  }
}
