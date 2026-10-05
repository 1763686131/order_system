<template>
  <PartyList ref="partyList" entity-type="supplier" />
</template>

<script setup>
import { ref } from 'vue'
import PartyList from '@/components/admin/PartyList.vue'

const partyList = ref(null)

defineExpose({
  loadSuppliers: () => partyList.value?.loadList(),
  openCreate: () => partyList.value?.handleAdd(),
  openEdit: record => partyList.value?.handleEdit(record)
})
</script>
