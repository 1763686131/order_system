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

ADMIN_EMPLOYEE_PERMISSIONS = {
    "read": "admin.employee.read",
    "detail": "admin.employee.detail",
    "create": "admin.employee.create",
    "edit": "admin.employee.edit",
    "delete": "admin.employee.delete",
}

ADMIN_DEPARTMENT_PERMISSIONS = {
    "read": "admin.department.read",
    "create": "admin.department.create",
    "edit": "admin.department.edit",
    "delete": "admin.department.delete",
}

ADMIN_ROUTE_PERMISSIONS = {
    "dashboard": "admin.route.dashboard",
    "products": "admin.route.products",
    "sales": "admin.route.sales",
    "purchase": "admin.route.purchase",
    "inventory": "admin.route.inventory",
    "finance": "admin.route.finance",
    "hr": "admin.route.hr",
    "system": "admin.route.system",
}

ADMIN_ROUTE_BRANCH_PERMISSIONS = {
    "products": {
        "list": "admin.route.products.list",
        "materials": "admin.route.products.materials",
    },
    "sales": {
        "orders": "admin.route.sales.orders",
        "logistics": "admin.route.sales.logistics",
        "returns": "admin.route.sales.returns",
        "customers": "admin.route.sales.customers",
    },
    "purchase": {
        "orders": "admin.route.purchase.orders",
        "suppliers": "admin.route.purchase.suppliers",
        "inbound": "admin.route.purchase.inbound",
    },
    "inventory": {
        "products": "admin.route.inventory.products",
        "materials": "admin.route.inventory.materials",
        "material_outbounds": "admin.route.inventory.material_outbounds",
        "stock_in": "admin.route.inventory.stock_in",
        "stock_out": "admin.route.inventory.stock_out",
        "warehouse": "admin.route.inventory.warehouse",
    },
    "finance": {
        "receivables": "admin.route.finance.receivables",
        "payment_history": "admin.route.finance.payment_history",
        "bank_accounts": "admin.route.finance.bank_accounts",
        "logistics_truck": "admin.route.finance.logistics_truck",
        "express_courier": "admin.route.finance.express_courier",
    },
    "hr": {
        "company": "admin.route.hr.company",
        "reports": "admin.route.hr.reports",
    },
    "system": {
        "stores": "admin.route.system.stores",
        "settings": "admin.route.system.settings",
        "roles": "admin.route.system.roles",
        "print_template": "admin.route.system.print_template",
    },
}

