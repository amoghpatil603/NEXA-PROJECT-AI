import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class AuthProvider extends ChangeNotifier {
  bool _isAuthenticated = false;
  String _token = '';

  bool get isAuthenticated => _isAuthenticated;
  String get token => _token;

  AuthProvider() {
    _loadSession();
  }

  Future<void> _loadSession() async {
    final prefs = await SharedPreferences.getInstance();
    _token = prefs.getString('auth_token') ?? '';
    _isAuthenticated = _token.isNotEmpty;
    notifyListeners();
  }

  Future<bool> login(String username, String password) async {
    // Simulate real backend authentication
    await Future.delayed(const Duration(seconds: 1));
    if (username.isNotEmpty && password.isNotEmpty) {
      _token = 'simulated_nexa_token_87654321';
      _isAuthenticated = true;
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('auth_token', _token);
      notifyListeners();
      return true;
    }
    return false;
  }

  Future<void> logout() async {
    _token = '';
    _isAuthenticated = false;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('auth_token');
    notifyListeners();
  }
}
