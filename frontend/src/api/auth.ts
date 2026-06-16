import client from "./client";

export interface RegisterParams {
  email: string;
  password: string;
}

export interface VerifyParams {
  email: string;
  code: string;
}

export interface LoginParams {
  email: string;
  password: string;
}

export interface LoginResult {
  access_token: string;
  token_type: string;
}

export interface UserInfo {
  id: string;
  email: string;
  is_verified: boolean;
  created_at: string;
}

/** 注册 — 发送验证码 */
export async function register(params: RegisterParams) {
  const { data } = await client.post("/auth/register", params);
  return data;
}

/** 验证邮箱 */
export async function verifyEmail(params: VerifyParams) {
  const { data } = await client.post("/auth/verify-email", params);
  return data;
}

/** 登录 */
export async function login(params: LoginParams): Promise<LoginResult> {
  const { data } = await client.post("/auth/login", params);
  return data;
}

/** 获取当前用户信息 */
export async function getMe(): Promise<UserInfo> {
  const { data } = await client.get("/auth/me");
  return data;
}
