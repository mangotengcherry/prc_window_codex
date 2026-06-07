<template>
  <section class="panel window-panel">
    <div class="panel-heading">
      <p>Window</p>
      <h2>{{ title }}</h2>
    </div>
    <p v-if="!analysis" class="empty">선택된 L1과 L3의 구간별 불량률이 표시됩니다.</p>
    <div v-show="analysis" ref="chartEl" class="chart" aria-label="Process window chart"></div>
  </section>
</template>

<script setup lang="ts">
import * as echarts from "echarts";
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue";
import type { SingleAnalysis } from "../types";

const props = defineProps<{ analysis: SingleAnalysis | null }>();
const chartEl = ref<HTMLDivElement | null>(null);
let chart: echarts.ECharts | null = null;

const title = computed(() => {
  if (!props.analysis) return "L1 vs L3";
  return `${props.analysis.l1_feature_name ?? "L1"} vs ${props.analysis.l3_item_name ?? "L3"}`;
});

function renderChart() {
  if (!props.analysis || !chartEl.value) return;
  if (!chart) chart = echarts.init(chartEl.value);

  const bins = props.analysis.bins;
  const labels = bins.map((row) => `${Number(row.l1_min).toFixed(1)}-${Number(row.l1_max).toFixed(1)}`);
  const ppm = bins.map((row) => Number(row.defect_ppm));
  const ciLow = bins.map((row) => Number(row.ci_low_ppm));
  const ciHigh = bins.map((row) => Number(row.ci_high_ppm));
  const volume = bins.map((row) => Number(row.volume_share) * 100);

  chart.setOption({
    color: ["#0071e3", "#34c759", "#a2845e"],
    tooltip: {
      trigger: "axis",
      valueFormatter: (value: number) => Number(value).toLocaleString(),
    },
    legend: { top: 2, right: 8, data: ["Defect ppm", "CI band", "Volume %"] },
    grid: { left: 58, right: 58, top: 48, bottom: 64 },
    xAxis: {
      type: "category",
      data: labels,
      axisLabel: { rotate: 28, fontSize: 10 },
      axisLine: { lineStyle: { color: "#d2d2d7" } },
    },
    yAxis: [
      { type: "value", name: "ppm", splitLine: { lineStyle: { color: "#eeeeef" } } },
      { type: "value", name: "volume", min: 0, max: 100, axisLabel: { formatter: "{value}%" } },
    ],
    series: [
      {
        name: "CI low",
        type: "line",
        data: ciLow,
        lineStyle: { opacity: 0 },
        symbol: "none",
        stack: "ci",
      },
      {
        name: "CI band",
        type: "line",
        data: ciHigh.map((value, index) => Math.max(value - ciLow[index], 0)),
        areaStyle: { color: "rgba(0, 113, 227, 0.14)" },
        lineStyle: { opacity: 0 },
        symbol: "none",
        stack: "ci",
      },
      {
        name: "Defect ppm",
        type: "line",
        data: ppm,
        smooth: true,
        symbolSize: 7,
        lineStyle: { width: 3, color: "#0071e3" },
        itemStyle: { color: "#0071e3" },
      },
      {
        name: "Volume %",
        type: "bar",
        yAxisIndex: 1,
        data: volume,
        itemStyle: { color: "rgba(52, 199, 89, 0.24)", borderRadius: [4, 4, 0, 0] },
      },
    ],
  }, true);
}

watch(
  () => props.analysis,
  async () => {
    await nextTick();
    renderChart();
  },
  { immediate: true },
);

window.addEventListener("resize", () => chart?.resize());

onBeforeUnmount(() => {
  chart?.dispose();
  chart = null;
});
</script>

<style scoped>
.window-panel {
  min-height: 360px;
}

.panel-heading p {
  margin: 0 0 6px;
  color: #86868b;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
}

h2 {
  margin: 0;
  font-size: 24px;
}

.empty {
  min-height: 230px;
  display: grid;
  place-items: center;
  color: #86868b;
}

.chart {
  height: 292px;
  width: 100%;
}
</style>
