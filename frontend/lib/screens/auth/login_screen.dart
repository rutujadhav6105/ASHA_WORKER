import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../context/auth_provider.dart';
import '../../utils/app_theme.dart';
import '../../translations/app_translations.dart';
import '../../widgets/common_widgets.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen>
    with SingleTickerProviderStateMixin {
  final _formKey = GlobalKey<FormState>();
  final _identifierCtrl = TextEditingController();
  final _mobileCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  String _selectedRole = 'asha';
  bool _showPassword = false;

  late AnimationController _animCtrl;
  late Animation<double> _fadeAnim;
  late Animation<Offset> _slideAnim;

  String t(String key) =>
      AppTranslations.get(key, context.read<AuthProvider>().language);

  @override
  void initState() {
    super.initState();
    _animCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 700),
    )..forward();
    _fadeAnim = CurvedAnimation(parent: _animCtrl, curve: Curves.easeOut);
    _slideAnim = Tween<Offset>(
      begin: const Offset(0, 0.08),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _animCtrl, curve: Curves.easeOut));
  }

  @override
  void dispose() {
    _animCtrl.dispose();
    _identifierCtrl.dispose();
    _mobileCtrl.dispose();
    _passwordCtrl.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    if (!_formKey.currentState!.validate()) return;
    final auth = context.read<AuthProvider>();
    final success = await auth.login(
      role: _selectedRole,
      identifier: _identifierCtrl.text.trim(),
      password: _passwordCtrl.text,
    );
    if (!mounted) return;
    if (success) {
      switch (_selectedRole) {
        case 'admin':      context.go('/dashboard/admin');      break;
        case 'supervisor': context.go('/dashboard/supervisor'); break;
        default:           context.go('/dashboard/asha');
      }
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(auth.errorMessage ?? t('invalidCredentials')),
          backgroundColor: AppColors.danger,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();

    return Scaffold(
      body: Stack(
        children: [
          // ── Background ─────────────────────────────────────────────────
          Container(
            height: MediaQuery.of(context).size.height * 0.38,
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: AppColors.gradientPrimary,
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
            ),
          ),

          SafeArea(
            child: SingleChildScrollView(
              child: Column(
                children: [
                  // ── Top Section ─────────────────────────────────────────
                  FadeTransition(
                    opacity: _fadeAnim,
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(24, 20, 24, 0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              // App icon
                              Container(
                                width: 48,
                                height: 48,
                                decoration: BoxDecoration(
                                  color: Colors.white.withValues(alpha: 0.2),
                                  borderRadius: BorderRadius.circular(14),
                                ),
                                child: const Icon(
                                  Icons.health_and_safety_rounded,
                                  color: Colors.white,
                                  size: 28,
                                ),
                              ),
                              LanguageSelector(
                                current: auth.language,
                                onChanged: (l) => auth.setLanguage(l),
                              ),
                            ],
                          ),
                          const SizedBox(height: 20),
                          const Text(
                            AppStrings.appName,
                            style: TextStyle(
                              fontSize: 34,
                              fontWeight: FontWeight.w800,
                              color: Colors.white,
                              fontFamily: 'Poppins',
                              letterSpacing: -1,
                            ),
                          ),
                          const Text(
                            AppStrings.tagline,
                            style: TextStyle(
                              fontSize: 13,
                              color: Colors.white70,
                              fontFamily: 'Poppins',
                            ),
                          ),
                          const SizedBox(height: 32),
                        ],
                      ),
                    ),
                  ),

                  // ── Card ────────────────────────────────────────────────
                  SlideTransition(
                    position: _slideAnim,
                    child: FadeTransition(
                      opacity: _fadeAnim,
                      child: Container(
                        margin: const EdgeInsets.symmetric(horizontal: 16),
                        decoration: BoxDecoration(
                          color: AppColors.surface,
                          borderRadius: BorderRadius.circular(AppRadius.xl),
                          boxShadow: [
                            BoxShadow(
                              color: Colors.black.withValues(alpha: 0.08),
                              blurRadius: 24,
                              offset: const Offset(0, 8),
                            ),
                          ],
                        ),
                        child: Padding(
                          padding: const EdgeInsets.all(24),
                          child: Form(
                            key: _formKey,
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'Sign In',
                                  style: TextStyle(
                                    fontSize: 22,
                                    fontWeight: FontWeight.w700,
                                    color: AppColors.textPrimary,
                                    fontFamily: 'Poppins',
                                    letterSpacing: -0.5,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                const Text(
                                  'Select your role to continue',
                                  style: TextStyle(
                                    fontSize: 13,
                                    color: AppColors.textSecondary,
                                    fontFamily: 'Poppins',
                                  ),
                                ),
                                const SizedBox(height: 20),

                                // Role Selector
                                _RoleSelector(
                                  selected: _selectedRole,
                                  onChanged: (r) => setState(() {
                                    _selectedRole = r;
                                    _identifierCtrl.clear();
                                    _mobileCtrl.clear();
                                  }),
                                ),
                                const SizedBox(height: 20),

                                // Identifier field
                                AppTextField(
                                  label: _selectedRole == 'admin'
                                      ? t('email')
                                      : _selectedRole == 'supervisor'
                                          ? t('supervisorId')
                                          : t('ashaId'),
                                  controller: _identifierCtrl,
                                  prefixIcon: Icon(
                                    _selectedRole == 'admin'
                                        ? Icons.alternate_email_rounded
                                        : Icons.badge_outlined,
                                    color: AppColors.textHint,
                                    size: 20,
                                  ),
                                  keyboardType: _selectedRole == 'admin'
                                      ? TextInputType.emailAddress
                                      : TextInputType.text,
                                  validator: (v) =>
                                      (v == null || v.isEmpty) ? t('required') : null,
                                ),
                                const SizedBox(height: 14),

                                if (_selectedRole != 'admin') ...[
                                  AppTextField(
                                    label: t('mobile'),
                                    controller: _mobileCtrl,
                                    prefixIcon: const Icon(Icons.phone_outlined,
                                        color: AppColors.textHint, size: 20),
                                    keyboardType: TextInputType.phone,
                                    maxLength: 10,
                                    validator: (v) {
                                      if (v == null || v.isEmpty) return t('required');
                                      if (v.length != 10) return t('mobileInvalid');
                                      return null;
                                    },
                                  ),
                                  const SizedBox(height: 14),
                                ],

                                AppTextField(
                                  label: t('password'),
                                  controller: _passwordCtrl,
                                  obscure: !_showPassword,
                                  prefixIcon: const Icon(Icons.lock_outline_rounded,
                                      color: AppColors.textHint, size: 20),
                                  suffixIcon: IconButton(
                                    icon: Icon(
                                      _showPassword
                                          ? Icons.visibility_off_outlined
                                          : Icons.visibility_outlined,
                                      color: AppColors.textHint,
                                      size: 20,
                                    ),
                                    onPressed: () =>
                                        setState(() => _showPassword = !_showPassword),
                                  ),
                                  validator: (v) =>
                                      (v == null || v.isEmpty) ? t('required') : null,
                                ),
                                const SizedBox(height: 28),

                                // Login button
                                ElevatedButton(
                                  onPressed: auth.isLoading ? null : _login,
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: _roleColor(),
                                    minimumSize: const Size(double.infinity, 52),
                                    shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(14),
                                    ),
                                  ),
                                  child: auth.isLoading
                                      ? const SizedBox(
                                          height: 20,
                                          width: 20,
                                          child: CircularProgressIndicator(
                                            color: Colors.white,
                                            strokeWidth: 2,
                                          ),
                                        )
                                      : Text(
                                          t('login'),
                                          style: const TextStyle(
                                            fontFamily: 'Poppins',
                                            fontWeight: FontWeight.w600,
                                            fontSize: 15,
                                          ),
                                        ),
                                ),

                                  const SizedBox(height: 16),
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.center,
                                    children: [
                                      Text(
                                        t('noAccount'),
                                        style: const TextStyle(
                                          color: AppColors.textSecondary,
                                          fontSize: 13,
                                          fontFamily: 'Poppins',
                                        ),
                                      ),
                                      TextButton(
                                        onPressed: () {
                                          if (_selectedRole == 'admin') {
                                            context.push('/register/admin');
                                          } else if (_selectedRole == 'supervisor') {
                                            context.push('/register/supervisor');
                                          } else {
                                            context.push('/register/asha');
                                          }
                                        },
                                        child: Text(
                                          t('register'),
                                          style: TextStyle(
                                            color: _roleColor(),
                                            fontWeight: FontWeight.w700,
                                            fontFamily: 'Poppins',
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 40),
                ],
              ),
            ),
          ),

          if (auth.isLoading) const LoadingOverlay(),
        ],
      ),
    );
  }

  Color _roleColor() {
    switch (_selectedRole) {
      case 'admin':      return AppColors.adminColor;
      case 'supervisor': return AppColors.supervisorColor;
      default:           return AppColors.primary;
    }
  }
}

class _RoleSelector extends StatelessWidget {
  final String selected;
  final ValueChanged<String> onChanged;

  const _RoleSelector({required this.selected, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    const roles = [
      {'key': 'admin',      'label': 'Admin',        'icon': Icons.admin_panel_settings_rounded},
      {'key': 'supervisor', 'label': 'Supervisor',   'icon': Icons.supervisor_account_rounded},
      {'key': 'asha',       'label': 'ASHA Worker',  'icon': Icons.medical_services_rounded},
    ];

    return Row(
      children: roles.map((r) {
        final isSelected = selected == r['key'];
        final color = r['key'] == 'admin'
            ? AppColors.adminColor
            : r['key'] == 'supervisor'
                ? AppColors.supervisorColor
                : AppColors.primary;

        return Expanded(
          child: GestureDetector(
            onTap: () => onChanged(r['key'] as String),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              margin: const EdgeInsets.only(right: 8),
              padding: const EdgeInsets.symmetric(vertical: 12),
              decoration: BoxDecoration(
                color: isSelected ? color.withValues(alpha: 0.1) : AppColors.background,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: isSelected ? color : AppColors.border,
                  width: isSelected ? 2 : 1,
                ),
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    r['icon'] as IconData,
                    color: isSelected ? color : AppColors.textHint,
                    size: 22,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    r['label'] as String,
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: isSelected ? FontWeight.w700 : FontWeight.w400,
                      color: isSelected ? color : AppColors.textSecondary,
                      fontFamily: 'Poppins',
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      }).toList(),
    );
  }
}
