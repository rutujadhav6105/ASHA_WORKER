import 'package:flutter/material.dart';
import '../utils/app_theme.dart';

// ─── Gradient App Bar Header ─────────────────────────────────────────────────
class GradientHeader extends StatelessWidget {
  final String title;
  final String subtitle;
  final String initials;
  final List<Color> gradientColors;
  final String language;
  final ValueChanged<String> onLanguageChanged;
  final VoidCallback? onProfileTap;
  final List<Widget>? actions;

  const GradientHeader({
    super.key,
    required this.title,
    required this.subtitle,
    required this.initials,
    required this.gradientColors,
    required this.language,
    required this.onLanguageChanged,
    this.onProfileTap,
    this.actions,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: gradientColors,
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      ),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  GestureDetector(
                    onTap: onProfileTap,
                    child: _PulsingAvatar(initials: initials),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          title,
                          style: const TextStyle(
                            color: Colors.white70,
                            fontSize: 12,
                            fontFamily: 'Poppins',
                            fontWeight: FontWeight.w400,
                          ),
                        ),
                        Text(
                          subtitle,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 16,
                            fontFamily: 'Poppins',
                            fontWeight: FontWeight.w700,
                            letterSpacing: -0.3,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                  LanguageSelector(current: language, onChanged: onLanguageChanged),
                  if (actions != null) ...actions!,
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _PulsingAvatar extends StatefulWidget {
  final String initials;
  const _PulsingAvatar({required this.initials});

  @override
  State<_PulsingAvatar> createState() => _PulsingAvatarState();
}

class _PulsingAvatarState extends State<_PulsingAvatar>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _anim;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(vsync: this, duration: const Duration(seconds: 2))
      ..repeat(reverse: true);
    _anim = Tween(begin: 1.0, end: 1.06).animate(
      CurvedAnimation(parent: _ctrl, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ScaleTransition(
      scale: _anim,
      child: Container(
        width: 48,
        height: 48,
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.25),
          shape: BoxShape.circle,
          border: Border.all(color: Colors.white.withValues(alpha: 0.5), width: 2),
        ),
        alignment: Alignment.center,
        child: Text(
          widget.initials.toUpperCase(),
          style: const TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.w700,
            fontFamily: 'Poppins',
            fontSize: 16,
          ),
        ),
      ),
    );
  }
}

// ─── Stat Card (improved with trend indicator) ───────────────────────────────
class StatCard extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color color;
  final String? trend;
  final bool trendUp;
  final VoidCallback? onTap;

  const StatCard({
    super.key,
    required this.label,
    required this.value,
    required this.icon,
    this.color = AppColors.primary,
    this.trend,
    this.trendUp = true,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(AppRadius.lg),
          border: Border.all(color: AppColors.divider),
          boxShadow: [
            BoxShadow(
              color: color.withValues(alpha: 0.06),
              blurRadius: 12,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: color.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(icon, color: color, size: 18),
                ),
                const Spacer(),
                if (trend != null)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: trendUp
                          ? AppColors.successSurface
                          : AppColors.dangerSurface,
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          trendUp ? Icons.trending_up : Icons.trending_down,
                          size: 10,
                          color: trendUp ? AppColors.success : AppColors.danger,
                        ),
                        const SizedBox(width: 2),
                        Text(
                          trend!,
                          style: TextStyle(
                            fontSize: 9,
                            fontWeight: FontWeight.w700,
                            color: trendUp ? AppColors.success : AppColors.danger,
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
            const Spacer(),
            Text(
              value,
              style: TextStyle(
                fontSize: 26,
                fontWeight: FontWeight.w800,
                color: color,
                fontFamily: 'Poppins',
                height: 1,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: const TextStyle(
                fontSize: 11,
                color: AppColors.textSecondary,
                fontFamily: 'Poppins',
              ),
              maxLines: 2,
            ),
          ],
        ),
      ),
    );
  }
}

// ─── Enhanced Module Tile ─────────────────────────────────────────────────────
class ModuleTile extends StatefulWidget {
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;
  final String? badge;

