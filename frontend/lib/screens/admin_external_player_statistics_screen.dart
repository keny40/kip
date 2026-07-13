import 'package:flutter/material.dart';

import '../models/external_player_admin.dart';
import '../routes/app_router.dart';
import '../services/api_client.dart';
import '../services/auth_service.dart';
import '../widgets/admin_readonly_widgets.dart';

typedef ExternalPlayerStatisticsLoader = Future<ExternalPlayerStatisticPage>
    Function(
  ExternalPlayerStatisticFilters filters,
  int page,
  int pageSize,
);
typedef ExternalPlayerStatisticDetailLoader
    = Future<ExternalPlayerStatisticAdmin> Function(int id);

class AdminExternalPlayerStatisticsScreen extends StatefulWidget {
  AdminExternalPlayerStatisticsScreen({
    super.key,
    AuthService? authService,
    ApiClient? apiClient,
    this.loader,
    this.detailLoader,
  })  : authService = authService ?? AuthService(),
        apiClient = apiClient;

  final AuthService authService;
  final ApiClient? apiClient;
  final ExternalPlayerStatisticsLoader? loader;
  final ExternalPlayerStatisticDetailLoader? detailLoader;

  @override
  State<AdminExternalPlayerStatisticsScreen> createState() =>
      _AdminExternalPlayerStatisticsScreenState();
}

