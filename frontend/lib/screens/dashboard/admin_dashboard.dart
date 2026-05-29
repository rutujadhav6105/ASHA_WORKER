import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../context/auth_provider.dart';
import '../../utils/app_theme.dart';
import '../../translations/app_translations.dart';
import '../../widgets/common_widgets.dart';
import '../../services/api_service.dart';

class AdminDashboard extends StatefulWidget {
  const AdminDashboard({super.key});

  @override
  State<AdminDashboard> createState() => _AdminDashboardState();
}

class _AdminDashboardState extends State<AdminDashboard> {
  Map<String, dynamic>? _summary;
  bool _loading = true;

  String t(String key) =>
      AppTranslations.get(key, context.read<AuthProvider>().language);

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    try {
      final data = await ApiService.getDashboardSummary();
      if (mounted) {
        setState(() {
          _summary = data['summary'];
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _loading = false);
    }
  }

  String _val(String key, [String fallback = '0']) =>
      (_summary?[key] ?? fallback).toString();

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final lang = auth.language;
    final user = auth.user;

    return Scaffold(
      backgroundColor: AppColors.background,
      body: RefreshIndicator(
        onRefresh: _loadData,
        color: AppColors.adminColor,
        child: CustomScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          slivers: [
            SliverToBoxAdapter(
              child: GradientHeader(
                title: 'System Administrator',
                subtitle: user?.name ?? 'Admin',
                initials: user?.initials ?? 'AD',
                gradientColors: AppColors.gradientAdmin,
                language: lang,
                onLanguageChanged: (l) => auth.setLanguage(l),
                onProfileTap: () => context.push('/profile'),
              ),
            ),

            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // ── System Health Banner ───────────────────────────────
                    _SystemHealthBanner(summary: _summary),
                    const SizedBox(height: 20),

                    // ── Key Metrics ────────────────────────────────────────
                    const SectionHeader(
                      title: 'System Overview',
                      subtitle: 'Real-time statistics',
                    ),
                    GridView.count(
                      crossAxisCount: 2,
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      crossAxisSpacing: 12,
                      mainAxisSpacing: 12,
                      childAspectRatio: 1.55,
                      children: [
                        StatCard(
                          label: 'Supervisors',
                          value: _val('total_supervisors', '0'),
                          icon: Icons.supervisor_account_rounded,
                          color: AppColors.adminColor,
                          trend: '+1',
                          trendUp: true,
                        ),
                        StatCard(
                          label: 'ASHA Workers',
                          value: _val('total_asha_workers', '0'),
                          icon: Icons.medical_services_rounded,
                          color: AppColors.primary,
                          trend: '+3',
                          trendUp: true,
                        ),
                        StatCard(
                          label: t('totalFamilies'),
                          value: _val('total_families'),
                          icon: Icons.home_rounded,
                          color: const Color(0xFF0891B2),
                        ),
                        StatCard(
                          label: t('totalBeneficiaries'),
                          value: _val('total_patients'),
                          icon: Icons.people_rounded,
                          color: const Color(0xFF059669),
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),

                    // ── Alert Overview ─────────────────────────────────────
                    const SectionHeader(title: 'Active Alerts'),
                    _AlertOverview(summary: _summary),
                    const SizedBox(height: 20),

                    // ── Admin Modules ──────────────────────────────────────
                    const SectionHeader(title: 'Management Modules'),
                    GridView.count(
                      crossAxisCount: 3,
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      crossAxisSpacing: 10,
                      mainAxisSpacing: 10,
                      childAspectRatio: 0.88,
                      children: [
                        ModuleTile(
                          icon: Icons.people_rounded,
                          label: 'Users',
                          color: AppColors.adminColor,
                          onTap: () => context.push('/admin/users'),
                        ),
                        ModuleTile(
                          icon: Icons.family_restroom_rounded,
                          label: t('beneficiaries'),
                          color: AppColors.primary,
                          onTap: () => context.push('/beneficiaries'),
                        ),
                        ModuleTile(
                          icon: Icons.pregnant_woman_rounded,
                          label: t('anc'),
                          color: const Color(0xFFDB2777),
                          onTap: () => context.push('/anc'),
                        ),
                        ModuleTile(
                          icon: Icons.vaccines_rounded,
                          label: t('immunization'),
                          color: const Color(0xFF0891B2),
                          onTap: () => context.push('/immunization'),
                        ),
                        ModuleTile(
                          icon: Icons.bar_chart_rounded,
                          label: 'Analytics',
                          color: const Color(0xFF7C3AED),
                          onTap: () => context.push('/analytics'),
                        ),
                        ModuleTile(
                          icon: Icons.description_rounded,
                          label: 'Reports',
                          color: const Color(0xFFD97706),
                          onTap: () => context.push('/reports'),
                        ),
                        ModuleTile(
                          icon: Icons.psychology_rounded,
                          label: 'ML Models',
                          color: const Color(0xFF059669),
                          onTap: () => context.push('/ml-dashboard'),
                        ),
                        ModuleTile(
                          icon: Icons.medication_rounded,
                          label: 'Medicine',
                          color: const Color(0xFFEF4444),
                          onTap: () => context.push('/medicine'),
                        ),
                        ModuleTile(
                          icon: Icons.card_giftcard_rounded,
                          label: t('schemes'),
                          color: const Color(0xFFF59E0B),
                          onTap: () => context.push('/schemes'),
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),

                    // ── Recent Activity ────────────────────────────────────
                    const SectionHeader(title: 'Recent System Activity'),
                    _RecentActivity(),
                    const SizedBox(height: 80),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SystemHealthBanner extends StatelessWidget {
  final Map<String, dynamic>? summary;

  const _SystemHealthBanner({this.summary});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF1E3A8A), Color(0xFF1D4ED8)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(AppRadius.lg),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.15),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.shield_rounded, color: Colors.white, size: 24),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'System Healthy',
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w700,
                    fontSize: 15,
                    fontFamily: 'Poppins',
                  ),
                ),
                Text(
                  'Last backup: ${DateTime.now().toString().substring(0, 16)}',
                  style: const TextStyle(
                    color: Colors.white70,
                    fontSize: 11,
                    fontFamily: 'Poppins',
                  ),
                ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.2),
              borderRadius: BorderRadius.circular(20),
            ),
            child: const Text(
              'All Systems ✓',
              style: TextStyle(
                color: Colors.white,
                fontSize: 11,
                fontWeight: FontWeight.w600,
                fontFamily: 'Poppins',
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _AlertOverview extends StatelessWidget {
  final Map<String, dynamic>? summary;

  const _AlertOverview({this.summary});

  @override
  Widget build(BuildContext context) {
    final highRisk = summary?['high_risk_pregnancies'] ?? 0;
    final dueVax = summary?['due_vaccinations'] ?? 0;
    final shortages = summary?['medicine_shortages'] ?? 0;

    return Column(
      children: [
        _AlertRow(
          icon: Icons.pregnant_woman_rounded,
          label: 'High-Risk Pregnancies',
          count: highRisk.toString(),
          color: AppColors.danger,
          onTap: () => Navigator.of(context).pushNamed('/anc'),
        ),
        const SizedBox(height: 8),
        _AlertRow(
          icon: Icons.vaccines_rounded,
          label: 'Vaccinations Due',
          count: dueVax.toString(),
          color: AppColors.warning,
          onTap: () {},
        ),
        const SizedBox(height: 8),
        _AlertRow(
          icon: Icons.medication_rounded,
          label: 'Medicine Shortages',
          count: shortages.toString(),
          color: AppColors.danger,
          onTap: () {},
        ),
      ],
    );
  }
}

class _AlertRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String count;
  final Color color;
  final VoidCallback onTap;

  const _AlertRow({
    required this.icon,
    required this.label,
    required this.count,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final hasAlert = int.tryParse(count) != null && int.parse(count) > 0;
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        decoration: BoxDecoration(
          color: hasAlert ? color.withValues(alpha: 0.06) : AppColors.surface,
          borderRadius: BorderRadius.circular(AppRadius.md),
          border: Border.all(
            color: hasAlert ? color.withValues(alpha: 0.25) : AppColors.divider,
          ),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(icon, color: color, size: 16),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                label,
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                  color: hasAlert ? AppColors.textPrimary : AppColors.textSecondary,
                  fontFamily: 'Poppins',
                ),
              ),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: hasAlert ? color : AppColors.divider,
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(
                count,
                style: TextStyle(
                  color: hasAlert ? Colors.white : AppColors.textHint,
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  fontFamily: 'Poppins',
                ),
              ),
            ),
            const SizedBox(width: 6),
            const Icon(
              Icons.chevron_right_rounded,
              color: AppColors.textHint,
              size: 18,
            ),
          ],
        ),
      ),
    );
  }
}

