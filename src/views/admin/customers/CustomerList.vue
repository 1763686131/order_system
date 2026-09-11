<template>
  <div class="customer-list-page">
    <!-- 筛选工具栏 -->
    <section class="search-panel" aria-label="客户筛选">
      <form class="search-grid" @submit.prevent="handleSearch">
        <label class="field-group">
          <span>关键词搜索</span>
          <span class="input-with-icon">
            <svg aria-hidden="true" viewBox="0 0 24 24">
              <circle cx="11" cy="11" r="7"></circle>
              <path d="m20 20-3.7-3.7"></path>
            </svg>
            <input
              v-model="filters.keyword"
              type="search"
              placeholder="搜索客户名称、编号、联系人、电话..."
            />
          </span>
        </label>

        <div class="field-group">
          <span>客户状态</span>
          <select v-model="filters.status">
            <option value="">全部状态</option>
            <option value="active">活跃</option>
            <option value="inactive">不活跃</option>
          </select>
        </div>

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

    <!-- 客户记录面板 -->
    <section class="records-panel">
      <header class="records-toolbar">
        <div class="toolbar-filters">
          <!-- 门店筛选滑块 -->
          <div class="material-type-slider" role="tablist" aria-label="门店筛选">
            <button
              :class="['slider-tab', { active: filters.storeId === null }]"
              type="button"
              @click="filters.storeId = null"
            >
              全部
            </button>
            <button
              v-for="store in allStores"
              :key="store.id"
              :class="['slider-tab', { active: filters.storeId === store.id }]"
              type="button"
              @click="filters.storeId = store.id"
            >
              {{ store.name }}
            </button>
          </div>
        </div>

        <div class="toolbar-actions">
          <button
            class="icon-button refresh-button"
            type="button"
            title="刷新列表"
            :disabled="loading"
            @click="loadCustomers"
          >
            <svg :class="{ spinning: loading }" aria-hidden="true" viewBox="0 0 24 24">
              <path d="M20 11a8.1 8.1 0 0 0-14.9-4L3 10"></path>
              <path d="M3 4v6h6"></path>
              <path d="M4 13a8.1 8.1 0 0 0 14.9 4L21 14"></path>
              <path d="M15 14h6v6"></path>
            </svg>
          </button>
          <button
            class="button button-export"
            type="button"
            title="导出Excel"
            @click="handleExport"
          >
            <svg aria-hidden="true" viewBox="0 0 24 24">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
            导出 Excel
          </button>
          <button
            class="button button-primary create-button"
            type="button"
            @click="handleAdd"
          >
            <svg aria-hidden="true" viewBox="0 0 24 24">
              <path d="M12 5v14"></path>
              <path d="M5 12h14"></path>
            </svg>
            新增客户
          </button>
        </div>
      </header>

      <div class="table-scroll">
        <table class="records-table">
          <thead>
            <tr>
              <th class="document-column">客户编号</th>
              <th>客户名称</th>
              <th>所属门店</th>
              <th>联系人</th>
              <th>联系电话</th>
              <th class="address-column">联系地址</th>
              <th class="number-column">储值余额</th>
              <th class="number-column">应收欠款</th>
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
            <tr v-else-if="filteredCustomers.length === 0">
              <td colspan="11" class="empty-cell">
                <div class="empty-mark" aria-hidden="true">
                  <svg viewBox="0 0 24 24">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                    <circle cx="9" cy="7" r="4"></circle>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"></path>
                  </svg>
                </div>
                <strong>暂无客户数据</strong>
                <span>调整筛选条件后重新查询</span>
              </td>
            </tr>
            <tr
              v-for="customer in paginatedCustomers"
              v-else
              :key="customer.id"
              class="record-row"
              tabindex="0"
              @click="handleView(customer)"
              @keydown.enter.self.prevent="handleView(customer)"
            >
              <td>
                <button class="document-link" type="button" @click.stop="handleView(customer)">
                  {{ customer.customerCode }}
                  <svg aria-hidden="true" viewBox="0 0 24 24">
                    <path d="m9 18 6-6-6-6"></path>
                  </svg>
                </button>
              </td>
              <td class="customer-name">{{ customer.customerName }}</td>
              <td class="date-cell">{{ customer.storeName }}</td>
              <td class="party-cell">{{ customer.contactPerson || '-' }}</td>
              <td>{{ customer.phone || '-' }}</td>
              <td class="address-cell" :title="customer.address">
                {{ truncateText(customer.address, 15) }}
              </td>
              <td class="number-column numeric money-value balance-amount">
                ¥{{ formatAmount(customer.balance) }}
              </td>
              <td class="number-column numeric money-value" :class="{ 'debt-amount': customer.receivable > 0 }">
                ¥{{ formatAmount(customer.receivable) }}
              </td>
              <td>
                <span :class="['status-tag', customer.status === 'active' ? 'status-active' : 'status-inactive']">
                  <i aria-hidden="true"></i>
                  {{ customer.status === 'active' ? '活跃' : '不活跃' }}
                </span>
              </td>
              <td class="date-cell">{{ formatDate(customer.createdAt) }}</td>
              <td class="operation-column" @click.stop>
                <div class="row-actions">
                  <button
                    type="button"
                    title="编辑"
                    @click="handleEdit(customer)"
                  >
                    <svg aria-hidden="true" viewBox="0 0 24 24">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                  </button>
                  <button
                    type="button"
                    title="删除"
                    @click="handleDelete(customer)"
                  >
                    <svg aria-hidden="true" viewBox="0 0 24 24">
                      <path d="M3 6h18"></path>
                      <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
                      <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
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
          共 <strong>{{ filteredCustomers.length }}</strong> 条记录
          <template v-if="filteredCustomers.length">，当前 {{ pageStart }}-{{ pageEnd }} 条</template>
        </span>
        <div class="pagination" aria-label="分页">
          <select v-model.number="pageSize" aria-label="每页条数">
            <option :value="20">20 条 / 页</option>
            <option :value="50">50 条 / 页</option>
            <option :value="99999">全部</option>
          </select>
          <button
            type="button"
            title="上一页"
            :disabled="currentPage <= 1"
            @click="currentPage--"
          >
            <svg aria-hidden="true" viewBox="0 0 24 24"><path d="m15 18-6-6 6-6"></path></svg>
          </button>
          <span>{{ currentPage }} / {{ totalPages }}</span>
          <button
            type="button"
            title="下一页"
            :disabled="currentPage >= totalPages"
            @click="currentPage++"
          >
            <svg aria-hidden="true" viewBox="0 0 24 24"><path d="m9 18 6-6-6-6"></path></svg>
          </button>
        </div>
      </footer>
    </section>

    <!-- 客户详情弹窗 -->
    <Teleport to="body">
      <Transition name="detail-modal">
        <div v-if="showDetailModal && selectedCustomer" class="detail-modal-layer">
          <div class="detail-modal-backdrop" @click="closeDetailModal"></div>
          <section
            class="detail-modal"
            role="dialog"
            aria-modal="true"
            aria-label="客户详情"
            tabindex="-1"
            @keydown.esc="closeDetailModal"
          >
            <header class="detail-modal-header">
              <div class="detail-modal-title-wrap">
                <span class="detail-modal-mark" aria-hidden="true">
                  <svg viewBox="0 0 24 24">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                    <circle cx="9" cy="7" r="4"></circle>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"></path>
                  </svg>
                </span>
                <div>
                  <span>客户详情</span>
                  <h2>{{ selectedCustomer.customerName }}</h2>
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
                  <span :class="['status-tag', selectedCustomer.status === 'active' ? 'status-active' : 'status-inactive']">
                    <i aria-hidden="true"></i>
                    {{ selectedCustomer.status === 'active' ? '活跃' : '不活跃' }}
                  </span>
                  <span>{{ selectedCustomer.storeName }}</span>
                </div>
                <dl class="meta-grid">
                  <div>
                    <dt>客户编号</dt>
                    <dd>{{ selectedCustomer.customerCode }}</dd>
                  </div>
                  <div>
                    <dt>客户名称</dt>
                    <dd>{{ selectedCustomer.customerName }}</dd>
                  </div>
                  <div>
                    <dt>联系人</dt>
                    <dd>{{ selectedCustomer.contactPerson || '-' }}</dd>
                  </div>
                  <div>
                    <dt>联系电话</dt>
                    <dd>{{ selectedCustomer.phone || '-' }}</dd>
                  </div>
                  <div>
                    <dt>联系地址</dt>
                    <dd>{{ selectedCustomer.address || '-' }}</dd>
                  </div>
                  <div>
                    <dt>创建时间</dt>
                    <dd>{{ formatDate(selectedCustomer.createdAt) }}</dd>
                  </div>
                </dl>
              </section>

              <!-- 财务信息 -->
              <section class="detail-section">
                <div class="section-heading">
                  <div>
                    <h3>财务信息</h3>
                  </div>
                </div>
                <div class="summary-strip financial-summary-strip">
                  <div>
                    <span>储值余额</span>
                    <strong class="balance-amount">¥{{ formatAmount(selectedCustomer.balance) }}</strong>
                  </div>
                  <div>
                    <span>期初欠款</span>
                    <strong>¥{{ formatAmount(selectedCustomer.initialReceivable || 0) }}</strong>
                  </div>
                  <div>
                    <span>应收欠款</span>
                    <strong :class="{ 'debt-amount': selectedCustomer.receivable > 0 }">
                      ¥{{ formatAmount(selectedCustomer.receivable) }}
                    </strong>
                  </div>
                </div>
              </section>

              <!-- 银行信息 -->
              <section v-if="selectedCustomer.bankName || selectedCustomer.bankAccount" class="detail-section">
                <div class="section-heading">
                  <div>
                    <h3>银行信息</h3>
                  </div>
                </div>
                <dl class="meta-grid">
                  <div v-if="selectedCustomer.bankName">
                    <dt>开户行</dt>
                    <dd>{{ selectedCustomer.bankName }}</dd>
                  </div>
                  <div v-if="selectedCustomer.bankAccount">
                    <dt>银行账号</dt>
                    <dd>{{ selectedCustomer.bankAccount }}</dd>
                  </div>
                  <div v-if="selectedCustomer.bankCode">
                    <dt>行号</dt>
                    <dd>{{ selectedCustomer.bankCode }}</dd>
                  </div>
                  <div v-if="selectedCustomer.taxNumber">
                    <dt>税号</dt>
                    <dd>{{ selectedCustomer.taxNumber }}</dd>
                  </div>
                </dl>
              </section>

              <!-- 备注信息 -->
              <section v-if="selectedCustomer.remark" class="detail-section">
                <div class="section-heading">
                  <div>
                    <h3>备注信息</h3>
                  </div>
                </div>
                <div style="padding: 15px;">
                  <p style="margin: 0; color: #374151; line-height: 1.6;">{{ selectedCustomer.remark }}</p>
                </div>
              </section>
            </div>

            <footer class="detail-modal-footer">
              <div class="detail-modal-left-actions">
                <button
                  class="button button-danger-light"
                  type="button"
                  @click="handleDelete(selectedCustomer)"
                >
                  删除
                </button>
              </div>
              <div class="detail-modal-actions">
                <button
                  class="button button-edit"
                  type="button"
                  @click="handleEdit(selectedCustomer)"
                >
                  编辑
                </button>
                <button
                  class="button button-secondary"
                  type="button"
                  @click="closeDetailModal"
                >
                  关闭
                </button>
              </div>
            </footer>
          </section>
        </div>
      </Transition>
    </Teleport>

    <!-- 编辑/新增弹窗 -->
    <Teleport to="body">
      <Transition name="detail-modal">
        <div v-if="showEditModal" class="detail-modal-layer">
          <div class="detail-modal-backdrop" @click="closeEditModal"></div>
          <section
            class="detail-modal create-modal"
            role="dialog"
            aria-modal="true"
            :aria-label="isEditMode ? '编辑客户' : '新增客户'"
            tabindex="-1"
            @keydown.esc="closeEditModal"
          >
            <header class="detail-modal-header">
              <div class="detail-modal-title-wrap">
                <span class="detail-modal-mark" aria-hidden="true">
                  <svg viewBox="0 0 24 24">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                    <circle cx="9" cy="7" r="4"></circle>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"></path>
                  </svg>
                </span>
                <div>
                  <span>客户管理</span>
                  <h2>{{ isEditMode ? '编辑客户' : '新增客户' }}</h2>
                </div>
              </div>
              <button class="detail-modal-close" type="button" title="关闭" @click="closeEditModal">
                <svg aria-hidden="true" viewBox="0 0 24 24">
                  <path d="m6 6 12 12M18 6 6 18"></path>
                </svg>
              </button>
            </header>

            <div class="detail-modal-body">
              <form class="customer-form" @submit.prevent="handleSubmit">
                <!-- 所属门店（突出显示） -->
                <section class="form-highlight-section">
                  <label class="form-field-inline">
                    <span class="field-label-inline">
                      <svg aria-hidden="true" viewBox="0 0 24 24">
                        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                        <polyline points="9 22 9 12 15 12 15 22"></polyline>
                      </svg>
                      所属门店 <em>*</em>
                    </span>
                    <div v-if="allStores.length > 0" class="store-pill-group">
                      <button
                        v-for="store in allStores"
                        :key="store.id"
                        type="button"
                        :class="['store-pill', { active: formData.storeId === store.id }]"
                        @click="formData.storeId = store.id"
                      >
                        {{ store.name }}
                      </button>
                    </div>
                    <div v-else class="empty-hint">
                      <svg aria-hidden="true" viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="12" y1="8" x2="12" y2="12"></line>
                        <line x1="12" y1="16" x2="12.01" y2="16"></line>
                      </svg>
                      暂无门店数据，请先添加门店
                    </div>
                  </label>
                </section>

                <!-- 基本信息 -->
                <section class="form-card">
                  <div class="form-card-header">
                    <svg aria-hidden="true" viewBox="0 0 24 24">
                      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
                      <circle cx="9" cy="7" r="4"></circle>
                      <line x1="19" y1="8" x2="19" y2="14"></line>
                      <line x1="22" y1="11" x2="16" y2="11"></line>
                    </svg>
                    <h4>基本信息</h4>
                  </div>
                  <div class="form-card-body">
                    <div class="form-row">
                      <label class="form-field">
                        <span class="field-label">客户名称 <em>*</em></span>
                        <input
                          v-model="formData.customerName"
                          type="text"
                          placeholder="请输入客户名称"
                          required
                        />
                      </label>

                      <label class="form-field">
                        <span class="field-label">客户编号 <em>*</em></span>
                        <input
                          v-model="formData.customerCode"
                          type="text"
                          placeholder="请输入客户编号"
                          required
                        />
                      </label>
                    </div>

                    <div class="form-row">
                      <label class="form-field">
                        <span class="field-label">联系人</span>
                        <input
                          v-model="formData.contactPerson"
                          type="text"
                          placeholder="请输入联系人姓名"
                        />
                      </label>

                      <label class="form-field">
                        <span class="field-label">联系电话</span>
                        <input
                          v-model="formData.phone"
                          type="tel"
                          placeholder="请输入联系电话"
                        />
                      </label>
                    </div>

                    <label class="form-field">
                      <span class="field-label">联系地址</span>
                      <textarea
                        v-model="formData.address"
                        rows="2"
                        placeholder="请输入详细联系地址"
                      ></textarea>
                    </label>
                  </div>
                </section>

                <!-- 财务信息 -->
                <section class="form-card">
                  <div class="form-card-header">
                    <svg aria-hidden="true" viewBox="0 0 24 24">
                      <line x1="12" y1="1" x2="12" y2="23"></line>
                      <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
                    </svg>
                    <h4>财务信息</h4>
                  </div>
                  <div class="form-card-body">
                    <div class="form-row">
                      <label class="form-field">
                        <span class="field-label">
                          <svg aria-hidden="true" viewBox="0 0 24 24" style="width: 14px; height: 14px;">
                            <circle cx="12" cy="12" r="10"></circle>
                            <path d="M12 6v6l4 2"></path>
                          </svg>
                          储值余额
                        </span>
                        <div class="input-with-prefix">
                          <span class="input-prefix">¥</span>
                          <input
                            v-model.number="formData.balance"
                            type="number"
                            step="0.01"
                            placeholder="0.00"
                          />
                        </div>
                      </label>

                      <label class="form-field">
                        <span class="field-label">
                          <svg aria-hidden="true" viewBox="0 0 24 24" style="width: 14px; height: 14px;">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16c0 1.1.9 2 2 2h12a2 2 0 0 0 2-2V8l-6-6z"></path>
                            <path d="M14 3v5h5M16 13H8M16 17H8M10 9H8"></path>
                          </svg>
                          期初欠款
                        </span>
                        <div class="input-with-prefix">
                          <span class="input-prefix">¥</span>
                          <input
                            v-model.number="formData.initialDebt"
                            type="number"
                            step="0.01"
                            placeholder="0.00"
                          />
                        </div>
                      </label>
                    </div>

                    <div class="form-row">
                      <label class="form-field">
                        <span class="field-label">开户行</span>
                        <input
                          v-model="formData.bankName"
                          type="text"
                          placeholder="如：中国工商银行"
                        />
                      </label>

                      <label class="form-field">
                        <span class="field-label">银行账号</span>
                        <input
                          v-model="formData.bankAccount"
                          type="text"
                          placeholder="请输入银行账号"
                        />
                      </label>
                    </div>

                    <div class="form-row">
                      <label class="form-field">
                        <span class="field-label">行号</span>
                        <input
                          v-model="formData.bankCode"
                          type="text"
                          placeholder="请输入银行行号"
                        />
                      </label>

                      <label class="form-field">
                        <span class="field-label">税号</span>
                        <input
                          v-model="formData.taxNumber"
                          type="text"
                          placeholder="请输入纳税人识别号"
                        />
                      </label>
                    </div>

                    <label class="form-field">
                      <span class="field-label">备注信息</span>
                      <textarea
                        v-model="formData.remark"
                        rows="3"
                        placeholder="可输入其他补充说明信息..."
                      ></textarea>
                    </label>
                  </div>
                </section>
              </form>
            </div>

            <footer class="detail-modal-footer">
              <div class="detail-modal-left-actions"></div>
              <div class="detail-modal-actions">
                <button
                  class="button button-secondary"
                  type="button"
                  @click="closeEditModal"
                >
                  取消
                </button>
                <button
                  class="button button-primary"
                  type="button"
                  :disabled="submitting"
                  @click="handleSubmit"
                >
                  {{ submitting ? '提交中...' : (isEditMode ? '保存' : '创建') }}
                </button>
              </div>
            </footer>
          </section>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import request from '@/api/request'

