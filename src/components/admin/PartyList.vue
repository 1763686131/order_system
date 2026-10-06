<template>
  <div class="party-list-page" @click="closeFilterMenu">
    <section class="search-panel" :aria-label="`${entityConfig.name}筛选`">
      <form class="search-grid" @submit.prevent="handleSearch">
        <label class="field-group">
          <span>关键词搜索</span>
          <span class="input-with-icon">
            <svg aria-hidden="true" viewBox="0 0 24 24">
              <circle cx="11" cy="11" r="7"></circle>
              <path d="m20 20-3.7-3.7"></path>
            </svg>
            <input
              v-model.trim="filters.keyword"
              type="search"
              :placeholder="`搜索${entityConfig.name}名称、编号、联系人、电话...`"
            />
          </span>
        </label>

        <label class="field-group">
          <span>{{ entityConfig.name }}状态</span>
          <select v-model="filters.status">
            <option value="">全部状态</option>
            <option value="active">{{ entityConfig.activeStatusLabel }}</option>
            <option value="inactive">{{ entityConfig.inactiveStatusLabel }}</option>
          </select>
        </label>

        <div class="search-actions">
          <button class="button button-secondary" type="button" @click="handleReset">
            <svg aria-hidden="true" viewBox="0 0 24 24">
              <path d="M3 12a9 9 0 1 0 3-6.7"></path>
              <path d="M3 4v6h6"></path>
            </svg>
            重置
          </button>
          <button class="button button-primary" type="submit">
            <svg aria-hidden="true" viewBox="0 0 24 24">
              <circle cx="11" cy="11" r="7"></circle>
              <path d="m20 20-3.7-3.7"></path>
            </svg>
            查询
          </button>
        </div>
      </form>
    </section>

    <section class="records-panel">
      <header class="records-toolbar">
        <div class="toolbar-filters">
          <div class="store-filter" role="tablist" aria-label="门店筛选">
            <button
              :class="['slider-tab', { active: filters.storeId === null }]"
              type="button"
              @click.stop="filters.storeId = null"
            >
              全部
            </button>
            <button
              v-for="store in allStores"
              :key="store.id"
              :class="['slider-tab', { active: String(filters.storeId) === String(store.id) }]"
              type="button"
              @click.stop="filters.storeId = store.id"
            >
              {{ store.name }}
            </button>
          </div>
        </div>

        <div class="toolbar-actions">
          <button
            class="icon-button"
            type="button"
            title="刷新列表"
            :disabled="loading"
            @click="loadList"
          >
            <svg :class="{ spinning: loading }" aria-hidden="true" viewBox="0 0 24 24">
              <path d="M20 11a8.1 8.1 0 0 0-14.9-4L3 10"></path>
              <path d="M3 4v6h6"></path>
              <path d="M4 13a8.1 8.1 0 0 0 14.9 4L21 14"></path>
              <path d="M15 14h6v6"></path>
            </svg>
          </button>
          <button class="button button-export" type="button" title="导出Excel" @click="handleExport">
            <svg aria-hidden="true" viewBox="0 0 24 24">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
            导出 Excel
          </button>
          <button class="button button-primary" type="button" @click="handleAdd">
            <svg aria-hidden="true" viewBox="0 0 24 24">
              <path d="M12 5v14"></path>
              <path d="M5 12h14"></path>
            </svg>
            新增{{ entityConfig.name }}
          </button>
        </div>
      </header>

      <div class="table-scroll">
        <table class="records-table">
          <thead>
            <tr>
              <th class="document-column">{{ entityConfig.name }}编号</th>
              <th>{{ entityConfig.name }}名称</th>
              <th>所属门店</th>
              <th>联系人</th>
              <th>联系电话</th>
              <th class="address-column">联系地址</th>
              <th class="number-column">{{ entityConfig.primaryMoneyLabel }}</th>
              <th class="number-column">{{ entityConfig.secondaryMoneyLabel }}</th>
              <th>状态</th>
              <th>创建时间</th>
              <th class="operation-column">操作</th>
            </tr>
          </thead>
          <tbody>
            <template v-if="loading">
              <tr v-for="index in 5" :key="`loading-${index}`" class="skeleton-row">
                <td v-for="cell in 11" :key="cell"><span></span></td>
              </tr>
            </template>
            <tr v-else-if="filteredRecords.length === 0">
              <td colspan="11" class="empty-cell">
                <div class="empty-mark" aria-hidden="true">
                  <svg viewBox="0 0 24 24">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                    <circle cx="9" cy="7" r="4"></circle>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"></path>
                  </svg>
                </div>
                <strong>{{ errorMessage ? `暂时无法显示${entityConfig.name}` : `暂无${entityConfig.name}数据` }}</strong>
                <span>{{ errorMessage || '调整筛选条件后重新查询' }}</span>
                <button v-if="errorMessage" class="button button-secondary retry-button" type="button" @click="loadList">
                  重新加载
                </button>
              </td>
            </tr>
            <tr
              v-for="record in paginatedRecords"
              v-else
              :key="record.id"
              class="record-row"
              tabindex="0"
              @click="handleView(record)"
              @keydown.enter.self.prevent="handleView(record)"
            >
              <td>
                <button class="document-link" type="button" @click.stop="handleView(record)">
                  {{ record.code || '未设置' }}
                  <svg aria-hidden="true" viewBox="0 0 24 24">
                    <path d="m9 18 6-6-6-6"></path>
                  </svg>
                </button>
              </td>
              <td class="party-name">{{ record.name }}</td>
              <td class="date-cell">{{ storeName(record.storeId) }}</td>
              <td class="party-cell">{{ record.contactPerson || '-' }}</td>
              <td>{{ record.phone || '-' }}</td>
              <td class="address-cell" :title="record.address">{{ truncateText(record.address, 15) }}</td>
              <td class="number-column numeric money-value primary-money">
                ¥{{ formatAmount(primaryMoney(record)) }}
              </td>
              <td class="number-column numeric money-value" :class="{ 'debt-amount': secondaryMoney(record) > 0 }">
                ¥{{ formatAmount(secondaryMoney(record)) }}
              </td>
              <td>
                <span :class="['status-tag', record.status === 'active' ? 'status-active' : 'status-inactive']">
                  <i aria-hidden="true"></i>
                  {{ statusLabel(record.status) }}
                </span>
              </td>
              <td class="date-cell">{{ formatDate(record.createdAt) }}</td>
              <td class="operation-column" @click.stop>
                <div class="row-actions">
                  <button type="button" title="查看详情" @click="handleView(record)">
                    <svg aria-hidden="true" viewBox="0 0 24 24">
                      <path d="M2.5 12s3.2-6 9.5-6 9.5 6 9.5 6-3.2 6-9.5 6-9.5-6-9.5-6Z"></path>
                      <circle cx="12" cy="12" r="2.5"></circle>
                    </svg>
                  </button>
                  <button type="button" title="编辑" @click="handleEdit(record)">
                    <svg aria-hidden="true" viewBox="0 0 24 24">
                      <path d="m4 16-.8 4.8L8 20l11.5-11.5a2.8 2.8 0 0 0-4-4Z"></path>
                      <path d="m13.5 6.5 4 4"></path>
                    </svg>
                  </button>
                  <button type="button" title="删除" @click="handleDelete(record)">
                    <svg aria-hidden="true" viewBox="0 0 24 24">
                      <path d="M4 7h16M9 7V4h6v3m-9 0 1 13h10l1-13M10 11v5m4-5v5"></path>
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <footer class="table-footer">
        <span>
          共 <strong>{{ filteredRecords.length }}</strong> 条记录
          <template v-if="filteredRecords.length">，当前 {{ pageStart }}-{{ pageEnd }} 条</template>
        </span>
        <div class="pagination" aria-label="分页">
          <select v-model.number="pageSize" aria-label="每页条数">
            <option :value="10">10 条 / 页</option>
            <option :value="20">20 条 / 页</option>
            <option :value="50">50 条 / 页</option>
            <option :value="99999">全部</option>
          </select>
          <button type="button" title="上一页" :disabled="currentPage <= 1" @click="currentPage--">
            <svg aria-hidden="true" viewBox="0 0 24 24"><path d="m15 18-6-6 6-6"></path></svg>
          </button>
          <span>{{ currentPage }} / {{ totalPages }}</span>
          <button type="button" title="下一页" :disabled="currentPage >= totalPages" @click="currentPage++">
            <svg aria-hidden="true" viewBox="0 0 24 24"><path d="m9 18 6-6-6-6"></path></svg>
          </button>
        </div>
      </footer>
    </section>

    <Teleport to="body">
      <Transition name="detail-modal">
        <div v-if="showDetailModal && selectedRecord" class="detail-modal-layer">
          <div class="detail-modal-backdrop" @click="closeDetailModal"></div>
          <section
            class="detail-modal"
            role="dialog"
            aria-modal="true"
            :aria-label="`${entityConfig.name}详情`"
            tabindex="-1"
            @keydown.esc="closeDetailModal"
          >
            <header class="detail-modal-header">
              <div class="detail-modal-title-wrap">
                <span class="detail-modal-mark" aria-hidden="true">
                  <svg viewBox="0 0 24 24">
                    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
                    <circle cx="9" cy="7" r="4"></circle>
                    <path d="M19 8v6M22 11h-6"></path>
                  </svg>
                </span>
                <div>
                  <span>{{ entityConfig.name }}详情</span>
                  <h2>{{ selectedRecord.name }}</h2>
                </div>
              </div>
              <button class="detail-modal-close" type="button" title="关闭" @click="closeDetailModal">
                <svg aria-hidden="true" viewBox="0 0 24 24">
                  <path d="m6 6 12 12M18 6 6 18"></path>
                </svg>
              </button>
            </header>

            <div class="detail-modal-body">
              <section class="detail-modal-overview">
                <div class="overview-head">
                  <span :class="['status-tag', selectedRecord.status === 'active' ? 'status-active' : 'status-inactive']">
                    <i aria-hidden="true"></i>
                    {{ statusLabel(selectedRecord.status) }}
                  </span>
                  <span>{{ storeName(selectedRecord.storeId) }}</span>
                </div>
                <dl class="meta-grid">
                  <div>
                    <dt>{{ entityConfig.name }}编号</dt>
                    <dd>{{ selectedRecord.code || '-' }}</dd>
                  </div>
                  <div>
                    <dt>{{ entityConfig.name }}名称</dt>
                    <dd>{{ selectedRecord.name }}</dd>
                  </div>
                  <div>
                    <dt>联系人</dt>
                    <dd>{{ selectedRecord.contactPerson || '-' }}</dd>
                  </div>
                  <div>
                    <dt>联系电话</dt>
                    <dd>{{ selectedRecord.phone || '-' }}</dd>
                  </div>
                  <div class="wide-meta">
                    <dt>联系地址</dt>
                    <dd>{{ selectedRecord.address || '-' }}</dd>
                  </div>
                  <div>
                    <dt>创建时间</dt>
                    <dd>{{ formatDate(selectedRecord.createdAt) }}</dd>
                  </div>
                </dl>
              </section>

              <section class="detail-section">
                <div class="section-heading"><h3>财务信息</h3></div>
                <div class="summary-strip">
                  <template v-if="!isSupplier">
                    <div>
                      <span>{{ entityConfig.primaryMoneyLabel }}</span>
                      <strong class="primary-money">¥{{ formatAmount(selectedRecord.balance) }}</strong>
                    </div>
                    <div>
                      <span>期初欠款</span>
                      <strong>¥{{ formatAmount(selectedRecord.initialReceivable) }}</strong>
                    </div>
                    <div>
                      <span>{{ entityConfig.secondaryMoneyLabel }}</span>
                      <strong :class="{ 'debt-amount': selectedRecord.receivable > 0 }">
                        ¥{{ formatAmount(selectedRecord.receivable) }}
                      </strong>
                    </div>
                  </template>
                  <template v-else>
                    <div>
                      <span>应付余额</span>
                      <strong class="debt-amount">¥{{ formatAmount(selectedRecord.payable) }}</strong>
                    </div>
                    <div>
                      <span>供应商预付款</span>
                      <strong>¥{{ formatAmount(selectedRecord.prepaymentBalance) }}</strong>
                    </div>
                    <div>
                      <span>供应商贷项</span>
                      <strong>¥{{ formatAmount(selectedRecord.creditBalance) }}</strong>
                    </div>
                  </template>
                </div>
              </section>

              <section v-if="selectedRecord.bankName || selectedRecord.bankAccount || selectedRecord.taxNumber" class="detail-section">
                <div class="section-heading"><h3>结算信息</h3></div>
                <dl class="meta-grid">
                  <div v-if="selectedRecord.bankName">
                    <dt>开户行</dt>
                    <dd>{{ selectedRecord.bankName }}</dd>
                  </div>
                  <div v-if="selectedRecord.bankAccount">
                    <dt>银行账号</dt>
                    <dd>{{ selectedRecord.bankAccount }}</dd>
                  </div>
                  <div v-if="selectedRecord.bankCode && !isSupplier">
                    <dt>行号</dt>
                    <dd>{{ selectedRecord.bankCode }}</dd>
                  </div>
                  <div v-if="selectedRecord.taxNumber">
                    <dt>税号</dt>
                    <dd>{{ selectedRecord.taxNumber }}</dd>
                  </div>
                </dl>
              </section>

              <section v-if="selectedRecord.remark" class="detail-section">
                <div class="section-heading"><h3>备注信息</h3></div>
                <p class="remark-text">{{ selectedRecord.remark }}</p>
              </section>
            </div>

            <footer class="detail-modal-footer">
              <button class="button button-danger-light" type="button" @click="handleDelete(selectedRecord)">删除</button>
              <div class="detail-modal-actions">
                <button class="button button-edit" type="button" @click="handleEdit(selectedRecord)">编辑</button>
                <button class="button button-secondary" type="button" @click="closeDetailModal">关闭</button>
              </div>
            </footer>
          </section>
        </div>
      </Transition>
    </Teleport>

    <Teleport to="body">
      <Transition name="detail-modal">
        <div v-if="showEditModal" class="detail-modal-layer">
          <div class="detail-modal-backdrop" @click="closeEditModal"></div>
          <section class="detail-modal create-modal" role="dialog" aria-modal="true" :aria-label="isEditMode ? `编辑${entityConfig.name}` : `新增${entityConfig.name}`">
            <header class="detail-modal-header">
              <div class="detail-modal-title-wrap">
                <span class="detail-modal-mark" aria-hidden="true">
                  <svg viewBox="0 0 24 24">
                    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
                    <circle cx="9" cy="7" r="4"></circle>
                    <path d="M19 8v6M22 11h-6"></path>
                  </svg>
                </span>
                <div>
                  <span>{{ entityConfig.name }}管理</span>
                  <h2>{{ isEditMode ? `编辑${entityConfig.name}` : `新增${entityConfig.name}` }}</h2>
                </div>
              </div>
              <button class="detail-modal-close" type="button" title="关闭" @click="closeEditModal">
                <svg aria-hidden="true" viewBox="0 0 24 24">
                  <path d="m6 6 12 12M18 6 6 18"></path>
                </svg>
              </button>
            </header>

            <div class="detail-modal-body">
              <form class="party-form" @submit.prevent="handleSubmit">
                <section class="form-highlight-section">
                  <label class="form-field-inline">
                    <span class="field-label-inline">
                      <svg aria-hidden="true" viewBox="0 0 24 24">
                        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                        <polyline points="9 22 9 12 15 12 15 22"></polyline>
                      </svg>
                      所属门店 <em v-if="!isSupplier">*</em>
                    </span>
                    <div v-if="allStores.length" class="store-pill-group">
                      <button
                        v-if="isSupplier"
                        type="button"
                        :class="['store-pill', { active: !formData.storeId }]"
                        @click="formData.storeId = ''"
                      >
                        通用供应商
                      </button>
                      <button
                        v-for="store in allStores"
                        :key="store.id"
                        type="button"
                        :class="['store-pill', { active: String(formData.storeId) === String(store.id) }]"
                        @click="formData.storeId = store.id"
                      >
                        {{ store.name }}
                      </button>
                    </div>
                    <div v-else class="empty-hint">暂无门店数据，请先添加门店</div>
                  </label>
                </section>

                <section class="form-card">
                  <div class="form-card-header"><h4>基本信息</h4></div>
                  <div class="form-card-body">
                    <div class="form-row">
                      <label class="form-field">
                        <span class="field-label">{{ entityConfig.name }}名称 <em>*</em></span>
                        <input v-model.trim="formData.name" type="text" :placeholder="`请输入${entityConfig.name}名称`" required />
                      </label>
                      <label class="form-field">
                        <span class="field-label">{{ entityConfig.name }}编号 <em v-if="!isSupplier">*</em></span>
                        <input v-model.trim="formData.code" type="text" :placeholder="isSupplier ? '选填，需保持唯一' : '请输入客户编号'" :required="!isSupplier" />
                      </label>
                    </div>
                    <div class="form-row">
                      <label class="form-field">
                        <span class="field-label">联系人</span>
                        <input v-model.trim="formData.contactPerson" type="text" placeholder="请输入联系人姓名" />
                      </label>
                      <label class="form-field">
                        <span class="field-label">联系电话</span>
                        <input v-model.trim="formData.phone" type="tel" placeholder="请输入联系电话" />
                      </label>
                    </div>
                    <label class="form-field">
                      <span class="field-label">联系地址</span>
                      <textarea v-model.trim="formData.address" rows="2" placeholder="请输入详细联系地址"></textarea>
                    </label>
                    <label v-if="isSupplier" class="form-field status-field">
                      <span class="field-label">供应商状态</span>
                      <select v-model="formData.status">
                        <option value="active">启用</option>
                        <option value="inactive">停用</option>
                      </select>
                    </label>
                  </div>
                </section>

                <section v-if="!isSupplier" class="form-card">
                  <div class="form-card-header"><h4>财务信息</h4></div>
                  <div class="form-card-body">
                    <div class="form-row">
                      <label class="form-field">
                        <span class="field-label">储值余额</span>
                        <div class="input-with-prefix">
                          <span class="input-prefix">¥</span>
                          <input v-model.number="formData.balance" type="number" min="0" step="0.01" placeholder="0.00" @input="handleMoneyInput('balance')" />
                        </div>
                      </label>
                      <label class="form-field">
                        <span class="field-label">期初欠款</span>
                        <div class="input-with-prefix">
                          <span class="input-prefix">¥</span>
                          <input v-model.number="formData.initialDebt" type="number" min="0" step="0.01" placeholder="0.00" @input="handleMoneyInput('initialDebt')" />
                        </div>
                      </label>
                    </div>
                    <div class="form-row">
                      <label class="form-field">
                        <span class="field-label">开户行</span>
                        <input v-model.trim="formData.bankName" type="text" placeholder="如：中国工商银行" />
                      </label>
                      <label class="form-field">
                        <span class="field-label">银行账号</span>
                        <input v-model.trim="formData.bankAccount" type="text" placeholder="请输入银行账号" />
                      </label>
                    </div>
                    <div class="form-row">
                      <label class="form-field">
                        <span class="field-label">行号</span>
                        <input v-model.trim="formData.bankCode" type="text" placeholder="请输入银行行号" />
                      </label>
                      <label class="form-field">
                        <span class="field-label">税号</span>
                        <input v-model.trim="formData.taxNumber" type="text" placeholder="请输入纳税人识别号" />
                      </label>
                    </div>
                    <label class="form-field">
                      <span class="field-label">备注信息</span>
                      <textarea v-model.trim="formData.remark" rows="3" placeholder="可输入其他补充说明信息..."></textarea>
                    </label>
                  </div>
                </section>

                <section v-else class="form-card">
                  <div class="form-card-header"><h4>结算信息</h4></div>
                  <div class="form-card-body">
                    <div class="form-row">
                      <label class="form-field">
                        <span class="field-label">欠款金额</span>
                        <div class="readonly-money">¥{{ formatAmount(formData.payable) }}</div>
                        <small class="field-hint">应付余额（只读）</small>
                      </label>
                      <label class="form-field">
                        <span class="field-label">应付欠款</span>
                        <div class="readonly-money">¥{{ formatAmount(formData.payable) }}</div>
                      </label>
                    </div>
                    <div class="form-row">
                      <label class="form-field">
                        <span class="field-label">开户行</span>
                        <input v-model.trim="formData.bankName" type="text" placeholder="如：中国工商银行" />
                      </label>
                      <label class="form-field">
                        <span class="field-label">银行账号</span>
                        <input v-model.trim="formData.bankAccount" type="text" placeholder="请输入银行账号" />
                      </label>
                    </div>
                    <div class="form-row">
                      <label class="form-field">
                        <span class="field-label">税号</span>
                        <input v-model.trim="formData.taxNumber" type="text" placeholder="请输入纳税人识别号" />
                      </label>
                      <label class="form-field">
                        <span class="field-label">备注信息</span>
                        <input v-model.trim="formData.remark" type="text" placeholder="可输入其他补充说明信息..." />
                      </label>
                    </div>
                  </div>
                </section>
              </form>
            </div>

            <footer class="detail-modal-footer">
              <span></span>
              <div class="detail-modal-actions">
                <button class="button button-secondary" type="button" @click="closeEditModal">取消</button>
                <button class="button button-primary" type="button" :disabled="submitting" @click="handleSubmit">
                  {{ submitting ? '提交中...' : (isEditMode ? '保存' : '创建') }}
                </button>
              </div>
            </footer>
          </section>
        </div>
      </Transition>
    </Teleport>

    <CustomModal
      v-model:visible="modal.visible"
      :type="modal.type"
      :title="modal.title"
      :message="modal.message"
      :confirm-text="modal.confirmText"
      :cancel-text="modal.cancelText"
      :show-cancel="modal.showCancel"
      :danger="modal.danger"
      @confirm="handleModalConfirm"
      @cancel="handleModalCancel"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import request from '@/api/request'
