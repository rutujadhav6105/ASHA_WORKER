import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../utils/app_theme.dart';
import '../../widgets/common_widgets.dart';
import '../../services/api_service.dart';

class AnalyticsScreen extends StatefulWidget {
  const AnalyticsScreen({super.key});

  @override
  State<AnalyticsScreen> createState() => _AnalyticsScreenState();
}

class _AnalyticsScreenState extends State<AnalyticsScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabCtrl;
  Map<String, dynamic>? _data;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _tabCtrl = TabController(length: 4, vsync: this);
    _loadData();
  }

  Future<void> _loadData() async {
    try {
      final res = await ApiService.getDashboardSummary();
      if (mounted) setState(() { _data = res['summary']; _loading = false; });
    } catch (e) {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  void dispose() { _tabCtrl.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Analytics & Reports'),
        backgroundColor: AppColors.primary,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded, color: Colors.white),
          onPressed: () => context.pop(),
        ),
        bottom: TabBar(
          controller: _tabCtrl,
          indicatorColor: Colors.white,
          indicatorWeight: 3,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white60,
          labelStyle: const TextStyle(fontFamily: 'Poppins', fontWeight: FontWeight.w600, fontSize: 12),
          tabs: const [
            Tab(text: 'Overview'),
            Tab(text: 'Pregnancy'),
            Tab(text: 'Nutrition'),
            Tab(text: 'Visits'),
          ],
        ),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: AppColors.primary))
          : TabBarView(
              controller: _tabCtrl,
              children: [
                _OverviewTab(data: _data),
                _PregnancyTab(data: _data),
                _NutritionTab(data: _data),
                _VisitsTab(data: _data),
              ],
            ),
    );
  }
}

// ─── Overview Tab ─────────────────────────────────────────────────────────────
class _OverviewTab extends StatelessWidget {
  final Map<String, dynamic>? data;
  const _OverviewTab({this.data});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Summary Metrics ──────────────────────────────────────────────
          const SectionHeader(title: 'Health Summary', subtitle: 'Current month'),
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
            childAspectRatio: 1.55,
            children: [
              StatCard(
                label: 'Total Patients',
                value: data?['total_patients']?.toString() ?? '0',
                icon: Icons.people_rounded,
                color: AppColors.primary,
              ),
              StatCard(
                label: 'High-Risk Cases',
                value: data?['high_risk_pregnancies']?.toString() ?? '0',
                icon: Icons.warning_rounded,
                color: AppColors.danger,
              ),
              StatCard(
                label: 'Vaccinations Due',
                value: data?['due_vaccinations']?.toString() ?? '0',
                icon: Icons.vaccines_rounded,
                color: AppColors.warning,
              ),
              StatCard(
                label: 'Medicine Shortages',
                value: data?['medicine_shortages']?.toString() ?? '0',
                icon: Icons.medication_rounded,
                color: AppColors.danger,
              ),
            ],
          ),
          const SizedBox(height: 24),

          // ── Monthly Trend Chart ──────────────────────────────────────────
          const SectionHeader(title: 'Monthly Trends'),
          _BarChart(
            title: 'Registrations vs Visits',
            data: [
              _Bar(label: 'Jan', reg: 12, visits: 18),
              _Bar(label: 'Feb', reg: 15, visits: 22),
              _Bar(label: 'Mar', reg: 10, visits: 16),
              _Bar(label: 'Apr', reg: 18, visits: 28),
              _Bar(label: 'May', reg: 14, visits: 20),
              _Bar(label: 'Jun', reg: 20, visits: 30),
            ],
          ),
          const SizedBox(height: 24),

          // ── Coverage Indicators ──────────────────────────────────────────
          const SectionHeader(title: 'Coverage Indicators'),
          _CoverageCard(
            indicators: [
              _CoverageItem('Immunization Coverage', 0.82, AppColors.success),
              _CoverageItem('ANC Visit Completion', 0.65, AppColors.primary),
              _CoverageItem('Institutional Delivery', 0.78, AppColors.info),
              _CoverageItem('Nutrition Screening', 0.55, AppColors.warning),
              _CoverageItem('Family Planning', 0.70, AppColors.supervisorColor),
            ],
          ),
          const SizedBox(height: 80),
        ],
      ),
    );
  }
}

