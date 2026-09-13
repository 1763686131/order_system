<template>
  <div class="settings-page">
    <!-- 搜索面板 - 可选，这里用作页面说明 -->
    <div class="search-panel">
      <div class="panel-header">
        <h3 class="panel-title">系统配置中心</h3>
        <p class="panel-desc">管理系统路径、消息通知、业务规则等全局配置项</p>
      </div>
    </div>

    <!-- 配置面板 -->
    <div class="records-panel">
      <!-- 第一排：路径参数设置 -->
      <div class="settings-section">
        <div class="section-header" @click="toggleSection('path')">
          <div class="header-left">
            <svg class="section-icon" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
              <polyline points="9 22 9 12 15 12 15 22"/>
            </svg>
            <h4 class="section-title">路径参数设置</h4>
            <span class="section-badge">5 项配置</span>
          </div>
          <svg
            class="toggle-icon"
            :class="{ expanded: expandedSections.path }"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </div>

        <div v-show="expandedSections.path" class="section-content">
          <div class="config-grid">
            <div class="config-item">
              <label class="config-label">
                <span class="label-text">检测报告文件路径</span>
                <span class="label-hint">用于存储质检报告的服务器目录</span>
              </label>
              <div class="input-group">
                <input
                  v-model="pathConfig.reportPath"
                  type="text"
                  class="config-input"
                  placeholder="/var/data/reports"
                />
                <button class="btn-secondary btn-sm" type="button" @click="openDirectoryBrowser">
                  获取文件夹
                </button>
                <button class="btn-secondary btn-sm" type="button" title="测试路径" @click="testPath('reportPath')">
                  <svg viewBox="0 0 24 24" class="btn-icon" aria-hidden="true">
                    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                  </svg>
                  测试
                </button>
              </div>
            </div>

            <div class="config-item">
              <label class="config-label">
                <span class="label-text">公司资料文件路径</span>
                <span class="label-hint">存放合同、资质等公司文档</span>
              </label>
              <div class="input-group">
                <input
                  v-model="pathConfig.documentPath"
                  type="text"
                  class="config-input"
                  placeholder="/var/data/documents"
                />
                <button class="btn-secondary btn-sm" type="button" title="测试路径" @click="testPath('documentPath')">
                  <svg viewBox="0 0 24 24" class="btn-icon" aria-hidden="true">
                    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                  </svg>
                  测试
                </button>
              </div>
            </div>

            <div class="config-item">
              <label class="config-label">
                <span class="label-text">回单上传路径</span>
                <span class="label-hint">客户回执单据的上传存储位置</span>
              </label>
              <div class="input-group">
                <input
                  v-model="pathConfig.receiptPath"
                  type="text"
                  class="config-input"
                  placeholder="/var/data/receipts"
                />
                <button class="btn-secondary btn-sm" type="button" title="测试路径" @click="testPath('receiptPath')">
                  <svg viewBox="0 0 24 24" class="btn-icon" aria-hidden="true">
                    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                  </svg>
                  测试
                </button>
              </div>
            </div>

            <div class="config-item">
              <label class="config-label">
                <span class="label-text">银行卡背景图路径</span>
                <span class="label-hint">银行卡背景图片的上传存储位置</span>
              </label>
              <div class="input-group">
                <input
                  v-model="pathConfig.bankCardBgPath"
                  type="text"
                  class="config-input"
                  placeholder="/app/uploads/bank-cards/backgrounds"
                />
                <button class="btn-secondary btn-sm" type="button" title="测试路径" @click="testPath('bankCardBgPath')">
                  <svg viewBox="0 0 24 24" class="btn-icon" aria-hidden="true">
                    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                  </svg>
                  测试
                </button>
              </div>
            </div>

            <div class="config-item">
              <label class="config-label">
                <span class="label-text">银行图标路径</span>
                <span class="label-hint">银行 LOGO 图标的上传存储位置</span>
              </label>
              <div class="input-group">
                <input
                  v-model="pathConfig.bankIconPath"
                  type="text"
                  class="config-input"
                  placeholder="/app/uploads/bank-cards/icons"
                />
                <button class="btn-secondary btn-sm" type="button" title="测试路径" @click="testPath('bankIconPath')">
                  <svg viewBox="0 0 24 24" class="btn-icon" aria-hidden="true">
                    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
                  </svg>
                  测试
                </button>
              </div>
            </div>
          </div>

          <div class="section-actions">
            <button class="btn-primary" :disabled="pathSaving" @click="savePathConfig">
              <svg viewBox="0 0 24 24" class="btn-icon" aria-hidden="true">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              保存路径配置
            </button>
          </div>
        </div>
      </div>

      <!-- 第二排：消息设置 -->
      <div class="settings-section">
        <div class="section-header" @click="toggleSection('message')">
          <div class="header-left">
            <svg class="section-icon" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            <h4 class="section-title">消息通知设置</h4>
            <span class="section-badge">4 项配置</span>
          </div>
          <svg
            class="toggle-icon"
            :class="{ expanded: expandedSections.message }"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </div>

        <div v-show="expandedSections.message" class="section-content">
          <div class="config-grid">
            <div class="config-item">
              <label class="config-label">
                <span class="label-text">审核通知设置</span>
                <span class="label-hint">订单审核完成后的消息推送</span>
              </label>
              <div class="toggle-group">
                <label class="toggle-option">
                  <input
                    v-model="messageConfig.auditNotify"
                    type="checkbox"
                    class="toggle-checkbox"
                  />
                  <span class="toggle-switch"></span>
                  <span class="toggle-label">启用审核通知</span>
                </label>
              </div>
              <div v-show="messageConfig.auditNotify" class="sub-options">
                <label class="checkbox-option">
                  <input
                    v-model="messageConfig.auditEmail"
                    type="checkbox"
                  />
                  邮件通知
                </label>
                <label class="checkbox-option">
                  <input
                    v-model="messageConfig.auditSms"
                    type="checkbox"
                  />
                  短信通知
                </label>
                <label class="checkbox-option">
                  <input
                    v-model="messageConfig.auditSystem"
                    type="checkbox"
                  />
                  站内消息
                </label>
              </div>
            </div>

            <div class="config-item">
              <label class="config-label">
                <span class="label-text">留言消息设置</span>
                <span class="label-hint">用户留言的实时提醒方式</span>
              </label>
              <div class="toggle-group">
                <label class="toggle-option">
                  <input
                    v-model="messageConfig.commentNotify"
                    type="checkbox"
                    class="toggle-checkbox"
                  />
                  <span class="toggle-switch"></span>
                  <span class="toggle-label">启用留言通知</span>
                </label>
              </div>
              <div v-show="messageConfig.commentNotify" class="sub-options">
                <label class="checkbox-option">
                  <input
                    v-model="messageConfig.commentEmail"
                    type="checkbox"
                  />
                  邮件通知
                </label>
                <label class="checkbox-option">
                  <input
                    v-model="messageConfig.commentSystem"
                    type="checkbox"
                  />
                  站内消息
                </label>
              </div>
            </div>

            <div class="config-item">
              <label class="config-label">
                <span class="label-text">订单状态变更通知</span>
                <span class="label-hint">订单状态发生变化时通知相关人员</span>
              </label>
              <div class="toggle-group">
                <label class="toggle-option">
                  <input
                    v-model="messageConfig.orderStatusNotify"
                    type="checkbox"
                    class="toggle-checkbox"
                  />
                  <span class="toggle-switch"></span>
                  <span class="toggle-label">启用状态变更通知</span>
                </label>
              </div>
            </div>

            <div class="config-item">
              <label class="config-label">
                <span class="label-text">系统异常告警</span>
                <span class="label-hint">服务异常或错误时的紧急通知</span>
              </label>
              <div class="toggle-group">
                <label class="toggle-option">
                  <input
                    v-model="messageConfig.errorAlert"
                    type="checkbox"
                    class="toggle-checkbox"
                  />
                  <span class="toggle-switch"></span>
                  <span class="toggle-label">启用异常告警</span>
                </label>
              </div>
              <div v-show="messageConfig.errorAlert" class="sub-options">
                <div class="input-inline">
                  <span class="input-prefix">告警接收人</span>
                  <input
                    v-model="messageConfig.alertRecipients"
                    type="text"
                    class="config-input-sm"
                    placeholder="多个邮箱用逗号分隔"
                  />
                </div>
              </div>
            </div>
          </div>

          <div class="section-actions">
            <button class="btn-primary" @click="saveMessageConfig">
              <svg viewBox="0 0 24 24" class="btn-icon" aria-hidden="true">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              保存消息配置
            </button>
          </div>
        </div>
      </div>

      <!-- 第三排：业务规则设置 -->
      <div class="settings-section">
        <div class="section-header" @click="toggleSection('business')">
          <div class="header-left">
            <svg class="section-icon" viewBox="0 0 24 24" aria-hidden="true">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
              <line x1="9" y1="3" x2="9" y2="21"/>
            </svg>
            <h4 class="section-title">业务规则设置</h4>
            <span class="section-badge">5 项配置</span>
          </div>
          <svg
            class="toggle-icon"
            :class="{ expanded: expandedSections.business }"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </div>

        <div v-show="expandedSections.business" class="section-content">
          <div class="config-grid">
            <div class="config-item">
              <label class="config-label">
                <span class="label-text">订单自动审核</span>
                <span class="label-hint">符合条件的订单自动通过审核</span>
              </label>
              <div class="toggle-group">
                <label class="toggle-option">
                  <input
                    v-model="businessConfig.autoAudit"
                    type="checkbox"
                    class="toggle-checkbox"
                  />
                  <span class="toggle-switch"></span>
                  <span class="toggle-label">启用自动审核</span>
                </label>
              </div>
              <div v-show="businessConfig.autoAudit" class="sub-options">
                <div class="input-inline">
                  <span class="input-prefix">金额阈值</span>
                  <input
                    v-model="businessConfig.autoAuditThreshold"
                    type="number"
                    class="config-input-sm"
                    placeholder="10000"
                  />
                  <span class="input-suffix">元以下自动通过</span>
                </div>
              </div>
            </div>

            <div class="config-item">
              <label class="config-label">
                <span class="label-text">库存预警设置</span>
                <span class="label-hint">原材料库存低于阈值时提醒</span>
              </label>
              <div class="toggle-group">
                <label class="toggle-option">
                  <input
                    v-model="businessConfig.stockAlert"
                    type="checkbox"
                    class="toggle-checkbox"
                  />
                  <span class="toggle-switch"></span>
                  <span class="toggle-label">启用库存预警</span>
                </label>
              </div>
              <div v-show="businessConfig.stockAlert" class="sub-options">
                <div class="input-inline">
                  <span class="input-prefix">预警比例</span>
                  <input
                    v-model="businessConfig.stockAlertRatio"
                    type="number"
                    class="config-input-sm"
                    placeholder="20"
                  />
                  <span class="input-suffix">% 时触发预警</span>
                </div>
              </div>
            </div>

            <div class="config-item">
              <label class="config-label">
                <span class="label-text">订单超时提醒</span>
                <span class="label-hint">订单长时间未处理时发送提醒</span>
              </label>
              <div class="toggle-group">
                <label class="toggle-option">
                  <input
                    v-model="businessConfig.orderTimeout"
                    type="checkbox"
                    class="toggle-checkbox"
                  />
                  <span class="toggle-switch"></span>
                  <span class="toggle-label">启用超时提醒</span>
                </label>
              </div>
              <div v-show="businessConfig.orderTimeout" class="sub-options">
                <div class="input-inline">
                  <span class="input-prefix">超时时长</span>
                  <input
                    v-model="businessConfig.orderTimeoutHours"
                    type="number"
                    class="config-input-sm"
                    placeholder="24"
                  />
                  <span class="input-suffix">小时</span>
                </div>
              </div>
            </div>

            <div class="config-item">
              <label class="config-label">
                <span class="label-text">价格波动监控</span>
                <span class="label-hint">原材料价格异常波动时预警</span>
              </label>
              <div class="toggle-group">
                <label class="toggle-option">
                  <input
                    v-model="businessConfig.priceMonitor"
                    type="checkbox"
                    class="toggle-checkbox"
                  />
                  <span class="toggle-switch"></span>
                  <span class="toggle-label">启用价格监控</span>
                </label>
              </div>
              <div v-show="businessConfig.priceMonitor" class="sub-options">
                <div class="input-inline">
                  <span class="input-prefix">波动阈值</span>
                  <input
                    v-model="businessConfig.priceFluctuation"
                    type="number"
                    class="config-input-sm"
                    placeholder="15"
                  />
                  <span class="input-suffix">% 涨跌幅触发</span>
                </div>
              </div>
            </div>

            <div class="config-item">
              <label class="config-label">
                <span class="label-text">数据备份策略</span>
                <span class="label-hint">定期自动备份系统数据</span>
              </label>
              <div class="toggle-group">
                <label class="toggle-option">
                  <input
                    v-model="businessConfig.autoBackup"
                    type="checkbox"
                    class="toggle-checkbox"
                  />
                  <span class="toggle-switch"></span>
                  <span class="toggle-label">启用自动备份</span>
                </label>
              </div>
              <div v-show="businessConfig.autoBackup" class="sub-options">
                <select v-model="businessConfig.backupFrequency" class="config-select">
                  <option value="daily">每日备份</option>
                  <option value="weekly">每周备份</option>
                  <option value="monthly">每月备份</option>
                </select>
              </div>
            </div>
          </div>

          <div class="section-actions">
            <button class="btn-primary" @click="saveBusinessConfig">
              <svg viewBox="0 0 24 24" class="btn-icon" aria-hidden="true">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              保存业务配置
            </button>
          </div>
        </div>
      </div>

      <!-- 第四排：系统安全设置 -->
      <div class="settings-section">
        <div class="section-header" @click="toggleSection('security')">
          <div class="header-left">
            <svg class="section-icon" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
            <h4 class="section-title">系统安全设置</h4>
            <span class="section-badge">4 项配置</span>
          </div>
          <svg
            class="toggle-icon"
            :class="{ expanded: expandedSections.security }"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </div>

        <div v-show="expandedSections.security" class="section-content">
          <div class="config-grid">
            <div class="config-item">
              <label class="config-label">
                <span class="label-text">登录失败锁定</span>
                <span class="label-hint">连续登录失败后暂时锁定账户</span>
              </label>
              <div class="toggle-group">
                <label class="toggle-option">
                  <input
                    v-model="securityConfig.loginLock"
                    type="checkbox"
                    class="toggle-checkbox"
                  />
                  <span class="toggle-switch"></span>
                  <span class="toggle-label">启用登录锁定</span>
                </label>
              </div>
              <div v-show="securityConfig.loginLock" class="sub-options">
                <div class="input-inline">
                  <span class="input-prefix">失败次数</span>
                  <input
                    v-model="securityConfig.loginFailLimit"
                    type="number"
                    class="config-input-sm"
                    placeholder="5"
                  />
                  <span class="input-suffix">次后锁定</span>
                </div>
                <div class="input-inline">
                  <span class="input-prefix">锁定时长</span>
                  <input
                    v-model="securityConfig.lockDuration"
                    type="number"
                    class="config-input-sm"
                    placeholder="30"
                  />
                  <span class="input-suffix">分钟</span>
                </div>
              </div>
            </div>

            <div class="config-item">
              <label class="config-label">
                <span class="label-text">会话超时设置</span>
                <span class="label-hint">用户无操作自动退出登录</span>
              </label>
              <div class="toggle-group">
                <label class="toggle-option">
                  <input
                    v-model="securityConfig.sessionTimeout"
                    type="checkbox"
                    class="toggle-checkbox"
                  />
                  <span class="toggle-switch"></span>
                  <span class="toggle-label">启用会话超时</span>
                </label>
              </div>
              <div v-show="securityConfig.sessionTimeout" class="sub-options">
                <div class="input-inline">
                  <span class="input-prefix">超时时长</span>
                  <input
                    v-model="securityConfig.sessionMinutes"
                    type="number"
                    class="config-input-sm"
                    placeholder="120"
                  />
                  <span class="input-suffix">分钟</span>
                </div>
              </div>
            </div>

            <div class="config-item">
              <label class="config-label">
                <span class="label-text">操作日志记录</span>
                <span class="label-hint">记录关键操作的审计日志</span>
              </label>
              <div class="toggle-group">
                <label class="toggle-option">
                  <input
                    v-model="securityConfig.auditLog"
                    type="checkbox"
                    class="toggle-checkbox"
                  />
                  <span class="toggle-switch"></span>
                  <span class="toggle-label">启用审计日志</span>
                </label>
              </div>
              <div v-show="securityConfig.auditLog" class="sub-options">
                <label class="checkbox-option">
                  <input
                    v-model="securityConfig.logLogin"
                    type="checkbox"
                  />
                  记录登录登出
                </label>
                <label class="checkbox-option">
                  <input
                    v-model="securityConfig.logDataChange"
                    type="checkbox"
                  />
                  记录数据变更
                </label>
                <label class="checkbox-option">
                  <input
                    v-model="securityConfig.logPermission"
                    type="checkbox"
                  />
                  记录权限操作
                </label>
              </div>
            </div>

            <div class="config-item">
              <label class="config-label">
                <span class="label-text">IP 访问控制</span>
                <span class="label-hint">限制允许访问系统的 IP 地址</span>
              </label>
              <div class="toggle-group">
                <label class="toggle-option">
                  <input
                    v-model="securityConfig.ipWhitelist"
                    type="checkbox"
                    class="toggle-checkbox"
                  />
                  <span class="toggle-switch"></span>
                  <span class="toggle-label">启用 IP 白名单</span>
                </label>
              </div>
              <div v-show="securityConfig.ipWhitelist" class="sub-options">
                <textarea
                  v-model="securityConfig.allowedIps"
                  class="config-textarea"
                  placeholder="每行一个 IP 地址或 CIDR 段&#10;例如：&#10;192.168.1.100&#10;10.0.0.0/8"
                  rows="4"
                ></textarea>
              </div>
            </div>
          </div>

          <div class="section-actions">
            <button class="btn-primary" @click="saveSecurityConfig">
              <svg viewBox="0 0 24 24" class="btn-icon" aria-hidden="true">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              保存安全配置
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div
    v-if="directoryBrowserVisible"
    class="directory-browser-mask"
    @click.self="directoryBrowserVisible = false"
  >
    <section class="directory-browser" role="dialog" aria-modal="true" aria-label="选择服务器文件夹">
      <div class="directory-browser-header">
        <div>
          <h3>选择服务器文件夹</h3>
          <p>这里显示的是 Docker 容器可访问的 NAS 挂载目录。</p>
        </div>
        <button class="directory-browser-close" type="button" @click="directoryBrowserVisible = false">×</button>
      </div>

      <div class="directory-browser-path">
        <input
          v-model="directoryBrowser.path"
          class="config-input"
          type="text"
          placeholder="/mnt/nas/reports"
          @keyup.enter="loadDirectories(directoryBrowser.path)"
        />
        <button class="btn-secondary btn-sm" type="button" @click="loadDirectories(directoryBrowser.path)">
          打开
        </button>
      </div>

      <p v-if="directoryBrowser.message" class="directory-browser-message">
        {{ directoryBrowser.message }}
      </p>

      <div class="directory-browser-actions">
        <button
          class="btn-secondary btn-sm"
          type="button"
          :disabled="!directoryBrowser.parentPath || directoryBrowser.loading"
          @click="loadDirectories(directoryBrowser.parentPath)"
        >
          返回上级
        </button>
        <button
          class="btn-primary btn-sm"
          type="button"
          :disabled="!directoryBrowser.path || directoryBrowser.loading"
          @click="useCurrentDirectory"
        >
          使用当前目录
        </button>
      </div>

      <div v-if="directoryBrowser.loading" class="directory-browser-empty">正在读取目录…</div>
      <div v-else class="directory-list">
        <button
          v-for="directory in directoryBrowser.directories"
          :key="directory.path"
          class="directory-item"
          type="button"
          @click="loadDirectories(directory.path)"
        >
          <span class="directory-icon">📁</span>
          <span>{{ directory.name }}</span>
        </button>
        <div v-if="!directoryBrowser.directories.length" class="directory-browser-empty">
          当前目录下没有可读取的子文件夹。
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import request from '@/api/request'