// 数据状态
const loading = ref(false)
const customers = ref([])
const allStores = ref([])

// 筛选条件
const filters = ref({
  keyword: '',
  storeId: null,
  status: ''
})

// 弹窗状态
const showDetailModal = ref(false)
const showEditModal = ref(false)
const isEditMode = ref(false)
const selectedCustomer = ref(null)
const submitting = ref(false)

// 分页
const currentPage = ref(1)
const pageSize = ref(20)

// 表单数据
const formData = ref({
  customerName: '',
  customerCode: '',
  storeId: '',
  contactPerson: '',
  phone: '',
  address: '',
  balance: 0,
  initialDebt: 0,
  bankName: '',
  bankAccount: '',
  bankCode: '',
  taxNumber: '',
  remark: ''
})

// 计算属性
const filteredCustomers = computed(() => {
  let result = [...customers.value]

  // 关键词搜索
  if (filters.value.keyword) {
    const keyword = filters.value.keyword.toLowerCase()
    result = result.filter(customer =>
      customer.customerName?.toLowerCase().includes(keyword) ||
      customer.customerCode?.toLowerCase().includes(keyword) ||
      customer.contactPerson?.toLowerCase().includes(keyword) ||
      customer.phone?.toLowerCase().includes(keyword)
    )
  }

  // 门店筛选
  if (filters.value.storeId !== null) {
    result = result.filter(customer => customer.storeId === filters.value.storeId)
  }

  // 状态筛选
  if (filters.value.status) {
    result = result.filter(customer => customer.status === filters.value.status)
  }

  return result
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredCustomers.value.length / pageSize.value)))

