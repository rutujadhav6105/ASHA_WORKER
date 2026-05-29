import 'package:flutter/material.dart';

class AppColors {
  // Primary palette – deep teal-green (health + trust)
  static const primary = Color(0xFF0D6B52);
  static const primaryLight = Color(0xFF1A9070);
  static const primaryDark = Color(0xFF064A38);
  static const primarySurface = Color(0xFFE6F4F1);

  // Accent – warm amber
  static const accent = Color(0xFFF59E0B);
  static const accentLight = Color(0xFFFDE68A);
  static const accentDark = Color(0xFFB45309);

  // Semantic colors
  static const danger = Color(0xFFDC2626);
  static const dangerSurface = Color(0xFFFEE2E2);
  static const warning = Color(0xFFD97706);
  static const warningSurface = Color(0xFFFEF3C7);
  static const success = Color(0xFF059669);
  static const successSurface = Color(0xFFD1FAE5);
  static const info = Color(0xFF2563EB);
  static const infoSurface = Color(0xFFDBEAFE);

  // Backgrounds
  static const background = Color(0xFFF4F7F6);
  static const surface = Color(0xFFFFFFFF);
  static const surfaceVariant = Color(0xFFF0F9F6);
  static const cardBg = Color(0xFFFFFFFF);

  // Text
  static const textPrimary = Color(0xFF0F1F1B);
  static const textSecondary = Color(0xFF4B6860);
  static const textHint = Color(0xFF9DB8B2);
  static const textOnDark = Color(0xFFFFFFFF);

  // Borders & dividers
  static const divider = Color(0xFFD1E8E3);
  static const border = Color(0xFFB8D8D1);

  // Role-specific
  static const adminColor = Color(0xFF1D4ED8);
  static const adminSurface = Color(0xFFEFF6FF);
  static const supervisorColor = Color(0xFF7C3AED);
  static const supervisorSurface = Color(0xFFF5F3FF);
  static const ashaColor = Color(0xFF0D6B52);
  static const ashaSurface = Color(0xFFE6F4F1);

  // Chart colors
  static const chart1 = Color(0xFF0D6B52);
  static const chart2 = Color(0xFFF59E0B);
  static const chart3 = Color(0xFF2563EB);
  static const chart4 = Color(0xFFDC2626);
  static const chart5 = Color(0xFF7C3AED);
  static const chart6 = Color(0xFF059669);

  // Gradient pairs
  static const gradientPrimary = [Color(0xFF064A38), Color(0xFF0D9471)];
  static const gradientAdmin = [Color(0xFF1E3A8A), Color(0xFF3B82F6)];
  static const gradientSupervisor = [Color(0xFF581C87), Color(0xFFA855F7)];
  static const gradientAccent = [Color(0xFFB45309), Color(0xFFF59E0B)];
  static const gradientDanger = [Color(0xFF991B1B), Color(0xFFEF4444)];
}

class AppTheme {
  static ThemeData get theme => ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: AppColors.primary,
      primary: AppColors.primary,
      secondary: AppColors.accent,
      background: AppColors.background,
      surface: AppColors.surface,
      error: AppColors.danger,
    ),
    scaffoldBackgroundColor: AppColors.background,
    fontFamily: 'Poppins',
    textTheme: _textTheme,
    appBarTheme: const AppBarTheme(
      backgroundColor: AppColors.primary,
      foregroundColor: Colors.white,
      elevation: 0,
      centerTitle: false,
      titleTextStyle: TextStyle(
        fontFamily: 'Poppins',
        fontSize: 18,
        fontWeight: FontWeight.w600,
        color: Colors.white,
        letterSpacing: -0.3,
      ),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        minimumSize: const Size(double.infinity, 52),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        textStyle: const TextStyle(
          fontFamily: 'Poppins',
          fontSize: 15,
          fontWeight: FontWeight.w600,
          letterSpacing: 0.3,
        ),
        elevation: 0,
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: AppColors.primary,
        side: const BorderSide(color: AppColors.primary, width: 1.5),
        minimumSize: const Size(double.infinity, 52),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: AppColors.surface,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: AppColors.border),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: AppColors.border),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: AppColors.primary, width: 2),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: AppColors.danger),
      ),
      labelStyle: const TextStyle(color: AppColors.textSecondary, fontFamily: 'Poppins'),
      hintStyle: const TextStyle(color: AppColors.textHint, fontFamily: 'Poppins'),
    ),
    cardTheme: CardThemeData(
      color: AppColors.cardBg,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: AppColors.divider),
      ),
      margin: EdgeInsets.zero,
    ),
    dividerTheme: const DividerThemeData(color: AppColors.divider, thickness: 1),
    chipTheme: ChipThemeData(
      backgroundColor: AppColors.surfaceVariant,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      labelStyle: const TextStyle(fontFamily: 'Poppins', fontSize: 12),
    ),
  );

  static const _textTheme = TextTheme(
    displayLarge: TextStyle(fontFamily: 'Poppins', fontWeight: FontWeight.w700, color: AppColors.textPrimary),
    displayMedium: TextStyle(fontFamily: 'Poppins', fontWeight: FontWeight.w700, color: AppColors.textPrimary),
    headlineLarge: TextStyle(fontFamily: 'Poppins', fontWeight: FontWeight.w700, fontSize: 24, color: AppColors.textPrimary),
    headlineMedium: TextStyle(fontFamily: 'Poppins', fontWeight: FontWeight.w600, fontSize: 20, color: AppColors.textPrimary),
    headlineSmall: TextStyle(fontFamily: 'Poppins', fontWeight: FontWeight.w600, fontSize: 18, color: AppColors.textPrimary),
    titleLarge: TextStyle(fontFamily: 'Poppins', fontWeight: FontWeight.w600, fontSize: 16, color: AppColors.textPrimary),
    titleMedium: TextStyle(fontFamily: 'Poppins', fontWeight: FontWeight.w500, fontSize: 14, color: AppColors.textPrimary),
    bodyLarge: TextStyle(fontFamily: 'Poppins', fontSize: 14, color: AppColors.textPrimary),
    bodyMedium: TextStyle(fontFamily: 'Poppins', fontSize: 13, color: AppColors.textSecondary),
    bodySmall: TextStyle(fontFamily: 'Poppins', fontSize: 12, color: AppColors.textHint),
    labelLarge: TextStyle(fontFamily: 'Poppins', fontWeight: FontWeight.w600, fontSize: 14),
  );
}

class AppStrings {
  static const appName = 'ASHA Seva';
  static const appNameHindi = 'आशा सेवा';
  static const tagline = 'Empowering Health at Every Doorstep';
}

// ─── Spacing constants ───────────────────────────────────────────────────────
class AppSpacing {
  static const xs = 4.0;
  static const sm = 8.0;
  static const md = 16.0;
  static const lg = 24.0;
  static const xl = 32.0;
  static const xxl = 48.0;
}

// ─── Border radius constants ─────────────────────────────────────────────────
class AppRadius {
  static const sm = 8.0;
  static const md = 12.0;
  static const lg = 16.0;
  static const xl = 20.0;
  static const full = 100.0;
}