// 控制各区块展开/收起
const expandedSections = reactive({
  path: true,
  message: false,
  business: false,
  security: false
})

// 路径配置
const pathConfig = reactive({
  reportPath: '/var/data/reports',
  documentPath: '/var/data/documents',
  receiptPath: '/var/data/receipts',
  bankCardBgPath: '/app/uploads/bank-cards/backgrounds',
  bankIconPath: '/app/uploads/bank-cards/icons'
})

const pathSaving = ref(false)
const directoryBrowserVisible = ref(false)
const directoryBrowser = reactive({
  loading: false,
  path: '',
  parentPath: '',
  directories: [],
  message: ''
})

// 消息配置
const messageConfig = reactive({
  auditNotify: true,
  auditEmail: true,
  auditSms: false,
  auditSystem: true,
  commentNotify: true,
  commentEmail: false,
  commentSystem: true,
  orderStatusNotify: true,
  errorAlert: true,
  alertRecipients: 'admin@example.com'
})

// 业务配置
const businessConfig = reactive({
  autoAudit: false,
  autoAuditThreshold: 10000,
  stockAlert: true,
  stockAlertRatio: 20,
  orderTimeout: true,
  orderTimeoutHours: 24,
  priceMonitor: true,
  priceFluctuation: 15,
  autoBackup: true,
  backupFrequency: 'daily'
})

