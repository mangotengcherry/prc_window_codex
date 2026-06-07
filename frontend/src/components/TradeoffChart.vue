<template>
  <section class="panel tradeoff-panel">
    <div class="panel-heading">
      <p>Trade-off</p>
      <h2>월 순효과 기준 SPEC 후보</h2>
    </div>

    <p v-if="!analysis" class="empty">월 생산량과 단가를 기준으로 후보별 손익이 표시됩니다.</p>
    <template v-else>
      <div class="effect-strip">
        <div>
          <span>경제적 최적 Target</span>
          <strong>{{ bestPoint ? bestPoint.target.toFixed(2) : "-" }}</strong>
        </div>
        <div>
          <span>월 순효과</span>
          <strong :class="{ negative: bestPoint && bestPoint.net < 0 }">{{ bestPoint ? wonShort(bestPoint.net) : "-" }}</strong>
        </div>
        <div>
          <span>생산 통과율</span>
          <strong>{{ bestPoint ? `${bestPoint.passRate.toFixed(1)}%` : "-" }}</strong>
        </div>
      </div>
      <div ref="chartEl" class="chart" aria-label="Business trade-off chart"></div>
    </template>
  </section>
</template>

<script setup lang="ts">
import * as echarts from "echarts";
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue";
import type { SingleAnalysis } from "../types";

type BusinessPoint = {
  target: number;
  passRate: number;
  productionLoss: number;
  residualPpm: number;
  defectSaving: number;
  lostSales: number;
  net: number;
};

const props = defineProps<{
  analysis: SingleAnalysis | null;
  monthlyVolume: number;
  chipPrice: number;
}>();

const chartEl = ref<HTMLDivElement | null>(null);
let chart: echarts.ECharts | null = null;

const points = computed<BusinessPoint[]>(() => {
  if (!props.analysis) return [];
  const baselinePpm = props.analysis.baseline_ppm;
  return props.analysis.candidate_specs.map((row) => {
    const productionLoss = Number(row.production_loss);
    const residualPpm = Number(row.residual_ppm);
    const passRate = 1 - productionLoss;
    const baselineBadValue = (props.monthlyVolume * baselinePpm * props.chipPrice) / 1_000_000;
    const residualBadValue = (props.monthlyVolume * passRate * residualPpm * props.chipPrice) / 1_000_000;
    const defectSaving = baselineBadValue - residualBadValue;
    const lostSales = props.monthlyVolume * productionLoss * props.chipPrice;
    return {
      target: Number(row.target),
      passRate: passRate * 100,
      productionLoss: productionLoss * 100,
      residualPpm,
      defectSaving,
      lostSales,
      net: defectSaving - lostSales,
    };
  });
});

const bestPoint = computed(() => {
  if (!points.value.length) return null;
  return points.value.reduce((best, point) => point.net > best.net ? point : best, points.value[0]);
});

function wonShort(value: number) {
  const abs = Math.abs(value);
  const sign = value < 0 ? "-" : "";
  if (abs >= 100_000_000) return `${sign}${(abs / 100_000_000).toFixed(1)}억`;
  if (abs >= 10_000) return `${sign}${(abs / 10_000).toFixed(0)}만`;
  return `${sign}${Math.round(abs).toLocaleString()}`;
}

function won(value: number) {
  return `${Math.round(value).toLocaleString()}원`;
}

function renderChart() {
  if (!props.analysis || !chartEl.value) return;
  if (!chart) chart = echarts.init(chartEl.value);

  const data = points.value.map((point) => [
    point.passRate,
    point.net,
    point.target,
    point.defectSaving,
    point.lostSales,
    point.residualPpm,
  ]);
  const best = bestPoint.value
    ? [[bestPoint.value.passRate, bestPoint.value.net, bestPoint.value.target]]
    : [];

  chart.setOption({
    color: ["#0071e3", "#ff9f0a"],
    tooltip: {
      trigger: "item",
      formatter: (params: { data: number[] }) => {
        const [passRate, net, target, saving, lostSales, residualPpm] = params.data;
        return [
          `Target ${target.toFixed(2)}`,
          `생산 통과율 ${passRate.toFixed(1)}%`,
          `월 순효과 <b>${won(net)}</b>`,
          `불량 절감 ${won(saving)}`,
          `생산 손실 -${won(lostSales)}`,
          `잔여 ${residualPpm.toFixed(0)} ppm`,
        ].join("<br/>");
      },
    },
    grid: { left: 82, right: 30, top: 34, bottom: 58 },
    xAxis: {
      type: "value",
      name: "생산 통과율",
      min: 50,
      max: 100,
      axisLabel: { formatter: "{value}%" },
      splitLine: { lineStyle: { color: "#eeeeef" } },
    },
    yAxis: {
      type: "value",
      name: "월 순효과",
      axisLabel: { formatter: (value: number) => wonShort(value) },
      splitLine: { lineStyle: { color: "#eeeeef" } },
    },
    series: [
      {
        name: "SPEC 후보",
        type: "scatter",
        symbolSize: (value: number[]) => Math.max(10, Math.min(24, 9 + Math.abs(value[1]) / 30_000_000)),
        data,
        itemStyle: { color: "#0071e3", opacity: 0.82 },
        markLine: {
          silent: true,
          symbol: "none",
          data: [{ yAxis: 0 }],
          lineStyle: { color: "#86868b", type: "dashed" },
        },
      },
      {
        name: "경제적 최적",
        type: "scatter",
        symbol: "diamond",
        symbolSize: 22,
        data: best,
        itemStyle: { color: "#ff9f0a" },
      },
    ],
  }, true);
}

watch(
  () => [props.analysis, props.monthlyVolume, props.chipPrice],
  async () => {
    await nextTick();
    renderChart();
  },
  { immediate: true, deep: true },
);

window.addEventListener("resize", () => chart?.resize());

onBeforeUnmount(() => {
  chart?.dispose();
  chart = null;
});
</script>

<style scoped>
.tradeoff-panel {
  min-height: 376px;
}

.panel-heading p {
  margin: 0 0 6px;
  color: #86868b;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
}

h2 {
  margin: 0 0 14px;
  font-size: 24px;
}

.effect-strip {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 12px;
}

.effect-strip div {
  border-radius: 8px;
  background: #f5f5f7;
  padding: 10px 12px;
}

.effect-strip span {
  display: block;
  color: #86868b;
  font-size: 12px;
}

.effect-strip strong {
  display: block;
  margin-top: 4px;
  font-size: 19px;
}

.effect-strip strong.negative {
  color: #b42318;
}

.empty {
  min-height: 230px;
  display: grid;
  place-items: center;
  color: #86868b;
}

.chart {
  height: 270px;
  width: 100%;
}
</style>
