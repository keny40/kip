import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../models/admin_import.dart';
import '../routes/app_router.dart';
import '../services/api_client.dart';
import '../services/auth_service.dart';
import '../services/csv_file_picker.dart';

typedef AdminCsvUploader = Future<AdminImportResult> Function({
  required String importType,
  required List<int> bytes,
  required String filename,
  required bool dryRun,
});

class AdminCsvUploadScreen extends StatefulWidget {
  AdminCsvUploadScreen({
    super.key,
    AuthService? authService,
    ApiClient? apiClient,
    CsvFilePicker? filePicker,
    AdminCsvUploader? uploader,
  })  : authService = authService ?? AuthService(),
        apiClient = apiClient,
        filePicker = filePicker ?? createCsvFilePicker(),
        uploader = uploader;

  final AuthService authService;
  final ApiClient? apiClient;
  final CsvFilePicker filePicker;
  final AdminCsvUploader? uploader;

  @override
  State<AdminCsvUploadScreen> createState() => _AdminCsvUploadScreenState();
}

class _AdminCsvUploadScreenState extends State<AdminCsvUploadScreen> {
  static const Map<String, String> _importLabels = {
    'tracks': '경기장',
    'players': '선수',
    'races': '경주',
    'entries': '출전 엔트리',
    'results': '결과',
  };

  static const List<String> _recommendedOrder = [
    'tracks',
    'players',
    'races',
    'entries',
    'results',
  ];

  String _importType = 'players';
  CsvFileSelection? _selectedFile;
  CsvFileSelection? _validatedFile;
  AdminImportResult? _validationResult;
  AdminImportResult? _applyResult;
  bool _isValidating = false;
  bool _isApplying = false;
  bool _permissionDenied = false;
  String? _errorMessage;

  late final ApiClient _apiClient = widget.apiClient ??
      ApiClient(
        bearerToken: widget.authService.accessToken,
      );

  late final AdminCsvUploader _uploader = widget.uploader ??
      ({required String importType, required List<int> bytes, required String filename, required bool dryRun}) {
        return _apiClient.importAdminCsv(
          importType: importType,
          bytes: bytes,
          filename: filename,
          dryRun: dryRun,
        );
      };

  bool get _hasSelection => _selectedFile != null;

  bool get _selectionMatchesValidation {
    final selected = _selectedFile;
    final validated = _validatedFile;
    if (selected == null || validated == null) {
      return false;
    }
    return selected.filename == validated.filename &&
        selected.bytes.length == validated.bytes.length &&
        listEquals(selected.bytes, validated.bytes);
  }

  bool get _canApply {
    final result = _validationResult;
    return !_isValidating &&
        !_isApplying &&
        !_permissionDenied &&
        !_selectedFileIsMissing &&
        !_applyCompleted &&
        _selectionMatchesValidation &&
        result != null &&
        result.failed == 0;
  }

  bool get _selectedFileIsMissing => _selectedFile == null;

  bool get _applyCompleted => _applyResult != null;

  String _typeLabel(String type) => _importLabels[type] ?? type;

  String _resultSummary(AdminImportResult result) {
    return [
      '총 ${result.total}행',
      '생성 ${result.created}건',
      '수정 ${result.updated}건',
      '스킵 ${result.skipped}건',
      '실패 ${result.failed}건',
    ].join(' · ');
  }

  String _currentSelectionSummary() {
    final file = _selectedFile;
    if (file == null) {
      return '선택된 파일 없음';
    }
    return '${_typeLabel(_importType)} · ${file.filename} (${file.bytes.length} bytes)';
  }

  void _invalidateValidation({bool keepSelectedFile = true}) {
    if (!keepSelectedFile) {
      _selectedFile = null;
    }
    _validatedFile = null;
    _validationResult = null;
    _applyResult = null;
    _permissionDenied = false;
    _errorMessage = null;
  }

  Future<void> _pickFile() async {
    final selection = await widget.filePicker.pickCsvFile();
    if (!mounted) {
      return;
    }
    if (selection == null) {
      setState(() {
        _invalidateValidation(keepSelectedFile: true);
      });
      return;
    }

    final shouldInvalidate = _selectedFile == null || !_sameSelection(_selectedFile!, selection);
    setState(() {
      _selectedFile = selection;
      if (shouldInvalidate) {
        _invalidateValidation(keepSelectedFile: true);
      } else {
        _errorMessage = null;
      }
    });
  }