// ─── Pregnancy Tab ────────────────────────────────────────────────────────────
class _PregnancyTab extends StatelessWidget {
  final Map<String, dynamic>? data;
  const _PregnancyTab({this.data});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SectionHeader(
            title: 'Pregnancy Risk Analysis',
            subtitle: 'AI-powered ML predictions',
          ),

          // ── Risk Distribution ────────────────────────────────────────────
          _DonutChart(
            title: 'Risk Level Distribution',
            segments: [
              _Segment('High Risk', 0.15, AppColors.danger),
              _Segment('Medium Risk', 0.30, AppColors.warning),
              _Segment('Low Risk', 0.55, AppColors.success),
            ],
          ),
          const SizedBox(height: 20),

          // ── Risk Factors ─────────────────────────────────────────────────
          const SectionCard(
            title: 'Key Risk Factors Detected',
            icon: Icons.analytics_rounded,
            iconColor: AppColors.danger,
            child: Column(
              children: [
                InfoRow(
                  label: 'Anemia (Hb < 8 g/dL)',
                  value: '12 cases',
                  icon: Icons.bloodtype_rounded,
                  valueColor: AppColors.danger,
                ),
                Divider(height: 12),
                InfoRow(
                  label: 'High Blood Pressure',
                  value: '8 cases',
                  icon: Icons.monitor_heart_rounded,
                  valueColor: AppColors.danger,
                ),
                Divider(height: 12),
                InfoRow(
                  label: 'Age < 18 or > 35',
                  value: '5 cases',
                  icon: Icons.cake_rounded,
                  valueColor: AppColors.warning,
                ),
                Divider(height: 12),
                InfoRow(
                  label: 'Previous Complications',
                  value: '7 cases',
                  icon: Icons.history_rounded,
                  valueColor: AppColors.warning,
                ),
              ],
            ),
          ),

          // ── ANC Visits Progress ──────────────────────────────────────────
          const SectionCard(
            title: 'ANC Visit Completion',
            icon: Icons.pregnant_woman_rounded,
            iconColor: Color(0xFFDB2777),
            child: Column(
              children: [
                _ANCProgressRow(label: 'ANC 1 (8-12 weeks)', value: 0.92),
                SizedBox(height: 12),
                _ANCProgressRow(label: 'ANC 2 (14-26 weeks)', value: 0.76),
                SizedBox(height: 12),
                _ANCProgressRow(label: 'ANC 3 (28-32 weeks)', value: 0.61),
                SizedBox(height: 12),
                _ANCProgressRow(label: 'ANC 4 (36+ weeks)', value: 0.45),
              ],
            ),
          ),
          const SizedBox(height: 80),
        ],
      ),
    );
  }
}

class _ANCProgressRow extends StatelessWidget {
  final String label;
  final double value;
  const _ANCProgressRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    final color = value >= 0.8 ? AppColors.success : value >= 0.6 ? AppColors.warning : AppColors.danger;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label, style: const TextStyle(fontSize: 12, fontFamily: 'Poppins', color: AppColors.textPrimary)),
            Text('${(value * 100).round()}%', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: color, fontFamily: 'Poppins')),
          ],
        ),
        const SizedBox(height: 4),
        MiniProgressBar(value: value, color: color, height: 8),
      ],
    );
  }
}

