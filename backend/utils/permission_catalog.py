"""Permission catalog used by auth schema, API responses, and UI metadata."""

ADMIN_SALES_ORDER_PERMISSIONS = {
    "create": "admin.sales.order.create",
    "edit": "admin.sales.order.edit",
    "delete": "admin.sales.order.delete",
    "print": "admin.sales.order.print",
    "export": "admin.sales.order.export",
    "complete": "admin.sales.order.complete",
    "reopen": "admin.sales.order.reopen",
    "audit": "admin.sales.order.audit",
    "reverse_audit": "admin.sales.order.reverse_audit",
}

ADMIN_MESSAGE_PERMISSIONS = {
    "read": "admin.message.read",
    "send": "admin.message.send",
    "attachment": "admin.message.attachment",
}

ADMIN_AUDIT_NOTIFICATION_PERMISSIONS = {
    "stock_inbound": "admin.inventory.stock_inbound.audit",
    "material_outbound": "admin.inventory.material_outbound.audit",
    "payment_receipt": "admin.finance.payment_receipt.audit",
    "return_order": "admin.sales.return.audit",
}

PERMISSION_MODULES = [
    {
        "code": "touch_terminal",
        "name": "触屏端权限",
        "description": "触屏端订单、发货回单和原材料出库操作",
        "permissions": [
            {
                "code": "touch.order.read",
                "name": "查看订单",
                "description": "查看触屏端订单列表和详情",
            },
            {
                "code": "touch.order.reopen",
                "name": "恢复订单",
                "description": "把已完成订单恢复为待处理",
            },
            {
                "code": "touch.order.copy",
                "name": "复制订单",
                "description": "复制当前订单信息",
            },
            {
                "code": "touch.order.delete",
                "name": "删除订单",
                "description": "删除未过账的订单记录",
            },
            {
                "code": "touch.order.complete",
                "name": "完成订单",
                "description": "将待处理订单标记为已完成",
            },
            {
                "code": "touch.shipment.audit",
                "name": "审核发货",
                "description": "录入物流信息并审核或反审核发货",
            },
            {
                "code": "touch.receipt.read",
                "name": "查看回单",
                "description": "查看订单回单图片",
            },
            {
                "code": "touch.receipt.upload",
                "name": "上传回单",
                "description": "上传或替换订单回单图片",
            },
            {
                "code": "touch.receipt.delete",
                "name": "删除回单",
                "description": "删除订单回单图片",
            },
            {
                "code": "touch.material.read",
                "name": "查看出库",
                "description": "查看原材料出库记录",
            },
            {
                "code": "touch.material.audit",
                "name": "审核出库",
                "description": "审核原材料出库单",
            },
            {
                "code": "touch.material.create",
                "name": "录入出库",
                "description": "提交原材料出库草稿",
            },
        ],
    },
    {
        "code": "admin_routes",
        "name": "后台路由",
        "description": "控制后台管理侧栏大类和对应页面访问",
        "permissions": [
            {
                "code": "admin.route.dashboard",
                "name": "访问首页",
                "description": "显示并访问后台数据看板",
            },
            {
                "code": "admin.route.products",
                "name": "访问商品",
                "description": "显示并访问商品和原材料管理",
            },
            {
                "code": "admin.route.sales",
                "name": "访问销售",
                "description": "显示并访问销售、物流、退货和客户管理",
            },
            {
                "code": "admin.route.purchase",
                "name": "访问采购",
                "description": "显示并访问采购订单、供应商和采购入库",
            },
            {
                "code": "admin.route.inventory",
                "name": "访问库存",
                "description": "显示并访问库存、出入库记录和仓库管理",
            },
            {
                "code": "admin.route.finance",
                "name": "访问财务",
                "description": "显示并访问应收、收款、账户和对账页面",
            },
            {
                "code": "admin.route.hr",
                "name": "访问人事行政",
                "description": "显示并访问员工、公司资料和检测报告",
            },
            {
                "code": "admin.route.system",
                "name": "访问设置",
                "description": "显示并访问门店、系统、角色组和打印模板",
            },
        ],
    },
    {
        "code": "admin_sales_orders",
        "name": "销售订单操作",
        "description": "控制后台销售订单列表中的新增、修改和状态操作",
        "permissions": [
            {
                "code": ADMIN_SALES_ORDER_PERMISSIONS["create"],
                "name": "新建/复制订单",
                "description": "新建销售订单或复制现有订单生成新单",
            },
            {
                "code": ADMIN_SALES_ORDER_PERMISSIONS["edit"],
                "name": "编辑订单",
                "description": "修改未过账销售订单的内容",
            },
            {
                "code": ADMIN_SALES_ORDER_PERMISSIONS["delete"],
                "name": "删除订单",
                "description": "删除未过账销售订单并恢复库存",
            },
            {
                "code": ADMIN_SALES_ORDER_PERMISSIONS["print"],
                "name": "打印订单",
                "description": "打开销售订单打印模板和预览",
            },
            {
                "code": ADMIN_SALES_ORDER_PERMISSIONS["export"],
                "name": "导出订单",
                "description": "导出销售订单列表",
            },
            {
                "code": ADMIN_SALES_ORDER_PERMISSIONS["complete"],
                "name": "完成订单",
                "description": "在后台将待处理订单标记为已完成",
            },
            {
                "code": ADMIN_SALES_ORDER_PERMISSIONS["reopen"],
                "name": "撤销完成",
                "description": "在后台将已完成订单恢复为待处理",
            },
            {
                "code": ADMIN_SALES_ORDER_PERMISSIONS["audit"],
                "name": "审核订单",
                "description": "审核已发货销售订单并更新客户账户",
            },
            {
                "code": ADMIN_SALES_ORDER_PERMISSIONS["reverse_audit"],
                "name": "反审核订单",
                "description": "撤销销售订单审核及相关客户账户流水",
            },
        ],
    },
    {
        "code": "admin_messages",
        "name": "留言与通知",
        "description": "控制后台留言、附件和审核通知功能",
        "permissions": [
            {
                "code": ADMIN_MESSAGE_PERMISSIONS["read"],
                "name": "查看留言",
                "description": "查看自己的会话、留言和未读数量",
            },
            {
                "code": ADMIN_MESSAGE_PERMISSIONS["send"],
                "name": "发送留言",
                "description": "向通讯录员工发送文字留言",
            },
            {
                "code": ADMIN_MESSAGE_PERMISSIONS["attachment"],
                "name": "收发附件",
                "description": "上传和下载留言中的服务器附件",
            },
        ],
    },
    {
        "code": "admin_audit_notifications",
        "name": "单据审核通知",
        "description": "决定角色组接收哪些待审核单据通知",
        "permissions": [
            {
                "code": ADMIN_AUDIT_NOTIFICATION_PERMISSIONS["stock_inbound"],
                "name": "采购入库审核",
                "description": "审核采购入库单并接收待审核通知",
            },
            {
                "code": ADMIN_AUDIT_NOTIFICATION_PERMISSIONS["material_outbound"],
                "name": "原材料出库审核",
                "description": "审核原材料出库单并接收待审核通知",
            },
            {
                "code": ADMIN_AUDIT_NOTIFICATION_PERMISSIONS["payment_receipt"],
                "name": "收款单审核",
                "description": "审核收款单并接收待审核通知",
            },
            {
                "code": ADMIN_AUDIT_NOTIFICATION_PERMISSIONS["return_order"],
                "name": "退货单审核",
                "description": "审核退货单并接收待审核通知",
            },
        ],
    },
]

ALL_PERMISSION_CODES = [
    permission["code"]
    for module in PERMISSION_MODULES
    for permission in module["permissions"]
]
