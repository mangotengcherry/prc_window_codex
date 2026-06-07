<template>
  <section class="wire-panel window-panel">
    <h2>Window 분석<br /><span>(L1 vs L3)</span></h2>
    <p v-if="!analysis">Ranking row를 선택하면 L1 구간별 불량률이 표시됩니다.</p>
    <div v-show="analysis" ref="chartEl" class="chart" aria-label="Process window chart"></div>
  </section>
</template>

<script setup lang="ts">
import * as echarts from "echarts";
import { nextTick, onBeforeUnmount, ref, watch } from "vue";
import type { SingleAnalysis } from "../types";

const props = defineProps<{ analysis: SingleAnalysis | null }>();
const chartEl = ref<HTMLDivElement | null>(null);
let chart: echarts.ECharts | null = null;

function renderChart() {
  if (!props.analysis || !chartEl.value) return;
  if (!chart) chart = echarts.init(chartEl.value);

  const bins = props.analysis.bins;
  const labels = bins.map((row) => String(row.bin_label));
  const ppm = bins.map((row) => Number(row.defect_ppm));
  const ciLow = bins.map((row) => Number(row.ci_low_ppm));
  const ciHigh = bins.map((row) => Number(row.ci_high_ppm));
  const volume = bins.map((row) => Number(row.volume_share) * 100);

  chart.setOption({
    tooltip: { trigger: "axis" },
    legend: { top: 0 },
    grid: { left: 58, right: 54, top: 44, bottom: 92 },
    xAxis: {
      type: "category",
      data: labels,
      axisLabel: { rotate: 35, fontSize: 10 },
    },
    yAxis: [
      { type: "value", name: "Defect ppm" },
      { type: "value", name: "Volume %", min: 0, max: 100 },
    ],
    series: [
      {
        name: "CI low",
        type: "line",
        data: ciLow,
        lineStyle: { opacity: 0 },
        symbol: "none",
        stack: "ci",
        tooltip: { valueFormatter: (value: number) => `${value.toFixed(0)} ppm` },
      },
      {
        name: "CI range",
        type: "line",
        data: ciHigh.map((value, index) => Math.max(value - ciLow[index], 0)),
        areaStyle: { color: "rgba(31, 94, 255, 0.14)" },
        lineStyle: { opacity: 0 },
        symbol: "none",
        stack: "ci",
        tooltip: { valueFormatter: (value: number) => `${value.toFixed(0)} ppm` },
      },
      {
        name: "Defect ppm",
        type: "line",
        data: ppm,
        smooth: true,
        symbolSize: 7,
        lineStyle: { width: 3, color: "#1f5eff" },
        itemStyle: { color: "#1f5eff" },
      },
      {
        name: "Volume %",
        type: "bar",
        yAxisIndex: 1,
        data: volume,
        itemStyle: { color: "rgba(80, 150, 120, 0.34)" },
      },
    ],
  });
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
.wire-panel {
  border: 1px solid #2f64ff;
  background: #fff;
}
.window-panel {
  min-height: 316px;
  padding: 12px;
  box-sizing: border-box;
}
h2 {
  margin: 0;
  text-align: center;
  font-size: 34px;
  font-weight: 500;
  line-height: 1.25;
}
h2 span {
  font-weight: 500;
}
p {
  color: #5b6578;
  text-align: center;
}
.chart {
  height: 240px;
  width: 100%;
}
</style>
