import client from "./client";

/** 发送管理员验证码 */
export function adminSendCode(email: string) {
  return client.post("/admin/send-code", { email });
}

/** 管理员验证码登录 */
export function adminLogin(email: string, code: string): Promise<{ access_token: string; token_type: string }> {
  return client.post("/admin/login", { email, code }).then(r => r.data);
}

/** Dashboard 统计 */
export interface DashboardStats {
  total_users: number;
  total_codes: number;
  used_codes: number;
  unused_codes: number;
  total_analyses: number;
  completed_analyses: number;
  failed_analyses: number;
  total_tickets_sold: number;
  total_tickets_used: number;
}
export function getDashboard(): Promise<DashboardStats> {
  return client.get("/admin/dashboard").then(r => r.data);
}

/** 卡密列表 */
export interface CodeItem {
  id: string;
  code: string;
  ticket_value: number;
  is_used: boolean;
  used_by: string | null;
  used_at: string | null;
  created_at: string;
}
export function getCodes(params: { page?: number; page_size?: number; search?: string; used_filter?: string }): Promise<{ total: number; items: CodeItem[] }> {
  return client.get("/admin/codes", { params }).then(r => r.data);
}

/** 导入卡密 CSV */
export function importCodes(file: File, ticketValue: number): Promise<{ imported: number; skipped: number; message: string }> {
  const form = new FormData();
  form.append("file", file);
  return client.post(`/admin/codes/import?ticket_value=${ticketValue}`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  }).then(r => r.data);
}

/** 用户列表 */
export interface UserItem {
  id: string;
  email: string;
  tickets: number;
  is_verified: boolean;
  created_at: string;
}
export function getUsers(params: { page?: number; page_size?: number; search?: string }): Promise<{ total: number; items: UserItem[] }> {
  return client.get("/admin/users", { params }).then(r => r.data);
}
