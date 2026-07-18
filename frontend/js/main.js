/* ========================================================
 * 🚀 核心运行配置与安全鉴权体系
 * ======================================================== */
const API_BASE = '/api';
let currentUser = { username: '', name: '', role: '', permissions: [] }; 
let allOrdersLocal = []; 
let currentTab = 0; // 0=未完成, 1=已完成, 2=已出库, 3=原材料
let activeKeyboardTargetId = 'materialInputUse';

function getRoleName(role) {
    const maps = { 'super_admin': '超级管理员', 'admin': '管理员', 'employee': '员工', 'operator': '员工' };
    return maps[role] || role;
}

function hasPerm(permKey) {
    if (currentUser.role === 'super_admin') return true;
    return currentUser.permissions && currentUser.permissions.includes(permKey);
}

function getHeaders() {
    return {
        'Content-Type': 'application/json',
        'Username': String(currentUser.username),
        'Role': String(currentUser.role)
    };
}

/* ========================================================
 * 🤖 权限引擎与基础交互 (UI级别动态屏蔽)
 * ======================================================== */
function renderUI() {
    const loginSection = document.getElementById('loginSection');
    const mainSection = document.getElementById('mainSection');
    const fabContainer = document.getElementById('fabContainer');
    
    if (!currentUser.username) {
        loginSection.classList.remove('hidden');
        mainSection.style.display = 'none';
        if(fabContainer) fabContainer.style.display = 'none';
        return;
    }

    loginSection.classList.add('hidden');
    mainSection.style.display = 'block';
    if(fabContainer) fabContainer.style.display = 'block';

    const btnOpenViewUser = document.getElementById('btnOpenViewUser');
    const fabAddOrder = document.getElementById('fabAddOrder');
    const fabAddMaterial = document.getElementById('fabAddMaterial');

    if (hasPerm('system.user_manage')) btnOpenViewUser.style.display = 'block';
    else btnOpenViewUser.style.display = 'none';

    if (hasPerm('pending.add')) fabAddOrder.style.display = 'block';
    else fabAddOrder.style.display = 'none';

    if (hasPerm('material.add')) fabAddMaterial.style.display = 'block';
    else fabAddMaterial.style.display = 'none';
}

async function handleLogin() {
    const usernameInput = document.getElementById('loginUsername').value.trim();
    const passwordInput = document.getElementById('loginPassword').value.trim();
    if (!usernameInput || !passwordInput) return alert('请填入账号密码！');

    try {
        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: usernameInput, password: passwordInput })
        });
        const resData = await response.json();
        if (response.ok && resData.success) {
            currentUser = resData.user;
            if (!currentUser.permissions) currentUser.permissions = [];
            localStorage.setItem('local_user', JSON.stringify(currentUser));
            
            document.querySelectorAll('.tab-pane').forEach(el => el.dataset.hash = '');
            
            renderUI();
            switchTab(0); 
            
            setTimeout(() => {
                const speechBubble = document.getElementById('aiSpeechBubble');
                if(speechBubble) {
                    speechBubble.textContent = `欢迎回来，${currentUser.name || currentUser.username} 主人！`;
                    speechBubble.classList.add('show');
                    setTimeout(() => speechBubble.classList.remove('show'), 4000);
                }
            }, 1000);
        } else { alert(resData.message || '凭证错误，登录失败'); }
    } catch (error) { alert('本地服务端连接失败，请检查系统。'); }
}

function handleLogout() {
    currentUser = { username: '', name: '', role: '', permissions: [] };
    localStorage.removeItem('local_user');
    window.location.reload();
}

/* ========================================================
 * 📦 业务功能整合：动态数据渲染与【显示全部】巨幕弹窗引擎
 * ======================================================== */
function formatTextWithBreaks(text) {
    if (!text) return '';
    return text.replace(/\n/g, '<br>');
}

function getCurrentDateTime() {
    const now = new Date();
    const Y = now.getFullYear();
    const M = String(now.getMonth() + 1).padStart(2, '0');
    const D = String(now.getDate()).padStart(2, '0');
    const h = String(now.getHours()).padStart(2, '0');
    const m = String(now.getMinutes()).padStart(2, '0');
    return `${Y}-${M}-${D} ${h}:${m}`;
}

// 🎯 全新打造：【显示全部】超大触屏宽屏模态框激活器
function openShowAllGoodsModal(orderId) {
    const order = allOrdersLocal.find(o => o.id === orderId);
    if (!order) return;
    
    // 生成弹窗的大字报高亮明细
    let goodsLines = (order.goods_name || '').split('\n').filter(l => l.trim() !== '');
    let goodsHtml = '';
    goodsLines.forEach(line => {
        let formattedLine = line.replace(/([a-zA-Z0-9.]+)/g, '<span class="text-red-large" style="font-size: 42px;">$1</span>');
        goodsHtml += `<div class="modal-product" style="font-size: 26px; font-weight: bold; margin-bottom: 20px; border-bottom: 1px dashed #eee; padding-bottom: 12px; text-align: left;">${formattedLine}</div>`;
    });
    
    // 重用系统的旧 modal 结构，注入无限空间
    document.getElementById('confirmTargetId').value = orderId;
    document.getElementById('confirmTargetStatus').value = 'view_only';
    document.getElementById('newConfirmTitle').innerText = `📦 ${order.order_client || '未命名'} · 货物全量清单明细`;
    document.getElementById('newConfirmSubtitle').innerHTML = `单据创建日期 &nbsp; ${order.date || '未知时间'}`;
    document.getElementById('newConfirmBody').innerHTML = `<div style="max-height: 55vh; overflow-y: auto; padding-right: 10px;">${goodsHtml}</div>`;
    
    const confirmBtn = document.querySelector('#confirmModal .modal-btn-confirm');
    confirmBtn.innerText = '看完关闭';
    confirmBtn.style.backgroundColor = '#1890ff';
    
    document.getElementById('confirmModal').style.display = 'flex';
}

