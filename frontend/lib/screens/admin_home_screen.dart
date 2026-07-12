import 'package:flutter/material.dart';

import '../models/current_user.dart';
import '../routes/app_router.dart';
import '../services/auth_service.dart';

class AdminHomeScreen extends StatefulWidget {
  AdminHomeScreen({
    super.key,
    AuthService? authService,
    this.currentUser,
  }) : authService = authService ?? AuthService();

  final AuthService authService;
  final CurrentUser? currentUser;

  @override
  State<AdminHomeScreen> createState() => _AdminHomeScreenState();
}

class _AdminHomeScreenState extends State<AdminHomeScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) {
        return;
      }
      if (widget.authService.currentUser == null) {
        Navigator.of(context).pushReplacementNamed(AppRouter.adminLogin);
      }
    });
  }

  Future<void> _logout() async {
    widget.authService.logout();
    if (!mounted) {
      return;
    }
    Navigator.of(context).pushReplacementNamed(AppRouter.adminLogin);
  }

  void _openCsvUpload() {
    Navigator.of(context).pushNamed(AppRouter.adminCsvUpload);
  }

  @override
  Widget build(BuildContext context) {
    final user = widget.currentUser ?? widget.authService.currentUser;
    if (user == null) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('관리자 홈'),
        actions: [
          IconButton(
            onPressed: _openCsvUpload,
            icon: const Icon(Icons.upload_file_outlined),
            tooltip: 'CSV 업로드',
          ),
          IconButton(
            onPressed: _logout,
            icon: const Icon(Icons.logout),
            tooltip: '로그아웃',
          ),
        ],
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 480),
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Card(
              elevation: 0,
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text('관리자 로그인 성공', style: Theme.of(context).textTheme.headlineSmall),
                    const SizedBox(height: 16),
                    Text('이메일: ${user.email}'),
                    const SizedBox(height: 8),
                    Text('역할: ${user.role}'),
                    const SizedBox(height: 8),
                    Text('상태: ${user.status}'),
                    const SizedBox(height: 24),
                    FilledButton.icon(
                      onPressed: _openCsvUpload,
                      icon: const Icon(Icons.upload_file),
                      label: const Text('CSV 업로드'),
                    ),
                    const SizedBox(height: 12),
                    OutlinedButton.icon(
                      onPressed: _logout,
                      icon: const Icon(Icons.logout),
                      label: const Text('로그아웃'),
                    ),
                    const SizedBox(height: 16),
                    const Text('관리자 데이터 관리 화면은 다음 단계에서 제공됩니다.'),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
