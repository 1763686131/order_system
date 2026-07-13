const API_BASE = '/api';
let currentUser = { username: '', role: '' };
let allOrdersLocal = []; 
let currentDashboardMode = 'order'; 

function getRoleName(role) {
    const maps = { 'super_admin': '超级管理员', 'admin': '管理员', 'operator': '操作员' };
    return maps[role] || role;
}

function getHeaders() {
    return {
        'Content-Type': 'application/json',
        'Username': String(currentUser.username),
        'Role': String(currentUser.role)
    };
}

function initFilterDates() {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - 3); 
    document.getElementById('filterStartDate').value = startDate.toISOString().split('T')[0];
    document.getElementById('filterEndDate').value = endDate.toISOString().split('T')[0];
}

function toggleModal(modalId, show) {
    const modal = document.getElementById(modalId);
    if (show) modal.classList.remove('hidden');
    else modal.classList.add('hidden');
}

function switchDashboardView() {
    const btn = document.getElementById('btnSwitchPanel');
    const orderGrid = document.getElementById('orderGrid');
    const materialWrapper = document.getElementById('materialViewWrapper');
    const filterStatus = document.getElementById('filterStatus');
    const statusFilterLabel = document.getElementById('statusFilterLabel');
    const listTitle = document.getElementById('listTitle');

    if (currentDashboardMode === 'order') {
        currentDashboardMode = 'material';
        btn.innerText = '📋 查看业务订单';
        listTitle.innerText = '🏭 原材料数据列表';
        orderGrid.classList.add('hidden');
        materialWrapper.classList.remove('hidden');
        filterStatus.classList.add('hidden');
        statusFilterLabel.classList.add('hidden');
        fetchMaterialRecords();
    } else {
        currentDashboardMode = 'order';
        btn.innerText = '📊 查看原材料数据';
        listTitle.innerText = '📋 订单看板列表';
        orderGrid.classList.remove('hidden');
        materialWrapper.classList.add('hidden');
        filterStatus.classList.remove('hidden');
        statusFilterLabel.classList.remove('hidden');
        fetchOrders();
    }
}

function refreshDashboardData() {
    if (currentDashboardMode === 'order') {
        fetchOrders();
    } else {
        fetchMaterialRecords();
    }
}

function renderUI() {
    const loginSection = document.getElementById('loginSection');
    const mainSection = document.getElementById('mainSection');
    const btnOpenAddUser = document.getElementById('btnOpenAddUser');
    const btnOpenViewUser = document.getElementById('btnOpenViewUser');
    const sidebarAdminSection = document.getElementById('sidebarAdminSection');
    const btnEditStockAction = document.getElementById('btnEditStockAction');

    if (!currentUser.username) {
        loginSection.classList.remove('hidden');
        mainSection.classList.add('hidden');
        return;
    }

    loginSection.classList.add('hidden');
    mainSection.classList.remove('hidden');

    document.getElementById('currentUsername').innerText = currentUser.username;
    document.getElementById('currentUserRoleTag').innerText = getRoleName(currentUser.role);

    // 🎯 权限隔离控制：只有超管和管理员才能看并操作总库设定修改按钮
    if (currentUser.role === 'super_admin') {
        btnOpenAddUser.classList.remove('hidden');
        btnOpenViewUser.classList.remove('hidden');
        sidebarAdminSection.classList.remove('hidden');
        btnEditStockAction.classList.remove('hidden');
    } else if (currentUser.role === 'admin') {
        btnOpenAddUser.classList.add('hidden');
        btnOpenViewUser.classList.add('hidden');
        sidebarAdminSection.classList.remove('hidden');
        btnEditStockAction.classList.remove('hidden');
    } else {
        btnOpenAddUser.classList.add('hidden');
        btnOpenViewUser.classList.add('hidden');
        sidebarAdminSection.classList.add('hidden');
        btnEditStockAction.classList.add('hidden');
    }
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
            localStorage.setItem('local_user', JSON.stringify(currentUser));
            renderUI();
            initFilterDates();
            refreshDashboardData();
        } else {
            alert(resData.message || '凭证错误，登录失败');
        }
    } catch (error) {
        alert('本地服务端连接失败，请检查 Docker。');
    }
}

