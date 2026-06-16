import client from "./client";

export interface RedeemResult {
  success: boolean;
  message: string;
  tickets_added: number;
  balance: number;
}

export interface BalanceResult {
  tickets: number;
  email: string;
}

/** 核销充值卡密 */
export async function redeemCode(code: string): Promise<RedeemResult> {
  const { data } = await client.post("/recharge/redeem", { code });
  return data;
}

/** 查询点券余额 */
export async function getBalance(): Promise<BalanceResult> {
  const { data } = await client.get("/recharge/balance");
  return data;
}
