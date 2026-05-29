import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../context/auth_provider.dart';
import '../../utils/app_theme.dart';
import '../../widgets/auth_widgets.dart';

class RegisterSupervisorScreen extends StatefulWidget {
  const RegisterSupervisorScreen({super.key});

  @override
  State<RegisterSupervisorScreen> createState() => _RegisterSupervisorScreenState();
}

class _RegisterSupervisorScreenState extends State<RegisterSupervisorScreen> {
  final _formKey       = GlobalKey<FormState>();
  final _supervisorIdCtrl = TextEditingController();
  final _nameCtrl      = TextEditingController();
  final _mobileCtrl    = TextEditingController();
  final _passwordCtrl  = TextEditingController();
  final _confirmCtrl   = TextEditingController();
  final _areaCtrl      = TextEditingController();
  final _districtCtrl  = TextEditingController();
  final _emailCtrl     = TextEditingController();

  bool _obscurePassword = true;
  bool _obscureConfirm  = true;

  @override
  void dispose() {
    _supervisorIdCtrl.dispose();
    _nameCtrl.dispose();
    _mobileCtrl.dispose();
    _passwordCtrl.dispose();
    _confirmCtrl.dispose();
    _areaCtrl.dispose();
    _districtCtrl.dispose();
    _emailCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    FocusScope.of(context).unfocus();

    final auth = context.read<AuthProvider>();
    final success = await auth.registerSupervisor(
      supervisorId: _supervisorIdCtrl.text.trim(),
      name:         _nameCtrl.text.trim(),
      mobile:       _mobileCtrl.text.trim(),
      password:     _passwordCtrl.text,
      area:         _areaCtrl.text.trim(),
      district:     _districtCtrl.text.trim(),
      email:        _emailCtrl.text.trim().isEmpty ? null : _emailCtrl.text.trim(),
    );

    if (!mounted) return;

    if (success) {
      context.go('/dashboard/supervisor');
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(auth.errorMessage ?? 'Registration failed. Please try again.'),
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
          'Supervisor Registration',
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
                  icon: Icons.supervisor_account_rounded,
                  title: 'Create Supervisor Account',
                  subtitle: 'Register as a block/district supervisor',
                ),
                const SizedBox(height: 28),

                const AuthSectionLabel(label: 'Identity'),
                const SizedBox(height: 12),
                AuthTextField(
                  controller: _supervisorIdCtrl,
                  label: 'Supervisor ID',
                  hint: 'e.g. SUP123456',
                  icon: Icons.badge_outlined,
                  inputFormatters: [
                    FilteringTextInputFormatter.allow(RegExp(r'[a-zA-Z0-9]')),
                  ],
                  validator: (v) {
                    if (v == null || v.trim().isEmpty) return 'Supervisor ID is required';
                    if (v.trim().length < 4) return 'ID must be at least 4 characters';
                    return null;
                  },
                ),
                const SizedBox(height: 14),
                AuthTextField(
                  controller: _nameCtrl,
                  label: 'Full Name',
                  hint: 'Your full name',
                  icon: Icons.person_outline_rounded,
                  textCapitalization: TextCapitalization.words,
                  validator: (v) =>
                      (v == null || v.trim().isEmpty) ? 'Full name is required' : null,
                ),
                const SizedBox(height: 14),
                AuthTextField(
                  controller: _mobileCtrl,
                  label: 'Mobile Number',
                  hint: '10-digit mobile number',
                  icon: Icons.phone_outlined,
                  keyboardType: TextInputType.phone,
                  inputFormatters: [
                    FilteringTextInputFormatter.digitsOnly,
                    LengthLimitingTextInputFormatter(10),
                  ],
                  validator: (v) {
                    if (v == null || v.trim().isEmpty) return 'Mobile number is required';
                    if (v.trim().length != 10) return 'Enter a valid 10-digit mobile number';
                    return null;
                  },
                ),
                const SizedBox(height: 14),
                AuthTextField(
                  controller: _emailCtrl,
                  label: 'Email',
                  hint: 'your@email.com',
                  icon: Icons.email_outlined,
                  keyboardType: TextInputType.emailAddress,
                  validator: (v) {
                    if (v == null || v.trim().isEmpty) return 'Email is required';
                    final emailRegex = RegExp(r'^[\w-.]+@([\w-]+\.)+[\w]{2,4}$');
                    if (!emailRegex.hasMatch(v.trim())) return 'Enter a valid email address';
                    return null;
                  },
                ),
                const SizedBox(height: 24),

                const AuthSectionLabel(label: 'Assignment'),
                const SizedBox(height: 12),
                AuthTextField(
                  controller: _areaCtrl,
                  label: 'Zone / Block',
                  hint: 'Your assigned area',
                  icon: Icons.location_city_outlined,
                  textCapitalization: TextCapitalization.words,
                  validator: (v) =>
                      (v == null || v.trim().isEmpty) ? 'Zone / Block is required' : null,
                ),
                const SizedBox(height: 14),
                AuthTextField(
                  controller: _districtCtrl,
                  label: 'District',
                  hint: 'Your district',
                  icon: Icons.map_outlined,
                  textCapitalization: TextCapitalization.words,
                  validator: (v) =>
                      (v == null || v.trim().isEmpty) ? 'District is required' : null,
                ),
                const SizedBox(height: 24),

                const AuthSectionLabel(label: 'Security'),
                const SizedBox(height: 12),
                AuthTextField(
                  controller: _passwordCtrl,
                  label: 'Password',
                  hint: 'Minimum 6 characters',
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
                    if (v.length < 6) return 'Password must be at least 6 characters';
                    return null;
                  },
                ),
                const SizedBox(height: 14),
                AuthTextField(
                  controller: _confirmCtrl,
                  label: 'Confirm Password',
                  hint: 'Re-enter your password',
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
                    if (v == null || v.isEmpty) return 'Please confirm your password';
                    if (v != _passwordCtrl.text) return 'Passwords do not match';
                    return null;
                  },
                ),
                const SizedBox(height: 32),

                SizedBox(
                  height: 52,
                  child: ElevatedButton(
                    onPressed: auth.isLoading ? null : _submit,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.supervisorColor,
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
                            'Register',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                  ),
                ),
                const SizedBox(height: 20),

                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Text(
                      'Already have an account? ',
                      style: TextStyle(color: AppColors.textSecondary),
                    ),
                    GestureDetector(
                      onTap: () => context.go('/login'),
                      child: const Text(
                        'Login',
                        style: TextStyle(
                          color: AppColors.supervisorColor,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
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