function formatTextWithBreaks(text) {
    if (!text) return '';
    return text.replace(/\n/g, '<br>');
}

function handleLogout() {
    currentUser = { username: '', role: '' };
    localStorage.removeItem('local_user');
    document.getElementById('loginUsername').value = '';
    document.getElementById('loginPassword').value = '';
    renderUI();
}

async function fetchOrders() {
    if (currentDashboardMode !== 'order') return;
    try {
        const response = await fetch(`${API_BASE}/orders`, { method: 'GET', headers: getHeaders() });
        const serverOrders = await response.json();
        allOrdersLocal = serverOrders;
        
        if (!document.getElementById('statusConfirmModal').classList.contains('hidden')) return; 

        const gridContainer = document.getElementById('orderGrid');
        gridContainer.innerHTML = ''; 

        const selectedStatus = document.getElementById('filterStatus').value;
        const startDateStr = document.getElementById('filterStartDate').value;
        const endDateStr = document.getElementById('filterEndDate').value;

        const filteredOrders = serverOrders.filter(order => {
            if (order.status !== selectedStatus) return false;
            if (order.date) {
                const orderDay = order.date.substring(0, 10); 
                if (startDateStr && orderDay < startDateStr) return false;
                if (endDateStr && orderDay > endDateStr) return false;
            }
            return true;
        });

        if (filteredOrders.length === 0) {
            gridContainer.innerHTML = '<div style="color: #999; grid-column: 1/-1; text-align:center; padding:40px;">当前筛选条件下无看板订单</div>';
            return;
        }

        filteredOrders.forEach(order => {
            const card = document.createElement('div');
            const orderType = order.type !== undefined ? order.type : 0;
            card.className = `order-card type-${orderType} status-${order.status}`;
            
            const typeText = orderType == 1 ? "绝缘订单" : "中固订单";
            let isActionHidden = (currentUser.role === 'operator' && order.status === 'completed');

            let actionBtn = '';
            if (!isActionHidden) {
                if (order.status === 'pending') {
                    actionBtn = `<button class="btn-success" onclick="triggerStatusConfirm(${order.id}, 'completed')">完成业务</button>`;
                } else {
                    actionBtn = `<button class="btn-secondary" onclick="triggerStatusConfirm(${order.id}, 'pending')">设为未完成</button>`;
                }
            }

            let superActionHtml = '';
            if (currentUser.role === 'super_admin') {
                superActionHtml = `
                <div class="action-row-super">
                    <button class="btn-warning" onclick="openEditOrderModal(${order.id})">✍️ 修改</button>
                    <button class="btn-danger" onclick="deleteOrder(${order.id})">🗑️ 删除</button>
                </div>
                `;
            }

            const footerActionsHtml = (actionBtn || superActionHtml) ? `
                <div class="card-actions">
                    ${actionBtn ? `<div class="action-row-main">${actionBtn}</div>` : ''}
                    ${superActionHtml}
                </div>
            ` : '';

            let completedDateHtml = '';
            if (order.status === 'completed' && order.completed_date) {
                completedDateHtml = `<div class="card-completed-date">✔ 完成: ${order.completed_date}</div>`;
            }

            card.innerHTML = `
                <div class="card-top">
                    <span class="card-title-tag">[#${order.id}] ${typeText}</span>
                    <span>🕒 创建: ${order.date || '未知'}</span>
                </div>
                <div class="card-body">
                    <h4>${formatTextWithBreaks(order.title)}</h4>
                </div>
                <div class="card-footer-wrapper">
                    ${completedDateHtml}
                    ${footerActionsHtml}
                </div>
            `;
            gridContainer.appendChild(card);
        });
    } catch (error) { console.error("订单数据加载失败", error); }
}

