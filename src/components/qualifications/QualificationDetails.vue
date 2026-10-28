<template>
  <section class="qualification-details" :aria-label="title">
    <h1 class="document-title">{{ title }}</h1>
    <dl class="document-fields">
      <div v-for="(field, index) in fields" :key="index" class="detail-row">
        <dt>{{ field.label }}：</dt>
        <dd>{{ field.value }}</dd>
      </div>
    </dl>
  </section>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  fields: { type: Array, required: true }
})
</script>

<style scoped>
.qualification-details {
  width: 100%;
  max-width: 760px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  box-sizing: border-box;
}

.document-title {
  margin: 0;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
  color: #1f2937;
  font-size: 16px;
  font-weight: 600;
  line-height: 1.65;
  overflow-wrap: anywhere;
}

.document-fields { margin: 0; }
.detail-row {
  padding: 12px 18px;
  border-bottom: 1px solid #e5e7eb;
  color: #374151;
  font-size: 16px;
  line-height: 1.65;
  overflow-wrap: anywhere;
}
.detail-row:last-child { border-bottom: 0; }
.detail-row dt { display: inline; font-weight: 600; }
.detail-row dd { display: inline; margin: 0; white-space: pre-wrap; }

@media (max-width: 600px) {
  .document-title { padding: 16px; }
  .detail-row { padding: 12px 16px; }
}
</style>
