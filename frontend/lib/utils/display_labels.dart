String statusLabel(String? value) {
  switch ((value ?? '').trim().toLowerCase()) {
    case 'active':
      return '활성';
    case 'inactive':
      return '비활성';
    case 'retired':
      return '은퇴';
    case 'scheduled':
      return '예정';
    case 'in_progress':
      return '진행 중';
    case 'completed':
      return '완료';
    case 'finished':
      return '완주';
    case 'confirmed':
      return '확정';
    case 'withdrawn':
      return '출전 취소';
    case 'disqualified':
      return '실격';
    case 'unknown':
      return '-';
    case '':
      return '-';
    default:
      return value ?? '-';
  }
}

String optionalLabel(String? value) {
  if (value == null || value.trim().isEmpty) {
    return '-';
  }
  if (value.trim().toLowerCase() == 'unknown') {
    return '-';
  }
  return value;
}
