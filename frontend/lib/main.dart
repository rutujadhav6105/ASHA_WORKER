// lib/main.dart
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'utils/api_constants.dart';
import 'services/api_service.dart';
import 'package:provider/provider.dart';
import 'context/auth_provider.dart';

import 'routes/app_router.dart';

// ─── Entry point ──────────────────────────────────────────────────────────────

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Lock to portrait orientation
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);

  // Transparent status bar
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor:                   Colors.transparent,
      statusBarIconBrightness:          Brightness.dark,
      systemNavigationBarColor:         Colors.white,
      systemNavigationBarIconBrightness: Brightness.dark,
    ),
  );

  // Restore session from previous run
  final prefs      = await SharedPreferences.getInstance();
  final savedToken = prefs.getString(ApiConstants.tokenKey);
  final savedRole  = prefs.getString(ApiConstants.roleKey);

  if (savedToken != null) ApiService.setToken(savedToken);

  runApp(AshaApp(initialToken: savedToken, initialRole: savedRole));
}

// ─── Root widget ──────────────────────────────────────────────────────────────

class AshaApp extends StatelessWidget {
  const AshaApp({super.key, this.initialToken, this.initialRole});

  final String? initialToken;
  final String? initialRole;

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => AuthProvider()..init(),
      child: MaterialApp.router(
        debugShowCheckedModeBanner: false,
        title: 'ASHA Seva',
        theme: _buildTheme(),
        routerConfig: AppRouter.router,
      ),
    );
  }

  String _resolveInitialRoute() {
    if (initialToken == null) return AppRoutes.login;
    if (initialRole == 'supervisor') return AppRoutes.supervisorDashboard;
    return AppRoutes.ashaDashboard;
  }
}

// ─── Theme ────────────────────────────────────────────────────────────────────

ThemeData _buildTheme() {
  const primaryGreen  = Color(0xFF2E7D32);
  const accentAmber   = Color(0xFFF9A825);
  const surfaceWhite  = Color(0xFFFAFAFA);
  const onSurfaceDark = Color(0xFF1C1C1C);
  const subtleGrey    = Color(0xFFEEEEEE);

  final base = ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor:  primaryGreen,
      primary:    primaryGreen,
      secondary:  accentAmber,
      surface:    surfaceWhite,
      onSurface:  onSurfaceDark,
      brightness: Brightness.light,
    ),
  );

  return base.copyWith(
    scaffoldBackgroundColor: surfaceWhite,
    splashFactory: InkRipple.splashFactory,

    // ── App bar ──────────────────────────────────────────────────────────
    appBarTheme: const AppBarTheme(
      backgroundColor: primaryGreen,
      foregroundColor: Colors.white,
      elevation:       0,
      centerTitle:     false,
      titleTextStyle: TextStyle(
        fontFamily:    'Poppins',
        fontWeight:    FontWeight.w600,
        fontSize:      20,
        color:         Colors.white,
        letterSpacing: 0.2,
      ),
      systemOverlayStyle: SystemUiOverlayStyle(
        statusBarColor:          Colors.transparent,
        statusBarIconBrightness: Brightness.light,
      ),
    ),

    // ── Bottom nav ───────────────────────────────────────────────────────
    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
      backgroundColor:      Colors.white,
      selectedItemColor:    primaryGreen,
      unselectedItemColor:  Color(0xFF9E9E9E),
      selectedLabelStyle:   TextStyle(fontFamily: 'Poppins', fontWeight: FontWeight.w600, fontSize: 11),
      unselectedLabelStyle: TextStyle(fontFamily: 'Poppins', fontSize: 11),
      type:                 BottomNavigationBarType.fixed,
      elevation:            12,
    ),

    // ── Cards — use CardThemeData (Flutter ≥ 3.7) ────────────────────────
    cardTheme: CardThemeData(
      color:       Colors.white,
      elevation:   2,
      shadowColor: Colors.black12,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
    ),

    // ── Elevated button ──────────────────────────────────────────────────
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: primaryGreen,
        foregroundColor: Colors.white,
        minimumSize:     const Size.fromHeight(52),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
        ),
        textStyle: const TextStyle(
          fontFamily:    'Poppins',
          fontWeight:    FontWeight.w600,
          fontSize:      16,
          letterSpacing: 0.4,
        ),
        elevation: 0,
      ),
    ),

    // ── Outlined button ──────────────────────────────────────────────────
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: primaryGreen,
        minimumSize:     const Size.fromHeight(52),
        side:            const BorderSide(color: primaryGreen, width: 1.5),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
        ),
        textStyle: const TextStyle(
          fontFamily: 'Poppins',
          fontWeight: FontWeight.w600,
          fontSize:   16,
        ),
      ),
    ),

    // ── Text button ──────────────────────────────────────────────────────
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: primaryGreen,
        textStyle: const TextStyle(
          fontFamily: 'Poppins',
          fontWeight: FontWeight.w500,
          fontSize:   14,
        ),
      ),
    ),

    // ── Input fields ─────────────────────────────────────────────────────
    inputDecorationTheme: InputDecorationTheme(
      filled:         true,
      fillColor:      subtleGrey,
      contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide:   BorderSide.none,
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide:   BorderSide.none,
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide:   const BorderSide(color: primaryGreen, width: 1.8),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide:   const BorderSide(color: Colors.redAccent, width: 1.5),
      ),
      labelStyle: const TextStyle(fontFamily: 'Poppins', color: Color(0xFF757575), fontSize: 14),
      hintStyle:  const TextStyle(fontFamily: 'Poppins', color: Color(0xFFBDBDBD), fontSize: 14),
    ),

    // ── Chip ─────────────────────────────────────────────────────────────
    chipTheme: ChipThemeData(
      backgroundColor:  subtleGrey,
      selectedColor:    const Color(0xFF2E7D32).withValues(alpha: 0.15),
      labelStyle: const TextStyle(fontFamily: 'Poppins', fontSize: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
    ),

    // ── Divider ───────────────────────────────────────────────────────────
    dividerTheme: const DividerThemeData(
      color:     Color(0xFFE0E0E0),
      thickness: 1,
      space:     1,
    ),

    // ── FAB ───────────────────────────────────────────────────────────────
    floatingActionButtonTheme: const FloatingActionButtonThemeData(
      backgroundColor: primaryGreen,
      foregroundColor: Colors.white,
      elevation:       4,
      shape:           CircleBorder(),
    ),

    // ── Snack bar ─────────────────────────────────────────────────────────
    snackBarTheme: SnackBarThemeData(
      backgroundColor: onSurfaceDark,
      contentTextStyle: const TextStyle(
        fontFamily: 'Poppins',
        color:      Colors.white,
        fontSize:   14,
      ),
      shape:    RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      behavior: SnackBarBehavior.floating,
    ),

    // ── Text theme ────────────────────────────────────────────────────────
    textTheme: const TextTheme(
      displayLarge:  TextStyle(fontFamily: 'Poppins', fontWeight: FontWeight.w700, fontSize: 32, color: onSurfaceDark),
      displayMedium: TextStyle(fontFamily: 'Poppins', fontWeight: FontWeight.w700, fontSize: 28, color: onSurfaceDark),
      headlineLarge: TextStyle(fontFamily: 'Poppins', fontWeight: FontWeight.w600, fontSize: 24, color: onSurfaceDark),
      headlineMedium:TextStyle(fontFamily: 'Poppins', fontWeight: FontWeight.w600, fontSize: 20, color: onSurfaceDark),
      titleLarge:    TextStyle(fontFamily: 'Poppins', fontWeight: FontWeight.w600, fontSize: 18, color: onSurfaceDark),
      titleMedium:   TextStyle(fontFamily: 'Poppins', fontWeight: FontWeight.w500, fontSize: 16, color: onSurfaceDark),
      titleSmall:    TextStyle(fontFamily: 'Poppins', fontWeight: FontWeight.w500, fontSize: 14, color: onSurfaceDark),
      bodyLarge:     TextStyle(fontFamily: 'Poppins', fontSize: 15, color: onSurfaceDark),
      bodyMedium:    TextStyle(fontFamily: 'Poppins', fontSize: 14, color: onSurfaceDark),
      bodySmall:     TextStyle(fontFamily: 'Poppins', fontSize: 12, color: Color(0xFF616161)),
      labelLarge:    TextStyle(fontFamily: 'Poppins', fontWeight: FontWeight.w600, fontSize: 14),
    ),
  );
}

