<template>
  <main class="app-shell">
    <header class="hero">
      <div>
        <p class="eyebrow">Process Window Studio</p>
        <h1>공정 Window를 경영효과까지 연결해 보는 분석 화면</h1>
      </div>
      <div class="hero-metrics">
        <div>
          <span>선택 L3</span>
          <strong>{{ selectedRow?.l3_item_name ?? "-" }}</strong>
        </div>
        <div>
          <span>Baseline</span>
          <strong>{{ analysis ? `${analysis.baseline_ppm.toFixed(0)} ppm` : "-" }}</strong>
        </div>
        <div>
          <span>월 순효과</span>
          <strong>{{ bestBusinessEffect }}</strong>
        </div>
      </div>
    </header>

    <section class="dashboard-grid">
      <aside class="control-panel panel">
        <div class="panel-heading">
          <p>Input</p>
          <h2>분석 조건</h2>
        </div>

        <label class="field">
          <span>제품</span>
          <select v-model="selectedProduct">
            <option v-for="product in products" :key="product" :value="product">{{ product }}</option>
          </select>
        </label>

        <div class="field">
          <span>L1 Feature</span>
          <div class="chip-group">
            <button
              v-for="feature in l1Features"
              :key="feature"
              type="button"
              class="chip"
              :class="{ active: selectedL1.includes(feature) }"
              @click="toggle(selectedL1, feature)"
            >
              {{ feature }}
            </button>
          </div>
        </div>

        <div class="field">
          <span>L3 Item</span>
          <div class="chip-group">
            <button
              v-for="item in l3Items"
              :key="item"
              type="button"
              class="chip"
              :class="{ active: selectedL3.includes(item) }"
              @click="toggle(selectedL3, item)"
            >
              {{ item }}
            </button>
          </div>
        </div>

        <div class="input-grid">
          <label class="field compact">
            <span>최소 wafer</span>
            <input v-model.number="minWaferCount" type="number" min="1" />
          </label>
          <label class="field compact">
            <span>허용 loss</span>
            <input v-model.number="maxLossRate" type="number" min="0" max="0.9" step="0.05" />
          </label>
        </div>

        <button class="run-button" type="button" :disabled="loading || !canRun" @click="loadAll">
          {{ loading ? "분석 중" : "분석 실행" }}
        </button>
        <p v-if="error" class="status-error">{{ error }}</p>
      </aside>

      <section class="result-column panel">
        <RankingPanel
          v-if="rankingRows.length"
          :rows="rankingRows"
          :selected-row="selectedRow"
          @select="selectRanking"
        />
        <div v-else class="empty-state">
          <span>Ranking</span>
          <strong>L3별 Top Feature</strong>
        </div>
        <CandidateTable :analysis="analysis" />
      </section>

      <section class="visual-column">
        <WindowChart :analysis="analysis" />

        <section class="business-panel panel">
          <div class="panel-heading">
            <p>Business Inputs</p>
            <h2>경영효과 기준</h2>
          </div>
          <div class="business-inputs">
            <label>
              <span>월 생산량</span>
              <input v-model.number="monthlyVolume" type="number" min="0" step="10000" />
              <small>chip/month</small>
            </label>
            <label>
              <span>Chip 단가</span>
              <input v-model.number="chipPrice" type="number" min="0" step="100" />
              <small>KRW/chip</small>
            </label>
          </div>
        </section>

        <TradeoffChart
          :analysis="analysis"
          :monthly-volume="monthlyVolume"
          :chip-price="chipPrice"
        />

        <section class="interaction-controls panel">
          <div class="panel-heading">
            <p>Interaction</p>
            <h2>Multi L1 vs L3</h2>
          </div>
          <div class="pair-grid">
            <label>
              <span>X Feature</span>
              <select v-model="interactionL1A" @change="loadInteraction">
                <option v-for="feature in l1Features" :key="feature" :value="feature">{{ feature }}</option>
              </select>
            </label>
            <label>
              <span>Y Feature</span>
              <select v-model="interactionL1B" @change="loadInteraction">
                <option v-for="feature in l1Features" :key="feature" :value="feature">{{ feature }}</option>
              </select>
            </label>
          </div>
        </section>

        <InteractionHeatmap :analysis="interaction" />
      </section>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { fetchCatalog, fetchInteractionAnalysis, fetchRanking, fetchSingleAnalysis } from "./api";
