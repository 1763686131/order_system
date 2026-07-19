/* ========================================================
 * ⚙️ 账户与权限管理控制台 (独立模块)
 * ========================================================
 * 负责用户列表拉取、新增用户、权限分配树渲染以及密码修改
 */

// 🎯 全新细粒度权限配置树（映射每一个前端功能按钮）
const PERMISSIONS_CONFIG = [
    {
        group: 'pending_order', label: '未完成订单 (车间看板)',
        children: [
            { key: 'pending.add', label: '显示：发布新订单 (悬浮球)' },
            { key: 'pending.view_detail', label: '显示：卡片翻转与详情页面' },
            { key: 'pending.complete', label: '操作：确定完成业务' },
            { key: 'pending.edit', label: '操作：修改订单信息' },
            { key: 'pending.copy', label: '显示：复制物流信息' },
            { key: 'pending.delete', label: '操作：物理删除订单' }
        ]
    },
    {
        group: 'completed_order', label: '已完成订单 (核对发货)',
        children: [
            { key: 'completed.ship', label: '操作：发货并出库' },
            { key: 'completed.uncomplete', label: '操作：撤销回未完成' },
            { key: 'completed.copy', label: '显示：复制物流信息' },
            { key: 'completed.delete', label: '操作：物理删除订单' }
        ]
    },
    {
        group: 'shipped_order', label: '已出库订单 (历史归档)',
        children: [
            { key: 'shipped.detail', label: '显示：查看历史详细信息' }
        ]
    },
    {
        group: 'material', label: '原材料监控中心',
        children: [
            { key: 'material.add', label: '操作：录入消耗与产出' },
            { key: 'material.edit', label: '操作：内页原地修改数据与备注' },
            { key: 'material.delete', label: '操作：物理删除流水记录' },
            { key: 'material.edit_stock', label: '隐藏接口：调整总物理库存' }
        ]
    },
    {
        group: 'system', label: '系统高级功能',
        children: [
            { key: 'system.user_manage', label: '显示：账户控制台 (悬浮球)' }
        ]
    }
];

let currentEditUser = null; 

async function openViewUserModal() { 
    toggleModal('viewUserModal', true); 
    document.getElementById('userDetailPanel').style.display = 'none';
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
            row.className = 'user-list-item';
            if (currentEditUser && currentEditUser.username === user.username) row.classList.add('active');
            if (currentUser.role === 'admin' && user.role !== 'employee' && user.role !== 'operator') return; 

            let roleName = getRoleName(user.role);
            let color = user.role === 'super_admin' ? '#ff4d4f' : (user.role === 'admin' ? '#faad14' : '#52c41a');
            let displayName = user.name ? user.name : user.username;
            row.innerHTML = `<div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size: 15px; font-weight: bold; color: #333;">${displayName} <span style="font-size:12px;color:#999;font-weight:normal;">(${user.username})</span></span>
                <span style="font-size: 12px; background: ${color}20; color: ${color}; padding: 2px 8px; border-radius: 12px; font-weight: bold;">${roleName}</span>
            </div>`;
            row.onclick = () => loadUserDetail(user);
            container.appendChild(row);
        });
    } catch (e) {}
}

function prepareCreateUser() {
    currentEditUser = null;
    document.querySelectorAll('.user-list-item').forEach(el => el.classList.remove('active'));
    document.getElementById('userDetailPanel').style.display = 'block';
    document.getElementById('detailTitle').innerText = "新建系统账户";
    document.getElementById('detailUsername').value = '';
    document.getElementById('detailUsername').disabled = false;
    document.getElementById('detailName').value = '';
    document.getElementById('detailPassword').value = '';
    document.getElementById('btnUpdatePwd').style.display = 'none';
    document.getElementById('btnDeleteUser').style.display = 'none';
    document.getElementById('btnSaveUser').style.display = 'inline-block';
    document.getElementById('detailRole').style.display = 'inline-block';
    document.getElementById('detailRoleText').style.display = 'none';
    renderPermissionTree([]);
}

function loadUserDetail(user) {
    currentEditUser = user;
    document.querySelectorAll('.user-list-item').forEach(el => el.classList.remove('active'));
    event.currentTarget.classList.add('active');
    
    document.getElementById('userDetailPanel').style.display = 'block';
    let detailDisplayName = user.name ? user.name : user.username;
    document.getElementById('detailTitle').innerText = `配置用户：${detailDisplayName}`;
    document.getElementById('detailUsername').value = user.username;
    document.getElementById('detailUsername').disabled = true; 
    document.getElementById('detailName').value = user.name || ''; 
    document.getElementById('detailPassword').value = user.password;
    document.getElementById('btnUpdatePwd').style.display = 'inline-block';
    document.getElementById('btnSaveUser').style.display = 'inline-block';
    
    if (currentUser.role === 'super_admin' && user.role !== 'super_admin') {
        document.getElementById('btnDeleteUser').style.display = 'inline-block';
    } else {
        document.getElementById('btnDeleteUser').style.display = 'none';
    }
    
    const roleSelect = document.getElementById('detailRole');
    const roleText = document.getElementById('detailRoleText');
    if (user.role === 'super_admin') {
        roleSelect.style.display = 'none';
        roleText.style.display = 'inline-block';
        roleText.innerText = '最高级安全守护者 (不可更改)';
        document.getElementById('permissionsWrapper').style.display = 'none'; 
    } else {
        roleSelect.style.display = 'inline-block';
        roleText.style.display = 'none';
        roleSelect.value = (user.role === 'operator') ? 'employee' : user.role;
        document.getElementById('permissionsWrapper').style.display = 'block';
        if (currentUser.role === 'admin') roleSelect.disabled = true;
        else roleSelect.disabled = false;
        renderPermissionTree(user.permissions || []);
    }
}