import CustomModal from '@/components/CustomModal.vue'

const props = defineProps({
  entityType: {
    type: String,
    default: 'customer',
    validator: value => ['customer', 'supplier'].includes(value)
  }
})

const isSupplier = computed(() => props.entityType === 'supplier')
const entityConfig = computed(() => isSupplier.value
  ? {
      name: '供应商',
      primaryMoneyLabel: '欠款金额',
      secondaryMoneyLabel: '应付欠款',
      activeStatusLabel: '启用',
      inactiveStatusLabel: '停用'
    }
  : {
      name: '客户',
      primaryMoneyLabel: '储值余额',
      secondaryMoneyLabel: '应收欠款',
      activeStatusLabel: '活跃',
      inactiveStatusLabel: '不活跃'
    })

const loading = ref(false)
const submitting = ref(false)
const errorMessage = ref('')
const records = ref([])
const allStores = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const showDetailModal = ref(false)
const showEditModal = ref(false)
const isEditMode = ref(false)
const selectedRecord = ref(null)

const filters = reactive({
  keyword: '',
  storeId: null,
  status: ''
})

const modal = reactive({
  visible: false,
  type: 'warning',
  title: '',
  message: '',
  confirmText: '确定',
  cancelText: '取消',
  showCancel: true,
  danger: false,
  onConfirm: null
})