// ─── Nutrition Tab ────────────────────────────────────────────────────────────
class _NutritionTab extends StatelessWidget {
  final Map<String, dynamic>? data;
  const _NutritionTab({this.data});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SectionHeader(
            title: 'Child Nutrition Analysis',
            subtitle: 'Based on WHO growth standards',
          ),
          _DonutChart(
            title: 'Nutrition Status Distribution',
            segments: [
              _Segment('Severely Acute\nMalnutrition', 0.08, AppColors.danger),
              _Segment('Moderate Acute\nMalnutrition', 0.18, AppColors.warning),
              _Segment('Normal', 0.74, AppColors.success),
            ],
          ),
          const SizedBox(height: 20),

          // ── Age Group Analysis ───────────────────────────────────────────
          const SectionCard(
            title: 'Malnutrition by Age Group',
            icon: Icons.child_care_rounded,
            iconColor: AppColors.warning,
            child: Column(
              children: [
                _NutritionBar(label: '0-6 months', severe: 0.04, moderate: 0.10),
                SizedBox(height: 10),
                _NutritionBar(label: '6-12 months', severe: 0.07, moderate: 0.15),
                SizedBox(height: 10),
                _NutritionBar(label: '1-3 years', severe: 0.12, moderate: 0.22),
                SizedBox(height: 10),
                _NutritionBar(label: '3-5 years', severe: 0.06, moderate: 0.18),
              ],
            ),
          ),

          const SectionCard(
            title: 'Interventions Recommended',
            icon: Icons.medical_information_rounded,
            iconColor: AppColors.primary,
            child: Column(
              children: [
                _InterventionRow(label: 'Supplementary Nutrition', count: '24 children', color: AppColors.warning),
                Divider(height: 16),
                _InterventionRow(label: 'Therapeutic Feeding', count: '8 children', color: AppColors.danger),
                Divider(height: 16),
                _InterventionRow(label: 'Growth Monitoring', count: '52 children', color: AppColors.info),
              ],
            ),
          ),
          const SizedBox(height: 80),
        ],
      ),
    );
  }
}

