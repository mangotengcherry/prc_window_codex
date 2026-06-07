<template>
  <section class="panel interaction-panel">
    <div class="panel-heading">
      <p>Heatmap</p>
      <h2>{{ title }}</h2>
    </div>

    <p v-if="!analysis" class="empty">서로 다른 L1 두 개를 선택하면 교호작용 heatmap이 표시됩니다.</p>
    <template v-else>
      <div class="heatmap-summary">
        <div>
          <span>Hotspot</span>
          <strong>{{ hotspot ? `${hotspot.defect_ppm.toFixed(0)} ppm` : "-" }}</strong>
        </div>
        <div>
          <span>Hotspot wafer</span>
          <strong>{{ hotspot?.wafer_count ?? "-" }}</strong>
        </div>
        <div>
          <span>Low sample cells</span>
          <strong>{{ unreliableCount }}</strong>
        </div>
      </div>
      <div ref="chartEl" class="heatmap" aria-label="Interaction heatmap chart"></div>
    </template>
  </section>
</template>

<script setup lang="ts">
import * as echarts from "echarts";
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue";
import type { InteractionAnalysis } from "../types";

const props = defineProps<{ analysis: InteractionAnalysis | null }>();
const chartEl = ref<HTMLDivElement | null>(null);
let chart: echarts.ECharts | null = null;

const title = computed(() => {
  if (!props.analysis) return "Multi L1 vs L3";
  return `${props.analysis.l1_feature_x} x ${props.analysis.l1_feature_y} -> ${props.analysis.l3_item_name}`;
});

const hotspot = computed(() => {
  const cells = props.analysis?.cells.filter((cell) => cell.wafer_count > 0) ?? [];
  if (!cells.length) return null;
  return cells.reduce((max, cell) => cell.defect_ppm > max.defect_ppm ? cell : max, cells[0]);
});

const unreliableCount = computed(() => props.analysis?.cells.filter((cell) => cell.unreliable).length ?? 0);

function renderChart() {
  if (!props.analysis || !chartEl.value) return;
  if (!chart) chart = echarts.init(chartEl.value);

  const cells = props.analysis.cells;
  const maxPpm = Math.max(...cells.map((cell) => cell.defect_ppm), 1);
  const xLabels = Array.from(
    new Map(cells.map((cell) => [cell.x_bin, cell.x_center.toFixed(1)])).values(),
  );
  const yLabels = Array.from(
    new Map(cells.map((cell) => [cell.y_bin, cell.y_center.toFixed(1)])).values(),
  );

  chart.setOption({
    tooltip: {
      position: "top",
      formatter: (params: { data: [number, number, number, number, boolean, number, number, number, number] }) => {
        const [x, y, ppm, wafers, unreliable, xMin, xMax, yMin, yMax] = params.data;
        return [
          `${props.analysis?.l1_feature_x} ${xMin.toFixed(2)} - ${xMax.toFixed(2)} (bin ${x})`,
          `${props.analysis?.l1_feature_y} ${yMin.toFixed(2)} - ${yMax.toFixed(2)} (bin ${y})`,
          `Defect ${ppm.toFixed(0)} ppm`,
          `Wafer ${wafers}`,
          unreliable ? "Low sample" : "Sample ok",
        ].join("<br/>");
      },
    },
    grid: { left: 58, right: 26, top: 18, bottom: 70 },
    xAxis: {
      type: "category",
      name: props.analysis.l1_feature_x,
      data: xLabels,
      splitArea: { show: true },
      axisLine: { lineStyle: { color: "#d2d2d7" } },
    },
    yAxis: {
      type: "category",
      name: props.analysis.l1_feature_y,
      data: yLabels,
      splitArea: { show: true },
      axisLine: { lineStyle: { color: "#d2d2d7" } },
    },
    visualMap: {
      min: 0,
      max: maxPpm,
      calculable: true,
      orient: "horizontal",
      left: "center",
      bottom: 10,
      inRange: { color: ["#f5fbff", "#7dc8ff", "#ff9f0a", "#bf2600"] },
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
          cell.x_min,
          cell.x_max,
          cell.y_min,
          cell.y_max,
        ]),
        label: {
          show: true,
          color: "#1d1d1f",
          fontSize: 10,
          formatter: (params: { data: [number, number, number] }) => params.data[2] > 0 ? params.data[2].toFixed(0) : "",
        },
        itemStyle: {
          borderColor: "#ffffff",
          borderWidth: 2,
          borderRadius: 4,
        },
        emphasis: {
          itemStyle: {
            borderColor: "#1d1d1f",
            borderWidth: 2,
          },
        },
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
.interaction-panel {
  min-height: 420px;
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

.heatmap-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 12px;
}

.heatmap-summary div {
  border-radius: 8px;
  background: #f5f5f7;
  padding: 10px 12px;
}

.heatmap-summary span {
  display: block;
  color: #86868b;
  font-size: 12px;
}

.heatmap-summary strong {
  display: block;
  margin-top: 4px;
  font-size: 19px;
}

.empty {
  min-height: 260px;
  display: grid;
  place-items: center;
  color: #86868b;
}

.heatmap {
  height: 310px;
  width: 100%;
}
</style>
