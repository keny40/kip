import 'package:flutter/material.dart';

import '../screens/admin_csv_upload_screen.dart';
import '../screens/admin_home_screen.dart';
import '../screens/admin_login_screen.dart';
import '../screens/admin_external_players_screen.dart';
import '../screens/admin_external_player_statistics_screen.dart';
import '../screens/admin_player_match_candidates_screen.dart';
import '../screens/admin_data_quality_screen.dart';

class AppRouter {
  AppRouter._();

  static const String adminLogin = '/admin/login';
  static const String adminHome = '/admin/home';
  static const String adminCsvUpload = '/admin/imports';
  static const String adminExternalPlayers = '/admin/external-players';
  static const String adminExternalPlayerStatistics =
      '/admin/external-player-statistics';
  static const String adminPlayerMatchCandidates =
      '/admin/player-match-candidates';
  static const String adminDataQuality = '/admin/data-quality';

  static final Map<String, WidgetBuilder> routes = {
    adminLogin: (context) => AdminLoginScreen(),
    adminHome: (context) => AdminHomeScreen(),
    adminCsvUpload: (context) => AdminCsvUploadScreen(),
    adminExternalPlayers: (context) => AdminExternalPlayersScreen(),
    adminExternalPlayerStatistics: (context) =>
        AdminExternalPlayerStatisticsScreen(),
    adminPlayerMatchCandidates: (context) => AdminPlayerMatchCandidatesScreen(),
    adminDataQuality: (context) => AdminDataQualityScreen(),
  };
}