const emptyForm = () => ({
  id: null,
  code: '',
  name: '',
  storeId: '',
  contactPerson: '',
  phone: '',
  address: '',
  balance: 0,
  initialDebt: 0,
  payable: 0,
  bankName: '',
  bankAccount: '',
  bankCode: '',
  taxNumber: '',
  remark: '',
  status: 'active'
})

const formData = reactive(emptyForm())

const extractList = response => {
  if (Array.isArray(response)) return response
  if (Array.isArray(response?.customers)) return response.customers
  if (Array.isArray(response?.suppliers)) return response.suppliers
  if (Array.isArray(response?.data)) return response.data
  return []
}

const normalizeRecord = source => {
  const item = source || {}
  if (isSupplier.value) {
    return {
      ...item,
      id: item.id,
      code: String(item.supplierCode ?? item.supplier_code ?? item.code ?? '').trim(),
      name: String(item.supplierName ?? item.supplier_name ?? item.name ?? '').trim(),
      storeId: item.storeId ?? item.store_id ?? null,
      contactPerson: String(item.contactPerson ?? item.contact_person ?? '').trim(),
      phone: String(item.phone ?? '').trim(),
      address: String(item.address ?? '').trim(),
      payable: Number(item.payable ?? item.payableAmount ?? 0) || 0,
      bankName: String(item.bankName ?? item.bank_name ?? '').trim(),
      bankAccount: String(item.bankAccount ?? item.bank_account ?? '').trim(),
      bankCode: '',
      taxNumber: String(item.taxNumber ?? item.tax_number ?? '').trim(),
      remark: String(item.remark ?? '').trim(),
      status: String(item.status || 'active').toLowerCase(),
      createdAt: item.createdAt ?? item.created_at ?? '',
      updatedAt: item.updatedAt ?? item.updated_at ?? ''
    }
  }

  return {
    ...item,
    id: item.id,
    code: String(item.customerCode ?? item.customer_code ?? item.code ?? '').trim(),
    name: String(item.customerName ?? item.customer_name ?? item.name ?? '').trim(),
    storeId: item.storeId ?? item.store_id ?? null,
    contactPerson: String(item.contactPerson ?? item.contact_person ?? '').trim(),
    phone: String(item.phone ?? '').trim(),
    address: String(item.address ?? '').trim(),
    balance: Number(item.balance ?? 0) || 0,
    initialReceivable: Number(item.initialReceivable ?? item.initial_receivable ?? item.initialDebt ?? 0) || 0,
    receivable: Number(item.receivable ?? 0) || 0,
    bankName: String(item.bankName ?? item.bank_name ?? '').trim(),
    bankAccount: String(item.bankAccount ?? item.bank_account ?? '').trim(),
    bankCode: String(item.bankCode ?? item.bank_code ?? '').trim(),
    taxNumber: String(item.taxNumber ?? item.tax_number ?? '').trim(),
    remark: String(item.remark ?? '').trim(),
    status: String(item.status || 'active').toLowerCase(),
    createdAt: item.createdAt ?? item.created_at ?? '',
    updatedAt: item.updatedAt ?? item.updated_at ?? ''
  }
}