class _NutritionBar extends StatelessWidget {
  final String label;
  final double severe;
  final double moderate;
  const _NutritionBar({required this.label, required this.severe, required this.moderate});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        SizedBox(
          width: 80,
          child: Text(label, style: const TextStyle(fontSize: 11, color: AppColors.textSecondary, fontFamily: 'Poppins')),
        ),
        Expanded(
          child: Column(
            children: [
              Row(
                children: [
                  Expanded(
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(4),
                      child: Row(
                        children: [
                          Flexible(
                            flex: (severe * 100).round(),
                            child: Container(height: 12, color: AppColors.danger),
                          ),
                          Flexible(
                            flex: (moderate * 100).round(),
                            child: Container(height: 12, color: AppColors.warning),
                          ),
                          Flexible(
                            flex: ((1 - severe - moderate) * 100).round(),
                            child: Container(height: 12, color: AppColors.successSurface),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _InterventionRow extends StatelessWidget {
  final String label;
  final String count;
  final Color color;
  const _InterventionRow({required this.label, required this.count, required this.color});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: const TextStyle(fontSize: 13, fontFamily: 'Poppins', color: AppColors.textPrimary)),
        StatusBadge(label: count, color: color),
      ],
    );
  }
}

// ─── Visits Tab ───────────────────────────────────────────────────────────────
class _VisitsTab extends StatelessWidget {
  final Map<String, dynamic>? data;
  const _VisitsTab({this.data});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SectionHeader(
            title: 'Home Visit Analysis',
            subtitle: 'Predicted visit compliance',
          ),

          // ── Visit Summary Cards ──────────────────────────────────────────
          Row(
            children: [
              const Expanded(child: MetricChip(label: 'Completed', value: '142', color: AppColors.success)),
              const SizedBox(width: 10),
              Expanded(child: MetricChip(label: 'Pending', value: data?['pending_visits']?.toString() ?? '0', color: AppColors.warning)),
              const SizedBox(width: 10),
              const Expanded(child: MetricChip(label: 'Overdue', value: '18', color: AppColors.danger)),
            ],
          ),
          const SizedBox(height: 20),

          // ── Likely to Miss Prediction ────────────────────────────────────
          SectionCard(
            title: 'ML: Likely to Miss Next Visit',
            icon: Icons.psychology_rounded,
            iconColor: AppColors.supervisorColor,
            child: Column(
              children: [
                const AlertCard(
                  title: 'Prediction Active',
                  message: 'Based on visit history, 14 patients are likely to miss their next appointment.',
                  type: 'warning',
                ),
                const SizedBox(height: 12),
                ...[
                  const _PatientRiskRow(name: 'Sunita Devi', village: 'Sangli', risk: 0.87, color: AppColors.danger),
                  const _PatientRiskRow(name: 'Rekha Patil', village: 'Miraj', risk: 0.74, color: AppColors.warning),
                  const _PatientRiskRow(name: 'Asha Kamble', village: 'Islampur', risk: 0.65, color: AppColors.warning),
                ].map((w) => Column(children: [const Divider(height: 16), w])),
              ],
            ),
          ),

          // ── Day-wise Distribution ────────────────────────────────────────
          SectionCard(
            title: 'Visit Distribution by Day',
            icon: Icons.calendar_month_rounded,
            child: Column(
              children: [
                for (final day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'])
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Row(
                      children: [
                        SizedBox(
                          width: 36,
                          child: Text(day, style: const TextStyle(fontSize: 12, fontFamily: 'Poppins', color: AppColors.textSecondary)),
                        ),
                        Expanded(
                          child: MiniProgressBar(
                            value: [0.8, 0.5, 0.9, 0.4, 0.7, 0.3][['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].indexOf(day)],
                            color: AppColors.primary,
                            height: 10,
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(height: 80),
        ],
      ),
    );
  }
}

class _PatientRiskRow extends StatelessWidget {
  final String name;
  final String village;
  final double risk;
  final Color color;
  const _PatientRiskRow({required this.name, required this.village, required this.risk, required this.color});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        InitialsAvatar(initials: name.substring(0, 1), radius: 18, backgroundColor: color.withValues(alpha: 0.2)),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(name, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, fontFamily: 'Poppins')),
              Text(village, style: const TextStyle(fontSize: 11, color: AppColors.textSecondary, fontFamily: 'Poppins')),
            ],
          ),
        ),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
          decoration: BoxDecoration(color: color.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(6)),
          child: Text(
            '${(risk * 100).round()}% risk',
            style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: color, fontFamily: 'Poppins'),
          ),
        ),
      ],
    );
  }
}

// ─── Reusable Chart Components ────────────────────────────────────────────────

class _Bar {
  final String label;
  final int reg;
  final int visits;
  _Bar({required this.label, required this.reg, required this.visits});
}

class _BarChart extends StatelessWidget {
  final String title;
  final List<_Bar> data;
  const _BarChart({required this.title, required this.data});

  @override
  Widget build(BuildContext context) {
    final max = data.map((b) => b.visits).reduce((a, b) => a > b ? a : b).toDouble();
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(AppRadius.lg),
        border: Border.all(color: AppColors.divider),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(title, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, fontFamily: 'Poppins', color: AppColors.textPrimary)),
              const Spacer(),
              const _Legend(color: AppColors.primary, label: 'Registrations'),
              const SizedBox(width: 10),
              const _Legend(color: AppColors.accent, label: 'Visits'),
            ],
          ),
          const SizedBox(height: 16),
          SizedBox(
            height: 120,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: data.map((b) => _BarGroup(bar: b, max: max)).toList(),
            ),
          ),
        ],
      ),
    );
  }
}

