<template>
  <section class="candidate-table">
    <h2>1D Window Candidate</h2>
    <p v-if="!analysis">Ranking row를 선택하면 후보가 표시됩니다.</p>
    <template v-else>
      <p>Baseline: {{ analysis.baseline_ppm.toFixed(1) }} ppm</p>
      <table>
        <thead>
          <tr>
            <th>Target</th>
            <th>Loss</th>
            <th>Residual ppm</th>
            <th>Improve</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, idx) in analysis.candidate_specs.slice(0, 6)" :key="idx">
            <td>{{ Number(row.target).toFixed(2) }}</td>
            <td>{{ (Number(row.production_loss) * 100).toFixed(1) }}%</td>
            <td>{{ Number(row.residual_ppm).toFixed(1) }}</td>
            <td>{{ Number(row.ppm_improvement).toFixed(1) }}</td>
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
  border-top: 1px solid #dbe4ff;
  padding-top: 14px;
}
h2 {
  margin: 0 0 12px;
  font-size: 18px;
}
p {
  color: #5b6578;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
th,
td {
  text-align: left;
  padding: 7px;
  border-bottom: 1px solid #dbe4ff;
}
</style>
