import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../utils/api_constants.dart';

// ============================================================
// API SERVICE LAYER — ASHA Seva
// Connected to FastAPI backend on port 8000.
// ============================================================

class ApiService {
  ApiService._();

  static String? _authToken;

  static void setToken(String token) => _authToken = token;
  static void clearToken() => _authToken = null;

  static Map<String, String> get _headers => {
        HttpHeaders.contentTypeHeader: 'application/json',
        HttpHeaders.acceptHeader: 'application/json',
        if (_authToken != null)
          HttpHeaders.authorizationHeader: 'Bearer $_authToken',
      };

  // ── Core HTTP helpers ─────────────────────────────────────────────────────

  static Future<T> _get<T>(String path) async {
    final res = await http
        .get(ApiConstants.uri(path), headers: _headers)
        .timeout(ApiConstants.receiveTimeout);
    return _handleResponse<T>(res);
  }

  static Future<T> _post<T>(String path, Map<String, dynamic> body) async {
    final res = await http
        .post(ApiConstants.uri(path),
            headers: _headers, body: jsonEncode(body))
        .timeout(ApiConstants.receiveTimeout);
    return _handleResponse<T>(res);
  }

  static Future<T> _put<T>(String path, Map<String, dynamic> body) async {
    final res = await http
        .put(ApiConstants.uri(path),
            headers: _headers, body: jsonEncode(body))
        .timeout(ApiConstants.receiveTimeout);
    return _handleResponse<T>(res);
  }

  static Future<T> _delete<T>(String path) async {
    final res = await http
        .delete(ApiConstants.uri(path), headers: _headers)
        .timeout(ApiConstants.receiveTimeout);
    return _handleResponse<T>(res);
  }

  // ── Response handler ──────────────────────────────────────────────────────

  static T _handleResponse<T>(http.Response res) {
    final body = _decodeBody(res.body);
    if (res.statusCode >= 200 && res.statusCode < 300) {
      return body as T;
    }
    final msg = (body is Map)
        ? (body['message'] ?? body['detail'] ?? body['error'])?.toString()
        : null;
    switch (res.statusCode) {
      case 400:
        throw Exception(msg ?? 'Invalid request.');
      case 401:
        throw Exception(msg ?? 'Unauthorised. Please log in again.');
      case 403:
        throw Exception(msg ?? 'Access denied.');
      case 404:
        throw Exception(msg ?? 'Resource not found.');
      case 409:
        throw Exception(msg ?? 'Conflict: record already exists.');
      case 422:
        throw Exception(msg ?? 'Validation failed.');
      case 429:
        throw Exception('Too many requests. Please wait and try again.');
      case 500:
      case 502:
      case 503:
        throw Exception('Server error. Please try again later.');
      default:
        throw Exception(msg ?? 'Unexpected error (${res.statusCode}).');
    }
  }

  static dynamic _decodeBody(String body) {
    try {
      return jsonDecode(body);
    } catch (_) {
      return <String, dynamic>{};
    }
  }

  // ─────────────────────────────────────────────────────────────────────────
  // AUTH
  // ─────────────────────────────────────────────────────────────────────────

  static Future<Map<String, dynamic>> login({
    required String role,
    required String identifier,
    required String password,
  }) =>
      _post('/login', {
        'username': identifier,
        'password': password,
        'role': role,
      });

  static Future<Map<String, dynamic>> registerSupervisor({
    required String supervisorId,
    required String name,
    required String mobile,
    required String password,
    required String area,
    required String district,
    String? email,
  }) =>
      _post('/register/supervisor', {
        'username': supervisorId,
        'email': email ?? '$supervisorId@asha.gov.in',
        'password': password,
        'full_name': name,
        'supervisor_id': supervisorId,
        'zone': area,
        'block': area,
        'district': district,
        'mobile': mobile,
      });

  static Future<Map<String, dynamic>> registerAsha({
    required String ashaId,
    required String name,
    required String mobile,
    required String password,
    required String area,
    required String district,
    required String supervisorId,
    String? email,
  }) =>
      _post('/register/asha', {
        'username': ashaId,
        'email': email ?? '$ashaId@asha.gov.in',
        'password': password,
        'full_name': name,
        'asha_id': ashaId,
        'village': area,
        'district': district,
        'mobile': mobile,
        'supervisor_id': supervisorId,
      });

  static Future<Map<String, dynamic>> registerAdmin({
    required String name,
    required String mobile,
    required String password,
    required String email,
    String? district,
  }) =>
      _post('/register/admin', {
        'username': email.split('@').first,
        'email': email,
        'password': password,
        'full_name': name,
        'district': district,
        'mobile': mobile,
      });

  static Future<Map<String, dynamic>> logout() async {
    final res = await _post<Map<String, dynamic>>('/logout', {});
    clearToken();
    return res;
  }