  const ModuleTile({
    super.key,
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
    this.badge,
  });

  @override
  State<ModuleTile> createState() => _ModuleTileState();
}

class _ModuleTileState extends State<ModuleTile>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _scale;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 120),
    );
    _scale = Tween(begin: 1.0, end: 0.93).animate(
      CurvedAnimation(parent: _ctrl, curve: Curves.easeOut),
    );
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) => _ctrl.forward(),
      onTapUp: (_) {
        _ctrl.reverse();
        widget.onTap();
      },
      onTapCancel: () => _ctrl.reverse(),
      child: ScaleTransition(
        scale: _scale,
        child: Stack(
          clipBehavior: Clip.none,
          children: [
            Container(
              decoration: BoxDecoration(
                color: widget.color.withValues(alpha: 0.07),
                borderRadius: BorderRadius.circular(AppRadius.lg),
                border: Border.all(color: widget.color.withValues(alpha: 0.18)),
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [
                          widget.color.withValues(alpha: 0.2),
                          widget.color.withValues(alpha: 0.1),
                        ],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      shape: BoxShape.circle,
                    ),
                    child: Icon(widget.icon, color: widget.color, size: 26),
                  ),
                  const SizedBox(height: 8),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 4),
                    child: Text(
                      widget.label,
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: widget.color.withValues(alpha: 0.9),
                        fontFamily: 'Poppins',
                        height: 1.3,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            if (widget.badge != null)
              Positioned(
                top: -4,
                right: -4,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: AppColors.danger,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: Colors.white, width: 1.5),
                  ),
                  child: Text(
                    widget.badge!,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 9,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

// ─── App Text Field ───────────────────────────────────────────────────────────
class AppTextField extends StatelessWidget {
  final String label;
  final TextEditingController controller;
  final bool obscure;
  final TextInputType keyboardType;
  final String? Function(String?)? validator;
  final Widget? prefixIcon;
  final Widget? suffixIcon;
  final int? maxLength;
  final bool readOnly;
  final VoidCallback? onTap;
  final String? hint;
  final int? maxLines;

  const AppTextField({
    super.key,
    required this.label,
    required this.controller,
    this.obscure = false,
    this.keyboardType = TextInputType.text,
    this.validator,
    this.prefixIcon,
    this.suffixIcon,
    this.maxLength,
    this.readOnly = false,
    this.onTap,
    this.hint,
    this.maxLines = 1,
  });

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      controller: controller,
      obscureText: obscure,
      keyboardType: keyboardType,
      validator: validator,
      maxLength: maxLength,
      readOnly: readOnly,
      onTap: onTap,
      maxLines: maxLines,
      style: const TextStyle(
        fontFamily: 'Poppins',
        fontSize: 14,
        color: AppColors.textPrimary,
      ),
      decoration: InputDecoration(
        labelText: label,
        hintText: hint,
        prefixIcon: prefixIcon,
        suffixIcon: suffixIcon,
        counterText: '',
      ),
    );
  }
}

// ─── Section Header ──────────────────────────────────────────────────────────
class SectionHeader extends StatelessWidget {
  final String title;
  final String? subtitle;
  final Widget? trailing;

  const SectionHeader({
    super.key,
    required this.title,
    this.subtitle,
    this.trailing,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                  color: AppColors.textPrimary,
                  fontFamily: 'Poppins',
                  letterSpacing: -0.3,
                ),
              ),
              if (subtitle != null)
                Text(
                  subtitle!,
                  style: const TextStyle(
                    fontSize: 12,
                    color: AppColors.textSecondary,
                    fontFamily: 'Poppins',
                  ),
                ),
            ],
          ),
          const Spacer(),
          if (trailing != null) trailing!,
        ],
      ),
    );
  }
}

// ─── Risk Badge ───────────────────────────────────────────────────────────────
class RiskBadge extends StatelessWidget {
  final String level; // low, medium, high

  const RiskBadge({super.key, required this.level});

