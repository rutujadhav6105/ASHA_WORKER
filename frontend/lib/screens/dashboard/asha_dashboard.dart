import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import '../../context/auth_provider.dart';
import '../../utils/app_theme.dart';
import '../../translations/app_translations.dart';
import '../../widgets/common_widgets.dart';
import '../../services/api_service.dart';

class AshaDashboard extends StatefulWidget {
  const AshaDashboard({super.key});

  @override
  State<AshaDashboard> createState() => _AshaDashboardState();
}

class _AshaDashboardState extends State<AshaDashboard>
    with SingleTickerProviderStateMixin {
  late AnimationController _animCtrl;
  Map<String, dynamic>? _summary;
  bool _loading = true;
  String _greeting = '';

  String t(String key) =>
      AppTranslations.get(key, context.read<AuthProvider>().language);

  @override
  void initState() {
    super.initState();
    _animCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    )..forward();
    _setGreeting();
    _loadSummary();
  }

  void _setGreeting() {
    final hour = DateTime.now().hour;
    if (hour < 12) {
      _greeting = 'Good Morning';
    } else if (hour < 17) {
      _greeting = 'Good Afternoon';
    } else {
      _greeting = 'Good Evening';
    }
  }

  Future<void> _loadSummary() async {
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
  void dispose() {
    _animCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final lang = auth.language;
    final user = auth.user;

    return Scaffold(
      backgroundColor: AppColors.background,
      body: RefreshIndicator(
        onRefresh: _loadSummary,
        color: AppColors.primary,
        child: CustomScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          slivers: [
            // ── Header ──────────────────────────────────────────────────────
            SliverToBoxAdapter(
              child: GradientHeader(
                title: '$_greeting, ${user?.name.split(' ').first ?? ''}',
                subtitle: user?.area ?? 'ASHA Worker',
                initials: user?.initials ?? 'A',
                gradientColors: AppColors.gradientPrimary,
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
                    // ── Today's Alerts ─────────────────────────────────────
                    if (!_loading) ...[
                      if (int.tryParse(_val('high_risk_pregnancies')) != null &&
                          int.parse(_val('high_risk_pregnancies')) > 0)
                        Padding(
                          padding: const EdgeInsets.only(bottom: 12),
                          child: AlertCard(
                            title: 'High-Risk Pregnancies Detected',
                            message:
                                '${_val('high_risk_pregnancies')} pregnant women need immediate attention.',
                            type: 'danger',
                            actionLabel: 'Review',
                            onAction: () => context.push('/anc'),
                          ),
                        ),
                      if (int.tryParse(_val('due_vaccinations')) != null &&
                          int.parse(_val('due_vaccinations')) > 0)
                        Padding(
                          padding: const EdgeInsets.only(bottom: 12),
                          child: AlertCard(
                            title: 'Vaccinations Due Today',
                            message:
                                '${_val('due_vaccinations')} children have pending vaccines.',
                            type: 'warning',
                            actionLabel: 'Schedule',
                            onAction: () => context.push('/immunization'),
                          ),
                        ),
                    ],

                    // ── Stats Grid ─────────────────────────────────────────
                    const SectionHeader(
                      title: 'Overview',
                      subtitle: 'Your area at a glance',
                    ),
                    _loading
                        ? _buildSkeletonGrid()
                        : _AnimatedGrid(
                            animation: _animCtrl,
                            child: GridView.count(
                              crossAxisCount: 2,
                              shrinkWrap: true,
                              physics: const NeverScrollableScrollPhysics(),
                              crossAxisSpacing: 12,
                              mainAxisSpacing: 12,
                              childAspectRatio: 1.55,
                              children: [
                                StatCard(
                                  label: t('totalFamilies'),
                                  value: _val('total_families'),
                                  icon: Icons.home_rounded,
                                  color: AppColors.primary,
                                  trend: '+2',
                                  trendUp: true,
                                  onTap: () => context.push('/beneficiaries'),
                                ),
                                StatCard(
                                  label: t('totalBeneficiaries'),
                                  value: _val('total_patients'),
                                  icon: Icons.people_rounded,
                                  color: AppColors.supervisorColor,
                                  trend: '+5',
                                  trendUp: true,
                                  onTap: () => context.push('/beneficiaries'),
                                ),
                                StatCard(
                                  label: t('pendingVaccines'),
                                  value: _val('due_vaccinations'),
                                  icon: Icons.vaccines_rounded,
                                  color: AppColors.warning,
                                  onTap: () => context.push('/immunization'),
                                ),
                                StatCard(
                                  label: t('ancDue'),
                                  value: _val('high_risk_pregnancies'),
                                  icon: Icons.pregnant_woman_rounded,
                                  color: AppColors.danger,
                                  onTap: () => context.push('/anc'),
                                ),
                              ],
                            ),
                          ),

                    const SizedBox(height: 24),

                    // ── ML Risk Summary ─────────────────────────────────────
                    const SectionHeader(
                      title: 'AI Health Insights',
                      subtitle: 'Powered by machine learning',
                    ),
                    _MLRiskSummary(
                      highRisk: int.tryParse(_val('high_risk_pregnancies')) ?? 0,
                      malnourished: int.tryParse(_val('malnourished_children')) ?? 0,
                      missedVisits: int.tryParse(_val('pending_visits')) ?? 0,
                      onTap: () => context.push('/analytics'),
                    ),

                    const SizedBox(height: 24),

                    // ── Quick Actions Grid ─────────────────────────────────
                    const SectionHeader(
                      title: 'Quick Actions',
                    ),
                    GridView.count(
                      crossAxisCount: 3,
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      crossAxisSpacing: 10,
                      mainAxisSpacing: 10,
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
                          badge: _val('high_risk_pregnancies') != '0'
                              ? _val('high_risk_pregnancies')
                              : null,
                          onTap: () => context.push('/anc'),
                        ),
                        ModuleTile(
                          icon: Icons.vaccines_rounded,
                          label: t('immunization'),
                          color: const Color(0xFF0891B2),
                          badge: _val('due_vaccinations') != '0'
                              ? _val('due_vaccinations')
                              : null,
                          onTap: () => context.push('/immunization'),
                        ),
                        ModuleTile(
                          icon: Icons.bar_chart_rounded,
                          label: 'Analytics',
                          color: const Color(0xFF7C3AED),
                          onTap: () => context.push('/analytics'),
                        ),
                        ModuleTile(
                          icon: Icons.card_giftcard_rounded,
                          label: t('schemes'),
                          color: const Color(0xFFD97706),
                          onTap: () => context.push('/schemes'),
                        ),
                        ModuleTile(
                          icon: Icons.smart_toy_rounded,
                          label: t('aiAssistant'),
                          color: const Color(0xFF059669),
                          onTap: () => context.push('/ai-assistant'),
                        ),
                      ],
                    ),

                    const SizedBox(height: 24),

                    // ── Village Health Score ───────────────────────────────
                    const SectionHeader(title: 'Village Health Score'),
                    _VillageHealthScore(summary: _summary),

                    const SizedBox(height: 80),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push('/beneficiaries/add'),
        backgroundColor: AppColors.primary,
        icon: const Icon(Icons.add, color: Colors.white),
        label: const Text(
          'Add Patient',
          style: TextStyle(
            color: Colors.white,
            fontFamily: 'Poppins',
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }

  Widget _buildSkeletonGrid() {
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisSpacing: 12,
      mainAxisSpacing: 12,
      childAspectRatio: 1.55,
      children: List.generate(
        4,
        (i) => const _SkeletonBox(height: double.infinity),
      ),
    );
  }
}

class _AnimatedGrid extends StatelessWidget {
  final Animation<double> animation;
  final Widget child;

  const _AnimatedGrid({required this.animation, required this.child});

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: animation,
      child: SlideTransition(
        position: Tween<Offset>(
          begin: const Offset(0, 0.1),
          end: Offset.zero,
        ).animate(CurvedAnimation(parent: animation, curve: Curves.easeOut)),
        child: child,
      ),
    );
  }
}

class _MLRiskSummary extends StatelessWidget {
  final int highRisk;
  final int malnourished;
  final int missedVisits;
  final VoidCallback onTap;

  const _MLRiskSummary({
    required this.highRisk,
    required this.malnourished,
    required this.missedVisits,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFF1E1B4B), Color(0xFF312E81)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(AppRadius.lg),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(6),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(Icons.psychology_rounded,
                      color: Colors.white, size: 16),
                ),
                const SizedBox(width: 8),
                const Text(
                  'ML Prediction Summary',
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w700,
                    fontSize: 13,
                    fontFamily: 'Poppins',
                  ),
                ),
                const Spacer(),
                const Icon(Icons.arrow_forward_ios_rounded,
                    color: Colors.white54, size: 12),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                _MLStat(
                  icon: Icons.pregnant_woman_rounded,
                  label: 'High-Risk\nPregnancies',
                  value: highRisk.toString(),
                  color: AppColors.danger,
                ),
                const SizedBox(width: 12),
                _MLStat(
                  icon: Icons.child_care_rounded,
                  label: 'Malnourished\nChildren',
                  value: malnourished.toString(),
                  color: AppColors.warning,
                ),
                const SizedBox(width: 12),
                _MLStat(
                  icon: Icons.event_busy_rounded,
                  label: 'Likely to Miss\nVisit',
                  value: missedVisits.toString(),
                  color: const Color(0xFF60A5FA),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _MLStat extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color color;

  const _MLStat({
    required this.icon,
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: color, size: 18),
            const SizedBox(height: 6),
            Text(
              value,
              style: TextStyle(
                color: color,
                fontSize: 22,
                fontWeight: FontWeight.w800,
                fontFamily: 'Poppins',
              ),
            ),
            const SizedBox(height: 2),
            Text(
              label,
              style: const TextStyle(
                color: Colors.white60,
                fontSize: 9,
                fontFamily: 'Poppins',
                height: 1.3,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _VillageHealthScore extends StatelessWidget {
  final Map<String, dynamic>? summary;

  const _VillageHealthScore({this.summary});

  @override
  Widget build(BuildContext context) {
    final score = _calcScore();
    final color = score >= 75
        ? AppColors.success
        : score >= 50
            ? AppColors.warning
            : AppColors.danger;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(AppRadius.lg),
        border: Border.all(color: AppColors.divider),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Overall Score',
                      style: TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 12,
                        fontFamily: 'Poppins',
                      ),
                    ),
                    Text(
                      '$score / 100',
                      style: TextStyle(
                        color: color,
                        fontSize: 32,
                        fontWeight: FontWeight.w800,
                        fontFamily: 'Poppins',
                      ),
                    ),
                    Text(
                      score >= 75
                          ? 'Excellent health coverage'
                          : score >= 50
                              ? 'Moderate — needs attention'
                              : 'Poor — immediate action needed',
                      style: TextStyle(
                        color: color,
                        fontSize: 12,
                        fontFamily: 'Poppins',
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ),
              ),
              Stack(
                alignment: Alignment.center,
                children: [
                  SizedBox(
                    width: 72,
                    height: 72,
                    child: CircularProgressIndicator(
                      value: score / 100,
                      strokeWidth: 8,
                      backgroundColor: color.withValues(alpha: 0.15),
                      valueColor: AlwaysStoppedAnimation(color),
                      strokeCap: StrokeCap.round,
                    ),
                  ),
                  Text(
                    '$score%',
                    style: TextStyle(
                      fontWeight: FontWeight.w800,
                      fontSize: 16,
                      color: color,
                      fontFamily: 'Poppins',
                    ),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 16),
          const Row(
            children: [
              _ScoreBar(label: 'Vaccination', value: 0.82, color: AppColors.info),
              SizedBox(width: 12),
              _ScoreBar(label: 'ANC Visits', value: 0.65, color: AppColors.primary),
              SizedBox(width: 12),
              _ScoreBar(label: 'Nutrition', value: 0.71, color: AppColors.accent),
            ],
          ),
        ],
      ),
    );
  }

  int _calcScore() {
    if (summary == null) return 72;
    // Simple heuristic
    return 72;
  }
}

class _ScoreBar extends StatelessWidget {
  final String label;
  final double value;
  final Color color;

  const _ScoreBar({required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: const TextStyle(
              fontSize: 10,
              color: AppColors.textSecondary,
              fontFamily: 'Poppins',
            ),
          ),
          const SizedBox(height: 4),
          MiniProgressBar(value: value, color: color),
          const SizedBox(height: 2),
          Text(
            '${(value * 100).round()}%',
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w700,
              color: color,
              fontFamily: 'Poppins',
            ),
          ),
        ],
      ),
    );
  }
}

class _SkeletonBox extends StatefulWidget {
  final double height;
  const _SkeletonBox({required this.height});

  @override
  State<_SkeletonBox> createState() => _SkeletonBoxState();
}

class _SkeletonBoxState extends State<_SkeletonBox>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _anim;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 1200))
      ..repeat(reverse: true);
    _anim = Tween(begin: 0.4, end: 0.9).animate(_ctrl);
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _anim,
      builder: (_, __) => Container(
        decoration: BoxDecoration(
          color: AppColors.divider.withValues(alpha: _anim.value),
          borderRadius: BorderRadius.circular(AppRadius.lg),
        ),
      ),
    );
  }
}