  // ─────────────────────────────────────────────────────────────────────────
  // PROFILE
  // ─────────────────────────────────────────────────────────────────────────

  static Future<Map<String, dynamic>> getProfile() =>
      _get('/profile');

  static Future<Map<String, dynamic>> updateProfile(
          Map<String, dynamic> data) =>
      _put('/profile', data);

  static Future<Map<String, dynamic>> changePassword({
    required String currentPassword,
    required String newPassword,
  }) =>
      _post('/change-password', {
        'currentPassword': currentPassword,
        'newPassword': newPassword,
      });

  // ─────────────────────────────────────────────────────────────────────────
  // DASHBOARD
  // ─────────────────────────────────────────────────────────────────────────

  static Future<Map<String, dynamic>> getDashboardSummary() =>
      _get('/dashboard/summary');

  static Future<Map<String, dynamic>> getVillageStats() =>
      _get('/dashboard/village-stats');

  // ─────────────────────────────────────────────────────────────────────────
  // PATIENTS
  // ─────────────────────────────────────────────────────────────────────────

  static Future<Map<String, dynamic>> getPatients({
    int page = 1,
    int limit = 20,
    String? search,
    String? village,
    String? riskLevel,
  }) {
    final params = <String, dynamic>{
      'page': page,
      'limit': limit,
      if (search != null) 'search': search,
      if (village != null) 'village': village,
      if (riskLevel != null) 'risk_level': riskLevel,
    };
    return _get(ApiConstants.uri('/patients', queryParams: params).toString()
        .replaceFirst(ApiConstants.baseUrl, ''));
  }

  static Future<Map<String, dynamic>> getPatient(int id) =>
      _get('/patients/$id');

  static Future<Map<String, dynamic>> createPatient(
          Map<String, dynamic> data) =>
      _post('/patients', data);

  static Future<Map<String, dynamic>> updatePatient(
          int id, Map<String, dynamic> data) =>
      _put('/patients/$id', data);

  static Future<Map<String, dynamic>> deletePatient(int id) =>
      _delete('/patients/$id');

  // ─────────────────────────────────────────────────────────────────────────
  // FAMILIES (beneficiaries)
  // ─────────────────────────────────────────────────────────────────────────

  static Future<Map<String, dynamic>> getFamilies() => _get('/family');

  static Future<Map<String, dynamic>> saveFamily(
          Map<String, dynamic> family) =>
      _post('/family', family);

  static Future<Map<String, dynamic>> addFamilyMember(
          Map<String, dynamic> member) =>
      _post('/family/member', member);

  // ─────────────────────────────────────────────────────────────────────────
  // PREGNANCIES / ANC
  // ─────────────────────────────────────────────────────────────────────────

  static Future<Map<String, dynamic>> getPregnancies({
    int page = 1,
    String? riskLevel,
  }) {
    final params = <String, dynamic>{
      'page': page,
      if (riskLevel != null) 'risk_level': riskLevel,
    };
    return _get(ApiConstants.uri('/pregnancies', queryParams: params).toString()
        .replaceFirst(ApiConstants.baseUrl, ''));
  }

  static Future<Map<String, dynamic>> getAncRecords() => _get('/anc');

  static Future<Map<String, dynamic>> saveAncRecord(
          Map<String, dynamic> record) =>
      _post('/anc', record);

  static Future<Map<String, dynamic>> updateAncRecord(
          int id, Map<String, dynamic> record) =>
      _put('/anc/$id', record);

  // ─────────────────────────────────────────────────────────────────────────
  // IMMUNIZATION
  // ─────────────────────────────────────────────────────────────────────────

  static Future<Map<String, dynamic>> getVaccineRecords() =>
      _get('/immunization');

  static Future<Map<String, dynamic>> saveVaccineRecord(
      Map<String, dynamic> record) {
    final isVaccineDose = record.remove('isVaccineDose') == true;
    final endpoint =
        isVaccineDose ? '/immunization/vaccine' : '/immunization';
    return _post(endpoint, record);
  }

  static Future<Map<String, dynamic>> getDueVaccinations() =>
      _get('/immunization/due');

  // ─────────────────────────────────────────────────────────────────────────
  // HOME VISITS
  // ─────────────────────────────────────────────────────────────────────────

  static Future<Map<String, dynamic>> getHomeVisits({int page = 1}) =>
      _get('/home-visits?page=$page');

  static Future<Map<String, dynamic>> createHomeVisit(
          Map<String, dynamic> data) =>
      _post('/home-visits', data);

  static Future<Map<String, dynamic>> updateHomeVisit(
          int id, Map<String, dynamic> data) =>
      _put('/home-visits/$id', data);

  // ─────────────────────────────────────────────────────────────────────────
  // MEDICINE STOCK
  // ─────────────────────────────────────────────────────────────────────────