// 安全配置
const securityConfig = reactive({
  loginLock: true,
  loginFailLimit: 5,
  lockDuration: 30,
  sessionTimeout: true,
  sessionMinutes: 120,
  auditLog: true,
  logLogin: true,
  logDataChange: true,
  logPermission: true,
  ipWhitelist: false,
  allowedIps: ''
})

// 切换区块展开状态
const toggleSection = (section) => {
  expandedSections[section] = !expandedSections[section]
}

// 保存各配置
const loadPathConfig = async () => {
  try {
    const response = await request.get('/settings/paths')
    if (response.success && response.data) {
      Object.assign(pathConfig, {
        reportPath: response.data.reportPath || '',
        documentPath: response.data.documentPath || '',
        receiptPath: response.data.receiptPath || '',
        bankCardBgPath: response.data.bankCardBgPath || '/app/uploads/bank-cards/backgrounds',
        bankIconPath: response.data.bankIconPath || '/app/uploads/bank-cards/icons'
      })
    }
  } catch (error) {
    console.error('加载路径配置失败:', error)
  }
}

const savePathConfig = async () => {
  if (pathSaving.value) return
  pathSaving.value = true
  try {
    const response = await request.put('/settings/paths', { ...pathConfig })
    if (!response.success) {
      throw new Error(response.message || '保存失败')
    }
    Object.assign(pathConfig, {
      reportPath: response.data?.reportPath || pathConfig.reportPath,
      documentPath: response.data?.documentPath || pathConfig.documentPath,
      receiptPath: response.data?.receiptPath || pathConfig.receiptPath,
      bankCardBgPath: response.data?.bankCardBgPath || pathConfig.bankCardBgPath,
      bankIconPath: response.data?.bankIconPath || pathConfig.bankIconPath
    })
    alert(response.message || '路径配置已保存')
  } catch (error) {
    alert(error.response?.data?.message || error.message || '保存路径配置失败')
  } finally {
    pathSaving.value = false
  }
}

