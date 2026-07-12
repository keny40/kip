import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:kip_frontend/models/current_user.dart';
import 'package:kip_frontend/screens/admin_home_screen.dart';
import 'package:kip_frontend/screens/admin_login_screen.dart';
import 'package:kip_frontend/services/auth_service.dart';

class FakeAuthService extends AuthService {
  FakeAuthService({
    required Future<CurrentUser> Function(String email, String password) onLogin,
    AuthSession? session,
  })  : _onLogin = onLogin,
        super(session: session ?? AuthSession());

  final Future<CurrentUser> Function(String email, String password) _onLogin;

  @override
  Future<CurrentUser> login(String email, String password) async {
    final user = await _onLogin(email, password);
    session.accessToken = 'token-123';
    session.currentUser = user;
    return user;
  }
}

CurrentUser _adminUser() {
  return CurrentUser(
    id: 1,
    email: 'admin@example.com',
    username: 'admin',
    role: 'admin',
    status: 'active',
    createdAt: DateTime.parse('2026-07-12T00:00:00Z'),
    updatedAt: DateTime.parse('2026-07-12T00:00:00Z'),
  );
}

void main() {
  Widget _buildApp(AuthService service) {
    return MaterialApp(
      home: AdminLoginScreen(authService: service),
    );
  }

  testWidgets('shows validation errors for empty fields and bad email format', (tester) async {
    final service = FakeAuthService(onLogin: (_, __) async => _adminUser());
    await tester.pumpWidget(_buildApp(service));

    await tester.tap(find.byKey(const Key('admin_login_button')));
    await tester.pump();

    expect(find.text('이메일을 입력해 주세요.'), findsOneWidget);
    expect(find.text('비밀번호를 입력해 주세요.'), findsOneWidget);

    await tester.enterText(find.byKey(const Key('admin_login_email')), 'invalid-email');
    await tester.enterText(find.byKey(const Key('admin_login_password')), 'secret');
    await tester.tap(find.byKey(const Key('admin_login_button')));
    await tester.pump();

    expect(find.text('올바른 이메일 형식이 아닙니다.'), findsOneWidget);
  });

  testWidgets('shows loading state while login is pending', (tester) async {
    final completer = Completer<CurrentUser>();
    final service = FakeAuthService(onLogin: (_, __) => completer.future);
    await tester.pumpWidget(_buildApp(service));

    await tester.enterText(find.byKey(const Key('admin_login_email')), 'admin@example.com');
    await tester.enterText(find.byKey(const Key('admin_login_password')), 'secret');
    await tester.tap(find.byKey(const Key('admin_login_button')));
    await tester.pump();

    expect(find.byType(CircularProgressIndicator), findsOneWidget);
  });

  testWidgets('shows failure message on invalid credentials', (tester) async {
    final service = FakeAuthService(
      onLogin: (_, __) async => throw AuthException.invalidCredentials(),
    );
    await tester.pumpWidget(_buildApp(service));

    await tester.enterText(find.byKey(const Key('admin_login_email')), 'admin@example.com');
    await tester.enterText(find.byKey(const Key('admin_login_password')), 'wrong');
    await tester.tap(find.byKey(const Key('admin_login_button')));
    await tester.pumpAndSettle();

    expect(find.text('이메일 또는 비밀번호가 올바르지 않습니다.'), findsOneWidget);
  });

  testWidgets('navigates to admin home after successful login', (tester) async {
    final service = FakeAuthService(onLogin: (_, __) async => _adminUser());
    await tester.pumpWidget(
      MaterialApp(
        routes: {
          '/admin/home': (_) => AdminHomeScreen(authService: service),
        },
        home: AdminLoginScreen(authService: service),
      ),
    );

    await tester.enterText(find.byKey(const Key('admin_login_email')), 'admin@example.com');
    await tester.enterText(find.byKey(const Key('admin_login_password')), 'secret');
    await tester.tap(find.byKey(const Key('admin_login_button')));
    await tester.pumpAndSettle();

    expect(find.text('관리자 로그인 성공'), findsOneWidget);
    expect(find.textContaining('admin@example.com'), findsOneWidget);
  });
}
