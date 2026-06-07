<template>
  <main class="app-shell">
    <aside class="side-nav">
      <button class="outline-control">제품 선택</button>
      <button class="outline-control">L1 선택</button>
      <button class="outline-control">L3 선택</button>
      <button class="outline-control">Filter 조건 입력</button>
      <button class="outline-control primary-action" @click="loadAll">분석 실행 버튼</button>
      <p v-if="loading" class="status-text">분석 중...</p>
      <p v-if="error" class="status-text error">{{ error }}</p>
    </aside>

    <section class="result-panel wire-panel">
      <RankingPanel
        v-if="rankingRows.length"
        :rows="rankingRows"
        @select="selectRanking"
      />
      <div v-else class="empty-result">
        <strong>분석 결과 테이블</strong>
        <span>좌측 분석 실행 버튼을 눌러 L3별 Top Feature를 확인하세요.</span>
      </div>
      <CandidateTable :analysis="analysis" />
    </section>

    <section class="analysis-panel">
      <WindowChart :analysis="analysis" />

      <div class="business-inputs">
        <label>
          <span>월 생산량 입력</span>
          <input v-model.number="monthlyVolume" type="number" min="0" />
        </label>
        <label>
          <span>Chip 단가 입력</span>
          <input v-model.number="chipPrice" type="number" min="0" />
        </label>
      </div>

      <TradeoffChart :analysis="analysis" />

      <div class="l1-pair-controls">
        <label>
          <span>L1 선택 1</span>
          <select v-model="interactionL1A" @change="loadInteraction">
            <option v-for="feature in l1Features" :key="feature" :value="feature">{{ feature }}</option>
          </select>
        </label>
        <label>
          <span>L1 선택 2</span>
          <select v-model="interactionL1B" @change="loadInteraction">
            <option v-for="feature in l1Features" :key="feature" :value="feature">{{ feature }}</option>
          </select>
        </label>
      </div>

      <InteractionHeatmap :analysis="interaction" />
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { fetchInteractionAnalysis, fetchRanking, fetchSingleAnalysis } from "./api";
import CandidateTable from "./components/CandidateTable.vue";
import InteractionHeatmap from "./components/InteractionHeatmap.vue";
import RankingPanel from "./components/RankingPanel.vue";
import TradeoffChart from "./components/TradeoffChart.vue";
import WindowChart from "./components/WindowChart.vue";
import type { InteractionAnalysis, RankingRow, SingleAnalysis } from "./types";

const loading = ref(false);
const error = ref("");
const ranking = ref<Record<string, RankingRow[]>>({});
const analysis = ref<SingleAnalysis | null>(null);
const interaction = ref<InteractionAnalysis | null>(null);
const selectedRow = ref<RankingRow | null>(null);
const monthlyVolume = ref(100000);
const chipPrice = ref(1.2);
const l1Features = ["cd_a", "thk_b", "ovl_c", "time_since_pm"];
const interactionL1A = ref("cd_a");
const interactionL1B = ref("ovl_c");

const rankingRows = computed(() => Object.values(ranking.value).flat());

async function loadAll() {
  loading.value = true;
  error.value = "";
  try {
    const rankPayload = await fetchRanking({
      product_id: "P_ALPHA",
      selected_l3_items: ["l3_x", "l3_y", "l3_z", "l3_pm"],
      selected_l1_features: l1Features,
    }) as { by_l3: Record<string, RankingRow[]> };
    ranking.value = rankPayload.by_l3;
    const first = Object.values(ranking.value)[0]?.[0];
    if (first) await selectRanking(first);
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Failed to load analysis";
  } finally {
    loading.value = false;
  }
}

async function selectRanking(row: RankingRow) {
  selectedRow.value = row;
  analysis.value = await fetchSingleAnalysis({
    product_id: "P_ALPHA",
    l1_feature_name: row.l1_feature_name,
    l3_item_name: row.l3_item_name,
    max_allowed_loss_rate: 0.45,
  });
  await loadInteraction();
}

async function loadInteraction() {
  if (!selectedRow.value) return;
  if (interactionL1A.value === interactionL1B.value) {
    interaction.value = null;
    return;
  }
  interaction.value = await fetchInteractionAnalysis({
    product_id: "P_ALPHA",
    l1_feature_x: interactionL1A.value,
    l1_feature_y: interactionL1B.value,
    l3_item_name: selectedRow.value.l3_item_name,
  });
}
</script>

<style>
body {
  margin: 0;
  font-family: Inter, system-ui, sans-serif;
  background: #ffffff;
  color: #101828;
}
button,
input,
select {
  font: inherit;
}
.app-shell {
  min-height: 100vh;
  width: 1180px;
  display: grid;
  grid-template-columns: 190px 300px minmax(430px, 1fr);
  gap: 24px;
  padding: 31px 18px 28px;
  box-sizing: border-box;
}
.wire-panel {
  border: 1px solid #2f64ff;
  background: #fff;
}
.side-nav {
  border-right: 1px solid #2f64ff;
  padding-right: 18px;
  min-height: calc(100vh - 62px);
}
.outline-control {
  width: 170px;
  height: 43px;
  display: block;
  margin: 0 0 28px;
  border: 1px solid #2f64ff;
  background: #fff;
  color: #101828;
  border-radius: 0;
  font-size: 20px;
  font-weight: 500;
  line-height: 1;
}
.primary-action {
  cursor: pointer;
}
.primary-action:hover {
  background: #eef4ff;
}
.status-text {
  width: 170px;
  color: #475467;
  font-size: 14px;
}
.status-text.error {
  color: #b42318;
}
.result-panel {
  min-height: calc(100vh - 62px);
  padding: 22px 18px;
  box-sizing: border-box;
  display: grid;
  grid-template-rows: minmax(360px, 1fr) auto;
  align-content: stretch;
  gap: 18px;
}
.empty-result {
  height: 100%;
  display: grid;
  place-items: center;
  text-align: center;
}
.empty-result strong {
  display: block;
  font-size: 38px;
  font-weight: 500;
}
.empty-result span {
  display: block;
  margin-top: 12px;
  color: #667085;
}
.analysis-panel {
  min-width: 0;
  display: grid;
  grid-template-rows: auto auto auto auto auto;
  gap: 18px;
}
.business-inputs,
.l1-pair-controls {
  display: flex;
  gap: 18px;
  align-items: center;
}
.business-inputs label,
.l1-pair-controls label {
  width: 210px;
  height: 42px;
  display: grid;
  grid-template-columns: 1fr;
  border: 1px solid #2f64ff;
  background: #fff;
  position: relative;
}
.business-inputs span,
.l1-pair-controls span {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  pointer-events: none;
  font-size: 20px;
}
.business-inputs input,
.l1-pair-controls select {
  width: 100%;
  height: 100%;
  border: 0;
  background: transparent;
  color: transparent;
  text-align: center;
}
.business-inputs label:focus-within span,
.business-inputs label:hover span,
.l1-pair-controls label:focus-within span,
.l1-pair-controls label:hover span {
  display: none;
}
.business-inputs input:focus,
.l1-pair-controls select:focus {
  color: #101828;
  outline: none;
}
</style>
