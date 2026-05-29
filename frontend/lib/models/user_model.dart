class UserModel {
  final String id;
  final String name;
  final String email;
  final String? phone;
  final String? profileImageUrl;
  final String role; // e.g. 'user', 'admin'
  final String? area;
  final bool isVerified;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  const UserModel({
    required this.id,
    required this.name,
    required this.email,
    this.phone,
    this.profileImageUrl,
    this.role = 'user',
    this.area,
    this.isVerified = false,
    this.createdAt,
    this.updatedAt,
  });

  // ── Deserialise from API / SharedPreferences ──────────────────────────────
  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id']?.toString() ?? '',
      name: json['name'] as String? ?? '',
      email: json['email'] as String? ?? '',
      phone: json['phone'] as String?,
      profileImageUrl: json['profile_image_url'] as String? ??
          json['avatar'] as String? ??
          json['profileImageUrl'] as String?,
      role: json['role'] as String? ?? 'user',
      isVerified: json['is_verified'] as bool? ??
          json['isVerified'] as bool? ??
          false,
      area: json['area'] as String? ?? json['village'] as String? ?? json['zone'] as String?,
      createdAt: _parseDate(json['created_at'] ?? json['createdAt']),
      updatedAt: _parseDate(json['updated_at'] ?? json['updatedAt']),
    );
  }

  // ── Serialise for storage / API ───────────────────────────────────────────
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'email': email,
      'phone': phone,
      'profile_image_url': profileImageUrl,
      'role': role,
      'is_verified': isVerified,
      'area': area,
      'created_at': createdAt?.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
    };
  }

  // ── CopyWith for immutable updates ────────────────────────────────────────
  UserModel copyWith({
    String? id,
    String? name,
    String? email,
    String? phone,
    String? profileImageUrl,
    String? role,
    bool? isVerified,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return UserModel(
      id: id ?? this.id,
      name: name ?? this.name,
      email: email ?? this.email,
      phone: phone ?? this.phone,
      profileImageUrl: profileImageUrl ?? this.profileImageUrl,
      role: role ?? this.role,
      area: area ?? area,
      isVerified: isVerified ?? this.isVerified,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  /// Returns first name only.
  String get firstName => name.split(' ').first;

  /// Returns initials for avatar fallback, e.g. "Asha Sharma" → "AS".
  String get initials {
    final parts = name.trim().split(' ');
    if (parts.length >= 2) {
      return '${parts.first[0]}${parts.last[0]}'.toUpperCase();
    }
    return name.isNotEmpty ? name[0].toUpperCase() : '?';
  }

  bool get isAdmin => role == 'admin';

  // ── Equality ──────────────────────────────────────────────────────────────
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is UserModel &&
          runtimeType == other.runtimeType &&
          id == other.id;

  @override
  int get hashCode => id.hashCode;

  @override
  String toString() =>
      'UserModel(id: $id, name: $name, email: $email, role: $role)';

  // ── Private ───────────────────────────────────────────────────────────────
  static DateTime? _parseDate(dynamic value) {
    if (value == null) return null;
    if (value is DateTime) return value;
    if (value is String) return DateTime.tryParse(value);
    return null;
  }
}