// 🎯 原材料核心数据驱动盘
async function fetchMaterialRecords() {
    if (currentDashboardMode !== 'material') return;
    try {
        const response = await fetch(`${API_BASE}/materials`, { method: 'GET', headers: getHeaders() });
        const resData = await response.json();
        
        // 渲染顶部工厂储备量文字标签
        document.getElementById('displayTotalStock').innerText = `${resData.total_stock} kg`;

        const container = document.getElementById('materialCapsuleList');
        container.innerHTML = '';

        const startDateStr = document.getElementById('filterStartDate').value;
        const endDateStr = document.getElementById('filterEndDate').value;

        const filteredRecords = resData.records.filter(item => {
            if (item.date) {
                const day = item.date.substring(0, 10);
                if (startDateStr && day < startDateStr) return false;
                if (endDateStr && day > endDateStr) return false;
            }
            return true;
        });

        // 工业联算公式
        let totalUsed = 0;
        resData.records.forEach(item => {
            totalUsed += parseFloat(item.used || 0);
        });
        const remains = parseFloat(resData.total_stock || 0) - totalUsed;
        document.getElementById('remainedMaterialCapsule').innerText = `剩余原材料：${remains.toFixed(2)} kg`;

        if (filteredRecords.length === 0) {
            container.innerHTML = '<div style="color: #999; text-align:center; padding:40px;">当前筛选区间内无原材料使用明细</div>';
            return;
        }

        filteredRecords.forEach(item => {
            const row = document.createElement('div');
            row.className = 'material-capsule-item';

            let actionHtml = '';
            if (currentUser.role === 'super_admin' || currentUser.role === 'admin') {
                actionHtml = `
                    <div class="capsule-right">
                        <button class="btn-warning" onclick="openEditMaterialModal(${item.id}, ${item.used}, ${item.produced})">✍️ 修改</button>
                    </div>
                `;
            }

            row.innerHTML = `
                <div class="capsule-left">
                    <span class="capsule-time">🕒 ${item.date}</span>
                    <span class="capsule-use-tag">原材料使用：<strong>${item.used} kg</strong></span>
                    <span class="capsule-product-tag">成品数量：<strong>${item.produced} kg</strong></span>
                </div>
                ${actionHtml}
            `;
            container.appendChild(row);
        });

    } catch (e) { console.error("获取原材料清单异常", e); }
}

// 🎯 上传原材料数据组，并调取屏幕中央提示模态框
async function uploadMaterialRecord() {
    const usedInput = document.getElementById('materialInputUse');
    const productInput = document.getElementById('materialInputProduct');
    const usedVal = parseFloat(usedInput.value);
    const productVal = parseFloat(productInput.value);

    if (isNaN(usedVal) || isNaN(productVal)) {
        return alert('录入失败：请确保原材料和出货成品数量均已填入有效数字！');
    }

    try {
        const response = await fetch(`${API_BASE}/materials`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ used: usedVal, produced: productVal })
        });
        if (response.ok) {
            usedInput.value = '';
            productInput.value = '';
            
            // 🎯 核心需求：触发屏幕正中央的优雅成功通知弹窗
            document.getElementById('successNotifyDetail').innerText = `已成功向系统存入以下盘点数据：\n消耗原材料: ${usedVal} kg\n产出总成品: ${productVal} kg`;
            toggleModal('uploadSuccessNotifyModal', true);

            refreshMaterialViewAfterAction();
        }
    } catch (e) { alert('物料断网上传异常'); }
}

// 🎯 触发工厂总储备修改窗口
function triggerStockModifyModal() {
    const currentStock = document.getElementById('displayTotalStock').innerText.replace(' kg', '');
    document.getElementById('newStockInput').value = currentStock;
    toggleModal('editTotalStockModal', true);
}

// 🎯 提交修改后的总储备
async function submitUpdateTotalStockValue() {
    const newStock = parseFloat(document.getElementById('newStockInput').value);
    if (isNaN(newStock) || newStock < 0) return alert('请输入有效的数字库存储备！');

    try {
        const response = await fetch(`${API_BASE}/materials/stock`, {
            method: 'PUT',
            headers: getHeaders(),
            body: JSON.stringify({ total_stock: newStock })
        });
        if (response.ok) {
            toggleModal('editTotalStockModal', false);
            fetchMaterialRecords();
        }
    } catch (e) { alert('更新总物料库异常'); }
}

