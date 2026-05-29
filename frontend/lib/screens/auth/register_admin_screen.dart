import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../context/auth_provider.dart';
import '../../utils/app_theme.dart';
import '../../widgets/auth_widgets.dart';

class RegisterAdminScreen extends StatefulWidget {
  const RegisterAdminScreen({super.key});

  @override
  State<RegisterAdminScreen> createState() => _RegisterAdminScreenState();
}

class _RegisterAdminScreenState extends State<RegisterAdminScreen> {
  final _formKey       = GlobalKey<FormState>();
  final _nameCtrl      = TextEditingController();
  final _mobileCtrl    = TextEditingController();
  final _emailCtrl     = TextEditingController();
  final _passwordCtrl  = TextEditingController();
  final _confirmCtrl   = TextEditingController();
  final _districtCtrl  = TextEditingController();

  bool _obscurePassword = true;
  bool _obscureConfirm  = true;

  @override
  void dispose() {
    _nameCtrl.dispose();
    _mobileCtrl.dispose();
    _emailCtrl.dispose();
    _passwordCtrl.dispose();
    _confirmCtrl.dispose();
    _districtCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    FocusScope.of(context).unfocus();

    final auth = context.read<AuthProvider>();
    final success = await auth.registerAdmin(
      name:     _nameCtrl.text.trim(),
      mobile:   _mobileCtrl.text.trim(),
      email:    _emailCtrl.text.trim(),
      password: _passwordCtrl.text,
      district: _districtCtrl.text.trim().isEmpty ? null : _districtCtrl.text.trim(),
    );

    if (!mounted) return;

    if (success) {
      context.go('/dashboard/admin');
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(auth.errorMessage ?? 'Admin registration failed. Note: You might need to be logged in as an existing admin.'),
          backgroundColor: AppColors.danger,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded),
          color: AppColors.textPrimary,
          onPressed: () => context.go('/login'),
        ),
        title: const Text(
          'Admin Registration',
          style: TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.bold),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const AuthSectionHeader(
                  icon: Icons.admin_panel_settings_rounded,
                  title: 'System Admin Setup',
                  subtitle: 'Create a new administrator account',
                ),
                const SizedBox(height: 28),

                const AuthSectionLabel(label: 'Identity'),
                const SizedBox(height: 12),
                AuthTextField(
                  controller: _nameCtrl,
                  label: 'Full Name',
                  hint: 'Administrator name',
                  icon: Icons.person_outline_rounded,
                  textCapitalization: TextCapitalization.words,
                  validator: (v) =>
                      (v == null || v.trim().isEmpty) ? 'Name is required' : null,
                ),
                const SizedBox(height: 14),
                AuthTextField(
                  controller: _mobileCtrl,
                  label: 'Mobile Number',
                  hint: '10-digit mobile',
                  icon: Icons.phone_outlined,
                  keyboardType: TextInputType.phone,
                  inputFormatters: [
                    FilteringTextInputFormatter.digitsOnly,
                    LengthLimitingTextInputFormatter(10),
                  ],
                  validator: (v) {
                    if (v == null || v.trim().isEmpty) return 'Mobile is required';
                    if (v.trim().length != 10) return 'Enter 10 digits';
                    return null;
                  },
                ),
                const SizedBox(height: 14),
                AuthTextField(
                  controller: _emailCtrl,
                  label: 'Admin Email',
                  hint: 'admin@asha.gov.in',
                  icon: Icons.alternate_email_rounded,
                  keyboardType: TextInputType.emailAddress,
                  validator: (v) {
                    if (v == null || v.trim().isEmpty) return 'Email is required';
                    final emailRegex = RegExp(r'^[\w-.]+@([\w-]+\.)+[\w]{2,4}$');
                    if (!emailRegex.hasMatch(v.trim())) return 'Invalid email';
                    return null;
                  },
                ),
                const SizedBox(height: 14),
                AuthTextField(
                  controller: _districtCtrl,
                  label: 'District (optional)',
                  hint: 'Assigned district',
                  icon: Icons.map_outlined,
                ),
                const SizedBox(height: 24),

                const AuthSectionLabel(label: 'Security'),
                const SizedBox(height: 12),
                AuthTextField(
                  controller: _passwordCtrl,
                  label: 'Password',
                  hint: 'Strong password required',
                  icon: Icons.lock_outline_rounded,
                  obscureText: _obscurePassword,
                  suffixIcon: IconButton(
                    icon: Icon(
                      _obscurePassword
                          ? Icons.visibility_off_outlined
                          : Icons.visibility_outlined,
                      color: AppColors.textSecondary,
                    ),
                    onPressed: () =>
                        setState(() => _obscurePassword = !_obscurePassword),
                  ),
                  validator: (v) {
                    if (v == null || v.isEmpty) return 'Password is required';
                    if (v.length < 8) return 'Min 8 characters';
                    return null;
                  },
                ),
                const SizedBox(height: 14),
                AuthTextField(
                  controller: _confirmCtrl,
                  label: 'Confirm Password',
                  hint: 'Confirm admin password',
                  icon: Icons.lock_outline_rounded,
                  obscureText: _obscureConfirm,
                  suffixIcon: IconButton(
                    icon: Icon(
                      _obscureConfirm
                          ? Icons.visibility_off_outlined
                          : Icons.visibility_outlined,
                      color: AppColors.textSecondary,
                    ),
                    onPressed: () =>
                        setState(() => _obscureConfirm = !_obscureConfirm),
                  ),
                  validator: (v) {
                    if (v == null || v.isEmpty) return 'Please confirm';
                    if (v != _passwordCtrl.text) return 'Passwords mismatch';
                    return null;
                  },
                ),
                const SizedBox(height: 32),

                SizedBox(
                  height: 52,
                  child: ElevatedButton(
                    onPressed: auth.isLoading ? null : _submit,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.adminColor,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14),
                      ),
                      elevation: 0,
                    ),
                    child: auth.isLoading
                        ? const SizedBox(
                            height: 22,
                            width: 22,
                            child: CircularProgressIndicator(
                              strokeWidth: 2.5,
                              color: Colors.white,
                            ),
                          )
                        : const Text(
                            'Setup Admin',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                  ),
                ),
                const SizedBox(height: 24),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