function renderPermissionTree(userPerms) {
    let treeHtml = '';
    // 管理员无权授予这些高危底层操作权限
    const adminRestricted = ['pending.delete', 'completed.delete', 'material.edit', 'material.edit_stock', 'material.delete', 'system.user_manage'];
    PERMISSIONS_CONFIG.forEach(group => {
        treeHtml += `<div class="perm-group"><label><input type="checkbox" class="perm-parent" data-group="${group.group}" onchange="toggleGroupPerms(this)"> ${group.label}</label><div class="perm-children">`;
        group.children.forEach(child => {
            let isChecked = userPerms.includes(child.key) ? 'checked' : '';
            let disabledStr = '';
            let labelClass = '';
            if (currentUser.role === 'admin' && adminRestricted.includes(child.key)) {
                disabledStr = 'disabled title="系统限制：管理员无权授予或撤销此危险权限"';
                labelClass = 'disabled-perm';
            }
            treeHtml += `<label class="${labelClass}"><input type="checkbox" class="perm-cb" value="${child.key}" data-group="${group.group}" onchange="checkParentPerm(this)" ${isChecked} ${disabledStr}> ${child.label}</label>`;
        });
        treeHtml += `</div></div>`;
    });
    document.getElementById('permTreeContainer').innerHTML = treeHtml;
    document.querySelectorAll('.perm-cb').forEach(cb => checkParentPerm(cb, false));
}

function toggleGroupPerms(parentCb) {
    const group = parentCb.dataset.group;
    const cbs = document.querySelectorAll(`.perm-cb[data-group="${group}"]:not([disabled])`);
    cbs.forEach(cb => cb.checked = parentCb.checked);
}

function checkParentPerm(childCb, cascade = true) {
    const group = childCb.dataset.group;
    const cbs = document.querySelectorAll(`.perm-cb[data-group="${group}"]`);
    const parentCb = document.querySelector(`.perm-parent[data-group="${group}"]`);
    parentCb.checked = Array.from(cbs).some(cb => cb.checked);
}

function getSelectedPermissions() {
    const perms = [];
    document.querySelectorAll('.perm-cb:checked').forEach(cb => perms.push(cb.value));
    return perms;
}

async function saveUserData() {
    const n = document.getElementById('detailName').value.trim(); 
    if (!currentEditUser) {
        const u = document.getElementById('detailUsername').value.trim();
        const p = document.getElementById('detailPassword').value.trim();
        const r = document.getElementById('detailRole').value;
        if (!u || !p) return alert('账号密码不能为空！');
        const payload = { username: u, name: n, password: p, role: r, permissions: getSelectedPermissions() };
        try {
            const res = await fetch(`${API_BASE}/users`, { method: 'POST', headers: getHeaders(), body: JSON.stringify(payload) });
            if (res.ok) { window.location.reload(); } else alert('账号已存在或无权限！');
        } catch(e) {}
    } else {
        const r = document.getElementById('detailRole').value;
        const payload = { name: n, permissions: getSelectedPermissions(), role: r }; 
        try {
            const res = await fetch(`${API_BASE}/users/${currentEditUser.username}/permissions`, { method: 'PUT', headers: getHeaders(), body: JSON.stringify(payload) });
            if (res.ok) { window.location.reload(); } else alert('更新失败，权限不足');
        } catch(e) {}
    }
}

async function updateUserPassword() {
    if (!currentEditUser) return;
    const p = document.getElementById('detailPassword').value.trim();
    if(!p) return alert('密码不能为空');
    try { 
        const res = await fetch(`${API_BASE}/users/${currentEditUser.username}/password`, { method: 'PUT', headers: getHeaders(), body: JSON.stringify({ password: p }) }); 
        if (res.ok) { window.location.reload(); }
    } catch(e) {}
}

async function deleteCurrentUser() {
    if (!currentEditUser) return;
    if (!confirm(`确定要彻底物理删除账户 [${currentEditUser.username}] 吗？`)) return;
    try { 
        const res = await fetch(`${API_BASE}/users/${currentEditUser.username}`, { method: 'DELETE', headers: getHeaders() }); 
        if (res.ok) { window.location.reload(); } 
    } catch(e) {}
}