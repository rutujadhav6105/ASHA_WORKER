import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../screens/auth/login_screen.dart';
import '../screens/auth/register_asha_screen.dart';
import '../screens/auth/register_supervisor_screen.dart';
import '../screens/auth/register_admin_screen.dart';
import '../screens/dashboard/asha_dashboard.dart';
import '../screens/dashboard/supervisor_dashboard.dart';

class AppRouter {
  AppRouter._();

  static final router = GoRouter(
    initialLocation: '/',
    debugLogDiagnostics: true,
    routes: [
      GoRoute(
        path: '/',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/register/asha',
        builder: (context, state) => const RegisterAshaScreen(),
      ),
      GoRoute(
        path: '/register/supervisor',
        builder: (context, state) => const RegisterSupervisorScreen(),
      ),
      GoRoute(
        path: '/register/admin',
        builder: (context, state) => const RegisterAdminScreen(),
      ),
      GoRoute(
        path: '/asha/dashboard',
        builder: (context, state) => const AshaDashboard(),
      ),
      GoRoute(
        path: '/supervisor/dashboard',
        builder: (context, state) => const SupervisorDashboard(),
      ),
      // Fallback/Redirect for old paths if any
      GoRoute(
        path: '/dashboard/asha',
        redirect: (context, state) => '/asha/dashboard',
      ),
      GoRoute(
        path: '/dashboard/supervisor',
        redirect: (context, state) => '/supervisor/dashboard',
      ),
    ],
    errorBuilder: (context, state) => Scaffold(
      body: Center(
        child: Text('Page not found: ${state.uri.path}'),
      ),
    ),
  );
}