const testPath = async (key) => {
  try {
    const response = await request.post('/settings/paths/test', {
      path: pathConfig[key]
    })
    alert(response.message || (response.success ? '路径可用' : '路径不可用'))
  } catch (error) {
    alert(error.response?.data?.message || '路径测试失败')
  }
}

const loadDirectories = async (path = '') => {
  directoryBrowser.loading = true
  try {
    const response = await request.get('/settings/directories', {
      params: path ? { path } : {}
    })
    if (!response.success) {
      throw new Error(response.message || '读取服务器目录失败')
    }
    Object.assign(directoryBrowser, {
      path: response.data.path || '',
      parentPath: response.data.parent_path || '',
      directories: response.data.directories || [],
      message: response.data.message || ''
    })
  } catch (error) {
    directoryBrowser.message = error.response?.data?.message || error.message || '读取服务器目录失败'
    directoryBrowser.directories = []
  } finally {
    directoryBrowser.loading = false
  }
}

const openDirectoryBrowser = async () => {
  directoryBrowserVisible.value = true
  await loadDirectories()
}

const useCurrentDirectory = () => {
  if (!directoryBrowser.path) return
  pathConfig.reportPath = directoryBrowser.path
  directoryBrowserVisible.value = false
}

const saveMessageConfig = () => {
  console.log('保存消息配置:', messageConfig)
  alert('消息配置已保存')
}