class _AdminExternalPlayerStatisticsScreenState
    extends State<AdminExternalPlayerStatisticsScreen> {
  final _year = TextEditingController(text: '2025');
  final _name = TextEditingController();
  final _period = TextEditingController();
  final _grade = TextEditingController();
  ExternalPlayerStatisticPage? _data;
  bool _loading = false;
  String? _error;
  int _page = 1;
  int _pageSize = 20;

  late final ApiClient _api = widget.apiClient ??
      ApiClient(bearerToken: widget.authService.accessToken);
  late final ExternalPlayerStatisticsLoader _loader = widget.loader ??
      (filters, page, pageSize) => _api.fetchAdminExternalPlayerStatistics(
            filters: filters,
            page: page,
            pageSize: pageSize,
          );
  late final ExternalPlayerStatisticDetailLoader _detailLoader =
      widget.detailLoader ?? _api.fetchAdminExternalPlayerStatistic;

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

  ExternalPlayerStatisticFilters get _filters => ExternalPlayerStatisticFilters(
        year: _year.text,
        racerName: _name.text,
        periodNumber: _period.text,
        grade: _grade.text,
      );

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final data = await _loader(_filters, _page, _pageSize);
      if (mounted) setState(() => _data = data);
    } on ApiException catch (error) {
      if (mounted) _handleError(error);
    } catch (_) {
      if (mounted) setState(() => _error = '네트워크 오류가 발생했습니다.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _handleError(ApiException error) {
    if (error.statusCode == 401) {
      widget.authService.logout();
      Navigator.of(context).pushReplacementNamed(AppRouter.adminLogin);
    } else if (error.statusCode == 403) {
      setState(() => _error = '관리자 권한이 없습니다.');
    } else {
      setState(() => _error = '서버 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.');
    }
  }

  void _reset() {
    _year.text = '2025';
    _name.clear();
    _period.clear();
    _grade.clear();
    _page = 1;
    _load();
  }

  Widget _field(String label, TextEditingController controller) => SizedBox(
        width: 180,
        child: TextField(
            controller: controller,
            decoration: InputDecoration(
                labelText: label, border: const OutlineInputBorder())),
      );

  Future<void> _showDetail(int id) async {
    try {
      final item = await _detailLoader(id);
      if (!mounted) return;
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('선수 통계 상세'),
          content: SizedBox(
            width: 600,
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                      '${item.standardYear} · ${item.racerName} · ${adminValue(item.periodNumber)}기 · ${item.grade}'),
                  const SizedBox(height: 12),
                  Text('출전 횟수: ${adminValue(item.runCount)}'),
                  Text('출전일수: ${adminValue(item.runDayCount)}'),
                  ...List.generate(
                      9,
                      (index) => Text(
                          '${index + 1}위 횟수: ${adminValue(item.rankCounts[index])}')),
                  Text('탈락 횟수: ${adminValue(item.eliminatedCount)}'),
                  Text('승률: ${adminValue(item.winRate)}'),
                  Text('연대율: ${adminValue(item.highRate)}'),
                  Text('삼연대율: ${adminValue(item.high3Rate)}'),
                  const SizedBox(height: 12),
                  Text('수집: ${adminDate(item.collectedAt)}'),
                  Text('생성: ${adminDate(item.createdAt)}'),
                  Text('수정: ${adminDate(item.updatedAt)}'),
                ],
              ),
            ),
          ),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('닫기'))
          ],
        ),
      );
    } on ApiException catch (error) {
      if (!mounted) return;
      if (error.statusCode == 404) {
        ScaffoldMessenger.of(context)
            .showSnackBar(const SnackBar(content: Text('상세 정보를 찾을 수 없습니다.')));
      } else {
        _handleError(error);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final data = _data;
    return Scaffold(
      appBar: AppBar(title: const Text('선수 통계 staging')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          AdminFilterPanel(
            onSearch: () {
              _page = 1;
              _load();
            },
            onReset: _reset,
            children: [
              _field('연도', _year),
              _field('선수명', _name),
              _field('기수', _period),
              _field('등급', _grade)
            ],
          ),
          if (_loading)
            const Padding(
                padding: EdgeInsets.all(32),
                child: Center(child: CircularProgressIndicator())),
          if (_error != null) adminMessageCard(context, _error!, error: true),
          if (!_loading && _error == null && data != null && data.items.isEmpty)
            adminMessageCard(context, '조건에 맞는 선수 통계가 없습니다.'),
          if (!_loading &&
              _error == null &&
              data != null &&
              data.items.isNotEmpty) ...[
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: DataTable(
                columns: const [
                  DataColumn(label: Text('연도')),
                  DataColumn(label: Text('선수명')),
                  DataColumn(label: Text('기수')),
                  DataColumn(label: Text('등급')),
                  DataColumn(label: Text('출전')),
                  DataColumn(label: Text('1위')),
                  DataColumn(label: Text('2위')),
                  DataColumn(label: Text('3위')),
                  DataColumn(label: Text('승률')),
                  DataColumn(label: Text('연대율')),
                  DataColumn(label: Text('삼연대율')),
                  DataColumn(label: Text('수집일시')),
                ],
                rows: data.items
                    .map((item) => DataRow(
                          onSelectChanged: (_) => _showDetail(item.id),
                          cells: [
                            DataCell(Text(item.standardYear)),
                            DataCell(Text(item.racerName)),
                            DataCell(Text(adminValue(item.periodNumber))),
                            DataCell(Text(item.grade)),
                            DataCell(Text(adminValue(item.runCount))),
                            DataCell(Text(adminValue(item.rankCounts[0]))),
                            DataCell(Text(adminValue(item.rankCounts[1]))),
                            DataCell(Text(adminValue(item.rankCounts[2]))),
                            DataCell(Text(adminValue(item.winRate))),
                            DataCell(Text(adminValue(item.highRate))),
                            DataCell(Text(adminValue(item.high3Rate))),
                            DataCell(Text(adminDate(item.collectedAt))),
                          ],
                        ))
                    .toList(),
              ),
            ),
            AdminPaginationBar(
              page: data.meta.page,
              pageSize: data.meta.pageSize,
              total: data.meta.total,
              onPrevious: _page > 1
                  ? () {
                      _page--;
                      _load();
                    }
                  : null,
              onNext: _page * _pageSize < data.meta.total
                  ? () {
                      _page++;
                      _load();
                    }
                  : null,
              onPageSizeChanged: (value) {
                if (value != null) {
                  _pageSize = value;
                  _page = 1;
                  _load();
                }
              },
            ),
          ],
        ],
      ),
    );
  }
}
