import client from "./client";

export interface AnalysisResponse {
  task_id: string;
  status: string;
  estimated_seconds: number;
}

export interface AnalysisStatus {
  task_id: string;
  stock_code: string;
  stock_name: string | null;
  status: string;
  progress: number;
  report: string | null;
  html_report: string | null;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface HistoryItem {
  task_id: string;
  stock_code: string;
  stock_name: string | null;
  status: string;
  created_at: string;
}

export interface HistoryResponse {
  total: number;
  page: number;
  page_size: number;
  items: HistoryItem[];
}

export const analysisApi = {
  start(stockCode: string, email: string, skillName = "cninfo-financial-analysis"): Promise<AnalysisResponse> {
    return client.post("/analysis/start", { stock_code: stockCode, email, skill_name: skillName }).then((r) => r.data);
  },

  getStatus(taskId: string): Promise<AnalysisStatus> {
    return client.get(`/analysis/${taskId}/status`).then((r) => r.data);
  },

  getHistory(page = 1, pageSize = 20): Promise<HistoryResponse> {
    return client.get("/analysis/history", { params: { page, page_size: pageSize } }).then((r) => r.data);
  },
};