const paginatedCustomers = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredCustomers.value.slice(start, end)
})

const pageStart = computed(() => filteredCustomers.value.length ? (currentPage.value - 1) * pageSize.value + 1 : 0)
const pageEnd = computed(() => Math.min(currentPage.value * pageSize.value, filteredCustomers.value.length))

// 方法
const loadStores = async () => {
  try {
    const response = await request({
      url: '/stores',
      method: 'GET'
    })
    if (response && Array.isArray(response)) {
      allStores.value = response.filter(store => store.status === 'active')
    }
  } catch (error) {
    console.error('加载门店失败:', error)
  }
}

const loadCustomers = async () => {
  loading.value = true
  try {
    const response = await request({
      url: '/customers',
      method: 'GET'
    })

    if (response && Array.isArray(response)) {
      customers.value = response.map(customer => {
        const store = allStores.value.find(s => s.id === customer.storeId)
        return {
          ...customer,
          storeName: store ? store.name : '未知门店'
        }
      })
    }
  } catch (error) {
    console.error('加载客户列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
}

const handleReset = () => {
  filters.value = {
    keyword: '',
    storeId: null,
    status: ''
  }
  currentPage.value = 1
}

const handleAdd = () => {
  isEditMode.value = false
  formData.value = {
    customerName: '',
    customerCode: '',
    storeId: allStores.value.length > 0 ? allStores.value[0].id : '',
    contactPerson: '',
    phone: '',
    address: '',
    balance: 0,
    initialDebt: 0,
    bankName: '',
    bankAccount: '',
    bankCode: '',
    taxNumber: '',
    remark: ''
  }
  showEditModal.value = true
}

const handleView = (customer) => {
  selectedCustomer.value = customer
  showDetailModal.value = true
}

const handleEdit = (customer) => {
  isEditMode.value = true
  selectedCustomer.value = customer
  formData.value = {
    customerName: customer.customerName,
    customerCode: customer.customerCode,
    storeId: customer.storeId,
    contactPerson: customer.contactPerson || '',
    phone: customer.phone || '',
    address: customer.address || '',
    balance: customer.balance || 0,
    initialDebt: customer.initialReceivable || customer.receivable || 0,
    bankName: customer.bankName || '',
    bankAccount: customer.bankAccount || '',
    bankCode: customer.bankCode || '',
    taxNumber: customer.taxNumber || '',
    remark: customer.remark || ''
  }
  closeDetailModal()
  showEditModal.value = true
}

const handleDelete = async (customer) => {
  if (!confirm(`确定要删除客户"${customer.customerName}"吗？`)) return

  try {
    await request({
      url: `/customers/${customer.id}`,
      method: 'DELETE'
    })
    alert('删除成功')
    closeDetailModal()
    await loadCustomers()
  } catch (error) {
    console.error('删除失败:', error)
    alert('删除失败：' + (error.response?.data?.error || error.message))
  }
}

const handleSubmit = async () => {
  if (!formData.value.customerName || !formData.value.customerCode || !formData.value.storeId) {
    alert('请填写必填项')
    return
  }

  submitting.value = true
  try {
    if (isEditMode.value) {
      await request({
        url: `/customers/${selectedCustomer.value.id}`,
        method: 'PUT',
        data: formData.value
      })
      alert('保存成功')
    } else {
      await request({
        url: '/customers',
        method: 'POST',
        data: formData.value
      })
      alert('创建成功')
    }
    closeEditModal()
    await loadCustomers()
  } catch (error) {
    console.error('保存失败:', error)
    alert(error.response?.data?.error || '保存失败')
  } finally {
    submitting.value = false
  }
}

const closeDetailModal = () => {
  showDetailModal.value = false
  selectedCustomer.value = null
}

const closeEditModal = () => {
  showEditModal.value = false
  isEditMode.value = false
  selectedCustomer.value = null
}

const handleExport = () => {
  alert('导出功能待实现')
}

const formatAmount = (amount) => {
  return amount ? amount.toFixed(2) : '0.00'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

const truncateText = (text, length) => {
  if (!text) return '-'
  if (text.length <= length) return text
  return text.substring(0, length) + '...'
}

onMounted(async () => {
  await loadStores()
  await loadCustomers()
})
</script>

<style scoped>
.customer-list-page {
  --accent: #0f9f78;
  --accent-rgb: 15, 159, 120;
  --accent-dark: #08745a;
  --accent-soft: #e9f8f3;
  --accent-border: #a9e5d2;
  --page-bg: #f4f8f5;
  --panel-bg: #ffffff;
  --border: #e2e8f0;
  --border-strong: #cbd5e1;
  --text: #172033;
  --text-secondary: #596579;
  --text-muted: #8a96a8;
  min-width: 0;
  min-height: calc(100vh - 100px);
  color: var(--text);
  background: var(--page-bg);
  font-size: 14px;
}

* {
  box-sizing: border-box;
}

button,
input,
select,
textarea {
  font: inherit;
}

button:focus-visible,
input:focus-visible,
select:focus-visible,
textarea:focus-visible,
.record-row:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

svg {
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

/* 搜索面板 */
.search-panel {
  padding: 18px 20px;
  background: var(--panel-bg);
  border: 1px solid var(--border);
  border-radius: 7px;
  box-shadow: 0 2px 10px rgba(15, 23, 42, 0.035);
}

.search-grid {
  display: grid;
  grid-template-columns: minmax(200px, 1fr) minmax(160px, 0.8fr) auto;
  gap: 14px;
  align-items: end;
}

.field-group {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 7px;
}

.field-group > span:first-child {
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
}

.field-group input,
.field-group select {
  width: 100%;
  height: 38px;
  color: var(--text);
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  padding: 0 11px;
  outline: none;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.field-group input::placeholder {
  color: #a2adba;
}

.field-group input:focus,
.field-group select:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.12);
}

.input-with-icon {
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
  color: var(--text-muted);
}

.input-with-icon input {
  padding-left: 35px;
}

.search-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.button {
  display: inline-flex;
  height: 38px;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 0 15px;
  border: 1px solid transparent;
  border-radius: 5px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  transition: background 0.18s ease, border-color 0.18s ease, color 0.18s ease, box-shadow 0.18s ease;
}

.button svg {
  width: 16px;
  height: 16px;
}

.button:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.button-primary {
  color: #ffffff;
  background: #08745a;
  border-color: var(--accent);
  box-shadow: 0 2px 5px rgba(var(--accent-rgb), 0.18);
  font-weight: 700;
}

.button-primary:hover:not(:disabled) {
  background: #08745a;
  border-color: var(--accent-dark);
}

.button-secondary {
  color: #445066;
  background: #fff;
  border-color: var(--border-strong);
}

.button-secondary:hover:not(:disabled) {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.button-export {
  color: #374151;
  background: #fff;
  border-color: #d1d5db;
}

.button-export:hover:not(:disabled) {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.button-edit {
  color: #fff;
  background: #2563eb;
  border-color: #2563eb;
  box-shadow: 0 2px 5px rgba(37, 99, 235, 0.2);
}

.button-edit:hover:not(:disabled) {
  background: #1d4ed8;
  border-color: #1d4ed8;
}

.button-danger-light {
  color: #b4232f;
  background: #fff;
  border-color: #efb5ba;
}

.button-danger-light:hover:not(:disabled) {
  color: #fff;
  background: #dc3545;
  border-color: #c92f3e;
}

/* 记录面板 */
.records-panel {
  margin-top: 14px;
  overflow: hidden;
  background: var(--panel-bg);
  border: 1px solid var(--border);
  border-radius: 7px;
  box-shadow: 0 3px 14px rgba(15, 23, 42, 0.045);
}

.records-toolbar {
  display: flex;
  min-height: 62px;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 11px 16px;
  border-bottom: 1px solid var(--border);
}

.toolbar-filters {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 10px;
}

.material-type-slider {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px;
  background: #f1f5f9;
  border-radius: 8px;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.08);
}

.slider-tab {
  display: inline-flex;
  height: 36px;
  align-items: center;
  gap: 7px;
  padding: 0 16px;
  color: var(--text-secondary);
  background: transparent;
  border: 0;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.2s ease;
}

.slider-tab:hover {
  color: var(--accent-dark);
  background: rgba(var(--accent-rgb), 0.1);
}

.slider-tab.active {
  color: #fff;
  background: var(--accent);
  box-shadow: 0 2px 6px rgba(var(--accent-rgb), 0.3);
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
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
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  cursor: pointer;
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
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 表格 */
.table-scroll {
  overflow-x: auto;
}

.records-table {
  width: 100%;
  min-width: 1400px;
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
  vertical-align: middle;
}

.records-table td {
  height: 57px;
  padding: 9px 12px;
  overflow: hidden;
  color: #344054;
  border-bottom: 1px solid #edf1f5;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: middle;
}

.records-table tbody tr:last-child td {
  border-bottom: 0;
}

.record-row {
  cursor: pointer;
  transition: background 0.15s ease;
}

.record-row:hover {
  background: rgba(var(--accent-rgb), 0.08);
}

.document-column { width: 140px; }
.address-column { width: 160px; }
.number-column { width: 110px; text-align: right !important; }
.operation-column { width: 100px; text-align: center; }

.numeric,
.money-value {
  font-variant-numeric: tabular-nums;
}

.money-value {
  color: #182230 !important;
  font-weight: 750;
}

.balance-amount {
  color: #0891b2 !important;
}

.debt-amount {
  color: #ef4444 !important;
}

.document-link {
  display: inline-flex;
  max-width: 100%;
  align-items: center;
  gap: 4px;
  overflow: hidden;
  padding: 3px 0;
  color: var(--accent-dark);
  background: transparent;
  border: 0;
  cursor: pointer;
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

.customer-name {
  color: #283548;
  font-weight: 600;
}

.date-cell,
.party-cell,
.address-cell {
  color: var(--text-secondary);
  font-size: 13px;
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
  white-space: nowrap;
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
  gap: 6px;
}

.row-actions button {
  display: inline-flex;
  width: 29px;
  height: 29px;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: #667085;
  background: #fff;
  border: 1px solid #d9e0e8;
  border-radius: 4px;
  cursor: pointer;
}

.row-actions button:hover:not(:disabled) {
  color: var(--accent-dark);
  background: var(--accent-soft);
  border-color: var(--accent-border);
}

.row-actions svg {
  width: 14px;
  height: 14px;
}

.empty-cell {
  height: 290px !important;
  color: var(--text-muted) !important;
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

/* 页脚 */
.table-footer {
  display: flex;
  min-height: 58px;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  color: var(--text-secondary);
  background: #fff;
  border-top: 1px solid var(--border);
  font-size: 12px;
}

.table-footer strong {
  color: var(--text);
  font-variant-numeric: tabular-nums;
}

.pagination {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pagination select {
  width: 103px;
  height: 32px;
  padding: 0 8px;
  color: var(--text-secondary);
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  font-size: 12px;
  outline: none;
}

.pagination button {
  display: inline-flex;
  width: 31px;
  height: 31px;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: #526074;
  background: #fff;
  border: 1px solid var(--border-strong);
  border-radius: 4px;
  cursor: pointer;
}

.pagination button:hover:not(:disabled) {
  color: var(--accent-dark);
  border-color: var(--accent);
}

.pagination button:disabled {
  cursor: not-allowed;
  opacity: 0.4;
}

.pagination button svg {
  width: 14px;
  height: 14px;
}

.pagination > span {
  min-width: 50px;
  text-align: center;
  font-variant-numeric: tabular-nums;
}

/* 弹窗 */
.detail-modal-layer {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  z-index: 2147482000;
}

.detail-modal-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.42);
  backdrop-filter: blur(1px);
}

.detail-modal {
  position: relative;
  display: flex;
  width: min(960px, calc(100vw - 48px));
  max-height: min(880px, calc(100vh - 48px));
  flex-direction: column;
  overflow: hidden;
  color: #172033;
  background: #f4f7f9;
  border: 1px solid #dfe5ec;
  border-radius: 8px;
  box-shadow: 0 24px 70px rgba(15, 23, 42, 0.24);
  outline: none;
}

.create-modal {
  width: min(800px, calc(100vw - 48px));
}

.detail-modal-header {
  display: flex;
  min-height: 78px;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 14px 20px;
  background: #fff;
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
  color: #172033;
  font-size: 18px;
  letter-spacing: 0;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-modal-close {
  display: inline-flex;
  width: 34px;
  height: 34px;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  color: #68758a;
  background: transparent;
  border: 0;
  border-radius: 5px;
  cursor: pointer;
}

.detail-modal-close:hover {
  color: #273245;
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
.detail-section {
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
  margin: 17px 0;
}

.meta-grid > div {
  min-width: 0;
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

.summary-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
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

.financial-summary-strip {
  margin: 15px;
}

.detail-section {
  margin-top: 15px;
  overflow: hidden;
}

.section-heading {
  display: flex;
  min-height: 53px;
  align-items: center;
  justify-content: space-between;
  padding: 11px 15px;
  border-bottom: 1px solid #e5eaf0;
}

.section-heading > div {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.section-heading h3 {
  margin: 0;
  color: #263348;
  font-size: 14px;
  letter-spacing: 0;
}

.detail-modal-footer {
  display: flex;
  min-height: 68px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 13px 18px;
  background: #fff;
  border-top: 1px solid #dfe5ec;
}

.detail-modal-left-actions,
.detail-modal-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.detail-modal-actions {
  justify-content: flex-end;
  margin-left: auto;
}

/* 表单样式 */
.customer-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 突出显示区域（门店选择） */
.form-highlight-section {
  background: linear-gradient(135deg, rgba(var(--accent-rgb), 0.08) 0%, rgba(var(--accent-rgb), 0.02) 100%);
  border: 1px solid rgba(var(--accent-rgb), 0.2);
  border-radius: 8px;
  padding: 18px;
}

.form-field-inline {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field-label-inline {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text);
  font-size: 13px;
  font-weight: 650;
}

.field-label-inline svg {
  width: 17px;
  height: 17px;
  color: var(--accent-dark);
}

.field-label-inline em {
  color: #ef4444;
  font-style: normal;
  margin-left: -2px;
}

.store-pill-group {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.store-pill {
  padding: 10px 20px;
  background: #ffffff;
  border: 1.5px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #334155;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
}

.store-pill:hover {
  background: #ffffff;
  border-color: var(--accent);
  color: var(--accent-dark);
  transform: translateY(-1px);
  box-shadow: 0 3px 8px rgba(var(--accent-rgb), 0.2);
}

.store-pill.active {
  background: #08745a;
  color: #ffffff;
  border-color: var(--accent);
  box-shadow: 0 3px 10px rgba(var(--accent-rgb), 0.35);
  font-weight: 700;
}

/* 表单卡片 */
.form-card {
  background: #fff;
  border: 1px solid #dfe5ec;
  border-radius: 8px;
  overflow: hidden;
}

.form-card-header {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 15px 18px;
  background: linear-gradient(to bottom, #fafbfc 0%, #f8fafb 100%);
  border-bottom: 1px solid #e5eaf0;
}

.form-card-header svg {
  width: 18px;
  height: 18px;
  color: var(--accent-dark);
}

.form-card-header h4 {
  margin: 0;
  color: #1e293b;
  font-size: 14px;
  font-weight: 650;
  letter-spacing: 0;
}

.form-card-body {
  padding: 20px 18px;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.form-row:last-child {
  margin-bottom: 0;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-label {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #475569;
  font-size: 12px;
  font-weight: 600;
}

.field-label svg {
  flex-shrink: 0;
}

.field-label em {
  color: #ef4444;
  font-style: normal;
  margin-left: -2px;
}

.form-field input,
.form-field select,
.form-field textarea {
  width: 100%;
  min-height: 40px;
  color: var(--text);
  background: #fff;
  border: 1.5px solid #cbd5e1;
  border-radius: 6px;
  padding: 10px 12px;
  outline: none;
  transition: all 0.2s ease;
  font-size: 14px;
}

.form-field input::placeholder,
.form-field textarea::placeholder {
  color: #94a3b8;
}

.form-field textarea {
  resize: vertical;
  font-family: inherit;
  line-height: 1.6;
  min-height: 44px;
}

.form-field input:focus,
.form-field select:focus,
.form-field textarea:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.12);
  background: #fefffe;
}

/* 带前缀的输入框 */
.input-with-prefix {
  position: relative;
  display: flex;
  align-items: center;
}

.input-prefix {
  position: absolute;
  left: 12px;
  color: #64748b;
  font-size: 14px;
  font-weight: 600;
  pointer-events: none;
  z-index: 1;
}

.input-with-prefix input {
  padding-left: 28px;
  font-variant-numeric: tabular-nums;
}

.empty-hint {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  background: #fef3e7;
  border: 1.5px solid #f9d8a5;
  border-radius: 7px;
  font-size: 13px;
  color: #92400e;
}

.empty-hint svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  color: #d97706;
}

.store-selector {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  padding: 4px 0;
}

.store-option {
  padding: 8px 16px;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 14px;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.3s;
  white-space: nowrap;
}

.store-option:hover {
  background: #e5e7eb;
  border-color: #d1d5db;
}

.store-option.active {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}

.detail-modal-enter-active,
.detail-modal-leave-active {
  transition: opacity 0.2s ease;
}

.detail-modal-enter-active .detail-modal,
.detail-modal-leave-active .detail-modal {
  transition: transform 0.22s ease, opacity 0.2s ease;
}

.detail-modal-enter-from,
.detail-modal-leave-to {
  opacity: 0;
}

.detail-modal-enter-from .detail-modal,
.detail-modal-leave-to .detail-modal {
  opacity: 0;
  transform: translateY(12px) scale(0.985);
}

@media (max-width: 1280px) {
  .search-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .form-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 780px) {
  .search-grid {
    grid-template-columns: 1fr;
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

  .detail-modal-footer {
    flex-wrap: wrap;
  }

  .store-pill-group {
    flex-direction: column;
  }

  .store-pill {
    width: 100%;
    text-align: center;
  }
}
</style>
