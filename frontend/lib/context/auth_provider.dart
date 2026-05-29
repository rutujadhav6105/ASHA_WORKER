import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/user_model.dart';
import '../services/auth_service.dart';
import '../utils/api_constants.dart';

enum AuthStatus {
  unknown,
  authenticated,
  unauthenticated,
}

class AuthProvider extends ChangeNotifier {
  AuthStatus _status = AuthStatus.unknown;
  UserModel? _user;
  String? _token;
  String? _role;
  bool _isLoading = false;
  String? _errorMessage;
  String _language = 'en';

  // ── Getters ───────────────────────────────────────────────────────────────
  AuthStatus get status => _status;
  UserModel? get user => _user;
  String? get token => _token;
  String? get role => _role;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  String get language => _language;
  bool get isAuthenticated => _status == AuthStatus.authenticated;
  bool get isAsha => _role == 'asha';
  bool get isSupervisor => _role == 'supervisor';
  bool get isAdmin => _role == 'admin';

  // ── Init: restore session on app start ───────────────────────────────────
  Future<void> init() async {
    _setLoading(true);
    try {
      final prefs = await SharedPreferences.getInstance();
      final savedToken = prefs.getString(ApiConstants.tokenKey);
      final savedUser  = prefs.getString(ApiConstants.userKey);
      final savedRole  = prefs.getString('auth_role');
      _language = prefs.getString('app_language') ?? 'en';

      if (savedToken != null && savedUser != null) {
        _token  = savedToken;
        _role   = savedRole;
        _user   = UserModel.fromJson(jsonDecode(savedUser));
        _status = AuthStatus.authenticated;
      } else {
        _status = AuthStatus.unauthenticated;
      }
    } catch (_) {
      _status = AuthStatus.unauthenticated;
    } finally {
      _setLoading(false);
    }
  }

  // ── Login ─────────────────────────────────────────────────────────────────
  Future<bool> login({
    required String role,
    required String identifier, // ASHA ID or Supervisor ID
    required String password,
  }) async {
    _setLoading(true);
    _clearError();

    try {
      final result = await AuthService.login(
        role: role,
        identifier: identifier,
        password: password,
      );

      _token  = result['access_token'] as String? ?? result['token'] as String;
      _role   = role;
      _user   = UserModel.fromJson(result['user'] as Map<String, dynamic>);
      _status = AuthStatus.authenticated;

      await _persistSession();
      notifyListeners();
      return true;
    } catch (e) {
      _errorMessage = _parseError(e);
      _status = AuthStatus.unauthenticated;
      notifyListeners();
      return false;
    } finally {
      _setLoading(false);
    }
  }

  // ── Register ASHA ─────────────────────────────────────────────────────────
  Future<bool> registerAsha({
    required String ashaId,
    required String name,
    required String mobile,
    required String password,
    required String area,
    required String district,
    required String supervisorId,
    String? email,
  }) async {
    _setLoading(true);
    _clearError();

    try {
      final result = await AuthService.registerAsha(
        ashaId: ashaId,
        name: name,
        mobile: mobile,
        password: password,
        area: area,
        district: district,
        supervisorId: supervisorId,
        email: email,
      );

      _token  = result['access_token'] as String? ?? result['token'] as String;
      _role   = 'asha_worker';
      _user   = UserModel.fromJson(result['user'] as Map<String, dynamic>);
      _status = AuthStatus.authenticated;

      await _persistSession();
      notifyListeners();
      return true;
    } catch (e) {
      _errorMessage = _parseError(e);
      notifyListeners();
      return false;
    } finally {
      _setLoading(false);
    }
  }

  // ── Register Supervisor ───────────────────────────────────────────────────
  Future<bool> registerSupervisor({
    required String supervisorId,
    required String name,
    required String mobile,
    required String password,
    required String area,
    required String district,
    String? email,
  }) async {
    _setLoading(true);
    _clearError();

    try {
      final result = await AuthService.registerSupervisor(
        supervisorId: supervisorId,
        name: name,
        mobile: mobile,
        password: password,
        area: area,
        district: district,
        email: email,
      );

      _token  = result['access_token'] as String? ?? result['token'] as String;
      _role   = 'supervisor';
      _user   = UserModel.fromJson(result['user'] as Map<String, dynamic>);
      _status = AuthStatus.authenticated;

      await _persistSession();
      notifyListeners();
      return true;
    } catch (e) {
      _errorMessage = _parseError(e);
      notifyListeners();
      return false;
    } finally {
      _setLoading(false);
    }
  }
  
  // ── Register Admin ──────────────────────────────────────────────────────────
  Future<bool> registerAdmin({
    required String name,
    required String mobile,
    required String password,
    required String email,
    String? district,
  }) async {
    _setLoading(true);
    _clearError();

    try {
      final result = await AuthService.registerAdmin(
        name: name,
        mobile: mobile,
        password: password,
        email: email,
        district: district,
        token: _token,
      );

      _token  = result['access_token'] as String? ?? result['token'] as String;
      _role   = 'admin';
      _user   = UserModel.fromJson(result['user'] as Map<String, dynamic>);
      _status = AuthStatus.authenticated;

      await _persistSession();
      notifyListeners();
      return true;
    } catch (e) {
      _errorMessage = _parseError(e);
      notifyListeners();
      return false;
    } finally {
      _setLoading(false);
    }
  }

  // ── Change Password ───────────────────────────────────────────────────────
  Future<bool> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    if (_token == null) return false;
    _setLoading(true);
    _clearError();

    try {
      await AuthService.changePassword(
        currentPassword: currentPassword,
        newPassword: newPassword,
        token: _token!,
      );
      notifyListeners();
      return true;
    } catch (e) {
      _errorMessage = _parseError(e);
      notifyListeners();
      return false;
    } finally {
      _setLoading(false);
    }
  }

  // ── Logout ────────────────────────────────────────────────────────────────
  Future<void> logout() async {
    _setLoading(true);
    try {
      await AuthService.logout(token: _token);
    } catch (_) {
      // Ignore server errors; clear locally regardless.
    } finally {
      await _clearSession();
      _status = AuthStatus.unauthenticated;
      _user   = null;
      _token  = null;
      _role   = null;
      _setLoading(false);
    }
  }

  // ── Language ───────────────────────────────────────────────────────────────
  Future<void> setLanguage(String lang) async {
    _language = lang;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('app_language', lang);
    notifyListeners();
  }

  // ── Update local user (e.g. after profile edit) ───────────────────────────
  Future<void> updateUser(UserModel updatedUser) async {
    _user = updatedUser;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(ApiConstants.userKey, jsonEncode(updatedUser.toJson()));
    notifyListeners();
  }

  // ── Private helpers ───────────────────────────────────────────────────────
  Future<void> _persistSession() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(ApiConstants.tokenKey, _token!);
    await prefs.setString(ApiConstants.userKey, jsonEncode(_user!.toJson()));
    if (_role != null) await prefs.setString('auth_role', _role!);
  }

  Future<void> _clearSession() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(ApiConstants.tokenKey);
    await prefs.remove(ApiConstants.userKey);
    await prefs.remove('auth_role');
  }

  void _setLoading(bool value) {
    _isLoading = value;
    notifyListeners();
  }

  void _clearError() => _errorMessage = null;

  String _parseError(Object e) {
    if (e is String) return e;
    return e.toString().replaceFirst('Exception: ', '');
  }
}