class _BarGroup extends StatelessWidget {
  final _Bar bar;
  final double max;
  const _BarGroup({required this.bar, required this.max});

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.end,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            _SingleBar(value: bar.reg / max, color: AppColors.primary),
            const SizedBox(width: 2),
            _SingleBar(value: bar.visits / max, color: AppColors.accent),
          ],
        ),
        const SizedBox(height: 4),
        Text(bar.label, style: const TextStyle(fontSize: 9, color: AppColors.textHint, fontFamily: 'Poppins')),
      ],
    );
  }
}

class _SingleBar extends StatelessWidget {
  final double value;
  final Color color;
  const _SingleBar({required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 600),
      curve: Curves.easeOut,
      width: 12,
      height: 90 * value,
      decoration: BoxDecoration(
        color: color,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(4)),
      ),
    );
  }
}

class _Legend extends StatelessWidget {
  final Color color;
  final String label;
  const _Legend({required this.color, required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(width: 10, height: 10, decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(2))),
        const SizedBox(width: 4),
        Text(label, style: const TextStyle(fontSize: 10, color: AppColors.textSecondary, fontFamily: 'Poppins')),
      ],
    );
  }
}

class _Segment {
  final String label;
  final double value;
  final Color color;
  _Segment(this.label, this.value, this.color);
}

class _DonutChart extends StatelessWidget {
  final String title;
  final List<_Segment> segments;
  const _DonutChart({required this.title, required this.segments});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(AppRadius.lg),
        border: Border.all(color: AppColors.divider),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, fontFamily: 'Poppins', color: AppColors.textPrimary)),
          const SizedBox(height: 16),
          Row(
            children: [
              // Simple visual donut representation
              SizedBox(
                width: 100,
                height: 100,
                child: CustomPaint(painter: _DonutPainter(segments: segments)),
              ),
              const SizedBox(width: 20),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: segments.map((s) => Padding(
                    padding: const EdgeInsets.symmetric(vertical: 5),
                    child: Row(
                      children: [
                        Container(width: 12, height: 12, decoration: BoxDecoration(color: s.color, shape: BoxShape.circle)),
                        const SizedBox(width: 8),
                        Expanded(child: Text(s.label, style: const TextStyle(fontSize: 11, fontFamily: 'Poppins', color: AppColors.textSecondary))),
                        Text('${(s.value * 100).round()}%', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: s.color, fontFamily: 'Poppins')),
                      ],
                    ),
                  )).toList(),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _DonutPainter extends CustomPainter {
  final List<_Segment> segments;
  _DonutPainter({required this.segments});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2;
    double startAngle = -3.14159 / 2;

    for (final s in segments) {
      final paint = Paint()
        ..color = s.color
        ..strokeWidth = 18
        ..style = PaintingStyle.stroke
        ..strokeCap = StrokeCap.butt;
      final sweepAngle = s.value * 2 * 3.14159;
      canvas.drawArc(
        Rect.fromCircle(center: center, radius: radius - 9),
        startAngle,
        sweepAngle - 0.05,
        false,
        paint,
      );
      startAngle += sweepAngle;
    }
  }

  @override
  bool shouldRepaint(_DonutPainter oldDelegate) => false;
}

// ─── Coverage Card ────────────────────────────────────────────────────────────
class _CoverageItem {
  final String label;
  final double value;
  final Color color;
  _CoverageItem(this.label, this.value, this.color);
}

class _CoverageCard extends StatelessWidget {
  final List<_CoverageItem> indicators;
  const _CoverageCard({required this.indicators});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(AppRadius.lg),
        border: Border.all(color: AppColors.divider),
      ),
      child: Column(
        children: indicators
            .map((i) => Padding(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(i.label, style: const TextStyle(fontSize: 12, fontFamily: 'Poppins', color: AppColors.textPrimary)),
                          Text('${(i.value * 100).round()}%',
                              style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: i.color, fontFamily: 'Poppins')),
                        ],
                      ),
                      const SizedBox(height: 4),
                      MiniProgressBar(value: i.value, color: i.color),
                    ],
                  ),
                ))
            .toList(),
      ),
    );
  }
}
