<template>
  <section class="wire-panel interaction-panel">
    <h2>교호작용 분석<br /><span>(Multi L1 vs L3)</span></h2>
    <p v-if="!analysis">L1 두 개를 선택하면 heatmap이 표시됩니다.</p>
    <div v-show="analysis" ref="chartEl" class="heatmap" aria-label="Interaction heatmap chart"></div>
  </section>
</template>

<script setup lang="ts">
import * as echarts from "echarts";
import { nextTick, onBeforeUnmount, ref, watch } from "vue";
import type { InteractionAnalysis } from "../types";

const props = defineProps<{ analysis: InteractionAnalysis | null }>();
const chartEl = ref<HTMLDivElement | null>(null);
let chart: echarts.ECharts | null = null;

function renderChart() {
  if (!props.analysis || !chartEl.value) return;
  if (!chart) chart = echarts.init(chartEl.value);

  const cells = props.analysis.cells;
  const maxX = Math.max(...cells.map((cell) => cell.x_bin), 0);
  const maxY = Math.max(...cells.map((cell) => cell.y_bin), 0);
  const maxPpm = Math.max(...cells.map((cell) => cell.defect_ppm), 1);

  chart.setOption({
    tooltip: {
      formatter: (params: { data: [number, number, number, number, boolean] }) => {
        const [x, y, ppm, wafers, unreliable] = params.data;
        return [
          `${props.analysis?.l1_feature_x} bin ${x}`,
          `${props.analysis?.l1_feature_y} bin ${y}`,
          `Defect: ${ppm.toFixed(0)} ppm`,
          `Wafers: ${wafers}`,
          unreliable ? "Low sample" : "Reliable",
        ].join("<br/>");
      },
    },
    grid: { left: 44, right: 24, top: 22, bottom: 40 },
    xAxis: {
      type: "category",
      name: props.analysis.l1_feature_x,
      data: Array.from({ length: maxX + 1 }, (_, index) => String(index)),
    },
    yAxis: {
      type: "category",
      name: props.analysis.l1_feature_y,
      data: Array.from({ length: maxY + 1 }, (_, index) => String(index)),
    },
    visualMap: {
      min: 0,
      max: maxPpm,
      calculable: true,
      orient: "horizontal",
      left: "center",
      bottom: 0,
      inRange: { color: ["#edf4ff", "#79a7ff", "#f07a4a"] },
    },
    series: [
      {
        type: "heatmap",
        data: cells.map((cell) => [
          cell.x_bin,
          cell.y_bin,
          cell.defect_ppm,
          cell.wafer_count,
          cell.unreliable,
        ]),
        itemStyle: {
          borderColor: "#ffffff",
          borderWidth: 2,
        },
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
.interaction-panel {
  min-height: 210px;
  padding: 14px;
}
h2 {
  margin: 0 0 8px;
  text-align: center;
  font-size: 24px;
  line-height: 1.25;
}
h2 span {
  font-weight: 500;
}
p {
  color: #5b6578;
  text-align: center;
}
.heatmap {
  height: 190px;
  width: 100%;
}
</style>