import CandidateTable from "./components/CandidateTable.vue";
import InteractionHeatmap from "./components/InteractionHeatmap.vue";
import RankingPanel from "./components/RankingPanel.vue";
import TradeoffChart from "./components/TradeoffChart.vue";
import WindowChart from "./components/WindowChart.vue";
import type { Catalog, InteractionAnalysis, RankingRow, SingleAnalysis } from "./types";

const loading = ref(false);
const error = ref("");
const catalog = ref<Catalog | null>(null);
const ranking = ref<Record<string, RankingRow[]>>({});
const analysis = ref<SingleAnalysis | null>(null);
const interaction = ref<InteractionAnalysis | null>(null);
const selectedRow = ref<RankingRow | null>(null);

const selectedProduct = ref("P_ALPHA");
const selectedL1 = ref<string[]>([]);
const selectedL3 = ref<string[]>([]);
const monthlyVolume = ref(1_000_000);
const chipPrice = ref(1000);
const minWaferCount = ref(30);
const maxLossRate = ref(0.45);
const interactionL1A = ref("cd_a");
const interactionL1B = ref("ovl_c");

const products = computed(() => catalog.value?.products ?? ["P_ALPHA"]);
const l1Features = computed(() => catalog.value?.l1_features ?? ["cd_a", "thk_b", "ovl_c", "time_since_pm"]);
const l3Items = computed(() => catalog.value?.l3_items ?? ["l3_x", "l3_y", "l3_z", "l3_pm"]);
const rankingRows = computed(() => Object.values(ranking.value).flat());
const canRun = computed(() => selectedProduct.value && selectedL1.value.length > 0 && selectedL3.value.length > 0);

const bestBusinessEffect = computed(() => {
  const candidates = analysis.value?.candidate_specs ?? [];
  if (!candidates.length) return "-";
  const best = candidates
    .map((row) => businessEffect(Number(row.production_loss), Number(row.residual_ppm)).net)
    .reduce((max, value) => Math.max(max, value), Number.NEGATIVE_INFINITY);
  return formatCurrency(best);
});

function formatCurrency(value: number) {
  const abs = Math.abs(value);
  const sign = value < 0 ? "-" : "";
  if (abs >= 100_000_000) return `${sign}${(abs / 100_000_000).toFixed(1)}억`;
  if (abs >= 10_000) return `${sign}${(abs / 10_000).toFixed(0)}만`;
  return `${sign}${abs.toLocaleString()}`;
}

function businessEffect(productionLoss: number, residualPpm: number) {
  const producedChips = monthlyVolume.value;
  const unitPrice = chipPrice.value;
  const baselinePpm = analysis.value?.baseline_ppm ?? 0;
  const passRate = 1 - productionLoss;
  const baselineBadValue = (producedChips * baselinePpm * unitPrice) / 1_000_000;
  const residualBadValue = (producedChips * passRate * residualPpm * unitPrice) / 1_000_000;
  const defectSaving = baselineBadValue - residualBadValue;
  const lostSales = producedChips * productionLoss * unitPrice;
  return {
    defectSaving,
    lostSales,
    net: defectSaving - lostSales,
  };
}

function toggle(list: string[], value: string) {
  const index = list.indexOf(value);
  if (index >= 0) list.splice(index, 1);
  else list.push(value);
}

async function loadCatalog() {
  catalog.value = await fetchCatalog();
  selectedProduct.value = catalog.value.products[0] ?? "P_ALPHA";
  selectedL1.value = [...catalog.value.l1_features];
  selectedL3.value = [...catalog.value.l3_items];
  interactionL1A.value = catalog.value.l1_features[0] ?? "cd_a";
  interactionL1B.value = catalog.value.l1_features[2] ?? catalog.value.l1_features[1] ?? "ovl_c";
}