  static Future<Map<String, dynamic>> getMedicineStock() =>
      _get('/medicine-stock');

  static Future<Map<String, dynamic>> updateMedicineStock(
          int id, Map<String, dynamic> data) =>
      _put('/medicine-stock/$id', data);

  static Future<Map<String, dynamic>> getLowStockAlerts() =>
      _get('/medicine-stock/low-stock');

  // ─────────────────────────────────────────────────────────────────────────
  // REPORTS
  // ─────────────────────────────────────────────────────────────────────────

  static Future<Map<String, dynamic>> getMonthlyReport({
    int? month,
    int? year,
  }) {
    final m = month ?? DateTime.now().month;
    final y = year ?? DateTime.now().year;
    return _get('/reports/monthly?month=$m&year=$y');
  }

  static Future<Map<String, dynamic>> getVillageReport(String village) =>
      _get('/reports/village?village=${Uri.encodeComponent(village)}');

  static Future<Map<String, dynamic>> getWorkerPerformanceReport() =>
      _get('/reports/worker-performance');

  // ─────────────────────────────────────────────────────────────────────────
  // MACHINE LEARNING
  // ─────────────────────────────────────────────────────────────────────────

  static Future<Map<String, dynamic>> predictPregnancyRisk({
    required double age,
    required double hemoglobin,
    required double systolicBP,
    required double diastolicBP,
    required bool previousComplications,
    required int gestationalWeek,
  }) =>
      _post('/ml/pregnancy-risk', {
        'age': age,
        'hemoglobin': hemoglobin,
        'systolic_bp': systolicBP,
        'diastolic_bp': diastolicBP,
        'previous_complications': previousComplications,
        'gestational_week': gestationalWeek,
      });

  static Future<Map<String, dynamic>> predictNutritionRisk({
    required double ageMonths,
    required double weightKg,
    required double heightCm,
  }) =>
      _post('/ml/nutrition-risk', {
        'age_months': ageMonths,
        'weight_kg': weightKg,
        'height_cm': heightCm,
      });

  static Future<Map<String, dynamic>> predictMissedVisit({
    required int patientId,
    required int daysSinceLastVisit,
    required int totalVisitsMissed,
    required double distanceKm,
  }) =>
      _post('/ml/missed-visit', {
        'patient_id': patientId,
        'days_since_last_visit': daysSinceLastVisit,
        'total_visits_missed': totalVisitsMissed,
        'distance_km': distanceKm,
      });

  // ─────────────────────────────────────────────────────────────────────────
  // VILLAGES
  // ─────────────────────────────────────────────────────────────────────────

  static Future<Map<String, dynamic>> getVillages() => _get('/villages');

  static Future<Map<String, dynamic>> getVillageHealth(String village) =>
      _get('/villages/${Uri.encodeComponent(village)}/health');

  // ─────────────────────────────────────────────────────────────────────────
  // SCHEMES
  // ─────────────────────────────────────────────────────────────────────────

  static Future<Map<String, dynamic>> getSchemes() => _get('/schemes');

  // ─────────────────────────────────────────────────────────────────────────
  // AI ASSISTANT
  // ─────────────────────────────────────────────────────────────────────────

  static Future<Map<String, dynamic>> askAiAssistant({
    required String message,
    required String language,
    String? context,
  }) =>
      _post('/ai-assistant', {
        'question': message,
        'language': language,
        if (context != null) 'context': context,
      });

  // ─────────────────────────────────────────────────────────────────────────
  // ALERTS
  // ─────────────────────────────────────────────────────────────────────────

  static Future<Map<String, dynamic>> getAlerts({bool unreadOnly = false}) =>
      _get('/alerts${unreadOnly ? '?unread=true' : ''}');

  static Future<Map<String, dynamic>> markAlertRead(int id) =>
      _put('/alerts/$id/read', {});

  // ─────────────────────────────────────────────────────────────────────────
  // TRAINING
  // ─────────────────────────────────────────────────────────────────────────

  static Future<Map<String, dynamic>> getTrainingRecords() =>
      _get('/training');

  static Future<Map<String, dynamic>> createTrainingRecord(
          Map<String, dynamic> data) =>
      _post('/training', data);

  // ─────────────────────────────────────────────────────────────────────────
  // SUPERVISOR NOTES
  // ─────────────────────────────────────────────────────────────────────────

  static Future<Map<String, dynamic>> getSupervisorNotes() =>
      _get('/supervisor-notes');

  static Future<Map<String, dynamic>> createSupervisorNote(
          Map<String, dynamic> data) =>
      _post('/supervisor-notes', data);

  // ─────────────────────────────────────────────────────────────────────────
  // SYNC
  // ─────────────────────────────────────────────────────────────────────────

  static Future<Map<String, dynamic>> syncOfflineData(
          Map<String, dynamic> offlineData) =>
      _post('/sync', offlineData);
}