// 🎯 核心控制台：全向动态订单请求与画布装配核心
async function fetchOrders() {
    if (currentTab !== 0 && currentTab !== 1 && currentTab !== 2) return; 

    try {
        const response = await fetch(`${API_BASE}/orders`, { method: 'GET', headers: getHeaders() });
        const serverOrders = await response.json();
        allOrdersLocal = serverOrders;
        
        const confirmModal = document.getElementById('confirmModal');
        const shipOrderModal = document.getElementById('shipOrderModal');
        // 如果用户正在查看【显示全部】大弹窗，拦截其3秒重绘，保证阅读不被打断
        if ((confirmModal && confirmModal.style.display === 'flex' && document.getElementById('confirmTargetStatus').value === 'view_only') || 
            (shipOrderModal && shipOrderModal.style.display === 'flex')) return;

        const targetContainer = document.getElementById(`tab-${currentTab}`);

        if (currentTab === 2) {
            let shippedOrders = serverOrders.filter(o => o.status === 'shipped');
            
            const currentDataHash = JSON.stringify(shippedOrders);
            if (targetContainer.dataset.hash === currentDataHash) return; 
            targetContainer.dataset.hash = currentDataHash;

            if (shippedOrders.length === 0) {
                targetContainer.innerHTML = '<div style="color: #999; width:100%; text-align:center; padding:60px 20px; font-size:16px;">当前暂无已出库物流单据记录</div>';
                return;
            }
            
            let groups = {};
            shippedOrders.forEach(o => {
                let day = o.shipped_date ? o.shipped_date.substring(0, 10) : (o.completed_date ? o.completed_date.substring(0, 10) : '未知日期');
                if (!groups[day]) groups[day] = [];
                groups[day].push(o);
            });
            
            let tHtml = '<div class="timeline-container">';
            Object.keys(groups).sort((a, b) => b.localeCompare(a)).forEach(date => {
                tHtml += `<div class="timeline-group"><div class="timeline-date">${date}</div><div class="shipped-grid">`;
                groups[date].forEach(o => {
                    let isEmployee = currentUser.role === 'employee' || currentUser.role === 'operator';
                    let typeText = o.type == 1 ? '绝缘订单' : '中固订单';
                    let tagsHtml = '';
                    if (o.goods_packaging) tagsHtml += `<div class="s-tag s-tag-purple">包装:${o.goods_packaging}</div>`;
                    if (o.goods_weight) tagsHtml += `<div class="s-tag s-tag-cyan">货物总重量:${o.goods_weight}</div>`;
                    if (o.goods_quantity) tagsHtml += `<div class="s-tag s-tag-green">件数:${o.goods_quantity}</div>`;
                    
                    let detailBtnHtml = '';
                    if (hasPerm('shipped.detail')) {
                        detailBtnHtml = `<div class="s-detail-btn" onclick="openEditOrderModal(${o.id})">详情</div>`;
                    }
                    
                    tHtml += `
                    <div class="shipped-card">
                        <div class="ribbon">已出库</div>
                        <div class="shipped-left">
                            <div class="shipped-title">${o.goods_name || '无货物名称'}</div>
                            <div class="expand-list-text">展开列表</div>
                            <div class="s-tags-wrapper">${tagsHtml}</div>
                            ${o.remark ? `<div class="s-tags-wrapper"><div class="s-tag s-tag-pink">备注信息:${o.remark}</div></div>` : ''}
                            <div class="s-tags-wrapper"><div class="s-tag s-tag-pink" style="background:#e6f7ff; color:#1890ff; border:1px solid #b7e1ff;">物流单号:${o.logistics_no || '暂无单号'}</div></div>
                            <div class="shipped-bottom">
                                <div><div class="s-time-label">出库发货时间</div><div class="s-time-value">${o.shipped_date || o.completed_date || '未知'}</div></div>
                                ${detailBtnHtml}
                            </div>
                        </div>
                        <div class="shipped-right">
                            <div class="s-sub-title">${typeText}</div><div class="s-main-title">${o.order_client || '未命名'}</div>
                            <div class="s-info-list">
                                <div>收货姓名：${o.receiver_name || '未填'}</div>
                                <div>联系电话：${isEmployee ? '***' : (o.receiver_phone || '未填')}</div>
                                <div style="display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;" title="${o.receiver_address || ''}">收货地址：${o.receiver_address || '未填'}</div>
                            </div>
                        </div>
                    </div>`;
                });
                tHtml += `</div></div>`;
            });
            targetContainer.innerHTML = tHtml + '</div>';
            setTimeout(initExpandButtons, 50); 
            return;
        }

        let targetStatus = (currentTab === 1) ? 'completed' : 'pending';
        let filteredOrders = serverOrders.filter(o => o.status === 'completed' || o.status === 'pending'); // 扩宽防闪缓存池
        let displayedOrders = serverOrders.filter(o => o.status === targetStatus);

        if (targetStatus === 'completed') {
            displayedOrders.sort((a, b) => (b.completed_date || '').localeCompare(a.completed_date || ''));
        } else {
            displayedOrders.sort((a, b) => (b.date || '').localeCompare(a.date || ''));
        }

        if (displayedOrders.length === 0) {
            targetContainer.innerHTML = `<div style="color: #999; width:100%; text-align:center; padding:60px 20px; font-size:16px;">当前列表下无任何订单单据记录</div>`;
            return;
        }

        let html = '';
        displayedOrders.forEach(o => {
            let isEmployee = currentUser.role === 'employee' || currentUser.role === 'operator';
            let typeName = o.type == 1 ? '绝缘订单' : '中固订单';
            let goodsLines = (o.goods_name || '').split('\n').filter(l => l.trim() !== '');
            let totalLines = goodsLines.length;

            // ==================================================================
            // 🏭 未完成订单 (Tab 0) - 🎯 超过8行进行硬切断并追加【显示全部】蓝色动作
            // ==================================================================
            if (currentTab === 0) {
                let frontGoodsHtml = '';
                
                // 判断行数是否超标（大于8行）
                let isOverLimit = totalLines > 8;
                let renderLines = isOverLimit ? goodsLines.slice(0, 8) : goodsLines;

                renderLines.forEach(line => {
                    let formattedLine = line.replace(/([a-zA-Z0-9.]+)/g, '<span class="text-red-large">$1</span>');
                    frontGoodsHtml += `<div class="product-item auto-fit-text">${formattedLine}</div>`;
                });

                let tagsHtml = '';
                // 只有当行数在正常范围内（小于等于8行）时，正面才显示标签，超过直接隐藏让给视图
                if (!isOverLimit) {
                    if (o.goods_packaging) tagsHtml += `<div class="tag tag-blue">包装:${o.goods_packaging}</div>`;
                    if (o.goods_weight) tagsHtml += `<div class="tag tag-cyan">货物总重量:${o.goods_weight}</div>`;
                    if (o.remark) tagsHtml += `<div class="tag tag-red">备注信息:${o.remark}</div>`;
                    if (o.goods_quantity) tagsHtml += `<div class="tag tag-green">件数:${o.goods_quantity}</div>`;
                }

                let frontActs = '';
                if (hasPerm('pending.complete')) {
                    frontActs += `<button class="btn btn-primary" onclick="triggerStatusConfirm(${o.id}, 'completed')">确定完成</button>`;
                }
                
                // 🚀 核心逻辑：超过8行则把“详情页面”替换为蓝色突出的【显示全部】呼出大弹窗
                if (isOverLimit) {
                    frontActs += `<button class="btn btn-primary" style="background-color: #002766; color:#fff;" onclick="openShowAllGoodsModal(${o.id})">显示全部</button>`;
                } else if (hasPerm('pending.view_detail')) {
                    frontActs += `<button class="btn btn-default" onclick="toggleCard(this)">详情页面</button>`;
                }

                let backGoodsHtml = '';
                goodsLines.forEach(line => {
                    backGoodsHtml += `<div class="info-row text-red text-bold" style="white-space: normal; word-break: break-all;">${line}</div>`;
                });

                let backActs = '';
                if (hasPerm('pending.view_detail')) backActs += `<button class="btn btn-default" onclick="toggleCard(this)">⇦返回</button>`;
                if (hasPerm('pending.complete')) backActs += `<button class="btn btn-primary" onclick="triggerStatusConfirm(${o.id}, 'completed')">确定完成</button>`;
                if (hasPerm('pending.edit')) backActs += `<button class="btn btn-danger" onclick="openEditOrderModal(${o.id})">修改订单</button>`;
                if (hasPerm('pending.copy')) backActs += `<button class="btn btn-success" onclick="copyOrderInfo(${o.id})">复制信息</button>`;

                html += `
                <div class="flip-container">
                  <div class="flipper">
                    <div class="order-card front">
                      <div class="order-title">${o.order_client || '未命名归属'}订单</div>
                      <div class="order-header"><span><strong>${typeName}</strong> 产品列表</span><span>${o.date || '未知时间'}</span></div>
                      
                      <div class="product-list" style="overflow: hidden;">
                        ${frontGoodsHtml || '<div class="product-item" style="color:#999;">暂无货物明细</div>'}
                      </div>
                      
                      ${!isOverLimit ? `<div class="tags-wrapper"><div class="tags-label">标签&备注</div><div class="tags-container">${tagsHtml}</div></div>` : ''}
                      <div class="actions">${frontActs}</div>
                    </div>
                    <div class="order-card back">
                      <div class="order-title">${o.order_client || '未命名归属'}订单</div>
                      <div class="order-header"><span><strong>${typeName}</strong> 产品列表</span><span>${o.date || '未知时间'}</span></div>
                      <div class="product-list" style="overflow-y: auto;">
                        <div class="info-row" style="display: flex; justify-content: space-between;">
                          <span>收货姓名：${o.receiver_name || '未填'}</span>
                          <span>联系电话：${isEmployee ? '***' : (o.receiver_phone || '未填')}</span>
                        </div>
                        <div class="info-row">收货地址：${o.receiver_address || '未填'}</div>
                        <div class="info-row info-label" style="margin-top: 12px;">货物信息：</div>
                        ${backGoodsHtml}
                        <div style="display: flex; gap: 24px; margin-top: 16px;">
                          <div class="info-row"><span class="info-label">货物包装：</span>${o.goods_packaging || '无'}</div>
                          <div class="info-row"><span class="info-label">货物数量：</span><span class="text-red text-bold">${o.goods_weight || '无'}</span></div>
                        </div>
                        <div style="display: flex; gap: 24px;">
                          <div class="info-row"><span class="info-label">货物件数：</span>${o.goods_quantity || '无'}</div>
                          <div class="info-row"><span class="info-label">物流服务：</span>${isEmployee ? '***' : (o.logistics_service || '无')}</div>
                        </div>
                        ${o.remark ? `<div class="info-row"><span class="info-label">备注信息：</span><span class="text-red text-bold">${o.remark}</span></div>` : ''}
                      </div>
                      <div class="actions-back">${backActs}</div>
                    </div>
                  </div>
                </div>`;
            } 
            // ==========================================
            // 🏭 已完成订单 (Tab 1)
            // ==========================================
            else if (currentTab === 1) {
                let cGoodsHtml = '';
                goodsLines.forEach(line => {
                    cGoodsHtml += `<div class="info-row text-red text-bold" style="flex-shrink: 0; white-space: normal; word-break: break-all;">${line}</div>`;
                });

                let cActs = '';
                if (hasPerm('completed.uncomplete')) {
                    cActs += `<button class="btn btn-default" onclick="triggerStatusConfirm(${o.id}, 'pending')">撤销完成</button>`;
                }
                if (hasPerm('completed.ship')) {
                    cActs += `<button class="btn btn-primary" onclick="triggerShipModal(${o.id})">发货出库</button>`;
                }
                if (hasPerm('completed.delete')) {
                    cActs += `<button class="btn btn-danger" onclick="deleteOrder(${o.id})">物理删除</button>`;
                }
                if (hasPerm('completed.copy')) {
                    cActs += `<button class="btn btn-success" onclick="copyOrderInfo(${o.id})">复制信息</button>`;
                }

                let shortDate = o.completed_date ? o.completed_date.split(' ')[0] : '未知日期';

                html += `
                <div class="completed-card" style="padding: 20px 24px; font-size: 15px;">
                  <div class="order-title" style="font-size: 28px; margin-bottom: 8px;">${o.order_client || '未命名归属'}订单</div>
                  <div class="order-header" style="font-size: 15px; padding-bottom: 8px; margin-bottom: 12px;">
                    <span><strong>${typeName}</strong> 发货核对明细</span>
                    <span>${shortDate}</span>
                  </div>
                  
                  <div class="product-list" style="gap: 10px; overflow-y: auto;">
                    <div class="info-row" style="display: flex; justify-content: space-between;">
                      <span>收货姓名：${o.receiver_name || '未填'}</span>
                      <span>联系电话：${isEmployee ? '***' : (o.receiver_phone || '未填')}</span>
                    </div>
                    <div class="info-row">收货地址：${o.receiver_address || '未填'}</div>
                    
                    <div class="info-row info-label" style="margin-top: 6px;">货物信息：</div>
                    ${cGoodsHtml || '<div class="info-row" style="color:#999; flex-shrink: 0;">暂无货物明细</div>'}
                    
                    <div style="margin-top: auto; padding-top: 12px; display: flex; flex-direction: column; gap: 4px; flex-shrink: 0;">
                        <div style="display: flex; gap: 24px;">
                          <div class="info-row"><span class="info-label">货物包装：</span>${o.goods_packaging || '无'}</div>
                          <div class="info-row"><span class="info-label">货物数量：</span><span class="text-red text-bold">${o.goods_weight || '无'}</span></div>
                        </div>
                        <div style="display: flex; gap: 24px;">
                          <div class="info-row"><span class="info-label">货物件数：</span>${o.goods_quantity || '无'}</div>
                          <div class="info-row"><span class="info-label">物流服务：</span>${isEmployee ? '***' : (o.logistics_service || '无')}</div>
                        </div>
                        ${o.remark ? `<div class="info-row"><span class="info-label">备注信息：</span><span class="text-red text-bold">${o.remark}</span></div>` : ''}
                        
                        <div class="info-row" style="color: #888; border-top: 1px dashed #f0f0f0; padding-top: 8px; margin-top: 4px;">
                          <span class="info-label" style="color: #333;">完成时间：</span>${o.completed_date || '未知'}
                        </div>
                    </div>
                  </div>
                  
                  <div class="actions-back" style="margin-top: 12px; padding-top: 12px;">${cActs}</div>
                </div>`;
            }
        });
        
        targetContainer.innerHTML = html;
        setTimeout(autoFitText, 50);

    } catch (error) { 
        console.error("数据拉取引擎异常", error); 
    }
}

