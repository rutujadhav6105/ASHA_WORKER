import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../utils/api_constants.dart';

class AuthService {
  AuthService._();

  static Map<String, String> get _headers => {
        HttpHeaders.contentTypeHeader: 'application/json',
        HttpHeaders.acceptHeader: 'application/json',
      };

  // ── Login ─────────────────────────────────────────────────────────────────
  static Future<Map<String, dynamic>> login({
    required String role,
    required String identifier,
    required String password,
  }) async {
    final response = await _post(
      endpoint: ApiConstants.loginEndpoint,
      body: {
        'username': identifier.trim(),
        'password': password,
        'role': role,
      },
    );
    return _handleResponse(response);
  }

  // ── Register ASHA ─────────────────────────────────────────────────────────
  static Future<Map<String, dynamic>> registerAsha({
    required String ashaId,
    required String name,
    required String mobile,
    required String password,
    required String area,
    required String district,
    required String supervisorId,
    String? email,
  }) async {
    final response = await _post(
      endpoint: ApiConstants.registerAshaEndpoint,
      body: {
        'username': ashaId,
        'email': email ?? '$ashaId@asha.gov.in',
        'password': password,
        'full_name': name,
        'asha_id': ashaId,
        'village': area,
        'district': district,
        'mobile': mobile,
        'supervisor_id': supervisorId,
      },
    );
    return _handleResponse(response);
  }

  // ── Register Supervisor ───────────────────────────────────────────────────
  static Future<Map<String, dynamic>> registerSupervisor({
    required String supervisorId,
    required String name,
    required String mobile,
    required String password,
    required String area,
    required String district,
    String? email,
  }) async {
    final response = await _post(
      endpoint: ApiConstants.registerSupervisorEndpoint,
      body: {
        'username': supervisorId,
        'email': email ?? '$supervisorId@asha.gov.in',
        'password': password,
        'full_name': name,
        'supervisor_id': supervisorId,
        'zone': area,
        'block': area,
        'district': district,
        'mobile': mobile,
      },
    );
    return _handleResponse(response);
  }

  // ── Register Admin ──────────────────────────────────────────────────────────
  static Future<Map<String, dynamic>> registerAdmin({
    required String name,
    required String mobile,
    required String password,
    required String email,
    String? district,
    String? token,
  }) async {
    final response = await _post(
      endpoint: '/register/admin',
      body: {
        'username': email.split('@').first,
        'email': email,
        'password': password,
        'full_name': name,
        'district': district,
        'mobile': mobile,
      },
      token: token,
    );
    return _handleResponse(response);
  }

  // ── Logout ────────────────────────────────────────────────────────────────
  static Future<void> logout({String? token}) async {
    try {
      await _post(
        endpoint: ApiConstants.logoutEndpoint,
        body: {},
        token: token,
      );
    } catch (_) {
      // Swallow — local session will be cleared regardless.
    }
  }

  // ── Change Password ───────────────────────────────────────────────────────
  static Future<String> changePassword({
    required String currentPassword,
    required String newPassword,
    required String token,
  }) async {
    final response = await _post(
      endpoint: ApiConstants.changePasswordEndpoint,
      body: {
        'currentPassword': currentPassword,
        'newPassword': newPassword,
      },
      token: token,
    );
    final data = _handleResponse(response);
    return data['message'] as String? ?? 'Password changed successfully.';
  }

  // ── Private: HTTP helpers ─────────────────────────────────────────────────

  static Future<http.Response> _post({
    required String endpoint,
    required Map<String, dynamic> body,
    String? token,
  }) async {
    final uri = ApiConstants.uri(endpoint);
    final headers = {
      ..._headers,
      if (token != null) HttpHeaders.authorizationHeader: 'Bearer $token',
    };

    try {
      final response = await http
          .post(uri, headers: headers, body: jsonEncode(body))
          .timeout(ApiConstants.receiveTimeout);
      return response;
    } on SocketException {
      throw Exception('No internet connection. Please check your network.');
    } on HttpException {
      throw Exception('Could not reach the server. Please try again.');
    } catch (e) {
      throw Exception('Something went wrong: $e');
    }
  }

  static Map<String, dynamic> _handleResponse(http.Response response) {
    final body = _decodeBody(response.body);

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return body;
    }

    final serverMessage = body['message'] as String? ??
        body['detail'] as String? ??
        body['error'] as String?;

    switch (response.statusCode) {
      case 400:
        throw Exception(serverMessage ?? 'Invalid request. Please check your input.');
      case 401:
        throw Exception(serverMessage ?? 'Invalid credentials. Please try again.');
      case 403:
        throw Exception(serverMessage ?? 'Access denied.');
      case 404:
        throw Exception(serverMessage ?? 'Resource not found.');
      case 409:
        throw Exception(serverMessage ?? 'An account with this ID already exists.');
      case 422:
        throw Exception(serverMessage ?? 'Validation failed. Please check your input.');
      case 429:
        throw Exception('Too many attempts. Please wait and try again.');
      case 500:
      case 502:
      case 503:
        throw Exception('Server error. Please try again later.');
      default:
        throw Exception(serverMessage ?? 'Unexpected error (${response.statusCode}).');
    }
  }

  static Map<String, dynamic> _decodeBody(String body) {
    try {
      final decoded = jsonDecode(body);
      if (decoded is Map<String, dynamic>) return decoded;
      return {'data': decoded};
    } catch (_) {
      return {};
    }
  }
}