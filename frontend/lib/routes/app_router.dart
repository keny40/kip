import 'package:flutter/material.dart';

import '../screens/admin_home_screen.dart';
import '../screens/admin_login_screen.dart';

class AppRouter {
  AppRouter._();

  static const String adminLogin = '/admin/login';
  static const String adminHome = '/admin/home';

  static final Map<String, WidgetBuilder> routes = {
    adminLogin: (context) => AdminLoginScreen(),
    adminHome: (context) => AdminHomeScreen(),
  };
}