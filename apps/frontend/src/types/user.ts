export interface UserProfile {
  id: number
  email: string
  username: string
  first_name?: string | null
  last_name?: string | null
  profile_image?: string | null
  profile_image_data?: string | null
  profile_image_mime?: string | null
  job_type?: string | null
  is_new_user: boolean
  survey_completed: boolean
  updated_at?: string
}

export interface PreferenceSummary {
  job?: string | null
  priorities: Record<string, number>
  completedAt?: string | null
}

export interface PreferenceSurveyPayload {
  job: string
  priorities: Record<string, number>
}