const storeMap = computed(() => new Map(
  allStores.value.map(store => [String(store.id), store.name || store.storeName || `门店 ${store.id}`])
))

const filteredRecords = computed(() => {
  const keyword = filters.keyword.toLowerCase()
  return records.value.filter(record => {
    const values = [record.name, record.code, record.contactPerson, record.phone]
    const matchesKeyword = !keyword || values.some(value => String(value || '').toLowerCase().includes(keyword))
    const matchesStore = filters.storeId === null || String(record.storeId) === String(filters.storeId)
    const matchesStatus = !filters.status || record.status === filters.status
    return matchesKeyword && matchesStore && matchesStatus
  })
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredRecords.value.length / pageSize.value)))
const paginatedRecords = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredRecords.value.slice(start, start + pageSize.value)
})
const pageStart = computed(() => filteredRecords.value.length ? (currentPage.value - 1) * pageSize.value + 1 : 0)
const pageEnd = computed(() => Math.min(currentPage.value * pageSize.value, filteredRecords.value.length))

watch(
  () => [filters.keyword, filters.storeId, filters.status, pageSize.value],
  () => { currentPage.value = 1 }
)
watch(totalPages, value => {
  if (currentPage.value > value) currentPage.value = value
})

const storeName = storeId => {
  if (storeId === null || storeId === undefined || storeId === '') {
    return isSupplier.value ? '通用供应商' : '未指定门店'
  }
  return storeMap.value.get(String(storeId)) || '未知门店'
}