  bool _sameSelection(CsvFileSelection left, CsvFileSelection right) {
    return left.filename == right.filename &&
        left.bytes.length == right.bytes.length &&
        listEquals(left.bytes, right.bytes);
  }

  Future<void> _validateCsv() async {
    final selection = _selectedFile;
    if (_isValidating || selection == null) {
      if (selection == null) {
        setState(() {
          _errorMessage = '사전 검증할 CSV 파일을 먼저 선택해 주세요.';
        });
      }
      return;
    }

    setState(() {
      _isValidating = true;
      _errorMessage = null;
      _permissionDenied = false;
      _applyResult = null;
    });

    try {
      final result = await _uploader(
        importType: _importType,
        bytes: selection.bytes,
        filename: selection.filename,
        dryRun: true,
      );
      if (!mounted) {
        return;
      }
      setState(() {
        _validatedFile = selection;
        _validationResult = result;
        _applyResult = null;
      });
    } on ApiException catch (error) {
      if (!mounted) {
        return;
      }
      _handleApiException(error);
    } catch (_) {
      if (!mounted) {
        return;
      }
      setState(() {
        _errorMessage = 'CSV 업로드 요청에 실패했습니다.';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isValidating = false;
        });
      }
    }
  }

  Future<void> _confirmAndApply() async {
    if (!_canApply) {
      return;
    }
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('실제 반영 확인'),
          content: const Text('사전 검증이 완료된 CSV 데이터를 실제 데이터베이스에 반영하시겠습니까?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: const Text('취소'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(context).pop(true),
              child: const Text('확인'),
            ),
          ],
        );
      },
    );
    if (confirmed != true || !mounted) {
      return;
    }
    await _applyCsv();
  }

  Future<void> _applyCsv() async {
    final selection = _selectedFile;
    if (_isApplying || selection == null || !_selectionMatchesValidation) {
      return;
    }

    setState(() {
      _isApplying = true;
      _errorMessage = null;
      _permissionDenied = false;
    });

    try {
      final result = await _uploader(
        importType: _importType,
        bytes: selection.bytes,
        filename: selection.filename,
        dryRun: false,
      );
      if (!mounted) {
        return;
      }
      setState(() {
        _applyResult = result;
        _validatedFile = null;
        _validationResult = null;
      });
    } on ApiException catch (error) {
      if (!mounted) {
        return;
      }
      _handleApiException(error);
    } catch (_) {
      if (!mounted) {
        return;
      }
      setState(() {
        _errorMessage = 'CSV 업로드 요청에 실패했습니다.';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isApplying = false;
        });
      }
    }
  }

  void _handleApiException(ApiException error) {
    final statusCode = error.statusCode;
    if (statusCode == 401) {
      widget.authService.logout();
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('로그인이 만료되었습니다. 다시 로그인해 주세요.')),
      );
      Navigator.of(context).pushReplacementNamed(AppRouter.adminLogin);
      return;
    }
    if (statusCode == 403) {
      setState(() {
        _permissionDenied = true;
        _errorMessage = '관리자 권한이 없습니다.';
      });
      return;
    }
    if (statusCode == 413) {
      setState(() {
        _errorMessage = '파일 크기가 허용 한도를 초과했습니다.';
      });
      return;
    }
    if (statusCode == 400 || statusCode == 422) {
      setState(() {
        _errorMessage = error.message;
      });
      return;
    }
    setState(() {
      _errorMessage = '서버 연결에 실패했습니다. 잠시 후 다시 시도해 주세요.';
    });
  }

  void _changeImportType(String? value) {
    if (value == null || value == _importType) {
      return;
    }
    setState(() {
      _importType = value;
      _invalidateValidation(keepSelectedFile: true);
    });
  }

  Widget _buildResultCard(String title, AdminImportResult result) {
    return Card(
      elevation: 0,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            Text(_resultSummary(result)),
            const SizedBox(height: 4),
            Text('파일: ${result.filename}'),
            const SizedBox(height: 4),
            Text("모드: ${result.dryRun ? '사전 검증' : '실제 반영'}"),
            if (!result.dryRun && result.failed == 0) ...[
              const SizedBox(height: 8),
              const Text('실제 반영이 완료되었습니다. 동일 파일로 다시 반영하려면 다시 검증해 주세요.'),
            ],
            if (result.dryRun && result.failed > 0) ...[
              const SizedBox(height: 8),
              const Text('오류가 있는 경우 파일을 수정한 뒤 다시 사전 검증해 주세요.'),
            ],
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final user = widget.authService.currentUser;
    final validationResult = _validationResult;
    final applyResult = _applyResult;

    return Scaffold(
      appBar: AppBar(
        title: const Text('관리자 CSV 업로드'),
        leading: BackButton(
          onPressed: () {
            if (Navigator.of(context).canPop()) {
              Navigator.of(context).pop();
            } else {
              Navigator.of(context).pushReplacementNamed(AppRouter.adminHome);
            }
          },
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            elevation: 0,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('업로드 대상', style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    initialValue: _importType,
                    items: _recommendedOrder
                        .map(
                          (type) => DropdownMenuItem<String>(
                            value: type,
                            child: Text(_typeLabel(type)),
                          ),
                        )
                        .toList(),
                    onChanged: _isValidating || _isApplying ? null : _changeImportType,
                    decoration: const InputDecoration(
                      labelText: 'Import type',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      FilledButton.icon(
                        key: const Key('admin_csv_pick_button'),
                        onPressed: _isValidating || _isApplying ? null : _pickFile,
                        icon: const Icon(Icons.attach_file),
                        label: const Text('CSV 선택'),
                      ),
                      OutlinedButton.icon(
                        key: const Key('admin_csv_validate_button'),
                        onPressed: _isValidating || _isApplying || !_hasSelection ? null : _validateCsv,
                        icon: _isValidating
                            ? const SizedBox(
                                width: 16,
                                height: 16,
                                child: CircularProgressIndicator(strokeWidth: 2),
                              )
                            : const Icon(Icons.verified_outlined),
                        label: Text(_isValidating ? '검증 중' : '사전 검증'),
                      ),
                      FilledButton.icon(
                        key: const Key('admin_csv_apply_button'),
                        onPressed: _canApply ? _confirmAndApply : null,
                        icon: _isApplying
                            ? const SizedBox(
                                width: 16,
                                height: 16,
                                child: CircularProgressIndicator(strokeWidth: 2),
                              )
                            : const Icon(Icons.cloud_upload_outlined),
                        label: Text(_isApplying ? '반영 중' : '실제 반영'),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text(_currentSelectionSummary()),
                  const SizedBox(height: 8),
                  Text('권장 순서: ${_recommendedOrder.map(_typeLabel).join(' → ')}'),
                  if (user != null) ...[
                    const SizedBox(height: 8),
                    Text('로그인 사용자: ${user.email}'),
                  ],
                  const SizedBox(height: 8),
                  Text(
                    _permissionDenied
                        ? '관리자 권한이 없습니다.'
                        : '사전 검증이 성공하고 실패 행이 0개일 때만 실제 반영을 진행할 수 있습니다.',
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          if (_errorMessage != null)
            Card(
              elevation: 0,
              color: Theme.of(context).colorScheme.errorContainer,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Text(
                  _errorMessage!,
                  style: TextStyle(color: Theme.of(context).colorScheme.onErrorContainer),
                ),
              ),
            ),
          if (validationResult != null) ...[
            _buildResultCard('사전 검증 결과', validationResult),
            if (validationResult.errors.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text('행별 오류', style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              ...validationResult.errors.map(
                (error) => Card(
                  elevation: 0,
                  child: ListTile(
                    dense: true,
                    title: Text('Row ${error.rowNumber} · ${error.errorCode}'),
                    subtitle: Text(error.errorMessage),
                  ),
                ),
              ),
            ],
          ],
          if (applyResult != null) ...[
            const SizedBox(height: 16),
            _buildResultCard('실제 반영 결과', applyResult),
          ],
        ],
      ),
    );
  }
}
