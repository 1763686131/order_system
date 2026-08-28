<template>
  <div class="dashboard-page">
    <!-- 顶部数据卡片区 -->
    <div class="stats-cards">
      <div class="stat-card">
        <div class="card-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
          <span class="icon-text">📊</span>
        </div>
        <div class="card-content">
          <div class="card-value">200</div>
          <div class="card-label">今日订单数量</div>
        </div>
        <div class="card-chart">
          <svg viewBox="0 0 100 40" class="mini-chart">
            <path d="M 0 30 Q 25 10, 50 20 T 100 15" fill="none" stroke="#667eea" stroke-width="2"/>
          </svg>
        </div>
      </div>

      <div class="stat-card">
        <div class="card-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
          <span class="icon-text">💰</span>
        </div>
        <div class="card-content">
          <div class="card-value">¥5000.00</div>
          <div class="card-label">今日营业总额</div>
        </div>
        <div class="card-chart">
          <svg viewBox="0 0 100 40" class="mini-chart">
            <path d="M 0 25 Q 25 5, 50 15 T 100 10" fill="none" stroke="#f5576c" stroke-width="2"/>
          </svg>
        </div>
      </div>

      <div class="stat-card">
        <div class="card-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
          <span class="icon-text">📦</span>
        </div>
        <div class="card-content">
          <div class="card-value">¥5000.00</div>
          <div class="card-label">库存总价值</div>
        </div>
        <div class="card-chart">
          <svg viewBox="0 0 100 40" class="mini-chart">
            <path d="M 0 20 Q 25 15, 50 18 T 100 12" fill="none" stroke="#00f2fe" stroke-width="2"/>
          </svg>
        </div>
      </div>

      <div class="stat-card">
        <div class="card-icon" style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);">
          <span class="icon-text">✅</span>
        </div>
        <div class="card-content">
          <div class="card-value">¥5000.00</div>
          <div class="card-label">本月完成总额</div>
        </div>
        <div class="card-chart">
          <svg viewBox="0 0 100 40" class="mini-chart">
            <path d="M 0 28 Q 25 12, 50 22 T 100 18" fill="none" stroke="#a8edea" stroke-width="2"/>
          </svg>
        </div>
      </div>
    </div>

    <!-- 主图表区域 -->
    <div class="main-chart-section">
      <div class="chart-container">
        <div class="chart-header">
          <h3 class="chart-title">📈 订单统计</h3>
          <div class="chart-filters">
            <button class="filter-btn">日</button>
            <button class="filter-btn active">周</button>
            <button class="filter-btn">月</button>
          </div>
        </div>
        <div class="chart-body">
          <div class="chart-placeholder">
            <p>图表区域 - 可集成 ECharts 或 Chart.js</p>
            <div class="mock-chart">
              <svg viewBox="0 0 600 200" class="line-chart">
                <path d="M 0 150 Q 100 120, 150 100 T 300 80 T 450 90 T 600 70"
                      fill="none" stroke="#667eea" stroke-width="3"/>
                <path d="M 0 170 Q 100 140, 150 130 T 300 110 T 450 120 T 600 100"
                      fill="none" stroke="#4facfe" stroke-width="3"/>
              </svg>
            </div>
          </div>
        </div>
        <div class="chart-legend">
          <div class="legend-item">
            <span class="legend-dot" style="background: #667eea;"></span>
            <span>本周订单</span>
            <strong>10000</strong>
          </div>
          <div class="legend-item">
            <span class="legend-dot" style="background: #4facfe;"></span>
            <span>本月订单总量</span>
            <strong>1000</strong>
          </div>
        </div>
      </div>

      <!-- 右侧快捷操作面板 -->
      <div class="quick-actions">
        <h4 class="actions-title">待办任务</h4>
        <div class="action-list">
          <div class="action-item active">
            <span class="action-text">待处理订单</span>
            <span class="action-badge">12</span>
          </div>
          <div class="action-item">
            <span class="action-text">待发货订单</span>
            <span class="action-badge">8</span>
          </div>
          <div class="action-item">
            <span class="action-text">待审核项目</span>
            <span class="action-badge">5</span>
          </div>
          <div class="action-item">
            <span class="action-text">待补货商品订单</span>
            <span class="action-badge">3</span>
          </div>
          <div class="action-item">
            <span class="action-text">待跟进客户订单</span>
            <span class="action-badge">15</span>
          </div>
          <div class="action-item">
            <span class="action-text">检验制单项目</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部统计区域 -->
    <div class="bottom-stats">
      <div class="stats-group">
        <h4 class="stats-title">商品总览</h4>
        <div class="stats-bars">
          <div class="bar-item">
            <div class="bar-label">总上架</div>
            <div class="bar-track">
              <div class="bar-fill" style="width: 80%; background: #667eea;"></div>
            </div>
            <div class="bar-value">400</div>
          </div>
          <div class="bar-item">
            <div class="bar-label">主下架</div>
            <div class="bar-track">
              <div class="bar-fill" style="width: 30%; background: #f5576c;"></div>
            </div>
            <div class="bar-value">150</div>
          </div>
          <div class="bar-item">
            <div class="bar-label">订货类</div>
            <div class="bar-track">
              <div class="bar-fill" style="width: 5%; background: #4facfe;"></div>
            </div>
            <div class="bar-value">20</div>
          </div>
        </div>
      </div>

      <div class="stats-group">
        <h4 class="stats-title">用户总览</h4>
        <div class="stats-bars">
          <div class="bar-item">
            <div class="bar-label">总主数</div>
            <div class="bar-track">
              <div class="bar-fill" style="width: 90%; background: #667eea;"></div>
            </div>
            <div class="bar-value">400</div>
          </div>
          <div class="bar-item">
            <div class="bar-label">总支类</div>
            <div class="bar-track">
              <div class="bar-fill" style="width: 50%; background: #f5576c;"></div>
            </div>
            <div class="bar-value">180</div>
          </div>
          <div class="bar-item">
            <div class="bar-label">没关支</div>
            <div class="bar-track">
              <div class="bar-fill" style="width: 60%; background: #4facfe;"></div>
            </div>
            <div class="bar-value">200</div>
          </div>
        </div>
      </div>

      <div class="stats-group">
        <h4 class="stats-title">快捷入口</h4>
        <div class="quick-buttons">
          <button class="quick-btn">添加订单</button>
          <button class="quick-btn">订单列表</button>
          <button class="quick-btn">用户管理</button>
          <button class="quick-btn">广告管理</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { inject, onMounted } from 'vue'