async function loadAll() {
  if (!canRun.value) return;
  loading.value = true;
  error.value = "";
  try {
    const rankPayload = await fetchRanking({
      product_id: selectedProduct.value,
      selected_l3_items: selectedL3.value,
      selected_l1_features: selectedL1.value,
      min_wafer_count: minWaferCount.value,
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
    product_id: selectedProduct.value,
    l1_feature_name: row.l1_feature_name,
    l3_item_name: row.l3_item_name,
    min_wafer_count: minWaferCount.value,
    max_allowed_loss_rate: maxLossRate.value,
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
    product_id: selectedProduct.value,
    l1_feature_x: interactionL1A.value,
    l1_feature_y: interactionL1B.value,
    l3_item_name: selectedRow.value.l3_item_name,
    min_wafer_count: Math.max(5, Math.round(minWaferCount.value / 3)),
  });
}

onMounted(async () => {
  try {
    await loadCatalog();
    await loadAll();
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Failed to initialize";
  }
});
</script>

<style>
:root {
  color: #1d1d1f;
  background: #f5f5f7;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

body {
  margin: 0;
  background:
    radial-gradient(circle at 18% 0%, rgba(64, 120, 255, 0.16), transparent 34%),
    linear-gradient(180deg, #fbfbfd 0%, #f5f5f7 52%, #ffffff 100%);
}

button,
input,
select {
  font: inherit;
}

.app-shell {
  max-width: 1480px;
  margin: 0 auto;
  padding: 30px 24px 44px;
  box-sizing: border-box;
}

.hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 28px;
  margin-bottom: 22px;
}

.eyebrow,
.panel-heading p {
  margin: 0 0 6px;
  color: #6e6e73;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

h1 {
  max-width: 760px;
  margin: 0;
  font-size: 34px;
  line-height: 1.12;
  letter-spacing: 0;
}

.hero-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(108px, 1fr));
  gap: 10px;
}

.hero-metrics div,
.panel {
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.84);
  box-shadow: 0 18px 44px rgba(25, 28, 38, 0.08);
}

.hero-metrics div {
  min-height: 64px;
  padding: 12px 14px;
  box-sizing: border-box;
}

.hero-metrics span {
  display: block;
  color: #86868b;
  font-size: 12px;
}

.hero-metrics strong {
  display: block;
  margin-top: 5px;
  font-size: 19px;
  letter-spacing: 0;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 260px 390px minmax(0, 1fr);
  gap: 18px;
  align-items: start;
}

.panel {
  padding: 18px;
  box-sizing: border-box;
}

.panel-heading h2 {
  margin: 0;
  font-size: 22px;
  line-height: 1.2;
  letter-spacing: 0;
}

.control-panel {
  position: sticky;
  top: 16px;
}

.field {
  display: grid;
  gap: 8px;
  margin-top: 18px;
}

.field > span,
.business-inputs span,
.pair-grid span {
  color: #515154;
  font-size: 13px;
  font-weight: 700;
}

select,
input {
  min-height: 38px;
  border: 1px solid #d2d2d7;
  border-radius: 8px;
  background: #ffffff;
  color: #1d1d1f;
  padding: 0 11px;
  box-sizing: border-box;
}

select:focus,
input:focus {
  border-color: #0071e3;
  outline: 3px solid rgba(0, 113, 227, 0.14);
}

.chip-group {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}

.chip {
  min-height: 34px;
  border: 1px solid #d2d2d7;
  border-radius: 999px;
  background: #ffffff;
  color: #1d1d1f;
  padding: 0 12px;
  cursor: pointer;
}

.chip.active {
  border-color: #0071e3;
  background: #0071e3;
  color: #ffffff;
}

.input-grid,
.pair-grid,
.business-inputs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  min-width: 0;
}

.field.compact {
  margin-top: 18px;
  min-width: 0;
}

.field.compact input {
  width: 100%;
  min-width: 0;
}

.run-button {
  width: 100%;
  min-height: 44px;
  margin-top: 22px;
  border: 0;
  border-radius: 8px;
  background: #0071e3;
  color: #ffffff;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 10px 24px rgba(0, 113, 227, 0.24);
}

.run-button:disabled {
  background: #a7a7ad;
  box-shadow: none;
  cursor: not-allowed;
}

.status-error {
  margin: 12px 0 0;
  color: #b42318;
  font-size: 13px;
}

.result-column {
  position: sticky;
  top: 16px;
  max-height: calc(100vh - 32px);
  overflow: auto;
}

.visual-column {
  display: grid;
  gap: 18px;
  min-width: 0;
}

.business-panel {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 18px;
}

.business-inputs {
  min-width: 430px;
}

.business-inputs label,
.pair-grid label {
  display: grid;
  gap: 6px;
}

.business-inputs small {
  color: #86868b;
  font-size: 12px;
}

.interaction-controls {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 18px;
}

.pair-grid {
  min-width: 380px;
}

.empty-state {
  min-height: 300px;
  display: grid;
  place-content: center;
  text-align: center;
  color: #86868b;
}

.empty-state strong {
  color: #1d1d1f;
  font-size: 24px;
}

@media (max-width: 1180px) {
  .hero,
  .business-panel,
  .interaction-controls {
    align-items: stretch;
    flex-direction: column;
  }

  .dashboard-grid {
    grid-template-columns: 1fr;
  }

  .control-panel,
  .result-column {
    position: static;
    max-height: none;
  }

  .business-inputs,
  .pair-grid {
    min-width: 0;
  }
}
</style>