const saveBusinessConfig = () => {
  console.log('保存业务配置:', businessConfig)
  alert('业务配置已保存')
}

const saveSecurityConfig = () => {
  console.log('保存安全配置:', securityConfig)
  alert('安全配置已保存')
}

onMounted(() => {
  loadPathConfig()
  // 这里可以加载配置数据
  console.log('设置页面已加载')
})
</script>

<style scoped>
.settings-page {
  --accent: #0f9f78;
  --accent-rgb: 15, 159, 120;
  --accent-dark: #08745a;
  --accent-soft: #e9f8f3;
  --accent-border: #a9e5d2;
  --page-bg: #f4f7f8;
  --panel-bg: #fff;
  --border: #e2e8f0;
  --border-strong: #cbd5e1;
  --text: #172033;
  --text-secondary: #596579;
  --text-muted: #8a96a8;

  width: 100%;
  min-height: 100vh;
  background: var(--page-bg);
  color: var(--text);
  font-size: 14px;
  padding: 20px;
}

/* 搜索面板样式 */
.search-panel {
  background: var(--panel-bg);
  border: 1px solid var(--border);
  border-radius: 7px;
  padding: 18px 20px;
  margin-bottom: 14px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.panel-header {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.panel-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text);
  margin: 0;
}

.panel-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0;
}