// ==========================================
// 🏭 引擎 D：原材料监控中心
// ==========================================
async function fetchMaterials() {
    if (currentTab !== 3) return;
    try {
        const response = await fetch(`${API_BASE}/materials`, { method: 'GET', headers: getHeaders() });
        const matData = await response.json();
        
        const targetContainer = document.getElementById('tab-3');
        let allRecords = matData.records || [];
        
        let currentStock = parseFloat(matData.total_stock) || 0;
        
        allRecords.sort((a, b) => a.date.localeCompare(b.date));
        allRecords.forEach(r => {
            currentStock -= (parseFloat(r.used) || 0);
            r.remaining = currentStock; 
        });
        
        const now = new Date();
        const threeDaysAgo = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 3).getTime();
        
        const filteredRecords = allRecords.filter(r => {
            const rDateMs = new Date(r.date.replace(/-/g, '/')).getTime();
            return rDateMs >= threeDaysAgo;
        });
        
        if (filteredRecords.length === 0) {
            targetContainer.innerHTML = '<div style="color: #999; width:100%; text-align:center; padding:60px 20px; font-size:16px;">最近 3 天内暂无原材料（树脂）使用记录</div>';
            return;
        }
        
        let groups = {};
        filteredRecords.forEach(r => {
            let day = r.date.substring(0, 10);
            if (!groups[day]) groups[day] = [];
            groups[day].push(r);
        });
        
        let html = '<div class="timeline-container">';
        Object.keys(groups).sort((a, b) => b.localeCompare(a)).forEach(date => {
            html += `<div class="timeline-group"><div class="timeline-date">${date}</div><div class="timeline-items">`;
            
            groups[date].sort((a, b) => b.date.localeCompare(a.date)).forEach(r => {
                let remarkText = r.remark ? r.remark : '无';
                html += `
                <div class="material-card">
                    <div class="m-data-group">
                        <div class="m-item"><span class="m-label-black">使用树脂：</span><span class="m-val-pink">${r.used} kg</span></div>
                        <div class="m-item"><span class="m-label-black">成品：</span><span class="m-val-green">${r.produced} kg</span></div>
                        <div class="m-item"><span class="m-label-blue">剩余：</span><span class="m-val-blue">${r.remaining.toFixed(1)} kg</span></div>
                        <div class="m-note">
                            <span class="m-note-label">备注：</span><span class="m-note-val">${remarkText}</span>
                        </div>
                    </div>
                </div>`;
            });
            html += `</div></div>`;
        });
        html += '</div>';
        
        targetContainer.innerHTML = html;
        
    } catch(error) {
        console.error('拉取原材料数据异常', error);
    }
}