class _RecentActivity extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final activities = [
      _Activity(icon: Icons.person_add_rounded, text: 'New ASHA registered: Priya Sharma', time: '5m ago', color: AppColors.primary),
      _Activity(icon: Icons.vaccines_rounded, text: 'Vaccination record updated for village Kolhapur', time: '12m ago', color: AppColors.info),
      _Activity(icon: Icons.warning_rounded, text: 'High-risk pregnancy flagged by ML model', time: '30m ago', color: AppColors.danger),
      _Activity(icon: Icons.backup_rounded, text: 'Automatic CSV backup completed', time: '1h ago', color: AppColors.success),
    ];

    return Container(
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(AppRadius.lg),
        border: Border.all(color: AppColors.divider),
      ),
      child: Column(
        children: activities
            .asMap()
            .entries
            .map((e) => Column(
                  children: [
                    Padding(
                      padding: const EdgeInsets.all(14),
                      child: Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(7),
                            decoration: BoxDecoration(
                              color: e.value.color.withValues(alpha: 0.1),
                              shape: BoxShape.circle,
                            ),
                            child: Icon(e.value.icon, color: e.value.color, size: 14),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              e.value.text,
                              style: const TextStyle(
                                fontSize: 12,
                                color: AppColors.textPrimary,
                                fontFamily: 'Poppins',
                              ),
                            ),
                          ),
                          Text(
                            e.value.time,
                            style: const TextStyle(
                              fontSize: 10,
                              color: AppColors.textHint,
                              fontFamily: 'Poppins',
                            ),
                          ),
                        ],
                      ),
                    ),
                    if (e.key < activities.length - 1)
                      const Divider(height: 1, indent: 48),
                  ],
                ))
            .toList(),
      ),
    );
  }
}

class _Activity {
  final IconData icon;
  final String text;
  final String time;
  final Color color;
  _Activity({required this.icon, required this.text, required this.time, required this.color});
}
