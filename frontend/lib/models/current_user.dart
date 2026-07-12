class CurrentUser {
  const CurrentUser({
    required this.id,
    required this.email,
    required this.username,
    required this.role,
    required this.status,
    required this.createdAt,
    required this.updatedAt,
  });

  final int id;
  final String email;
  final String username;
  final String role;
  final String status;
  final DateTime createdAt;
  final DateTime updatedAt;

  factory CurrentUser.fromJson(Map<String, dynamic> json) {
    return CurrentUser(
      id: json['id'] as int,
      email: json['email'] as String,
      username: json['username'] as String,
      role: json['role'] as String,
      status: json['status'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }
}
