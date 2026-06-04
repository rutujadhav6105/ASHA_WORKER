// lib/utils/api_constants.dart

class ApiConstants {
  ApiConstants._();

  // ─── Base URL ────────────────────────────────────────────────────────────────
  static const String baseUrl = 'http://localhost:5000/api'; // Windows desktop / backend on localhost:5000
  // static const String baseUrl = 'http://localhost:5000'; // iOS simulator
  // static const String baseUrl = 'https://api.ashaapp.in'; // Production

  // ─── Timeouts ────────────────────────────────────────────────────────────────
  static const Duration connectTimeout = Duration(seconds: 30);
  static const Duration receiveTimeout = Duration(seconds: 30);
  static const Duration sendTimeout    = Duration(seconds: 30);

  // ─── URI Factory ─────────────────────────────────────────────────────────────
  /// Builds a [Uri] from [path], optionally appending [queryParams].
  ///   ApiConstants.uri('/patients')
  ///   ApiConstants.uri('/patients', queryParams: {'page': 1, 'limit': 20})
  static Uri uri(String path, {Map<String, dynamic>? queryParams}) {
    final base = Uri.parse(baseUrl);
    final stringParams = queryParams?.map(
      (k, v) => MapEntry(k, v.toString()),
    );
    return Uri(
      scheme: base.scheme,
      host:   base.host,
      port:   base.port,
      path:   '${base.path}$path',
      queryParameters: (stringParams?.isNotEmpty ?? false) ? stringParams : null,
    );
  }

  // ─── Auth Endpoints ──────────────────────────────────────────────────────────
  static const String login              = '/auth/login';
  static const String logout             = '/auth/logout';
  static const String registerSupervisor = '/auth/register/supervisor';
  static const String registerAsha       = '/auth/register/asha';
  static const String changePassword     = '/auth/change-password';

  // Aliases used by auth_service.dart
  static const String loginEndpoint                = login;
  static const String logoutEndpoint               = logout;
  static const String registerAshaEndpoint         = registerAsha;
  static const String registerSupervisorEndpoint   = registerSupervisor;
  static const String changePasswordEndpoint       = changePassword;

  // ─── Profile ─────────────────────────────────────────────────────────────────
  static const String profile            = '/auth/profile';

  // ─── Dashboard ───────────────────────────────────────────────────────────────
  static const String dashboardSummary   = '/dashboard/summary';
  static const String villageStats       = '/dashboard/village-stats';

  // ─── Patients ────────────────────────────────────────────────────────────────
  static const String patients           = '/patients';

  // ─── Families ────────────────────────────────────────────────────────────────
  static const String family             = '/family';
  static const String familyMember       = '/family/member';

  // ─── Pregnancies / ANC ───────────────────────────────────────────────────────
  static const String pregnancies        = '/pregnancies';
  static const String anc                = '/anc';

  // ─── Immunization ────────────────────────────────────────────────────────────
  static const String immunization        = '/immunization';
  static const String immunizationVaccine = '/immunization/vaccine';
  static const String immunizationDue     = '/immunization/due';

  // ─── Home Visits ─────────────────────────────────────────────────────────────
  static const String homeVisits          = '/home-visits';

  // ─── Medicine Stock ──────────────────────────────────────────────────────────
  static const String medicineStock       = '/medicine-stock';
  static const String lowStockAlerts      = '/medicine-stock/low-stock';

  // ─── Reports ─────────────────────────────────────────────────────────────────
  static const String reportsMonthly           = '/reports/monthly';
  static const String reportsVillage           = '/reports/village';
  static const String reportsWorkerPerformance = '/reports/worker-performance';

  // ─── ML ──────────────────────────────────────────────────────────────────────
  static const String mlPregnancyRisk    = '/ml/pregnancy-risk';
  static const String mlNutritionRisk    = '/ml/nutrition-risk';
  static const String mlMissedVisit      = '/ml/missed-visit';

  // ─── Villages ────────────────────────────────────────────────────────────────
  static const String villages           = '/villages';

  // ─── Schemes ─────────────────────────────────────────────────────────────────
  static const String schemes            = '/schemes';

  // ─── AI Assistant ────────────────────────────────────────────────────────────
  static const String aiAssistant        = '/ai-assistant';

  // ─── Alerts ──────────────────────────────────────────────────────────────────
  static const String alerts             = '/alerts';

  // ─── Training ────────────────────────────────────────────────────────────────
  static const String training           = '/training';

  // ─── Supervisor Notes ────────────────────────────────────────────────────────
  static const String supervisorNotes    = '/supervisor-notes';

  // ─── Sync ────────────────────────────────────────────────────────────────────
  static const String sync               = '/sync';

  // ─── SharedPreferences Keys ──────────────────────────────────────────────────
  static const String tokenKey        = 'auth_token';
  static const String refreshTokenKey = 'refresh_token';
  static const String roleKey         = 'user_role';
  static const String userKey         = 'user_data';
  static const String onboardingKey   = 'is_onboarded';
}