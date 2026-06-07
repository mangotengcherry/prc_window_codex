<template>
  <section class="result-table">
    <div class="table-heading">
      <p>Ranking</p>
      <h2>L3별 Top Feature</h2>
    </div>

    <div v-for="group in groupedRows" :key="group.l3" class="l3-group">
      <div class="group-title">
        <strong>{{ group.l3 }}</strong>
        <span>{{ group.rows[0]?.baseline_ppm.toFixed(0) }} ppm</span>
      </div>
      <button
        v-for="row in group.rows"
        :key="`${row.l3_item_name}-${row.l1_feature_name}`"
        type="button"
        class="rank-row"
        :class="{ active: isSelected(row) }"
        @click="$emit('select', row)"
      >
        <span class="rank-main">
          <strong>{{ row.l1_feature_name }}</strong>
          <small>R2 {{ row.u_safe_r2.toFixed(3) }}</small>
        </span>
        <span class="score">{{ row.priority_score.toFixed(3) }}</span>
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { RankingRow } from "../types";

const props = defineProps<{ rows: RankingRow[]; selectedRow: RankingRow | null }>();
defineEmits<{ select: [row: RankingRow] }>();

const groupedRows = computed(() => {
  const groups = new Map<string, RankingRow[]>();
  for (const row of props.rows) {
    const rows = groups.get(row.l3_item_name) ?? [];
    rows.push(row);
    groups.set(row.l3_item_name, rows);
  }
  return Array.from(groups.entries()).map(([l3, rows]) => ({ l3, rows }));
});

function isSelected(row: RankingRow) {
  return props.selectedRow?.l3_item_name === row.l3_item_name
    && props.selectedRow?.l1_feature_name === row.l1_feature_name;
}
</script>

<style scoped>
.table-heading p {
  margin: 0 0 6px;
  color: #86868b;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
}

h2 {
  margin: 0 0 18px;
  font-size: 22px;
}

.l3-group {
  margin-bottom: 18px;
}

.group-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  color: #515154;
}

.group-title span {
  color: #86868b;
  font-size: 12px;
}

.rank-row {
  width: 100%;
  min-height: 52px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 7px;
  border: 1px solid #e5e5ea;
  border-radius: 8px;
  background: #ffffff;
  color: #1d1d1f;
  padding: 10px 12px;
  cursor: pointer;
  text-align: left;
}

.rank-row:hover,
.rank-row.active {
  border-color: #0071e3;
  background: #f0f7ff;
}

.rank-main {
  display: grid;
  gap: 3px;
}

.rank-main small {
  color: #86868b;
}

.score {
  min-width: 62px;
  border-radius: 999px;
  background: #f5f5f7;
  color: #0071e3;
  padding: 5px 8px;
  font-weight: 700;
  text-align: center;
}
</style>
