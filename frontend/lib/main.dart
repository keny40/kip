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
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF2563EB),
          brightness: Brightness.light,
          surface: Colors.white,
        ),
        scaffoldBackgroundColor: const Color(0xFFF8FAFC),
        cardTheme: const CardThemeData(
          color: Colors.white,
          surfaceTintColor: Colors.transparent,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.all(Radius.circular(8)),
          ),
        ),
        navigationBarTheme: const NavigationBarThemeData(
          backgroundColor: Colors.white,
          indicatorColor: Color(0xFFE0ECFF),
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Colors.white,
          foregroundColor: Color(0xFF0F172A),
          surfaceTintColor: Colors.transparent,
        ),
      ),
      home: const MainShellScreen(),
      routes: AppRouter.routes,
    );
  }
}
