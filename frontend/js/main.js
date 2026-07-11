const API_BASE = '/api';
let currentUser = { username: '', role: '' };
let allOrdersLocal = []; 

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

function renderUI() {
    const loginSection = document.getElementById('loginSection');
    const mainSection = document.getElementById('mainSection');
    const btnOpenAddUser = document.getElementById('btnOpenAddUser');
    const btnOpenViewUser = document.getElementById('btnOpenViewUser');
    const sidebarAdminSection = document.getElementById('sidebarAdminSection');

    if (!currentUser.username) {
        loginSection.classList.remove('hidden');
        mainSection.classList.add('hidden');
        return;
    }

    loginSection.classList.add('hidden');
    mainSection.classList.remove('hidden');

    document.getElementById('currentUsername').innerText = currentUser.username;
    document.getElementById('currentUserRoleTag').innerText = getRoleName(currentUser.role);

    if (currentUser.role === 'super_admin') {
        btnOpenAddUser.classList.remove('hidden');
        btnOpenViewUser.classList.remove('hidden');
        sidebarAdminSection.classList.remove('hidden');
    } else if (currentUser.role === 'admin') {
        btnOpenAddUser.classList.add('hidden');
        btnOpenViewUser.classList.add('hidden');
        sidebarAdminSection.classList.remove('hidden');
    } else {
        btnOpenAddUser.classList.add('hidden');
        btnOpenViewUser.classList.add('hidden');
        sidebarAdminSection.classList.add('hidden');
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
            fetchOrders();
        } else {
            alert(resData.message || '凭证错误，登录失败');
        }
    } catch (error) {
        alert('本地服务端连接失败，请检查 Docker。');
    }
}

// 🎯 核心功能：处理长文本中的换行符，变成网页能识别的 <br> 标签
function formatTextWithBreaks(text) {
    if (!text) return '';
    // 将 \n 换行符全局替换为 HTML 换行标签 <br>
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
    try {
        const response = await fetch(`${API_BASE}/orders`, { method: 'GET', headers: getHeaders() });
        const serverOrders = await response.json();
        allOrdersLocal = serverOrders;
        
        const statusConfirmModal = document.getElementById('statusConfirmModal');
        if (statusConfirmModal && !statusConfirmModal.classList.contains('hidden')) {
            return; 
        }

        const gridContainer = document.getElementById('orderGrid');
        gridContainer.innerHTML = ''; 

        const selectedStatus = document.getElementById('filterStatus').value;
        const startDateStr = document.getElementById('filterStartDate').value;
        const endDateStr = document.getElementById('filterEndDate').value;

        const filteredOrders = serverOrders.filter(order => {
            if (order.status !== selectedStatus) return false;
            if (order.date) {
                const orderDay = order.date.split(' ')[0]; 
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

            // 🎯 核心渲染处：将内容传给换行转换函数处理后再输出
            const formattedContent = formatTextWithBreaks(order.title);

            card.innerHTML = `
                <div class="card-top">
                    <span class="card-title-tag">[#${order.id}] ${typeText}</span>
                    <span>🕒 创建: ${order.date || '未知'}</span>
                </div>
                <div class="card-body">
                    <h4>${formattedContent}</h4>
                </div>
                <div class="card-footer-wrapper">
                    ${completedDateHtml}
                    ${footerActionsHtml}
                </div>
            `;
            gridContainer.appendChild(card);
        });
    } catch (error) {
        console.error("看板数据加载失败", error);
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
    
    // 弹窗里也兼容换行展示
    document.getElementById('previewCardTitle').innerHTML = formatTextWithBreaks(order.title);

    const previewBox = document.getElementById('confirmCardPreview');
    const tipText = document.getElementById('confirmTipText');
    const submitBtn = document.getElementById('btnConfirmSubmit');

    if (targetStatus === 'completed') {
        tipText.innerText = "🛑 确认将以下订单标记为【已完成】吗？";
        previewBox.className = "confirm-card-preview preview-completed";
        submitBtn.className = "btn-success";
        submitBtn.innerText = "确认完成并变绿";
    } else {
        tipText.innerText = "⚠️ 确认将以下订单恢复为【未完成】吗？";
        previewBox.className = "confirm-card-preview preview-pending";
        submitBtn.className = "btn-warning";
        submitBtn.innerText = "回滚为未完成";
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
    } catch (error) {
        alert('调整状态失败');
    }
}

async function createOrder() {
    const titleInput = document.getElementById('newOrderTitle');
    const typeSelect = document.getElementById('newOrderType');
    const title = titleInput.value; // 保留原始换行
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
    } catch (error) {
        alert('断网发单失败');
    }
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
            body: JSON.stringify({
                username: usernameInput.value.trim(),
                password: passwordInput.value.trim(),
                role: roleSelect.value
            })
        });
        const data = await response.json();
        if (response.ok && data.success) {
            alert('系统级账号创建成功！');
            usernameInput.value = '';
            passwordInput.value = '';
            toggleModal('addUserModal', false);
        }
    } catch (e) { alert('请求异常'); }
}

async function openViewUserModal() {
    toggleModal('viewUserModal', true);
    await refreshUserList();
}

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
            const actionHtml = isSelf ? 
                `<span style="color:#aaa; font-size:12px;">原始核心安全策略保护</span>` : 
                `
                <input id="pwd_${user.username}" placeholder="输入新密码" value="${user.password}" style="width:110px; padding:4px; font-size:12px; margin-right:5px;" />
                <button class="btn-primary" style="padding:4px 8px; font-size:12px;" onclick="modifyUserPassword('${user.username}')">改密</button>
                <button class="btn-danger" style="padding:4px 8px; font-size:12px;" onclick="deleteUser('${user.username}')">注销</button>
                `;

            row.innerHTML = `
                <div class="user-item-info">
                    <h5>ID: ${user.username}</h5>
                    <span>岗位分工: <strong>${getRoleName(user.role)}</strong></span>
                </div>
                <div style="display:flex; align-items:center;">${actionHtml}</div>
            `;
            container.appendChild(row);
        });
    } catch (e) { console.error("获取账户清单失败", e); }
}

async function modifyUserPassword(targetUser) {
    const newPwd = document.getElementById(`pwd_${targetUser}`).value.trim();
    if(!newPwd) return alert('密码不能为空');
    try {
        const response = await fetch(`${API_BASE}/users/${targetUser}/password`, {
            method: 'PUT',
            headers: getHeaders(),
            body: JSON.stringify({ password: newPwd })
        });
        if(response.ok) alert('密码重置成功！');
    } catch(e) { alert('修改异常'); }
}

async function deleteUser(targetUser) {
    if(!confirm(`危险操作：确定要彻底销毁账号 [ ${targetUser} ] 吗？`)) return;
    try {
        const response = await fetch(`${API_BASE}/users/${targetUser}`, { method: 'DELETE', headers: getHeaders() });
        if(response.ok) { alert('该凭证已被剔除系统。'); refreshUserList(); }
    } catch(e) { alert('注销异常'); }
}

window.onload = function() {
    const savedUser = localStorage.getItem('local_user');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        renderUI();
        initFilterDates();
        fetchOrders();
        
        setInterval(function() {
            fetchOrders();
            const viewUserModal = document.getElementById('viewUserModal');
            if (viewUserModal && !viewUserModal.classList.contains('hidden')) {
                refreshUserList();
            }
        }, 3000); 
    } else {
        renderUI();
    }
};