import 'package:flutter/material.dart';

import '../screens/analytics_dashboard_screen.dart';
import '../screens/main_shell_screen.dart';
import '../screens/players_screen.dart';
import '../screens/tracks_screen.dart';
import '../screens/today_races_screen.dart';

class AppRouter {
  static Map<String, WidgetBuilder> get routes => {
        '/': (context) => const MainShellScreen(),
        '/races': (context) => const TodayRacesScreen(),
        '/players': (context) => const PlayersScreen(),
        '/tracks': (context) => const TracksScreen(),
        '/analytics': (context) => const AnalyticsDashboardScreen(),
      };
}
