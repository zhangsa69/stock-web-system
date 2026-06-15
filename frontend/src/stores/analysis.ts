import { defineStore } from "pinia";
import { ref } from "vue";
import { analysisApi, type AnalysisStatus } from "../api/analysis";

export const useAnalysisStore = defineStore("analysis", () => {
  const currentTaskId = ref<string | null>(null);
  const currentStatus = ref<AnalysisStatus | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  async function startAnalysis(stockCode: string) {
    isLoading.value = true;
    error.value = null;
    const result = await analysisApi.start(stockCode);
    currentTaskId.value = result.task_id;

    // 如果已缓存，直接获取结果
    if (result.status === "completed") {
      await fetchStatus(result.task_id);
      isLoading.value = false;
      return;
    }

    // 开始轮询
    await pollStatus(result.task_id);
  }

  async function fetchStatus(taskId: string) {
    const status = await analysisApi.getStatus(taskId);
    currentStatus.value = status;
    return status;
  }

  async function pollStatus(taskId: string, maxAttempts = 120) {
    for (let i = 0; i < maxAttempts; i++) {
      await new Promise((r) => setTimeout(r, 2000));
      const status = await fetchStatus(taskId);
      if (status.status === "completed" || status.status === "failed") {
        isLoading.value = false;
        if (status.status === "failed") {
          error.value = status.error || "分析失败";
        }
        return status;
      }
    }
    isLoading.value = false;
    error.value = "分析超时";
    return null;
  }

  function reset() {
    currentTaskId.value = null;
    currentStatus.value = null;
    isLoading.value = false;
    error.value = null;
  }

  return {
    currentTaskId,
    currentStatus,
    isLoading,
    error,
    startAnalysis,
    fetchStatus,
    reset,
  };
});