  @override
  Widget build(BuildContext context) {
    Color bg, fg;
    IconData icon;
    String label;
    switch (level.toLowerCase()) {
      case 'high':
        bg = AppColors.dangerSurface;
        fg = AppColors.danger;
        icon = Icons.warning_rounded;
        label = 'High Risk';
        break;
      case 'medium':
        bg = AppColors.warningSurface;
        fg = AppColors.warning;
        icon = Icons.info_rounded;
        label = 'Medium Risk';
        break;
      default:
        bg = AppColors.successSurface;
        fg = AppColors.success;
        icon = Icons.check_circle_rounded;
        label = 'Low Risk';
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: fg, size: 12),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              color: fg,
              fontFamily: 'Poppins',
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Status Badge ─────────────────────────────────────────────────────────────
class StatusBadge extends StatelessWidget {
  final String label;
  final Color color;

  const StatusBadge({super.key, required this.label, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w600,
          color: color,
          fontFamily: 'Poppins',
        ),
      ),
    );
  }
}

// ─── Mini Progress Bar ────────────────────────────────────────────────────────
class MiniProgressBar extends StatelessWidget {
  final double value; // 0.0 to 1.0
  final Color color;
  final double height;

  const MiniProgressBar({
    super.key,
    required this.value,
    this.color = AppColors.primary,
    this.height = 6,
  });

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(100),
      child: LinearProgressIndicator(
        value: value.clamp(0, 1),
        backgroundColor: color.withValues(alpha: 0.12),
        valueColor: AlwaysStoppedAnimation(color),
        minHeight: height,
      ),
    );
  }
}

// ─── Info Row ─────────────────────────────────────────────────────────────────
class InfoRow extends StatelessWidget {
  final String label;
  final String value;
  final IconData? icon;
  final Color? valueColor;

  const InfoRow({
    super.key,
    required this.label,
    required this.value,
    this.icon,
    this.valueColor,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          if (icon != null) ...[
            Icon(icon!, size: 14, color: AppColors.textSecondary),
            const SizedBox(width: 6),
          ],
          Text(
            label,
            style: const TextStyle(
              fontSize: 12,
              color: AppColors.textSecondary,
              fontFamily: 'Poppins',
            ),
          ),
          const Spacer(),
          Text(
            value,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: valueColor ?? AppColors.textPrimary,
              fontFamily: 'Poppins',
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Alert Card ───────────────────────────────────────────────────────────────
class AlertCard extends StatelessWidget {
  final String title;
  final String message;
  final String type; // info, warning, danger, success
  final VoidCallback? onAction;
  final String? actionLabel;

  const AlertCard({
    super.key,
    required this.title,
    required this.message,
    this.type = 'info',
    this.onAction,
    this.actionLabel,
  });

  @override
  Widget build(BuildContext context) {
    Color bg, border, fg;
    IconData icon;
    switch (type) {
      case 'warning':
        bg = AppColors.warningSurface;
        border = AppColors.warning.withValues(alpha: 0.3);
        fg = AppColors.warning;
        icon = Icons.warning_amber_rounded;
        break;
      case 'danger':
        bg = AppColors.dangerSurface;
        border = AppColors.danger.withValues(alpha: 0.3);
        fg = AppColors.danger;
        icon = Icons.error_rounded;
        break;
      case 'success':
        bg = AppColors.successSurface;
        border = AppColors.success.withValues(alpha: 0.3);
        fg = AppColors.success;
        icon = Icons.check_circle_rounded;
        break;
      default:
        bg = AppColors.infoSurface;
        border = AppColors.info.withValues(alpha: 0.3);
        fg = AppColors.info;
        icon = Icons.info_rounded;
    }

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: border),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: fg, size: 18),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: fg,
                    fontFamily: 'Poppins',
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  message,
                  style: TextStyle(
                    fontSize: 12,
                    color: fg.withValues(alpha: 0.8),
                    fontFamily: 'Poppins',
                  ),
                ),
              ],
            ),
          ),
          if (onAction != null)
            TextButton(
              onPressed: onAction,
              style: TextButton.styleFrom(
                foregroundColor: fg,
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                minimumSize: Size.zero,
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
              child: Text(
                actionLabel ?? 'View',
                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700),
              ),
            ),
        ],
      ),
    );
  }
}