const statusLabel = status => status === 'inactive'
  ? entityConfig.value.inactiveStatusLabel
  : entityConfig.value.activeStatusLabel

const primaryMoney = record => isSupplier.value ? record.payable : record.balance
const secondaryMoney = record => isSupplier.value ? record.payable : record.receivable

const formatAmount = amount => Number(amount || 0).toFixed(2)

const formatDate = value => {
  if (!value) return '-'
  const date = new Date(String(value).replace(' ', 'T'))
  if (Number.isNaN(date.getTime())) return String(value).slice(0, 10)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

const truncateText = (text, length) => {
  if (!text) return '-'
  return String(text).length <= length ? text : `${String(text).slice(0, length)}...`
}

const extractError = (error, fallback) =>
  error?.response?.data?.message
  || error?.response?.data?.error
  || error?.message
  || fallback

const showAlert = (message, type = 'success', title = '') => {
  Object.assign(modal, {
    visible: true,
    type,
    title: title || (type === 'success' ? '操作成功' : type === 'error' ? '操作失败' : '提示'),
    message,
    confirmText: '确定',
    cancelText: '取消',
    showCancel: false,
    danger: false,
    onConfirm: null
  })
}

const showConfirm = (message, onConfirm) => {
  Object.assign(modal, {
    visible: true,
    type: 'warning',
    title: '删除确认',
    message,
    confirmText: '确定删除',
    cancelText: '取消',
    showCancel: true,
    danger: true,
    onConfirm
  })
}

const handleModalConfirm = async () => {
  const callback = modal.onConfirm
  modal.visible = false
  modal.onConfirm = null
  if (callback) await callback()
}

const handleModalCancel = () => {
  modal.visible = false
  modal.onConfirm = null
}

const loadStores = async () => {
  try {
    const response = await request({ url: '/stores', method: 'GET' })
    allStores.value = extractList(response)
      .filter(store => store && store.id !== undefined && store.id !== null)
      .filter(store => !store.status || store.status === 'active')
      .map(store => ({ ...store, name: store.name || store.storeName || store.store_name || `门店 ${store.id}` }))
  } catch (error) {
    allStores.value = []
    showAlert(extractError(error, '门店列表加载失败'), 'error', '加载失败')
  }
}

const loadList = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await request({ url: isSupplier.value ? '/suppliers' : '/customers', method: 'GET' })
    records.value = extractList(response).map(normalizeRecord)
  } catch (error) {
    records.value = []
    errorMessage.value = extractError(error, `请检查${entityConfig.value.name}接口后重试`)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
}

const handleReset = () => {
  Object.assign(filters, { keyword: '', storeId: null, status: '' })
  currentPage.value = 1
}

const resetForm = () => {
  Object.assign(formData, emptyForm())
}

const handleAdd = () => {
  resetForm()
  formData.storeId = isSupplier.value ? '' : (allStores.value[0]?.id ?? '')
  isEditMode.value = false
  showEditModal.value = true
}

const handleView = record => {
  selectedRecord.value = record
  showDetailModal.value = true
}

const handleEdit = record => {
  selectedRecord.value = record
  Object.assign(formData, {
    id: record.id,
    code: record.code,
    name: record.name,
    storeId: record.storeId ?? '',
    contactPerson: record.contactPerson,
    phone: record.phone,
    address: record.address,
    balance: record.balance ?? 0,
    initialDebt: record.initialReceivable ?? 0,
    payable: record.payable ?? 0,
    bankName: record.bankName,
    bankAccount: record.bankAccount,
    bankCode: record.bankCode,
    taxNumber: record.taxNumber,
    remark: record.remark,
    status: record.status === 'inactive' ? 'inactive' : 'active'
  })
  showDetailModal.value = false
  showEditModal.value = true
  isEditMode.value = true
}

const closeDetailModal = () => {
  showDetailModal.value = false
  selectedRecord.value = null
}

const closeEditModal = () => {
  if (submitting.value) return
  showEditModal.value = false
  isEditMode.value = false
  selectedRecord.value = null
  resetForm()
}

const handleDelete = record => {
  showConfirm(`确定要删除${entityConfig.value.name}“${record.name}”吗？`, async () => {
    try {
      await request({
        url: `/${isSupplier.value ? 'suppliers' : 'customers'}/${record.id}`,
        method: 'DELETE'
      })
      closeDetailModal()
      showAlert(`${entityConfig.value.name}已删除`, 'success')
      await loadList()
    } catch (error) {
      showAlert(extractError(error, `删除${entityConfig.value.name}失败`), 'error', '删除失败')
    }
  })
}

