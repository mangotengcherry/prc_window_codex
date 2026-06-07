<template>
  <section class="result-table">
    <h2>분석 결과 테이블</h2>
    <table>
      <thead>
        <tr>
          <th>L3</th>
          <th>L1</th>
          <th>Score</th>
          <th>R2</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="`${row.l3_item_name}-${row.l1_feature_name}`" @click="$emit('select', row)">
          <td>{{ row.l3_item_name }}</td>
          <td>{{ row.l1_feature_name }}</td>
          <td>{{ row.priority_score.toFixed(3) }}</td>
          <td>{{ row.u_safe_r2.toFixed(3) }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup lang="ts">
import type { RankingRow } from "../types";

defineProps<{ rows: RankingRow[] }>();
defineEmits<{ select: [row: RankingRow] }>();
</script>

<style scoped>
.result-table {
  min-height: 0;
}
h2 {
  margin: 0 0 18px;
  text-align: center;
  font-size: 30px;
  font-weight: 500;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
th,
td {
  text-align: left;
  padding: 8px;
  border-bottom: 1px solid #dbe4ff;
}
tr {
  cursor: pointer;
}
tr:hover {
  background: #f3f6ff;
}
</style>
