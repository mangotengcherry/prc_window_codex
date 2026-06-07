<template>
  <section class="candidate-table">
    <div class="candidate-heading">
      <p>Candidate</p>
      <h2>1D Window 후보</h2>
    </div>
    <p v-if="!analysis" class="empty">Ranking 선택 후 후보가 표시됩니다.</p>
    <template v-else>
      <div class="baseline-pill">Baseline {{ analysis.baseline_ppm.toFixed(0) }} ppm</div>
      <table>
        <thead>
          <tr>
            <th>Target</th>
            <th>Loss</th>
            <th>Residual</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, idx) in analysis.candidate_specs.slice(0, 6)" :key="idx">
            <td>{{ Number(row.target).toFixed(2) }}</td>
            <td>{{ (Number(row.production_loss) * 100).toFixed(1) }}%</td>
            <td>{{ Number(row.residual_ppm).toFixed(0) }} ppm</td>
          </tr>
        </tbody>
      </table>
    </template>
  </section>
</template>

<script setup lang="ts">
import type { SingleAnalysis } from "../types";

defineProps<{ analysis: SingleAnalysis | null }>();
</script>

<style scoped>
.candidate-table {
  border-top: 1px solid #e5e5ea;
  margin-top: 18px;
  padding-top: 18px;
}

.candidate-heading p {
  margin: 0 0 6px;
  color: #86868b;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
}

h2 {
  margin: 0 0 12px;
  font-size: 20px;
}

.empty {
  color: #86868b;
}

.baseline-pill {
  display: inline-flex;
  margin-bottom: 10px;
  border-radius: 999px;
  background: #f5f5f7;
  color: #515154;
  padding: 6px 10px;
  font-size: 12px;
  font-weight: 700;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

th,
td {
  text-align: left;
  padding: 8px 4px;
  border-bottom: 1px solid #eeeeef;
}

th {
  color: #86868b;
  font-weight: 700;
}
</style>