function triggerShipModal(orderId) {
    document.getElementById('shipTargetId').value = orderId;
    document.getElementById('shipLogisticsNo').value = ''; 
    document.getElementById('shipOrderModal').style.display = 'flex';
}

function closeShipModal() {
    document.getElementById('shipOrderModal').style.display = 'none';
}

async function submitShipOrder() {
    const id = document.getElementById('shipTargetId').value;
    let logisticsNo = document.getElementById('shipLogisticsNo').value.trim();
    if (!logisticsNo) logisticsNo = '专车配送/自提'; 
    const currentDateTime = getCurrentDateTime();
    try {
        const response = await fetch(`${API_BASE}/orders/${id}`, {
            method: 'PUT',
            headers: getHeaders(),
            body: JSON.stringify({ status: 'shipped', logistics_no: logisticsNo, shipped_date: currentDateTime, completed_date: currentDateTime })
        });
        if (response.ok) { closeShipModal(); fetchOrders(); }
    } catch (e) { alert('发货出库网络通讯失败'); }
}

function triggerStatusConfirm(orderId, targetStatus) {
    // 🚀 安全拦截判定：如果是看完关闭【显示全部】大弹窗，直接关闭离开，不要发网络请求
    if (targetStatus === 'view_only') {
        closeModal();
        return;
    }

    const order = allOrdersLocal.find(o => o.id === orderId);
    if (!order) return;
    document.getElementById('confirmTargetId').value = orderId;
    document.getElementById('confirmTargetStatus').value = targetStatus;
    document.getElementById('newConfirmTitle').innerText = `${order.order_client || '未命名'}订单`;
    document.getElementById('newConfirmSubtitle').innerHTML = `单据日期 &nbsp; ${order.date || '未知时间'}`;
    
    let goodsLines = (order.goods_name || '').split('\n').filter(l => l.trim() !== '');
    let goodsHtml = '';
    goodsLines.forEach(line => {
        let formattedLine = line.replace(/([a-zA-Z0-9.]+)/g, '<span class="text-red-large">$1</span>');
        goodsHtml += `<div class="modal-product">${formattedLine}</div>`;
    });
    if (goodsHtml === '') goodsHtml = '<div class="modal-product" style="color:#999;">无详细货物内容</div>';
    
    document.getElementById('newConfirmBody').innerHTML = goodsHtml;
    const confirmBtn = document.querySelector('#confirmModal .modal-btn-confirm');
    if (targetStatus === 'pending') {
        confirmBtn.innerText = '确认撤销至未完成状态';
        confirmBtn.style.backgroundColor = '#ff4d4f'; 
    } else {
        confirmBtn.innerText = '确定完成';
        confirmBtn.style.backgroundColor = '#1890ff'; 
    }
    document.getElementById('confirmModal').style.display = 'flex';
}