// ─── Loading Overlay ──────────────────────────────────────────────────────────
class LoadingOverlay extends StatelessWidget {
  const LoadingOverlay({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.black.withValues(alpha: 0.3),
      child: const Center(
        child: Card(
          child: Padding(
            padding: EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                CircularProgressIndicator(color: AppColors.primary),
                SizedBox(height: 16),
                Text(
                  'Please wait...',
                  style: TextStyle(
                    fontFamily: 'Poppins',
                    color: AppColors.textSecondary,
                    fontSize: 13,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// ─── Language Selector ────────────────────────────────────────────────────────
class LanguageSelector extends StatelessWidget {
  final String current;
  final ValueChanged<String> onChanged;

  const LanguageSelector({super.key, required this.current, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        _LangBtn(label: 'EN', code: 'en', current: current, onTap: () => onChanged('en')),
        const SizedBox(width: 4),
        _LangBtn(label: 'मर', code: 'mr', current: current, onTap: () => onChanged('mr')),
        const SizedBox(width: 4),
        _LangBtn(label: 'हि', code: 'hi', current: current, onTap: () => onChanged('hi')),
      ],
    );
  }
}

class _LangBtn extends StatelessWidget {
  final String label, code, current;
  final VoidCallback onTap;
  const _LangBtn({required this.label, required this.code, required this.current, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final selected = code == current;
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: selected ? Colors.white.withValues(alpha: 0.25) : Colors.transparent,
          borderRadius: BorderRadius.circular(6),
          border: Border.all(
            color: selected ? Colors.white.withValues(alpha: 0.6) : Colors.white.withValues(alpha: 0.3),
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 11,
            fontWeight: selected ? FontWeight.w700 : FontWeight.w400,
            color: Colors.white,
            fontFamily: 'Poppins',
          ),
        ),
      ),
    );
  }
}

// ─── Section Card ─────────────────────────────────────────────────────────────
class SectionCard extends StatelessWidget {
  final String title;
  final Widget child;
  final IconData? icon;
  final Color? iconColor;

  const SectionCard({super.key, required this.title, required this.child, this.icon, this.iconColor});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(AppRadius.lg),
        border: Border.all(color: AppColors.divider),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
            child: Row(
              children: [
                if (icon != null) ...[
                  Container(
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: (iconColor ?? AppColors.primary).withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Icon(icon!, color: iconColor ?? AppColors.primary, size: 16),
                  ),
                  const SizedBox(width: 10),
                ],
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary,
                    fontFamily: 'Poppins',
                  ),
                ),
              ],
            ),
          ),
          const Divider(height: 20),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
            child: child,
          ),
        ],
      ),
    );
  }
}

// ─── Initials Avatar ──────────────────────────────────────────────────────────
class InitialsAvatar extends StatelessWidget {
  final String initials;
  final double radius;
  final Color? backgroundColor;

  const InitialsAvatar({
    super.key,
    required this.initials,
    this.radius = 24,
    this.backgroundColor,
  });

  @override
  Widget build(BuildContext context) {
    return CircleAvatar(
      radius: radius,
      backgroundColor: backgroundColor ?? AppColors.primary,
      child: Text(
        initials.toUpperCase(),
        style: TextStyle(
          color: Colors.white,
          fontWeight: FontWeight.w700,
          fontSize: radius * 0.55,
          fontFamily: 'Poppins',
        ),
      ),
    );
  }
}

// ─── Metric Chip ──────────────────────────────────────────────────────────────
class MetricChip extends StatelessWidget {
  final String label;
  final String value;
  final Color color;

  const MetricChip({
    super.key,
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withValues(alpha: 0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            value,
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w800,
              color: color,
              fontFamily: 'Poppins',
            ),
          ),
          Text(
            label,
            style: const TextStyle(
              fontSize: 10,
              color: AppColors.textSecondary,
              fontFamily: 'Poppins',
            ),
          ),
        ],
      ),
    );
  }
}
