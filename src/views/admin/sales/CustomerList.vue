<template>
  <PartyList ref="partyList" entity-type="customer" />
</template>

<script setup>
import { ref } from 'vue'
import PartyList from '@/components/admin/PartyList.vue'

const partyList = ref(null)

defineExpose({
  loadCustomers: () => partyList.value?.loadList(),
  handleAdd: () => partyList.value?.handleAdd(),
  handleEdit: record => partyList.value?.handleEdit(record)
})
</script>