function openEditMaterialModal(id, used, produced) {
    document.getElementById('editMaterialId').value = id;
    document.getElementById('editMaterialUse').value = used;
    document.getElementById('editMaterialProduct').value = produced;
    toggleModal('editMaterialModal', true);
}

async function submitEditMaterial() {
    const id = document.getElementById('editMaterialId').value;
    const used = parseFloat(document.getElementById('editMaterialUse').value) || 0;
    const produced = parseFloat(document.getElementById('editMaterialProduct').value) || 0;

    try {
        const response = await fetch(`${API_BASE}/materials/${id}`, {
            method: 'PUT',
            headers: getHeaders(),
            body: JSON.stringify({ used: used, produced: produced })
        });
        if (response.ok) {
            toggleModal('editMaterialModal', false);
            fetchMaterialRecords();
        }
    } catch (e) { alert('修改流水失败'); }
}

function refreshMaterialViewAfterAction() {
    if (currentDashboardMode !== 'material') {
        switchDashboardView(); 
    } else {
        fetchMaterialRecords();
    }
}

function triggerStatusConfirm(orderId, targetStatus) {
    const order = allOrdersLocal.find(o => o.id === orderId);
    if (!order) return;
    document.getElementById('confirmTargetId').value = orderId;
    document.getElementById('confirmTargetStatus').value = targetStatus;
    const orderType = order.type !== undefined ? order.type : 0;
    document.getElementById('previewCardType').innerText = `[#${order.id}] ${orderType == 1 ? '绝缘订单' : '中固订单'}`;
    document.getElementById('previewCardDate').innerText = `🕒 创建: ${order.date || '未知'}`;
    document.getElementById('previewCardTitle').innerHTML = formatTextWithBreaks(order.title);
    const previewBox = document.getElementById('confirmCardPreview');
    const tipText = document.getElementById('confirmTipText');
    const submitBtn = document.getElementById('btnConfirmSubmit');
    if (targetStatus === 'completed') {
        tipText.innerText = "🛑 确认将以下订单标记为【已完成】吗？";
        previewBox.className = "confirm-card-preview preview-completed";
        submitBtn.className = "btn-success";
    } else {
        tipText.innerText = "⚠️ 确认将以下订单恢复为【未完成】吗？";
        previewBox.className = "confirm-card-preview preview-pending";
        submitBtn.className = "btn-warning";
    }
    toggleModal('statusConfirmModal', true);
}

async function submitUpdateOrderStatus() {
    const id = document.getElementById('confirmTargetId').value;
    const status = document.getElementById('confirmTargetStatus').value;
    try {
        const response = await fetch(`${API_BASE}/orders/${id}`, {
            method: 'PUT',
            headers: getHeaders(),
            body: JSON.stringify({ status: status })
        });
        if (response.ok) {
            toggleModal('statusConfirmModal', false);
            fetchOrders();
        }
    } catch (error) { alert('调整状态失败'); }
}

async function createOrder() {
    const titleInput = document.getElementById('newOrderTitle');
    const typeSelect = document.getElementById('newOrderType');
    const title = titleInput.value; 
    if (!title.trim()) return alert('请录入商品参数或货物文本！');
    try {
        const response = await fetch(`${API_BASE}/orders`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ title: title, type: parseInt(typeSelect.value) })
        });
        if (response.ok) {
            titleInput.value = '';
            fetchOrders();
        }
    } catch (error) { alert('断网发单失败'); }
}

function openEditOrderModal(orderId) {
    const order = allOrdersLocal.find(o => o.id === orderId);
    if (!order) return;
    document.getElementById('editOrderId').value = order.id;
    document.getElementById('editOrderType').value = order.type !== undefined ? order.type : 0;
    document.getElementById('editOrderTitle').value = order.title;
    document.getElementById('editOrderDate').value = order.date || '';
    toggleModal('editOrderModal', true);
}

