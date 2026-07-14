import 'package:flutter/material.dart';

import '../models/external_player_admin.dart';
import '../routes/app_router.dart';
import '../services/api_client.dart';
import '../services/auth_service.dart';
import '../services/external_link_opener.dart';
import '../utils/display_labels.dart';
import '../widgets/admin_readonly_widgets.dart';

typedef ExternalPlayersLoader = Future<ExternalPlayerPage> Function(
  ExternalPlayerFilters filters,
  int page,
  int pageSize,
);
typedef ExternalPlayerDetailLoader = Future<ExternalPlayerAdmin> Function(
    int id);

class AdminExternalPlayersScreen extends StatefulWidget {
  AdminExternalPlayersScreen({
    super.key,
    AuthService? authService,
    ApiClient? apiClient,
    this.loader,
    this.detailLoader,
    this.linkOpener = openExternalLink,
  })  : authService = authService ?? AuthService(),
        apiClient = apiClient;

  final AuthService authService;
  final ApiClient? apiClient;
  final ExternalPlayersLoader? loader;
  final ExternalPlayerDetailLoader? detailLoader;
  final void Function(String url) linkOpener;

  @override
  State<AdminExternalPlayersScreen> createState() =>
      _AdminExternalPlayersScreenState();
}

class _AdminExternalPlayersScreenState
    extends State<AdminExternalPlayersScreen> {
  final _source = TextEditingController(text: 'kcycle');
  final _name = TextEditingController();
  final _period = TextEditingController();
  final _grade = TextEditingController();
  final _status = TextEditingController();
  ExternalPlayerPage? _data;
  bool _loading = false;
  String? _error;
  int _page = 1;
  int _pageSize = 20;

  late final ApiClient _api = widget.apiClient ??
      ApiClient(bearerToken: widget.authService.accessToken);
  late final ExternalPlayersLoader _loader = widget.loader ??
      (filters, page, pageSize) => _api.fetchAdminExternalPlayers(
            filters: filters,
            page: page,
            pageSize: pageSize,
          );
  late final ExternalPlayerDetailLoader _detailLoader =
      widget.detailLoader ?? _api.fetchAdminExternalPlayer;

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
    for (final controller in [_source, _name, _period, _grade, _status]) {
      controller.dispose();
    }
    super.dispose();
  }

  ExternalPlayerFilters get _filters => ExternalPlayerFilters(
        source: _source.text,
        name: _name.text,
        periodNumber: _period.text,
        grade: _grade.text,
        status: _status.text,
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
    _source.text = 'kcycle';
    for (final controller in [_name, _period, _grade, _status]) {
      controller.clear();
    }
    _page = 1;
    _load();
  }

  Future<void> _showDetail(int id) async {
    try {
      final item = await _detailLoader(id);
      if (!mounted) return;
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('외부 선수 상세'),
          content: SizedBox(
            width: 560,
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _detail('External ID', item.externalId),
                  _detail('이름', item.name),
                  _detail('기수', adminValue(item.periodNumber)),
                  _detail('등급', optionalLabel(item.grade)),
                  _detail('지역', optionalLabel(item.region)),
                  _detail('상태', statusLabel(item.status)),
                  _detail('원본 갱신', adminDate(item.sourceUpdatedAt)),
                  _detail('수집', adminDate(item.collectedAt)),
                  _detail('생성', adminDate(item.createdAt)),
                  _detail('수정', adminDate(item.updatedAt)),
                  if (item.detailUrl != null)
                    TextButton.icon(
                      key: const Key('external_player_detail_link'),
                      onPressed: () => widget.linkOpener(item.detailUrl!),
                      icon: const Icon(Icons.open_in_new),
                      label: const Text('KCYCLE 상세 새 창으로 열기'),
                    ),
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

  Widget _detail(String label, String value) => Padding(
        padding: const EdgeInsets.only(bottom: 8),
        child: Text('$label: $value'),
      );

  Widget _field(String label, TextEditingController controller) => SizedBox(
        width: 180,
        child: TextField(
            controller: controller,
            decoration: InputDecoration(
                labelText: label, border: const OutlineInputBorder())),
      );

  @override
  Widget build(BuildContext context) {
    final data = _data;
    return Scaffold(
      appBar: AppBar(title: const Text('외부 선수 staging')),
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
              _field('출처', _source),
              _field('이름', _name),
              _field('기수', _period),
              _field('등급', _grade),
              _field('상태', _status),
            ],
          ),
          if (_loading)
            const Padding(
                padding: EdgeInsets.all(32),
                child: Center(child: CircularProgressIndicator())),
          if (_error != null) adminMessageCard(context, _error!, error: true),
          if (!_loading && _error == null && data != null && data.items.isEmpty)
            adminMessageCard(context, '조건에 맞는 외부 선수가 없습니다.'),
          if (!_loading &&
              _error == null &&
              data != null &&
              data.items.isNotEmpty) ...[
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: DataTable(
                columns: const [
                  DataColumn(label: Text('출처')),
                  DataColumn(label: Text('External ID')),
                  DataColumn(label: Text('이름')),
                  DataColumn(label: Text('기수')),
                  DataColumn(label: Text('등급')),
                  DataColumn(label: Text('지역')),
                  DataColumn(label: Text('상태')),
                  DataColumn(label: Text('수집일시')),
                ],
                rows: data.items
                    .map((item) => DataRow(
                          onSelectChanged: (_) => _showDetail(item.id),
                          cells: [
                            DataCell(Text(item.source)),
                            DataCell(Text(item.externalId)),
                            DataCell(Text(item.name)),
                            DataCell(Text(adminValue(item.periodNumber))),
                            DataCell(Text(optionalLabel(item.grade))),
                            DataCell(Text(optionalLabel(item.region))),
                            DataCell(Chip(label: Text(statusLabel(item.status)))),
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