const handleMoneyInput = field => {
  if (!Number.isFinite(Number(formData[field])) || Number(formData[field]) < 0) formData[field] = 0
}

const handleSubmit = async () => {
  if (!formData.name || (!isSupplier.value && !formData.code) || (!isSupplier.value && !formData.storeId)) {
    showAlert('请填写必填项', 'warning', '提示')
    return
  }

  const editing = isEditMode.value
  submitting.value = true
  const payload = isSupplier.value
    ? {
        supplierCode: formData.code,
        supplierName: formData.name,
        storeId: formData.storeId ? Number(formData.storeId) : null,
        contactPerson: formData.contactPerson,
        phone: formData.phone,
        address: formData.address,
        taxNumber: formData.taxNumber,
        bankName: formData.bankName,
        bankAccount: formData.bankAccount,
        remark: formData.remark,
        status: formData.status
      }
    : {
        customerCode: formData.code,
        customerName: formData.name,
        storeId: formData.storeId ? Number(formData.storeId) : null,
        contactPerson: formData.contactPerson,
        phone: formData.phone,
        address: formData.address,
        balance: Number(formData.balance) || 0,
        initialDebt: Number(formData.initialDebt) || 0,
        bankName: formData.bankName,
        bankAccount: formData.bankAccount,
        bankCode: formData.bankCode,
        taxNumber: formData.taxNumber,
        remark: formData.remark,
        ...(isEditMode.value ? { status: formData.status } : {})
      }

  try {
    const baseUrl = isSupplier.value ? '/suppliers' : '/customers'
    const response = await request({
      url: isEditMode.value ? `${baseUrl}/${formData.id}` : baseUrl,
      method: isEditMode.value ? 'PUT' : 'POST',
      data: payload
    })
    closeEditModal()
    showAlert(response?.message || `${entityConfig.value.name}${editing ? '保存成功' : '创建成功'}`, 'success')
    await loadList()
  } catch (error) {
    showAlert(extractError(error, `${entityConfig.value.name}保存失败`), 'error', '保存失败')
  } finally {
    submitting.value = false
  }
}

const csvEscape = value => `"${String(value ?? '').replace(/"/g, '""')}"`

