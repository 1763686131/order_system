/* ========================================================
 * 🛠️ 全局公共工具库 (tools.js)
 * ========================================================
 * 封装与具体业务逻辑无关的纯净工具函数
 */

// 1. 基础文本换行转义
function formatTextWithBreaks(text) { 
    return !text ? '' : text.replace(/\n/g, '<br>'); 
}

// 2. 获取当前高精度时间 (精确到分)
function getCurrentDateTime() {
    const now = new Date();
    const Y = now.getFullYear(); const M = String(now.getMonth() + 1).padStart(2, '0'); const D = String(now.getDate()).padStart(2, '0');
    const h = String(now.getHours()).padStart(2, '0'); const m = String(now.getMinutes()).padStart(2, '0');
    return `${Y}-${M}-${D} ${h}:${m}`;
}

// 3. 智能单行文本动态缩放比例引擎 (横向防挤压)
function calculateTextScale(text, targetLen = 15) {
    if (!text) return 1;
    let currentLen = 0;
    for(let i = 0; i < text.length; i++) {
        // 🔥 核心修复：精准正则表达式捕获！
        // 只有纯数字和纯英文字母算 0.55 宽度。汉字、+-*/、标点符号、空格统统算 1 宽度！
        if (/[a-zA-Z0-9]/.test(text[i])) {
            currentLen += 0.55;
        } else {
            currentLen += 1;
        }
    }
    if (currentLen === 0) return 1;
    
    // 计算缩放比例：基准长度 / 实际长度
    let scale = targetLen / currentLen;
    
    // 限制缩放范围：最大放大 1.4 倍（防止字太少变得像巨无霸），最小缩小 0.4 倍（保证长文本也能在一行显示全）
    return Math.min(Math.max(scale, 0.4), 1.4);
}

// 4. 兼容性剪贴板复制兜底工具
function fallbackCopyTextToClipboard(text) {
    let textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed"; textArea.style.opacity = "0";
    document.body.appendChild(textArea);
    textArea.focus(); textArea.select();
    try { 
        document.execCommand('copy'); 
        alert('✅ 极简物流信息已成功复制！'); 
    } catch (err) { 
        alert('⚠️ 自动复制失败，请手动复制。'); 
    }
    document.body.removeChild(textArea);
}

// 5. 新增/修改表单的有效性数据校验
function validatePayload(payload) {
    if (!payload.receiver_phone || !payload.receiver_address || !payload.goods_name || !payload.goods_weight) return '【收货电话】、【地址】、【名称】、【重量】为必填项！';
    if (!/^(?:1[3-9]\d{9}|0\d{2,3}-\d{7,8})$/.test(payload.receiver_phone)) return '【收货电话】格式不正确！必须是11位手机号或带区号的座机。';
    return null; 
}

// 6. 订单长文本智能一键分词与表单填充引擎
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
        let nameMatch = strWithoutPhone.match(/(?:姓名|收货人)[:：]\s*([^\s。，,;；]{1,5})/);
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
        document.getElementById(`${prefix}ReceiverAddress`).value = address.replace(/(?:地址)[:：]?/g, '').replace(/^[。，,;；\s]+|[。，,;；\s]+$/g, '');
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