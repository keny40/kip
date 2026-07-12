import 'package:flutter/material.dart';

import 'screens/main_shell_screen.dart';
import 'theme/app_theme.dart';

void main() {
  runApp(const KipApp());
}

class KipApp extends StatelessWidget {
  const KipApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Keirin Intelligence Platform',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      home: const MainShellScreen(),
    );
  }
}
