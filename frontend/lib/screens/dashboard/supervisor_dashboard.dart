import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../context/auth_provider.dart';
import '../../utils/app_theme.dart';
import '../../translations/app_translations.dart';
import '../../widgets/common_widgets.dart';
import '../../services/api_service.dart';

class SupervisorDashboard extends StatefulWidget {
  const SupervisorDashboard({super.key});

  @override
  State<SupervisorDashboard> createState() => _SupervisorDashboardState();
}

class _SupervisorDashboardState extends State<SupervisorDashboard> {
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
      if (mounted) setState(() { _summary = data['summary']; _loading = false; });
    } catch (_) {
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
        color: AppColors.supervisorColor,
        child: CustomScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          slivers: [
            SliverToBoxAdapter(
              child: GradientHeader(
                title: 'Supervisor · ${user?.area ?? ''}',
                subtitle: user?.name ?? 'Supervisor',
                initials: user?.initials ?? 'S',
                gradientColors: AppColors.gradientSupervisor,
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
                    // ── Zone Summary ───────────────────────────────────────
                    const SectionHeader(title: 'Zone Overview'),
                    GridView.count(
                      crossAxisCount: 2,
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      crossAxisSpacing: 12, mainAxisSpacing: 12,
                      childAspectRatio: 1.55,
                      children: [
                        StatCard(
                          label: 'ASHA Workers',
                          value: _val('total_asha_workers'),
                          icon: Icons.medical_services_rounded,
                          color: AppColors.supervisorColor,
                        ),
                        StatCard(
                          label: t('totalFamilies'),
                          value: _val('total_families'),
                          icon: Icons.home_rounded,
                          color: AppColors.primary,
                          trend: '+2',
                          trendUp: true,
                        ),
                        StatCard(
                          label: t('pendingVaccines'),
                          value: _val('due_vaccinations'),
                          icon: Icons.vaccines_rounded,
                          color: AppColors.warning,
                        ),
                        StatCard(
                          label: 'High-Risk Cases',
                          value: _val('high_risk_pregnancies'),
                          icon: Icons.warning_rounded,
                          color: AppColors.danger,
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),

                    // ── ASHA Worker Performance ────────────────────────────
                    const SectionHeader(
                      title: 'Worker Performance',
                      subtitle: 'This month',
                    ),
                    const _WorkerPerformanceList(),
                    const SizedBox(height: 20),

                    // ── Modules ────────────────────────────────────────────
                    const SectionHeader(title: 'Modules'),
                    GridView.count(
                      crossAxisCount: 3,
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      crossAxisSpacing: 10, mainAxisSpacing: 10,
                      childAspectRatio: 0.88,
                      children: [
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
                          badge: _val('high_risk_pregnancies') != '0' ? _val('high_risk_pregnancies') : null,
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
                          color: AppColors.supervisorColor,
                          onTap: () => context.push('/analytics'),
                        ),
                        ModuleTile(
                          icon: Icons.note_alt_rounded,
                          label: 'Notes',
                          color: const Color(0xFFD97706),
                          onTap: () => context.push('/supervisor-notes'),
                        ),
                        ModuleTile(
                          icon: Icons.person_outline_rounded,
                          label: t('profile'),
                          color: Colors.blueGrey.shade600,
                          onTap: () => context.push('/profile'),
                        ),
                      ],
                    ),
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

class _WorkerPerformanceList extends StatelessWidget {
  final _workers = const [
    {'name': 'Priya Sharma', 'village': 'Sangli', 'visits': 28, 'target': 35, 'compliance': 0.80},
    {'name': 'Rekha Patil', 'village': 'Miraj', 'visits': 32, 'target': 35, 'compliance': 0.91},
    {'name': 'Sunita Devi', 'village': 'Islampur', 'visits': 18, 'target': 35, 'compliance': 0.51},
  ];

  const _WorkerPerformanceList();

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(AppRadius.lg),
        border: Border.all(color: AppColors.divider),
      ),
      child: Column(
        children: _workers.asMap().entries.map((e) {
          final w = e.value;
          final compliance = w['compliance'] as double;
          final color = compliance >= 0.8 ? AppColors.success
              : compliance >= 0.6 ? AppColors.warning
              : AppColors.danger;
          return Column(
            children: [
              Padding(
                padding: const EdgeInsets.all(14),
                child: Column(
                  children: [
                    Row(
                      children: [
                        InitialsAvatar(
                          initials: (w['name'] as String).substring(0, 1),
                          radius: 18,
                          backgroundColor: AppColors.supervisorColor.withValues(alpha: 0.2),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(w['name'] as String,
                                  style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, fontFamily: 'Poppins')),
                              Text(w['village'] as String,
                                  style: const TextStyle(fontSize: 11, color: AppColors.textSecondary, fontFamily: 'Poppins')),
                            ],
                          ),
                        ),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: [
                            Text(
                              '${w['visits']}/${w['target']} visits',
                              style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: color, fontFamily: 'Poppins'),
                            ),
                            Text(
                              '${(compliance * 100).round()}% compliance',
                              style: const TextStyle(fontSize: 10, color: AppColors.textHint, fontFamily: 'Poppins'),
                            ),
                          ],
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    MiniProgressBar(value: compliance, color: color),
                  ],
                ),
              ),
              if (e.key < _workers.length - 1) const Divider(height: 1),
            ],
          );
        }).toList(),
      ),
    );
  }
}