ADMIN_ROUTE_BRANCH_PARENT_MAP = {
    branch_code: ADMIN_ROUTE_PERMISSIONS[group_code]
    for group_code, branches in ADMIN_ROUTE_BRANCH_PERMISSIONS.items()
    for branch_code in branches.values()
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
                "code": ADMIN_ROUTE_PERMISSIONS["dashboard"],
                "name": "访问首页",
                "description": "显示并访问后台数据看板",
            },
            {
                "code": ADMIN_ROUTE_PERMISSIONS["products"],
                "name": "访问商品",
                "description": "显示并访问商品和原材料管理",
            },
            {
                "code": ADMIN_ROUTE_PERMISSIONS["sales"],
                "name": "访问销售",
                "description": "显示并访问销售、物流、退货和客户管理",
            },
            {
                "code": ADMIN_ROUTE_PERMISSIONS["purchase"],
                "name": "访问采购",
                "description": "显示并访问采购订单、供应商和采购入库",
            },
            {
                "code": ADMIN_ROUTE_PERMISSIONS["inventory"],
                "name": "访问库存",
                "description": "显示并访问库存、出入库记录和仓库管理",
            },
            {
                "code": ADMIN_ROUTE_PERMISSIONS["finance"],
                "name": "访问财务",
                "description": "显示并访问应收、收款、账户和对账页面",
            },
            {
                "code": ADMIN_ROUTE_PERMISSIONS["hr"],
                "name": "访问人事行政",
                "description": "显示并访问员工、公司资料和检测报告",
            },
            {
                "code": ADMIN_ROUTE_PERMISSIONS["system"],
                "name": "访问设置",
                "description": "显示并访问门店、系统、角色组和打印模板",
            },
            {
                "code": ADMIN_ROUTE_BRANCH_PERMISSIONS["products"]["list"],
                "name": "访问商品列表",
                "description": "显示并访问成品商品管理",
            },
            {
                "code": ADMIN_ROUTE_BRANCH_PERMISSIONS["products"]["materials"],
                "name": "访问原材料列表",
                "description": "显示并访问原材料管理",
            },
            {
                "code": ADMIN_ROUTE_BRANCH_PERMISSIONS["sales"]["orders"],
                "name": "访问销售订单",
                "description": "显示并访问销售订单列表和订单表单",
            },
            {
                "code": ADMIN_ROUTE_BRANCH_PERMISSIONS["sales"]["logistics"],
                "name": "访问物流列表",
                "description": "显示并访问物流对账和物流订单",
            },
            {
                "code": ADMIN_ROUTE_BRANCH_PERMISSIONS["sales"]["returns"],
                "name": "访问退货订单",
                "description": "显示并访问退货订单及退货表单",
            },
            {
                "code": ADMIN_ROUTE_BRANCH_PERMISSIONS["sales"]["customers"],
                "name": "访问客户列表",
                "description": "显示并访问客户档案和客户列表",
            },
            {
                "code": ADMIN_ROUTE_BRANCH_PERMISSIONS["purchase"]["orders"],
                "name": "访问采购订单",
                "description": "显示并访问采购订单管理",
            },
            {
                "code": ADMIN_ROUTE_BRANCH_PERMISSIONS["purchase"]["suppliers"],
                "name": "访问供应商管理",
                "description": "显示并访问供应商管理",
            },
            {
                "code": ADMIN_ROUTE_BRANCH_PERMISSIONS["purchase"]["inbound"],
                "name": "访问采购入库",
                "description": "显示并访问采购入库管理",
            },
            {
                "code": ADMIN_ROUTE_BRANCH_PERMISSIONS["inventory"]["products"],
                "name": "访问成品库存",
                "description": "显示并访问成品库存",
            },
            {
                "code": ADMIN_ROUTE_BRANCH_PERMISSIONS["inventory"]["materials"],
                "name": "访问原材料库存",
                "description": "显示并访问原材料库存",
            },
            {
                "code": ADMIN_ROUTE_BRANCH_PERMISSIONS["inventory"]["material_outbounds"],
                "name": "访问原材料出库",
                "description": "显示并访问原材料出库记录",
            },
            {
                "code": ADMIN_ROUTE_BRANCH_PERMISSIONS["inventory"]["stock_in"],
                "name": "访问入库记录",
                "description": "显示并访问入库记录",
            },
            {
                "code": ADMIN_ROUTE_BRANCH_PERMISSIONS["inventory"]["stock_out"],
                "name": "访问出库记录",
                "description": "显示并访问出库记录",
            },
            {
                "code": ADMIN_ROUTE_BRANCH_PERMISSIONS["inventory"]["warehouse"],
                "name": "访问仓库管理",
                "description": "显示并访问仓库管理",
            },
            {
                "code": ADMIN_ROUTE_BRANCH_PERMISSIONS["finance"]["receivables"],
                "name": "访问应收欠款",
                "description": "显示并访问应收欠款和债务详情",
            },
            {
                "code": ADMIN_ROUTE_BRANCH_PERMISSIONS["finance"]["payment_history"],
                "name": "访问收款历史",
                "description": "显示并访问收款历史",
            },
            {
                "code": ADMIN_ROUTE_BRANCH_PERMISSIONS["finance"]["bank_accounts"],
                "name": "访问银行账户",
                "description": "显示并访问银行账户",
            },
            {
                "code": ADMIN_ROUTE_BRANCH_PERMISSIONS["finance"]["logistics_truck"],
                "name": "访问物流专车对账",
                "description": "显示并访问物流和专车对账",
            },
            {
                "code": ADMIN_ROUTE_BRANCH_PERMISSIONS["finance"]["express_courier"],
                "name": "访问快运快递对账",
                "description": "显示并访问快运和快递对账",
            },
            {
                "code": ADMIN_ROUTE_BRANCH_PERMISSIONS["hr"]["company"],
                "name": "访问公司资料",
                "description": "显示并访问公司资料",
            },
            {
                "code": ADMIN_ROUTE_BRANCH_PERMISSIONS["hr"]["reports"],
                "name": "访问检测报告",
                "description": "显示并访问检测报告",
            },
            {
                "code": ADMIN_ROUTE_BRANCH_PERMISSIONS["system"]["stores"],
                "name": "访问门店管理",
                "description": "显示并访问门店管理",
            },
            {
                "code": ADMIN_ROUTE_BRANCH_PERMISSIONS["system"]["settings"],
                "name": "访问系统设置",
                "description": "显示并访问系统设置",
            },
            {
                "code": ADMIN_ROUTE_BRANCH_PERMISSIONS["system"]["roles"],
                "name": "访问权限管理",
                "description": "显示并访问角色组权限管理",
            },
            {
                "code": ADMIN_ROUTE_BRANCH_PERMISSIONS["system"]["print_template"],
                "name": "访问打印模板",
                "description": "显示并访问打印模板管理",
            },
        ],
    },
    {
        "code": "admin_employee_management",
        "name": "员工信息管理",
        "description": "控制员工档案、登录账号和员工头像的查看与维护",
        "permissions": [
            {
                "code": ADMIN_EMPLOYEE_PERMISSIONS["read"],
                "name": "查看员工列表",
                "description": "查看员工列表、账号状态、部门和最近活跃概览",
            },
            {
                "code": ADMIN_EMPLOYEE_PERMISSIONS["detail"],
                "name": "查看员工详情",
                "description": "打开员工完整档案、登录账号和权限详情",
            },
            {
                "code": ADMIN_EMPLOYEE_PERMISSIONS["create"],
                "name": "新增员工信息",
                "description": "创建员工档案并按需开通登录账号",
            },
            {
                "code": ADMIN_EMPLOYEE_PERMISSIONS["edit"],
                "name": "编辑员工信息",
                "description": "修改员工档案、账号状态、密码和头像",
            },
            {
                "code": ADMIN_EMPLOYEE_PERMISSIONS["delete"],
                "name": "删除员工信息",
                "description": "删除员工档案及其绑定的登录账号",
            },
        ],
    },
    {
        "code": "admin_department_management",
        "name": "部门管理",
        "description": "控制部门列表、部门配置和部门删除操作",
        "permissions": [
            {
                "code": ADMIN_DEPARTMENT_PERMISSIONS["read"],
                "name": "查看部门列表",
                "description": "查看部门列表、部门状态和员工数量",
            },
            {
                "code": ADMIN_DEPARTMENT_PERMISSIONS["create"],
                "name": "新增部门",
                "description": "创建新的部门配置",
            },
            {
                "code": ADMIN_DEPARTMENT_PERMISSIONS["edit"],
                "name": "编辑部门",
                "description": "修改部门名称、状态和排序",
            },
            {
                "code": ADMIN_DEPARTMENT_PERMISSIONS["delete"],
                "name": "删除部门",
                "description": "删除没有员工和下级部门的部门",
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
