import { http } from './http'
import type { Teacher } from '@/types/domain'

export interface RegisterPayload {
  username: string
  password: string
  display_name: string
}

export const authApi = {
  register(payload: RegisterPayload) {
    return http.post<Teacher>('/auth/register', payload).then((r) => r.data)
  },
  login(username: string, password: string) {
    // OAuth2PasswordRequestForm 需要 form-urlencoded
    const form = new URLSearchParams()
    form.append('username', username)
    form.append('password', password)
    return http
      .post<{ access_token: string; token_type: string }>('/auth/login', form)
      .then((r) => r.data)
  },
  me() {
    return http.get<Teacher>('/auth/me').then((r) => r.data)
  },
}
