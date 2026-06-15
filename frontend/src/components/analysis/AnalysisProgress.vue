<script setup lang="ts">
import { computed } from "vue";
import { Download, Brain, FileCheck, CheckCircle2, Loader2 } from "lucide-vue-next";

const props = defineProps<{
  status: {
    status: string;
    progress: number;
    stock_code: string;
    stock_name?: string | null;
  };
}>();

const steps = [
  { key: "pending", icon: Download, label: "提交任务" },
  { key: "running", icon: Brain, label: "AI 分析中" },
  { key: "completed", icon: FileCheck, label: "生成报告" },
];

const currentStep = computed(() => {
  if (props.status.status === "completed") return 3;
  if (props.status.status === "running") return 2;
  return 1;
});

const percent = computed(() => Math.round(props.status.progress * 100));
</script>

<template>
  <div class="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-8 mb-8 animate-slide-up">
    <!-- 股票信息 -->
    <div class="flex items-center gap-3 mb-6">
      <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-[#D4A843]/20 to-[#F0C060]/20 flex items-center justify-center">
        <Brain :size="20" class="text-[#F0C060]" />
      </div>
      <div>
        <p class="text-sm font-semibold text-[#E8EDF5]">
          {{ status.stock_name || status.stock_code }}
        </p>
        <p class="text-xs text-[#5C6E8A]">{{ status.stock_code }}</p>
      </div>
      <div class="ml-auto text-2xl font-bold text-[#D4A843]">{{ percent }}%</div>
    </div>

    <!-- 进度条 -->
    <div class="w-full h-2 bg-white/5 rounded-full overflow-hidden mb-8">
      <div
        class="h-full bg-gradient-to-r from-[#D4A843] to-[#F0C060] rounded-full transition-all duration-700 ease-out"
        :style="{ width: percent + '%' }"
      />
    </div>

    <!-- 步骤指示器 -->
    <div class="flex justify-between">
      <div
        v-for="(step, idx) in steps"
        :key="step.key"
        class="flex flex-col items-center gap-2 flex-1"
      >
        <div
          :class="[
            'w-10 h-10 rounded-full flex items-center justify-center transition-all',
            idx < currentStep
              ? 'bg-gradient-to-br from-green-500 to-green-600'
              : idx === currentStep
                ? 'bg-gradient-to-br from-[#D4A843] to-[#F0C060] animate-pulse-slow'
                : 'bg-white/10',
          ]"
        >
          <CheckCircle2 v-if="idx < currentStep" :size="18" class="text-white" />
          <component v-else-if="idx === currentStep - 1" :is="step.icon" :size="18" class="text-[#0A1929]" />
          <component v-else :is="step.icon" :size="18" class="text-[#5C6E8A]" />
        </div>
        <p
          :class="[
            'text-xs font-medium',
            idx <= currentStep ? 'text-[#E8EDF5]' : 'text-[#5C6E8A]',
          ]"
        >
          {{ step.label }}
        </p>
      </div>
    </div>
  </div>
</template>