/* 记录面板 */
.records-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* 设置区块 */
.settings-section {
  background: var(--panel-bg);
  border: 1px solid var(--border);
  border-radius: 7px;
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  transition: box-shadow 0.18s ease;
}

.settings-section:hover {
  box-shadow: 0 2px 4px rgba(15, 23, 42, 0.08);
}

/* 区块头部 */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  cursor: pointer;
  user-select: none;
  transition: background 0.18s ease;
  border-bottom: 1px solid transparent;
}

.section-header:hover {
  background: rgba(var(--accent-rgb), 0.03);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-icon {
  width: 20px;
  height: 20px;
  fill: none;
  stroke: var(--accent);
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
  flex-shrink: 0;
}

.section-title {
  font-size: 15px;
  font-weight: 650;
  color: var(--text);
  margin: 0;
}

.section-badge {
  font-size: 11px;
  font-weight: 700;
  color: var(--accent-dark);
  background: var(--accent-soft);
  padding: 3px 9px;
  border-radius: 999px;
  min-height: 20px;
  display: inline-flex;
  align-items: center;
}

.toggle-icon {
  width: 18px;
  height: 18px;
  fill: none;
  stroke: var(--text-secondary);
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.toggle-icon.expanded {
  transform: rotate(180deg);
}

/* 区块内容 */
.section-content {
  padding: 20px;
  border-top: 1px solid var(--border);
}

/* 配置网格 */
.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.config-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 配置标签 */
.config-label {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.label-text {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}

.label-hint {
  font-size: 12px;
  color: var(--text-muted);
}

/* 输入组 */
.input-group {
  display: flex;
  gap: 8px;
  align-items: center;
}

.config-input {
  flex: 1;
  height: 38px;
  padding: 0 11px;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  font-size: 14px;
  color: var(--text);
  background: var(--panel-bg);
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
  font-variant-numeric: tabular-nums;
}

.config-input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.1);
}

.config-input::placeholder {
  color: var(--text-muted);
}

/* 开关组 */
.toggle-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.toggle-option {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;
}

.toggle-checkbox {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.toggle-switch {
  position: relative;
  width: 44px;
  height: 24px;
  background: var(--border-strong);
  border-radius: 999px;
  transition: background 0.2s ease;
  flex-shrink: 0;
}

.toggle-switch::after {
  content: '';
  position: absolute;
  left: 3px;
  top: 3px;
  width: 18px;
  height: 18px;
  background: var(--panel-bg);
  border-radius: 50%;
  transition: transform 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
}

.toggle-checkbox:checked + .toggle-switch {
  background: var(--accent);
}

.toggle-checkbox:checked + .toggle-switch::after {
  transform: translateX(20px);
}

.toggle-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}

/* 子选项 */
.sub-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-left: 16px;
  border-left: 2px solid var(--border);
  margin-top: 4px;
}