async function submitEditOrder() {
    const id = document.getElementById('editOrderId').value;
    const type = document.getElementById('editOrderType').value;
    const title = document.getElementById('editOrderTitle').value;
    const date = document.getElementById('editOrderDate').value.trim();
    if (!title.trim() || !date) return alert('修改项不能为空！');
    try {
        const response = await fetch(`${API_BASE}/orders/${id}/edit`, {
            method: 'PUT',
            headers: getHeaders(),
            body: JSON.stringify({ title: title, type: parseInt(type), date: date })
        });
        if (response.ok) {
            toggleModal('editOrderModal', false);
            fetchOrders();
        }
    } catch (e) { alert('请求异常'); }
}

async function deleteOrder(id) {
    if (!confirm(`安全警告：确定要物理【删除】单号为 #${id} 的订单吗？`)) return;
    try {
        const response = await fetch(`${API_BASE}/orders/${id}`, { method: 'DELETE', headers: getHeaders() });
        if (response.ok) fetchOrders();
    } catch (e) { alert('删除异常'); }
}

async function createUser() {
    const usernameInput = document.getElementById('newUsername');
    const passwordInput = document.getElementById('newPassword');
    const roleSelect = document.getElementById('newRole');
    if (!usernameInput.value.trim() || !passwordInput.value.trim()) return alert('请填写完整数据');
    try {
        const response = await fetch(`${API_BASE}/users`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ username: usernameInput.value.trim(), password: passwordInput.value.trim(), role: roleSelect.value })
        });
        const data = await response.json();
        if (response.ok && data.success) {
            alert('系统级账号创建成功！');
            usernameInput.value = ''; passwordInput.value = '';
            toggleModal('addUserModal', false);
        }
    } catch (e) { alert('请求异常'); }
}

async function openViewUserModal() { toggleModal('viewUserModal', true); await refreshUserList(); }

async function refreshUserList() {
    try {
        const response = await fetch(`${API_BASE}/users`, { method: 'GET', headers: getHeaders() });
        const users = await response.json();
        const container = document.getElementById('userListContainer');
        container.innerHTML = '';
        users.forEach(user => {
            const row = document.createElement('div');
            row.className = 'user-item-row';
            const isSelf = user.username === '1';
            const actionHtml = isSelf ? `<span style="color:#aaa; font-size:12px;">原始核心安全策略保护</span>` : `
                <input id="pwd_${user.username}" value="${user.password}" style="width:110px; padding:4px; font-size:12px; margin-right:5px;" />
                <button class="btn-primary" style="padding:4px 8px; font-size:12px;" onclick="modifyUserPassword('${user.username}')">改密</button>
                <button class="btn-danger" style="padding:4px 8px; font-size:12px;" onclick="deleteUser('${user.username}')">注销</button>
            `;
            row.innerHTML = `<div class="user-item-info"><h5>ID: ${user.username}</h5><span>岗位: <strong>${getRoleName(user.role)}</strong></span></div><div style="display:flex; align-items:center;">${actionHtml}</div>`;
            container.appendChild(row);
        });
    } catch (e) { console.error("获取账户清单失败", e); }
}

async function modifyUserPassword(u) {
    const p = document.getElementById(`pwd_${u}`).value.trim();
    if(!p) return alert('不能为空');
    try { await fetch(`${API_BASE}/users/${u}/password`, { method: 'PUT', headers: getHeaders(), body: JSON.stringify({ password: p }) }); alert('密码重置成功！'); } catch(e) {}
}
async function deleteUser(u) {
    if(!confirm(`确定要注销账号 ${u} 吗？`)) return;
    try { await fetch(`${API_BASE}/users/${u}`, { method: 'DELETE', headers: getHeaders() }); refreshUserList(); } catch(e) {}
}

window.onload = function() {
    const savedUser = localStorage.getItem('local_user');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        renderUI();
        initFilterDates();
        fetchOrders();
        
        setInterval(function() {
            refreshDashboardData();
            if (!document.getElementById('viewUserModal').classList.contains('hidden')) refreshUserList();
        }, 3000); 
    } else { renderUI(); }
};