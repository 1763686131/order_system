<template>
  <div
    :class="['gugu-order-message', { 'has-customer-options': message.question?.type === 'customer' }]"
  >
    <p class="gugu-order-text">{{ message.content }}</p>

    <div
      v-if="message.options?.length"
      :class="['gugu-order-options', { 'is-customer-options': message.question?.type === 'customer' }]"
    >
      <button
        v-for="option in message.options"
        :key="option.key"
        type="button"
        :title="option.label"
        :disabled="!active || busy"
        @click="emit('answer', option)"
      >
        {{ option.label }}
      </button>
    </div>

    <template v-if="message.summary">
      <dl class="gugu-order-details">
        <dt>门店 / 仓库</dt>
        <dd>{{ message.summary.storeName }} / {{ message.summary.warehouseName }}</dd>
        <dt>客户</dt>
        <dd>{{ message.summary.customerName }}</dd>
        <dt>收货人</dt>
        <dd>{{ message.summary.contactPerson }} {{ message.summary.contactPhone }}</dd>
        <dt>收货地址</dt>
        <dd>{{ message.summary.contactAddress }}</dd>
        <template v-if="message.summary.projectName">
          <dt>项目</dt>
          <dd>{{ message.summary.projectName }}</dd>
        </template>
        <template v-if="message.summary.orderRemark">
          <dt>备注</dt>
          <dd>{{ message.summary.orderRemark }}</dd>
        </template>
      </dl>
      <ol class="gugu-order-items">
        <li v-for="(item, index) in message.summary.items" :key="index">
          <strong>{{ item.label }}</strong>
          <span>{{ item.packages }} 件 · {{ item.quantity }} {{ item.unit }}</span>
          <small v-if="item.remark">{{ item.remark }}</small>
        </li>
      </ol>
      <button
        class="gugu-order-confirm"
        type="button"
        :disabled="!active || busy"
        @click="emit('confirm')"
      >
        <FilePlus2 :size="16" :stroke-width="1.8" />
        确认并填充新增订单
      </button>
    </template>
  </div>
</template>

<script setup>
import { FilePlus2 } from '@lucide/vue'

defineProps({
  message: { type: Object, required: true },
  active: { type: Boolean, default: false },
  busy: { type: Boolean, default: false }
})
const emit = defineEmits(['answer', 'confirm'])
</script>

<style scoped>
.gugu-order-message {
  min-width: 0;
  max-width: 100%;
  padding: 11px 13px;
  border: 1px solid #e1e8ed;
  border-radius: 8px;
  background: #fff;
  color: #253349;
  font-size: 13px;
  line-height: 1.65;
  overflow-wrap: anywhere;
}

.gugu-order-message.has-customer-options {
  width: min(100%, 680px);
}

.gugu-order-text {
  margin: 0;
  white-space: pre-wrap;
}

.gugu-order-options {
  display: grid;
  gap: 6px;
  margin-top: 10px;
}

.gugu-order-options.is-customer-options {
  grid-template-columns: repeat(auto-fit, minmax(min(120px, 100%), 1fr));
  width: 100%;
  max-height: min(42vh, 320px);
  overflow-y: auto;
  padding-right: 2px;
}

.gugu-order-options.is-customer-options button {
  min-height: 30px;
  padding: 5px 8px;
  font-size: 12px;
  line-height: 1.35;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.gugu-order-options button,
.gugu-order-confirm {
  min-width: 0;
  max-width: 100%;
  padding: 8px 10px;
  border: 1px solid #c8dfd7;
  border-radius: 5px;
  background: #f1faf6;
  color: #08745a;
  font: inherit;
  line-height: 1.5;
  text-align: left;
  overflow-wrap: anywhere;
  cursor: pointer;
}

.gugu-order-options button:hover:enabled {
  border-color: #0c9876;
  background: #e6f5ee;
}

.gugu-order-details {
  display: grid;
  grid-template-columns: 78px minmax(0, 1fr);
  gap: 6px 8px;
  margin: 12px 0;
  padding-top: 12px;
  border-top: 1px solid #e8edf2;
}

.gugu-order-details dt {
  color: #64748b;
}

.gugu-order-details dd {
  min-width: 0;
  margin: 0;
}

.gugu-order-items {
  margin: 0 0 12px;
  padding-left: 22px;
}

.gugu-order-items li {
  padding: 8px 0;
  border-top: 1px solid #e8edf2;
}

.gugu-order-items strong,
.gugu-order-items span,
.gugu-order-items small {
  display: block;
}

.gugu-order-items strong {
  font-weight: 600;
}

.gugu-order-items small {
  color: #64748b;
}

.gugu-order-confirm {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  background: #078362;
  border-color: #078362;
  color: #fff;
}

.gugu-order-confirm svg {
  flex: 0 0 16px;
}

.gugu-order-confirm:hover:enabled {
  background: #066b50;
}

.gugu-order-options button:disabled,
.gugu-order-confirm:disabled {
  cursor: default;
  opacity: 0.5;
}

.gugu-order-options button:focus-visible,
.gugu-order-confirm:focus-visible {
  outline: 2px solid #089374;
  outline-offset: 2px;
}
</style>