.checkbox-option {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  user-select: none;
}

.checkbox-option input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: var(--accent);
}

/* 内联输入 */
.input-inline {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.input-prefix,
.input-suffix {
  font-size: 13px;
  color: var(--text-secondary);
  white-space: nowrap;
}

.config-input-sm {
  width: 120px;
  height: 32px;
  padding: 0 10px;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  font-size: 13px;
  color: var(--text);
  background: var(--panel-bg);
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
  font-variant-numeric: tabular-nums;
}

.config-input-sm:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.1);
}

.config-select {
  height: 32px;
  padding: 0 10px;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  font-size: 13px;
  color: var(--text);
  background: var(--panel-bg);
  cursor: pointer;
  transition: border-color 0.18s ease;
}

.config-select:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.1);
}

.config-textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--border-strong);
  border-radius: 5px;
  font-size: 13px;
  color: var(--text);
  background: var(--panel-bg);
  font-family: 'Consolas', 'Monaco', monospace;
  resize: vertical;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.config-textarea:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.1);
}

/* 操作按钮区 */
.section-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}

/* 按钮样式 */
.btn-primary {
  display: inline-flex;
  height: 38px;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 0 15px;
  border: 1px solid var(--accent);
  background: var(--accent);
  color: #fff;
  border-radius: 5px;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
  transition: background 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.btn-primary:hover {
  background: var(--accent-dark);
  border-color: var(--accent-dark);
  box-shadow: 0 2px 4px rgba(var(--accent-rgb), 0.2);
}

.btn-primary:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.btn-secondary {
  display: inline-flex;
  height: 38px;
  align-items: center;
  justify-content: center;
  gap: 7px;
  padding: 0 15px;
  border: 1px solid var(--border-strong);
  background: var(--panel-bg);
  color: var(--text);
  border-radius: 5px;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
  transition: background 0.18s ease, border-color 0.18s ease, color 0.18s ease;
}

.btn-secondary:hover {
  background: var(--accent-soft);
  border-color: var(--accent-border);
  color: var(--accent-dark);
}

.btn-secondary:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.btn-sm {
  height: 32px;
  padding: 0 12px;
  font-size: 12px;
}

.btn-icon {
  width: 16px;
  height: 16px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
  flex-shrink: 0;
}

/* 响应式 */
@media (max-width: 1280px) {
  .config-grid {
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  }
}

@media (max-width: 780px) {
  .settings-page {
    padding: 12px;
  }

  .config-grid {
    grid-template-columns: 1fr;
  }

  .input-group {
    flex-direction: column;
    align-items: stretch;
  }

  .btn-secondary.btn-sm {
    width: 100%;
  }

  .section-actions {
    flex-direction: column;
  }

  .btn-primary {
    width: 100%;
  }
}
.directory-browser-mask {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(15, 23, 42, 0.45);
}

.directory-browser {
  width: min(720px, 100%);
  max-height: min(680px, calc(100vh - 40px));
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 20px;
  overflow: hidden;
  border-radius: 10px;
  background: var(--panel-bg);
  box-shadow: 0 24px 64px rgba(15, 23, 42, 0.3);
}

.directory-browser-header,
.directory-browser-actions,
.directory-browser-path {
  display: flex;
  align-items: center;
  gap: 10px;
}

.directory-browser-header {
  justify-content: space-between;
}

.directory-browser-header h3,
.directory-browser-header p {
  margin: 0;
}

.directory-browser-header h3 {
  font-size: 16px;
}

.directory-browser-header p,
.directory-browser-message {
  margin: 4px 0 0;
  color: var(--text-secondary);
  font-size: 12px;
}

.directory-browser-close {
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 5px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 24px;
  line-height: 1;
  cursor: pointer;
}

.directory-browser-close:hover {
  background: #f1f5f9;
  color: var(--text);
}

.directory-browser-path .config-input {
  min-width: 0;
}

.directory-browser-actions {
  justify-content: space-between;
}

.directory-list {
  min-height: 180px;
  overflow: auto;
  border: 1px solid var(--border);
  border-radius: 6px;
}

.directory-item {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 9px;
  padding: 10px 12px;
  border: 0;
  border-bottom: 1px solid var(--border);
  background: transparent;
  color: var(--text);
  text-align: left;
  cursor: pointer;
}

.directory-item:last-child {
  border-bottom: 0;
}

.directory-item:hover {
  background: var(--accent-soft);
  color: var(--accent-dark);
}

.directory-icon {
  font-size: 16px;
}

.directory-browser-empty {
  padding: 28px 16px;
  color: var(--text-muted);
  text-align: center;
}

@media (max-width: 780px) {
  .directory-browser-path {
    align-items: stretch;
    flex-direction: column;
  }

  .directory-browser-path .btn-secondary {
    width: 100%;
  }
}
</style>
