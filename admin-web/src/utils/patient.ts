export interface PatientIdentityView {
  patient_code?: string
  full_name?: string | null
  patient_name?: string | null
}

export function patientDisplayName(patient: PatientIdentityView): string {
  return patient.full_name || patient.patient_name || '姓名待补充'
}

export function patientLabel(patient: PatientIdentityView): string {
  return `${patient.patient_code || '未编号'} · ${patientDisplayName(patient)}`
}
