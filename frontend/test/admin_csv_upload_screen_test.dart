import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:kip_frontend/models/admin_import.dart';
import 'package:kip_frontend/models/current_user.dart';
import 'package:kip_frontend/routes/app_router.dart';
import 'package:kip_frontend/screens/admin_csv_upload_screen.dart';
import 'package:kip_frontend/screens/admin_login_screen.dart';
import 'package:kip_frontend/services/api_client.dart';
import 'package:kip_frontend/services/auth_service.dart';
import 'package:kip_frontend/services/csv_file_picker.dart';

void main() {
  CurrentUser adminUser() {
    return CurrentUser(
      id: 1,
      email: 'admin@example.com',
      username: 'admin',
      role: 'admin',
      status: 'active',
      createdAt: DateTime.parse('2026-01-01T00:00:00Z'),
      updatedAt: DateTime.parse('2026-01-01T00:00:00Z'),
    );
  }

  TestAuthService buildAuthService() {
    final session = AuthSession();
    session.accessToken = 'token';
    session.currentUser = adminUser();
    return TestAuthService(session: session);
  }

  testWidgets('initial apply button is disabled', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        routes: {
          AppRouter.adminLogin: (_) => AdminLoginScreen(authService: buildAuthService()),
        },
        home: AdminCsvUploadScreen(
          authService: buildAuthService(),
          filePicker: FakeCsvFilePicker(null),
          uploader: fakeUploader,
        ),
      ),
    );

    final applyButton = tester.widget<FilledButton>(find.byKey(const Key('admin_csv_apply_button')));
    expect(applyButton.onPressed, isNull);
  });

  testWidgets('validation success enables apply button and apply confirms dry-run false', (tester) async {
    final calls = <AdminCsvUploadCall>[];

    Future<AdminImportResult> uploader({
      required String importType,
      required List<int> bytes,
      required String filename,
      required bool dryRun,
    }) async {
      calls.add(
        AdminCsvUploadCall(
          importType: importType,
          filename: filename,
          bytes: bytes,
          dryRun: dryRun,
        ),
      );
      return AdminImportResult(
        importType: importType,
        filename: filename,
        dryRun: dryRun,
        total: 2,
        created: 2,
        updated: 0,
        skipped: 0,
        failed: 0,
        errors: const [],
      );
    }

    final picker = MutableCsvFilePicker(
      const CsvFileSelection(
        filename: 'players.csv',
        bytes: [1, 2, 3],
      ),
    );

    await tester.pumpWidget(
      MaterialApp(
        routes: {
          AppRouter.adminLogin: (_) => AdminLoginScreen(authService: buildAuthService()),
        },
        home: AdminCsvUploadScreen(
          authService: buildAuthService(),
          filePicker: picker,
          uploader: uploader,
        ),
      ),
    );

    await tester.tap(find.byKey(const Key('admin_csv_pick_button')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('admin_csv_validate_button')));
    await tester.pumpAndSettle();

    final applyButton = tester.widget<FilledButton>(find.byKey(const Key('admin_csv_apply_button')));
    expect(applyButton.onPressed, isNotNull);

    await tester.tap(find.byKey(const Key('admin_csv_apply_button')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('확인'));
    await tester.pumpAndSettle();

    expect(calls, hasLength(2));
    expect(calls[0].dryRun, isTrue);
    expect(calls[1].dryRun, isFalse);
    expect(find.textContaining('실제 반영이 완료되었습니다.'), findsOneWidget);

    final disabledApply = tester.widget<FilledButton>(find.byKey(const Key('admin_csv_apply_button')));
    expect(disabledApply.onPressed, isNull);
  });

  testWidgets('failed validation keeps apply disabled', (tester) async {
    Future<AdminImportResult> uploader({
      required String importType,
      required List<int> bytes,
      required String filename,
      required bool dryRun,
    }) async {
      return AdminImportResult(
        importType: importType,
        filename: filename,
        dryRun: dryRun,
        total: 2,
        created: 1,
        updated: 0,
        skipped: 0,
        failed: 1,
        errors: const [
          AdminImportError(rowNumber: 2, errorCode: 'INVALID_VALUE', errorMessage: '필수 값이 누락되었습니다.'),
        ],
      );
    }

    await tester.pumpWidget(
      MaterialApp(
        home: AdminCsvUploadScreen(
          authService: buildAuthService(),
          filePicker: FakeCsvFilePicker(
            const CsvFileSelection(
              filename: 'players.csv',
              bytes: [1, 2, 3],
            ),
          ),
          uploader: uploader,
        ),
      ),
    );

    await tester.tap(find.byKey(const Key('admin_csv_pick_button')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('admin_csv_validate_button')));
    await tester.pumpAndSettle();

    expect(find.textContaining('실패 1건'), findsOneWidget);
    final applyButton = tester.widget<FilledButton>(find.byKey(const Key('admin_csv_apply_button')));
    expect(applyButton.onPressed, isNull);
  });

  testWidgets('changing type or file invalidates validation', (tester) async {
    final picker = MutableCsvFilePicker(
      const CsvFileSelection(
        filename: 'players.csv',
        bytes: [1, 2, 3],
      ),
    );

    await tester.pumpWidget(
      MaterialApp(
        home: AdminCsvUploadScreen(
          authService: buildAuthService(),
          filePicker: picker,
          uploader: fakeUploader,
        ),
      ),
    );

    await tester.tap(find.byKey(const Key('admin_csv_pick_button')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('admin_csv_validate_button')));
    await tester.pumpAndSettle();

    picker.selection = const CsvFileSelection(
      filename: 'players-updated.csv',
      bytes: [4, 5, 6],
    );
    await tester.tap(find.byKey(const Key('admin_csv_pick_button')));
    await tester.pumpAndSettle();

    final applyAfterFileChange = tester.widget<FilledButton>(find.byKey(const Key('admin_csv_apply_button')));
    expect(applyAfterFileChange.onPressed, isNull);

    await tester.tap(find.byType(DropdownButtonFormField<String>));
    await tester.pumpAndSettle();
    await tester.tap(find.text('경주').last);
    await tester.pumpAndSettle();

    final applyAfterTypeChange = tester.widget<FilledButton>(find.byKey(const Key('admin_csv_apply_button')));
    expect(applyAfterTypeChange.onPressed, isNull);
  });

  testWidgets('canceling file selection invalidates validation', (tester) async {
    final picker = MutableCsvFilePicker(
      const CsvFileSelection(
        filename: 'players.csv',
        bytes: [1, 2, 3],
      ),
    );

    await tester.pumpWidget(
      MaterialApp(
        home: AdminCsvUploadScreen(
          authService: buildAuthService(),
          filePicker: picker,
          uploader: fakeUploader,
        ),
      ),
    );

    await tester.tap(find.byKey(const Key('admin_csv_pick_button')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('admin_csv_validate_button')));
    await tester.pumpAndSettle();

    picker.selection = null;
    await tester.tap(find.byKey(const Key('admin_csv_pick_button')));
    await tester.pumpAndSettle();

    final applyButton = tester.widget<FilledButton>(find.byKey(const Key('admin_csv_apply_button')));
    expect(applyButton.onPressed, isNull);
  });

  testWidgets('403 keeps file state and shows permission error', (tester) async {
    Future<AdminImportResult> uploader({
      required String importType,
      required List<int> bytes,
      required String filename,
      required bool dryRun,
    }) async {
      throw ApiException('관리자 권한이 없습니다.', statusCode: 403);
    }

    await tester.pumpWidget(
      MaterialApp(
        home: AdminCsvUploadScreen(
          authService: buildAuthService(),
          filePicker: FakeCsvFilePicker(
            const CsvFileSelection(
              filename: 'players.csv',
              bytes: [1, 2, 3],
            ),
          ),
          uploader: uploader,
        ),
      ),
    );

    await tester.tap(find.byKey(const Key('admin_csv_pick_button')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('admin_csv_validate_button')));
    await tester.pumpAndSettle();

    expect(find.text('관리자 권한이 없습니다.').last, findsOneWidget);
    final applyButton = tester.widget<FilledButton>(find.byKey(const Key('admin_csv_apply_button')));
    expect(applyButton.onPressed, isNull);
  });

  testWidgets('401 clears session and redirects to admin login', (tester) async {
    final authService = buildAuthService();

    Future<AdminImportResult> uploader({
      required String importType,
      required List<int> bytes,
      required String filename,
      required bool dryRun,
    }) async {
      throw ApiException('로그인이 만료되었습니다.', statusCode: 401);
    }

    await tester.pumpWidget(
      MaterialApp(
        routes: {
          AppRouter.adminLogin: (_) => AdminLoginScreen(authService: authService),
        },
        home: AdminCsvUploadScreen(
          authService: authService,
          filePicker: FakeCsvFilePicker(
            const CsvFileSelection(
              filename: 'players.csv',
              bytes: [1, 2, 3],
            ),
          ),
          uploader: uploader,
        ),
      ),
    );

    await tester.tap(find.byKey(const Key('admin_csv_pick_button')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('admin_csv_validate_button')));
    await tester.pumpAndSettle();

    expect(authService.isLoggedIn, isFalse);
    expect(find.byType(AdminLoginScreen), findsOneWidget);
  });

  testWidgets('413 shows file size error and keeps file selection', (tester) async {
    Future<AdminImportResult> uploader({
      required String importType,
      required List<int> bytes,
      required String filename,
      required bool dryRun,
    }) async {
      throw ApiException('CSV file exceeds maximum size of 10 bytes', statusCode: 413);
    }

    await tester.pumpWidget(
      MaterialApp(
        home: AdminCsvUploadScreen(
          authService: buildAuthService(),
          filePicker: FakeCsvFilePicker(
            const CsvFileSelection(
              filename: 'players.csv',
              bytes: [1, 2, 3],
            ),
          ),
          uploader: uploader,
        ),
      ),
    );

    await tester.tap(find.byKey(const Key('admin_csv_pick_button')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('admin_csv_validate_button')));
    await tester.pumpAndSettle();

    expect(find.text('파일 크기가 허용 한도를 초과했습니다.'), findsOneWidget);
    expect(find.textContaining('players.csv'), findsWidgets);
  });

  testWidgets('network failure keeps file and type for retry', (tester) async {
    Future<AdminImportResult> uploader({
      required String importType,
      required List<int> bytes,
      required String filename,
      required bool dryRun,
    }) async {
      throw ApiException('Request failed');
    }

    await tester.pumpWidget(
      MaterialApp(
        home: AdminCsvUploadScreen(
          authService: buildAuthService(),
          filePicker: FakeCsvFilePicker(
            const CsvFileSelection(
              filename: 'players.csv',
              bytes: [1, 2, 3],
            ),
          ),
          uploader: uploader,
        ),
      ),
    );

    await tester.tap(find.byKey(const Key('admin_csv_pick_button')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('admin_csv_validate_button')));
    await tester.pumpAndSettle();

    expect(find.text('서버 연결에 실패했습니다. 잠시 후 다시 시도해 주세요.'), findsOneWidget);
    expect(find.textContaining('players.csv'), findsWidgets);
  });
}

class TestAuthService extends AuthService {
  TestAuthService({required super.session});
}

class FakeCsvFilePicker implements CsvFilePicker {
  FakeCsvFilePicker(this.selection);

  CsvFileSelection? selection;

  @override
  Future<CsvFileSelection?> pickCsvFile() async => selection;
}

class MutableCsvFilePicker extends FakeCsvFilePicker {
  MutableCsvFilePicker(super.selection);
}

class AdminCsvUploadCall {
  AdminCsvUploadCall({
    required this.importType,
    required this.filename,
    required this.bytes,
    required this.dryRun,
  });

  final String importType;
  final String filename;
  final List<int> bytes;
  final bool dryRun;
}

Future<AdminImportResult> fakeUploader({
  required String importType,
  required List<int> bytes,
  required String filename,
  required bool dryRun,
}) async {
  return AdminImportResult(
    importType: importType,
    filename: filename,
    dryRun: dryRun,
    total: bytes.length,
    created: 0,
    updated: 0,
    skipped: 0,
    failed: 0,
    errors: const [],
  );
}
