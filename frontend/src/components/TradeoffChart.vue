<template>
  <section class="wire-panel tradeoff-panel">
    <h2>L1 구간 별 Trade Off 분석<br /><span>(생산비율 vs 월 판매비용)</span></h2>
    <p v-if="!analysis">추천 후보의 생산손실과 잔여 ppm이 표시됩니다.</p>
    <div v-show="analysis" ref="chartEl" class="chart" aria-label="SPEC trade-off chart"></div>
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

  const rows = props.analysis.candidate_specs.map((row) => ({
    productionLoss: Number(row.production_loss) * 100,
    residualPpm: Number(row.residual_ppm),
    target: Number(row.target),
    improvement: Number(row.ppm_improvement),
  }));

  chart.setOption({
    tooltip: {
      trigger: "item",
      formatter: (params: { data: [number, number, number, number] }) => {
        const [loss, ppm, target, improvement] = params.data;
        return [
          `Production loss: ${loss.toFixed(1)}%`,
          `Residual: ${ppm.toFixed(0)} ppm`,
          `Target: ${target.toFixed(2)}`,
          `Improvement: ${improvement.toFixed(0)} ppm`,
        ].join("<br/>");
      },
    },
    grid: { left: 62, right: 24, top: 28, bottom: 52 },
    xAxis: {
      type: "value",
      name: "Production loss %",
      min: 0,
    },
    yAxis: {
      type: "value",
      name: "Residual ppm",
    },
    series: [
      {
        name: "Candidates",
        type: "scatter",
        symbolSize: 12,
        data: rows.map((row) => [row.productionLoss, row.residualPpm, row.target, row.improvement]),
        itemStyle: { color: "#db6b39" },
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
.tradeoff-panel {
  min-height: 182px;
  padding: 12px;
  box-sizing: border-box;
}
h2 {
  margin: 0;
  text-align: center;
  font-size: 30px;
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
  height: 128px;
  width: 100%;
}
</style>