// 注入 Admin 组件提供的方法
const setHeaderActions = inject('setHeaderActions', null)

// 数据看板不需要顶部按钮，清空
onMounted(() => {
  if (setHeaderActions) {
    setHeaderActions(null)
  }
})
// 仪表盘组件
</script>

<style scoped>
.dashboard-page {
  width: 100%;
}

/* 顶部数据卡片 */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.3s;
  position: relative;
  overflow: hidden;
}

.stat-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.card-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  flex-shrink: 0;
}

.icon-text {
  font-size: 28px;
}

.card-content {
  flex: 1;
}

.card-value {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 4px;
}

.card-label {
  font-size: 13px;
  color: #6b7280;
}

.card-chart {
  width: 80px;
  height: 40px;
  opacity: 0.3;
}

.mini-chart {
  width: 100%;
  height: 100%;
}

/* 主图表区域 */
.main-chart-section {
  display: flex;
  gap: 20px;
  margin-bottom: 24px;
}

.chart-container {
  flex: 1;
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 2px solid #667eea;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.chart-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
}

.chart-filters {
  display: flex;
  gap: 8px;
}

.filter-btn {
  padding: 6px 16px;
  border: 1px solid #e5e7eb;
  background: #fff;
  border-radius: 6px;
  font-size: 14px;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.3s;
}

.filter-btn:hover {
  border-color: #667eea;
  color: #667eea;
}

.filter-btn.active {
  background: #667eea;
  color: #fff;
  border-color: #667eea;
}

.chart-body {
  margin-bottom: 20px;
}

.chart-placeholder {
  height: 250px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #f9fafb;
  border-radius: 8px;
  color: #9ca3af;
}

.mock-chart {
  width: 100%;
  height: 200px;
}

.line-chart {
  width: 100%;
  height: 100%;
}

.chart-legend {
  display: flex;
  gap: 32px;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #6b7280;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.legend-item strong {
  color: #1f2937;
  margin-left: 8px;
}

/* 右侧快捷操作 */
.quick-actions {
  width: 280px;
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.actions-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 16px 0;
}

.action-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.action-item:hover {
  background: #e5e7eb;
}

.action-item.active {
  background: #667eea;
  color: #fff;
}

.action-text {
  font-size: 14px;
}

.action-badge {
  background: #ef4444;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 10px;
  min-width: 24px;
  text-align: center;
}

.action-item.active .action-badge {
  background: #fff;
  color: #667eea;
}

/* 底部统计区域 */
.bottom-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.stats-group {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.stats-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 16px 0;
}

.stats-bars {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.bar-item {
  display: grid;
  grid-template-columns: 60px 1fr 60px;
  align-items: center;
  gap: 12px;
}

.bar-label {
  font-size: 14px;
  color: #6b7280;
}

.bar-track {
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.6s ease;
}

.bar-value {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  text-align: right;
}

.quick-buttons {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.quick-btn {
  padding: 12px;
  background: #667eea;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.quick-btn:hover {
  background: #5568d3;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
}

/* 响应式 */
@media (max-width: 1200px) {
  .main-chart-section {
    flex-direction: column;
  }

  .quick-actions {
    width: 100%;
  }

  .action-list {
    flex-direction: row;
    flex-wrap: wrap;
  }

  .action-item {
    flex: 1;
    min-width: 200px;
  }
}
</style>