// ─── Route names ──────────────────────────────────────────────────────────────

class AppRoutes {
  AppRoutes._();

  static const String login               = '/';
  static const String ashaDashboard       = '/asha/dashboard';
  static const String supervisorDashboard = '/supervisor/dashboard';
  static const String registerAsha       = '/register/asha';
  static const String registerSupervisor = '/register/supervisor';
  static const String registerAdmin      = '/register/admin';
  static const String patients            = '/patients';
  static const String patientDetail       = '/patients/detail';
  static const String addPatient          = '/patients/add';
  static const String pregnancies         = '/pregnancies';
  static const String immunization        = '/immunization';
  static const String homeVisits          = '/home-visits';
  static const String medicineStock       = '/medicine-stock';
  static const String reports             = '/reports';
  static const String aiAssistant         = '/ai-assistant';
  static const String profile             = '/profile';
  static const String schemes             = '/schemes';
  static const String alerts              = '/alerts';
  static const String training            = '/training';
  static const String villageStats        = '/village-stats';
}

// ─── Navigation helper ────────────────────────────────────────────────────────

class AppNavigator {
  AppNavigator._();

  static Future<T?> push<T>(BuildContext context, String route, {Object? arguments}) =>
      Navigator.pushNamed<T>(context, route, arguments: arguments);

  static Future<T?> pushReplacement<T>(BuildContext context, String route, {Object? arguments}) =>
      Navigator.pushReplacementNamed<T, void>(context, route, arguments: arguments);

  static void pushAndRemoveAll(BuildContext context, String route) =>
      Navigator.pushNamedAndRemoveUntil(context, route, (_) => false);

  static void pop<T>(BuildContext context, [T? result]) =>
      Navigator.pop<T>(context, result);

  /// Land the user on the correct dashboard after login.
  static void navigateAfterLogin(BuildContext context, String role) {
    final route = role == 'supervisor'
        ? AppRoutes.supervisorDashboard
        : AppRoutes.ashaDashboard;
    pushAndRemoveAll(context, route);
  }

  /// Clear stack and return to login (used on logout).
  static void navigateToLogin(BuildContext context) =>
      pushAndRemoveAll(context, AppRoutes.login);
}

// ─── Navigator observer ───────────────────────────────────────────────────────

class AppNavigatorObserver extends NavigatorObserver {
  @override
  void didPush(Route route, Route? previousRoute) =>
      debugPrint('[NAV] push → ${route.settings.name}');

  @override
  void didPop(Route route, Route? previousRoute) =>
      debugPrint('[NAV] pop  ← ${route.settings.name}');

  @override
  void didReplace({Route? newRoute, Route? oldRoute}) =>
      debugPrint('[NAV] replace ${oldRoute?.settings.name} → ${newRoute?.settings.name}');
}