import 'package:flutter/material.dart';

import 'routes/app_router.dart';
import 'screens/main_shell_screen.dart';

void main() {
  runApp(const KipApp());
}

class KipApp extends StatelessWidget {
  const KipApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'KIP',
      debugShowCheckedModeBanner: false,
      home: const MainShellScreen(),
      routes: AppRouter.routes,
    );
  }
}