function closeModal() { document.getElementById('confirmModal').style.display = 'none'; }

async function submitUpdateOrderStatus() {
    const id = document.getElementById('confirmTargetId').value;
    const status = document.getElementById('confirmTargetStatus').value;
    
    // 🚀 安全拦截：如果是只读查看模式，点击底部按钮直接退弹窗，不要更新接口
    if (status === 'view_only') {
        closeModal();
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/orders/${id}`, { method: 'PUT', headers: getHeaders(), body: JSON.stringify({ status: status }) });
        if (response.ok) { closeModal(); fetchOrders(); }
    } catch (error) { alert("流转操作异常"); }
}

async function deleteOrder(id) {
    if (!confirm(`严重安全警告：您确定要彻底物理删除这条订单记录吗？此操作无法撤销！`)) return;
    try {
        const response = await fetch(`${API_BASE}/orders/${id}`, { method: 'DELETE', headers: getHeaders() });
        if (response.ok) fetchOrders();
    } catch (e) {}
}

function copyOrderInfo(orderId) {
    const order = allOrdersLocal.find(o => o.id === orderId);
    if (!order) return;
    
    let isEmployee = currentUser.role === 'employee' || currentUser.role === 'operator';
    const typeText = (order.type == 1) ? '绝缘订单' : '中固订单';
    let nameLimit = (order.type == 1) ? 8 : 5;
    let shortGoodsName = (order.goods_name || '').replace(/\n/g, '').trim().substring(0, nameLimit);
    
    let clipText = `【${typeText}】\n`;
    if (order.receiver_name) clipText += `姓名：${order.receiver_name}\n`;
    if (!isEmployee && order.receiver_phone) clipText += `电话：${order.receiver_phone}\n`;
    if (order.receiver_address) clipText += `地址：${order.receiver_address}\n`;
    if (shortGoodsName) clipText += `名称：${shortGoodsName}\n`;
    if (order.goods_weight) clipText += `重量：${order.goods_weight}\n`;
    if (order.goods_quantity) clipText += `件数：${order.goods_quantity}\n`;
    if (order.goods_packaging) clipText += `包装：${order.goods_packaging}\n`;
    if (!isEmployee && order.logistics_service) clipText += `服务：${order.logistics_service}\n`;
    if (order.remark) clipText += `备注：${order.remark}\n`;

    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(clipText).then(() => { alert('✅ 极简物流信息已成功复制！'); }).catch(() => fallbackCopyTextToClipboard(clipText));
    } else fallbackCopyTextToClipboard(clipText);
}

function fallbackCopyTextToClipboard(text) {
    let textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed"; textArea.style.opacity = "0";
    document.body.appendChild(textArea);
    textArea.focus(); textArea.select();
    try { document.execCommand('copy'); alert('✅ 极简物流信息已成功复制！'); } 
    catch (err) { alert('⚠️ 自动复制失败，请手动复制。'); }
    document.body.removeChild(textArea);
}

function validatePayload(payload) {
    if (!payload.receiver_phone || !payload.receiver_address || !payload.goods_name || !payload.goods_weight) return '【收货电话】、【地址】、【名称】、【重量】为必填项！';
    if (!/^(?:1[3-9]\d{9}|0\d{2,3}-\d{7,8})$/.test(payload.receiver_phone)) return '【收货电话】格式不正确！必须是11位手机号或带区号的座机。';
    return null; 
}

function smartParse(prefix) {
    const text = document.getElementById(`${prefix}OrderTitle`).value;
    if (!text.trim()) return alert('请先在上方输入框粘贴或填写内容，再点击识别！');
    const lines = text.split('\n').map(l => l.trim()).filter(l => l !== '');
    if (lines.length === 0) return;
    
    document.getElementById(`${prefix}OrderClient`).value = lines[0].replace(/[:：]$/, '').trim();
    if (lines.length > 1) {
        let line2 = lines[1];
        let phoneMatch = line2.match(/(1[3-9]\d{9}|0\d{2,3}-\d{7,8})/);
        let phone = phoneMatch ? phoneMatch[0] : '';
        let name = '', address = '';
        let strWithoutPhone = line2.replace(phone, '').replace(/(?:电话|联系方式|手机)[:：]?\s*/g, '');
        let nameMatch = strWithoutPhone.match(/(?:姓名|收货人)[:：]\s*([^\s宏区区县镇村街道路号栋室楼]{1,5})/);
        if (nameMatch) { name = nameMatch[1]; strWithoutPhone = strWithoutPhone.replace(nameMatch[0], ''); }
        else {
            let qMatch = strWithoutPhone.match(/[?？]\s*([^\s。，,;；:：]{1,4})/);
            if (qMatch) { name = qMatch[1]; strWithoutPhone = strWithoutPhone.replace(qMatch[0], ''); }
        }
        let addrMatch = strWithoutPhone.match(/(?:地址)[:：]?\s*(.*)/);
        if (addrMatch) { address = addrMatch[1]; strWithoutPhone = strWithoutPhone.replace(addrMatch[0], ''); } 
        else { address = strWithoutPhone; }
        
        if (!name) {
            let parts = address.split(/[\s。，,;；]+/).filter(p => p.trim() !== '');
            let potentialName = parts.find(p => p.length >= 2 && p.length <= 4 && !/[省市区县镇村街道路号栋室楼]/.test(p));
            if (potentialName) { name = potentialName; address = address.replace(potentialName, ''); } 
            else {
                let fallbackParts = line2.split(phone);
                name = fallbackParts[0].replace(/收货人|电话|联系方式|:|：/g, '').trim();
                address = (fallbackParts[1] || '').replace(/^[。，,.;:\s]+/, '').trim();
                if (name.length > 6 && address.length <= 6) { let temp = name; name = address; address = temp; }
            }
        }
        document.getElementById(`${prefix}ReceiverName`).value = name.replace(/^[。，,;；\s]+|[。，,;；\s]+$/g, '').replace(/[?？]/g, '');
        document.getElementById(`${prefix}ReceiverPhone`).value = phone;
        document.getElementById(`${prefix}ReceiverAddress`).value = address.replace(/(?:地址)[:：]?g, '').replace(/^[。，,;；\s]+|[。，,;；\s]+$/g, '');
    }

    if (lines.length > 2) {
        let goodsStr = lines.slice(2).join('\n');
        document.getElementById(`${prefix}GoodsName`).value = goodsStr;
        let totalWeight = 0, tempStr = goodsStr;
        let calcRegex1 = /(\d+(?:\.\d+)?)\s*(?:[A-Za-z\u4e00-\u9fa5]{0,6})?\s*([*xX✖️×\/÷])\s*(\d+(?:\.\d+)?)/g;
        let match;
        while ((match = calcRegex1.exec(tempStr)) !== null) {
            let val = /[*/÷]/.test(match[2]) ? (/[*xX✖️×]/.test(match[2]) ? parseFloat(match[1]) * parseFloat(match[3]) : parseFloat(match[1]) / parseFloat(match[3])) : 0;
            if (tempStr.substring(0, match.index).trim().endsWith('-')) totalWeight -= val; else totalWeight += val; 
            tempStr = tempStr.substring(0, match.index) + " ".repeat(match[0].length) + tempStr.substring(match.index + match[0].length);
        }
        let calcRegex2 = /([+-])\s*(\d+(?:\.\d+)?)/g;
        while ((match = calcRegex2.exec(tempStr)) !== null) {
            if (match[1] === '+') totalWeight += parseFloat(match[2]); else totalWeight -= parseFloat(match[2]);
        }
        if (totalWeight !== 0) document.getElementById(`${prefix}GoodsWeight`).value = (Math.round(totalWeight * 100) / 100) + 'kg';
        else document.getElementById(`${prefix}GoodsWeight`).value = '';
    }
}

async function createOrder() {
    const payload = {
        title: document.getElementById('newOrderTitle').value, 
        type: parseInt(document.getElementById('newOrderType').value),
        order_client: document.getElementById('newOrderClient').value.trim(), 
        receiver_name: document.getElementById('newReceiverName').value.trim(),
        receiver_phone: document.getElementById('newReceiverPhone').value.trim(), 
        receiver_address: document.getElementById('newReceiverAddress').value.trim(),
        goods_name: document.getElementById('newGoodsName').value.trim(), 
        goods_weight: document.getElementById('newGoodsWeight').value.trim(),
        goods_quantity: document.getElementById('newGoodsQuantity').value.trim(), 
        goods_packaging: document.getElementById('newGoodsPackaging').value,
        logistics_service: document.getElementById('newLogisticsService').value, 
        remark: document.getElementById('newOrderRemark').value.trim()
    };
    const errMsg = validatePayload(payload);
    if (errMsg) return alert('发单失败：' + errMsg);
    try {
        const response = await fetch(`${API_BASE}/orders`, { method: 'POST', headers: getHeaders(), body: JSON.stringify(payload) });
        if (response.ok) {
            toggleModal('createOrderModal', false); 
            document.querySelectorAll('#createOrderModal input, #createOrderModal textarea').forEach(el => el.value = '');
            switchTab(0); 
        }
    } catch (error) {}
}

function openEditOrderModal(orderId) {
    const order = allOrdersLocal.find(o => o.id === orderId);
    if (!order) return;
    document.getElementById('editOrderId').value = order.id;
    document.getElementById('editOrderDate').value = order.date || '';
    document.getElementById('editOrderType').value = order.type !== undefined ? order.type : 0;
    document.getElementById('editOrderTitle').value = order.title || '';
    
    ['OrderClient', 'ReceiverName', 'ReceiverPhone', 'ReceiverAddress', 'GoodsName', 'GoodsWeight', 'GoodsQuantity'].forEach(k => {
        const el = document.getElementById(`edit${k}`);
        if (el) el.value = order[k.replace(/([A-Z])/g, "_$1").toLowerCase().substring(1)] || '';
    });
    
    document.getElementById('editGoodsPackaging').value = order.goods_packaging || '桶装';
    document.getElementById('editLogisticsService').value = order.logistics_service || '送货上门+回单拍照回传';
    document.getElementById('editOrderRemark').value = order.remark || '';
    
    const delBtn = document.getElementById('btnDeleteOrderInEdit');
    if (delBtn) {
        if (hasPerm('pending.delete') || hasPerm('completed.delete')) delBtn.style.display = 'inline-block';
        else delBtn.style.display = 'none';
    }
    toggleModal('editOrderModal', true);
}

async function submitEditOrder() {
    const id = document.getElementById('editOrderId').value;
    const date = document.getElementById('editOrderDate').value.trim();
    if (!date) return alert('时间不能为空！');
    const payload = {
        title: document.getElementById('editOrderTitle').value, 
        type: parseInt(document.getElementById('editOrderType').value), 
        date: date,
        order_client: document.getElementById('editOrderClient').value.trim(), 
        receiver_name: document.getElementById('editReceiverName').value.trim(),
        receiver_phone: document.getElementById('editReceiverPhone').value.trim(), 
        receiver_address: document.getElementById('editReceiverAddress').value.trim(),
        goods_name: document.getElementById('editGoodsName').value.trim(), 
        goods_weight: document.getElementById('editGoodsWeight').value.trim(),
        goods_quantity: document.getElementById('editGoodsQuantity').value.trim(), 
        goods_packaging: document.getElementById('editGoodsPackaging').value,
        logistics_service: document.getElementById('editLogisticsService').value, 
        remark: document.getElementById('editOrderRemark').value.trim()
    };
    const errMsg = validatePayload(payload);
    if (errMsg) return alert('修改失败：' + errMsg);
    try {
        const response = await fetch(`${API_BASE}/orders/${id}/edit`, { method: 'PUT', headers: getHeaders(), body: JSON.stringify(payload) });
        if (response.ok) { toggleModal('editOrderModal', false); fetchOrders(); }
    } catch (e) { alert('请求异常'); }
}

async function deleteOrderInEdit() {
    const id = document.getElementById('editOrderId').value;
    if (!id) return;
    if (!confirm('安全警告：您确定要彻底物理删除这条订单记录吗？此操作无法撤销！')) return;
    try {
        const response = await fetch(`${API_BASE}/orders/${id}`, { method: 'DELETE', headers: getHeaders() });
        if (response.ok) { toggleModal('editOrderModal', false); fetchOrders(); }
    } catch (e) { alert('物理删除请求异常'); }
}

/* ========================================================
 * 🏭 原材料录入与物理键盘
 * ======================================================== */
function openUploadMaterialModal() {
    toggleModal('uploadMaterialModal', true);
    setActiveKeyboardTarget('materialInputUse');
    document.getElementById('materialInputUse').value = '';
    document.getElementById('materialInputProduct').value = '';
}

function setActiveKeyboardTarget(id) {
    activeKeyboardTargetId = id;
    document.querySelectorAll('.keyboard-target').forEach(el => el.classList.remove('active-target'));
    document.getElementById(id).classList.add('active-target');
}

function pressKey(key) {
    const targetInput = document.getElementById(activeKeyboardTargetId);
    let currentVal = targetInput.value;
    if (key === 'clear') targetInput.value = '';
    else if (key === 'backspace') targetInput.value = currentVal.substring(0, currentVal.length - 1);
    else if (key === '.') { if (!currentVal.includes('.')) targetInput.value = currentVal + '.'; }
    else targetInput.value = currentVal + key;
}

async function uploadMaterialRecord() {
    const usedVal = parseFloat(document.getElementById('materialInputUse').value);
    const productVal = parseFloat(document.getElementById('materialInputProduct').value);
    if (isNaN(usedVal) || isNaN(productVal)) return alert('录入失败：请完整输入耗材与产出量！');

    try {
        const response = await fetch(`${API_BASE}/materials`, { method: 'POST', headers: getHeaders(), body: JSON.stringify({ used: usedVal, produced: productVal }) });
        if (response.ok) {
            toggleModal('uploadMaterialModal', false); 
            document.getElementById('successNotifyDetail').innerText = `物料报表已存入：\n消耗: ${usedVal} kg\n产出: ${productVal} kg`;
            toggleModal('uploadSuccessNotifyModal', true);
            if (currentTab === 3) fetchMaterials();
        }
    } catch (e) {}
}

/* ========================================================
 * 🎨 前端 UI 界面的交互动效 
 * ======================================================== */
function toggleModal(modalId, show) {
    const modal = document.getElementById(modalId);
    if (show) modal.classList.remove('hidden');
    else modal.classList.add('hidden');
}

function switchTab(index) {
  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach(item => item.classList.remove('active'));
  navItems[index].classList.add('active');

  const tabPanes = document.querySelectorAll('.tab-pane');
  tabPanes.forEach(pane => pane.classList.remove('active'));
  document.getElementById('tab-' + index).classList.add('active');

  currentTab = index;
  
  if (index === 0 || index === 1 || index === 2) {
      fetchOrders();
  } else if (index === 3) {
      fetchMaterials();
  }

  if (index === 2) initExpandButtons(); 
}

function toggleCard(btn) {
  const flipper = btn.closest('.flipper');
  if (flipper) {
      flipper.classList.toggle('flipped');
      setTimeout(autoFitText, 350); 
  }
}

function autoFitText() {
    document.querySelectorAll(`#tab-${currentTab} .auto-fit-text`).forEach(el => {
        el.style.fontSize = '';
        const largeTexts = el.querySelectorAll('.text-red-large');
        largeTexts.forEach(c => c.style.fontSize = '');
        if (el.clientWidth === 0) return;
        let currentSize = parseFloat(window.getComputedStyle(el).fontSize);
        let childrenDeltas = Array.from(largeTexts).map(c => { return parseFloat(window.getComputedStyle(c).fontSize) - currentSize; });
        let iterations = 0; 
        while (el.scrollWidth > el.clientWidth && currentSize > 12 && iterations < 50) {
            currentSize -= 0.5;
            el.style.fontSize = currentSize + 'px';
            largeTexts.forEach((c, index) => { c.style.fontSize = (currentSize + childrenDeltas[index]) + 'px'; });
            iterations++;
        }
    });
}