const handleExport = () => {
  const header = [
    `${entityConfig.value.name}编号`,
    `${entityConfig.value.name}名称`,
    '所属门店',
    '联系人',
    '联系电话',
    entityConfig.value.primaryMoneyLabel,
    entityConfig.value.secondaryMoneyLabel,
    '状态',
    '创建时间'
  ]
  const rows = filteredRecords.value.map(record => [
    record.code,
    record.name,
    storeName(record.storeId),
    record.contactPerson,
    record.phone,
    formatAmount(primaryMoney(record)),
    formatAmount(secondaryMoney(record)),
    statusLabel(record.status),
    formatDate(record.createdAt)
  ])
  const csv = `\ufeff${[header, ...rows].map(row => row.map(csvEscape).join(',')).join('\n')}`
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${entityConfig.value.name}列表.csv`
  link.click()
  URL.revokeObjectURL(url)
}

const closeFilterMenu = () => {}

defineExpose({ loadList, handleAdd, handleEdit })

onMounted(async () => {
  await loadStores()
  await loadList()
})
</script>

<style scoped>
.party-list-page {
  --accent: #0f9f78;
  --accent-dark: #08745a;
  --accent-soft: #e9f8f3;
  --accent-border: #a9e5d2;
  --page-bg: #f4f8f5;
  --panel-bg: #fff;
  --border: #e2e8f0;
  --text: #172033;
  --muted: #667085;
  min-height: 100%;
  color: var(--text);
  background: var(--page-bg);
}

.party-list-page,
.party-list-page * {
  box-sizing: border-box;
}

button,
input,
select,
textarea {
  font: inherit;
}

button {
  cursor: pointer;
}

svg {
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.search-panel,
.records-panel {
  overflow: hidden;
  background: var(--panel-bg);
  border: 1px solid var(--border);
  border-radius: 7px;
  box-shadow: 0 3px 14px rgba(15, 23, 42, .045);
}

.search-panel {
  padding: 16px;
}

.search-grid {
  display: grid;
  grid-template-columns: minmax(250px, 1fr) minmax(150px, 220px) auto;
  align-items: end;
  gap: 14px;
}

.field-group,
.form-field {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 7px;
  color: #566176;
  font-size: 12px;
  font-weight: 600;
}

.field-group input,
.field-group select,
.form-field input,
.form-field select,
.form-field textarea {
  width: 100%;
  min-height: 38px;
  padding: 0 11px;
  color: var(--text);
  background: #fff;
  border: 1px solid #cbd5e1;
  border-radius: 5px;
  outline: none;
  transition: border-color .18s, box-shadow .18s;
}

.form-field textarea {
  min-height: 74px;
  padding: 10px 11px;
  resize: vertical;
}

input:focus,
select:focus,
textarea:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(15, 159, 120, .12);
}

.input-with-icon,
.input-with-prefix {
  position: relative;
  display: block;
}

.input-with-icon svg {
  position: absolute;
  top: 11px;
  left: 11px;
  z-index: 1;
  width: 16px;
  height: 16px;
  color: var(--muted);
}

.input-with-icon input {
  padding-left: 35px;
}

.input-prefix {
  position: absolute;
  top: 10px;
  left: 12px;
  color: #64748b;
  pointer-events: none;
}

.input-with-prefix input {
  padding-left: 28px;
}

.search-actions,
.toolbar-actions,
.detail-modal-actions,
.pagination {
  display: flex;
  align-items: center;
  gap: 8px;
}

.button {
  display: inline-flex;
  min-height: 38px;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 0 15px;
  border: 1px solid transparent;
  border-radius: 5px;
  font-size: 13px;
  font-weight: 650;
  white-space: nowrap;
  transition: background .18s, border-color .18s, color .18s;
}

.button svg {
  width: 16px;
  height: 16px;
}

.button:disabled,
.icon-button:disabled {
  cursor: not-allowed;
  opacity: .45;
}

.button-primary {
  color: #fff;
  background: var(--accent);
  border-color: var(--accent);
}

.button-primary:hover:not(:disabled) {
  background: var(--accent-dark);
  border-color: var(--accent-dark);
}

.button-secondary,
.button-export {
  color: #445066;
  background: #fff;
  border-color: #cbd5e1;
}

.button-secondary:hover:not(:disabled),
.button-export:hover:not(:disabled) {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.button-edit {
  color: #fff;
  background: #2563eb;
  border-color: #2563eb;
}

.button-danger-light {
  color: #b4232f;
  background: #fff;
  border-color: #efb5ba;
}

.button-danger-light:hover {
  color: #fff;
  background: #dc3545;
}

.records-panel {
  margin-top: 14px;
}

.records-toolbar {
  display: flex;
  min-height: 62px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 11px 16px;
  border-bottom: 1px solid var(--border);
}

.toolbar-filters {
  min-width: 0;
  overflow-x: auto;
}

.store-filter {
  display: flex;
  width: max-content;
  gap: 6px;
  padding: 4px;
  background: #f1f5f9;
  border-radius: 8px;
}

.slider-tab {
  height: 36px;
  padding: 0 16px;
  color: var(--muted);
  background: transparent;
  border: 0;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
}

.slider-tab:hover {
  color: var(--accent-dark);
  background: rgba(15, 159, 120, .1);
}

.slider-tab.active {
  color: #fff;
  background: var(--accent);
}

.icon-button {
  display: inline-flex;
  width: 36px;
  height: 36px;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: #667085;
  background: #fff;
  border: 1px solid #cbd5e1;
  border-radius: 5px;
}

.icon-button:hover:not(:disabled) {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.icon-button svg {
  width: 17px;
  height: 17px;
}

.spinning {
  animation: spin .8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.table-scroll {
  overflow-x: auto;
}

.records-table {
  width: 100%;
  min-width: 1340px;
  border-collapse: collapse;
  table-layout: fixed;
}

.records-table th {
  height: 45px;
  padding: 0 12px;
  color: #566176;
  background: #f8fafc;
  border-bottom: 1px solid var(--border);
  font-size: 12px;
  font-weight: 650;
  text-align: left;
  white-space: nowrap;
}

.records-table td {
  height: 57px;
  padding: 9px 12px;
  overflow: hidden;
  color: #344054;
  border-bottom: 1px solid #edf1f5;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.record-row {
  cursor: pointer;
  transition: background .15s ease;
}

.record-row:hover {
  background: rgba(15, 159, 120, .08);
}

.document-column { width: 140px; }
.address-column { width: 160px; }
.number-column { width: 112px; text-align: right !important; }
.operation-column { width: 115px; text-align: center; }

.document-link {
  display: inline-flex;
  max-width: 100%;
  align-items: center;
  gap: 4px;
  padding: 3px 0;
  overflow: hidden;
  color: var(--accent-dark);
  background: transparent;
  border: 0;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.document-link:hover {
  text-decoration: underline;
}

.document-link svg {
  width: 13px;
  height: 13px;
  flex: 0 0 auto;
}

.party-name {
  color: #283548;
  font-weight: 600;
}

.date-cell,
.party-cell,
.address-cell {
  color: var(--muted);
  font-size: 13px;
}

.numeric,
.money-value {
  font-variant-numeric: tabular-nums;
}

.money-value {
  color: #182230 !important;
  font-weight: 750;
}

.primary-money {
  color: #0891b2 !important;
}

.debt-amount {
  color: #ef4444 !important;
}

.status-tag {
  display: inline-flex;
  min-height: 25px;
  align-items: center;
  gap: 6px;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 650;
}

.status-tag i {
  width: 6px;
  height: 6px;
  background: currentColor;
  border-radius: 50%;
}

.status-active {
  color: #13734f;
  background: #eaf8f1;
  border: 1px solid #a7e2c9;
}

.status-inactive {
  color: #6b7280;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
}

.row-actions {
  display: flex;
  justify-content: center;
  gap: 5px;
}

.row-actions button {
  display: inline-flex;
  width: 30px;
  height: 30px;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: #667085;
  background: #fff;
  border: 1px solid #d9e0e8;
  border-radius: 4px;
}

.row-actions button:hover {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.row-actions button:last-child:hover {
  color: #b4232f;
  background: #fff3f3;
  border-color: #efb5ba;
}

.row-actions svg {
  width: 15px;
  height: 15px;
}

.empty-cell {
  height: 290px !important;
  color: #98a3b2 !important;
  text-align: center;
}

.empty-cell strong,
.empty-cell span {
  display: block;
}

.empty-cell strong {
  margin-top: 11px;
  color: #4c586b;
  font-size: 14px;
}

.empty-cell span {
  margin-top: 5px;
  font-size: 12px;
}

.empty-mark {
  display: inline-flex;
  width: 48px;
  height: 48px;
  align-items: center;
  justify-content: center;
  color: #9aa6b6;
  background: #f1f4f7;
  border-radius: 50%;
}

.empty-mark svg {
  width: 24px;
  height: 24px;
}

.retry-button {
  margin-top: 14px;
}

.skeleton-row td span {
  display: block;
  width: 78%;
  height: 10px;
  background: linear-gradient(90deg, #edf1f5 25%, #f8fafc 50%, #edf1f5 75%);
  background-size: 200% 100%;
  border-radius: 3px;
  animation: skeleton 1.25s infinite linear;
}

@keyframes skeleton {
  to { background-position: -200% 0; }
}

.table-footer {
  display: flex;
  min-height: 58px;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 16px;
  color: var(--muted);
  border-top: 1px solid var(--border);
  font-size: 12px;
}

.table-footer strong {
  color: var(--text);
}

.pagination select,
.pagination button {
  height: 32px;
  padding: 0 8px;
  color: #526074;
  background: #fff;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  font-size: 12px;
}

.pagination button {
  display: inline-flex;
  width: 31px;
  align-items: center;
  justify-content: center;
}

.pagination button:hover:not(:disabled) {
  color: var(--accent-dark);
  border-color: var(--accent);
}

.pagination button:disabled {
  cursor: not-allowed;
  opacity: .4;
}

.pagination button svg {
  width: 14px;
  height: 14px;
}

.detail-modal-layer {
  position: fixed;
  z-index: 2147482000;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.detail-modal-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, .42);
}

.detail-modal {
  position: relative;
  display: flex;
  width: min(960px, calc(100vw - 48px));
  max-height: min(880px, calc(100vh - 48px));
  flex-direction: column;
  overflow: hidden;
  background: #f4f7f9;
  border: 1px solid #dfe5ec;
  border-radius: 8px;
  box-shadow: 0 24px 70px rgba(15, 23, 42, .24);
}

.create-modal {
  width: min(800px, calc(100vw - 48px));
}

.detail-modal-header,
.detail-modal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: #fff;
}

.detail-modal-header {
  min-height: 78px;
  padding: 14px 20px;
  border-bottom: 1px solid #dfe5ec;
}

.detail-modal-title-wrap {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 12px;
}

.detail-modal-mark {
  display: inline-flex;
  width: 40px;
  height: 40px;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-radius: 7px;
}

.detail-modal-mark svg {
  width: 21px;
  height: 21px;
}

.detail-modal-title-wrap > div {
  min-width: 0;
}

.detail-modal-title-wrap span:not(.detail-modal-mark) {
  color: #758195;
  font-size: 11px;
  font-weight: 600;
}

.detail-modal-title-wrap h2 {
  margin: 3px 0 0;
  overflow: hidden;
  color: var(--text);
  font-size: 18px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-modal-close {
  display: inline-flex;
  width: 34px;
  height: 34px;
  align-items: center;
  justify-content: center;
  color: #68758a;
  background: transparent;
  border: 0;
  border-radius: 5px;
}

.detail-modal-close:hover {
  background: #f0f3f6;
}

.detail-modal-close svg {
  width: 20px;
  height: 20px;
}

.detail-modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 18px;
}

.detail-modal-overview,
.detail-section,
.form-card {
  overflow: hidden;
  background: #fff;
  border: 1px solid #dfe5ec;
  border-radius: 7px;
}

.detail-modal-overview {
  padding: 17px;
}

.overview-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 14px;
  border-bottom: 1px solid #edf1f5;
}

.overview-head > span:last-child {
  color: #5e6a7e;
  font-size: 12px;
  font-weight: 600;
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px 22px;
  margin: 17px 0 0;
}

.meta-grid > div {
  min-width: 0;
}

.wide-meta {
  grid-column: 1 / -1;
}

.meta-grid dt {
  margin-bottom: 5px;
  color: #8a96a8;
  font-size: 11px;
}

.meta-grid dd {
  margin: 0;
  overflow: hidden;
  color: #283548;
  font-size: 13px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-section {
  margin-top: 15px;
}

.section-heading {
  min-height: 53px;
  padding: 17px 15px;
  border-bottom: 1px solid #e5eaf0;
}

.section-heading h3 {
  margin: 0;
  color: #263348;
  font-size: 14px;
}

.summary-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin: 15px;
  overflow: hidden;
  background: #f8fafb;
  border: 1px solid #e5eaf0;
  border-radius: 6px;
}

.summary-strip > div {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 5px;
  padding: 13px 15px;
  border-right: 1px solid #e5eaf0;
}

.summary-strip > div:last-child {
  border-right: 0;
}

.summary-strip span {
  color: #7a8698;
  font-size: 11px;
}

.summary-strip strong {
  overflow: hidden;
  color: #243145;
  font-size: 16px;
  font-variant-numeric: tabular-nums;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.finance-hint,
.remark-text {
  margin: 0 15px 15px;
  color: #7a8698;
  font-size: 12px;
}

.remark-text {
  color: #374151;
  line-height: 1.6;
  white-space: pre-wrap;
}

.detail-modal-footer {
  min-height: 68px;
  padding: 13px 18px;
  border-top: 1px solid #dfe5ec;
}

.party-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-highlight-section {
  padding: 18px;
  background: rgba(15, 159, 120, .06);
  border: 1px solid rgba(15, 159, 120, .2);
  border-radius: 8px;
}

.form-field-inline {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field-label-inline,
.field-label {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #475569;
  font-size: 12px;
  font-weight: 650;
}

.field-label-inline svg {
  width: 17px;
  height: 17px;
  color: var(--accent-dark);
}

em {
  color: #ef4444;
  font-style: normal;
}

.store-pill-group {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.store-pill {
  padding: 9px 16px;
  color: #334155;
  background: #fff;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
}

.store-pill.active {
  color: #fff;
  background: var(--accent);
  border-color: var(--accent);
}

.empty-hint {
  padding: 12px;
  color: #92400e;
  background: #fef3e7;
  border: 1px solid #f9d8a5;
  border-radius: 6px;
  font-size: 13px;
}

.form-card-header {
  padding: 15px 18px;
  background: #fafbfc;
  border-bottom: 1px solid #e5eaf0;
}

.form-card-header h4 {
  margin: 0;
  color: #1e293b;
  font-size: 14px;
}

.form-card-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px 18px;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.status-field {
  max-width: calc(50% - 8px);
}

.field-hint {
  color: #94a3b8;
  font-size: 11px;
  font-weight: 400;
}

.readonly-money {
  min-height: 38px;
  padding: 9px 11px;
  color: #ef4444;
  background: #fff8f8;
  border: 1px solid #f1c4c8;
  border-radius: 5px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.detail-modal-enter-active,
.detail-modal-leave-active {
  transition: opacity .2s ease;
}

.detail-modal-enter-active .detail-modal,
.detail-modal-leave-active .detail-modal {
  transition: transform .22s ease, opacity .2s ease;
}

.detail-modal-enter-from,
.detail-modal-leave-to {
  opacity: 0;
}

.detail-modal-enter-from .detail-modal,
.detail-modal-leave-to .detail-modal {
  opacity: 0;
  transform: translateY(12px) scale(.985);
}

@media (max-width: 900px) {
  .search-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .search-actions {
    justify-content: flex-end;
  }

  .records-toolbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .toolbar-actions {
    width: 100%;
    justify-content: flex-end;
  }
}

@media (max-width: 780px) {
  .search-grid,
  .form-row {
    grid-template-columns: 1fr;
  }

  .search-actions {
    justify-content: stretch;
  }

  .search-actions .button {
    flex: 1;
  }

  .table-footer {
    align-items: flex-start;
    flex-direction: column;
  }

  .pagination {
    width: 100%;
    justify-content: space-between;
  }

  .detail-modal-layer {
    padding: 0;
  }

  .detail-modal {
    width: 100vw;
    height: 100vh;
    max-height: 100vh;
    border-radius: 0;
  }

  .meta-grid {
    grid-template-columns: 1fr;
  }

  .wide-meta {
    grid-column: auto;
  }

  .summary-strip {
    grid-template-columns: 1fr;
  }

  .summary-strip > div {
    border-right: 0;
    border-bottom: 1px solid #e5eaf0;
  }

  .summary-strip > div:last-child {
    border-bottom: 0;
  }

  .status-field {
    max-width: none;
  }
}
</style>