window.addEventListener('resize', () => {
    initExpandButtons();
    if (currentTab === 0 || currentTab === 1) autoFitText();
});

function initExpandButtons() {
  const containers = document.querySelectorAll('#tab-2 .shipped-left');
  containers.forEach(container => {
    const title = container.querySelector('.shipped-title');
    const expandBtn = container.querySelector('.expand-list-text');
    if (title && expandBtn) {
      const isExpanded = title.classList.contains('expanded');
      title.classList.remove('expanded');
      if (title.scrollWidth > title.clientWidth) {
        expandBtn.style.display = 'block'; 
        if (isExpanded) {
          title.classList.add('expanded');
          expandBtn.textContent = '收起列表';
        } else expandBtn.textContent = '展开列表';
      } else expandBtn.style.display = 'none';

      if (!expandBtn.dataset.bound) {
        expandBtn.dataset.bound = "true";
        expandBtn.addEventListener('click', function() {
          if (title.classList.contains('expanded')) { title.classList.remove('expanded'); expandBtn.textContent = '展开列表'; } 
          else { title.classList.add('expanded'); expandBtn.textContent = '收起列表'; }
        });
      }
    }
  });
}

window.addEventListener('load', initExpandButtons);

/* ========================================================
 * 🖱️ 工业触屏/滑鼠滚轮横向映射控制 (全屏画廊左右滑完美恢复)
 * ======================================================== */
document.querySelectorAll('#tab-0, #tab-1').forEach(container => {
    container.addEventListener('wheel', function(e) {
        if (e.deltaY !== 0) {
            e.preventDefault(); 
            this.scrollLeft += e.deltaY; 
        }
    }, { passive: false });
});

/* ========================================================
 * 🔄 系统初始化启动挂载点
 * ======================================================== */
window.onload = function() {
    const savedUser = localStorage.getItem('local_user');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        if (!currentUser.permissions) currentUser.permissions = [];
        renderUI();
        switchTab(0);

        setInterval(function() {
            const editModal = document.getElementById('editOrderModal');
            const shipModal = document.getElementById('shipOrderModal');
            
            if (document.querySelector('.flipper.flipped') || 
                document.getElementById('confirmModal').style.display === 'flex' ||
                (shipModal && shipModal.style.display === 'flex') ||
                (editModal && !editModal.classList.contains('hidden'))) {
                return;
            }
            
            if (currentTab === 0) {
                fetchOrders();
            }
            
            if (typeof refreshUserList === 'function' && !document.getElementById('viewUserModal').classList.contains('hidden')) {
                refreshUserList();
            }
            
        }, 3000); 

    } else {
        renderUI(); 
    }
};