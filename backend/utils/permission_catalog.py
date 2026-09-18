"""Permission catalog used by auth schema, API responses, and UI metadata."""

PERMISSION_MODULES = [
    {
        "code": "touch_orders",
        "name": "触屏订单",
        "description": "触屏端订单新增、编辑、完成和复制",
        "permissions": [
            {
                "code": "touch.order.read",
                "name": "查看订单",
                "description": "查看触屏端订单列表和详情",
            },
            {
                "code": "touch.order.create",
                "name": "新增订单",
                "description": "创建触屏端销售订单",
            },
            {
                "code": "touch.order.update",
                "name": "编辑订单",
                "description": "修改未完成订单内容",
            },
            {
                "code": "touch.order.complete",
                "name": "完成订单",
                "description": "将待处理订单标记为已完成",
            },
            {
                "code": "touch.order.reopen",
                "name": "恢复订单",
                "description": "把已完成订单恢复为待处理",
            },
            {
                "code": "touch.order.copy",
                "name": "复制订单",
                "description": "复制订单信息用于新建",
            },
            {
                "code": "touch.order.delete",
                "name": "删除订单",
                "description": "删除未过账的订单记录",
            },
        ],
    },
    {
        "code": "touch_shipment",
        "name": "发货回单",
        "description": "触屏端发货审核和回单处理",
        "permissions": [
            {
                "code": "touch.shipment.audit",
                "name": "审核发货",
                "description": "审核或反审核已发货订单",
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
        ],
    },
    {
        "code": "touch_material",
        "name": "触屏原料",
        "description": "触屏端原材料出库草稿和审核",
        "permissions": [
            {
                "code": "touch.material.read",
                "name": "查看出库",
                "description": "查看原材料出库记录",
            },
            {
                "code": "touch.material.create",
                "name": "录入出库",
                "description": "提交原材料出库草稿",
            },
            {
                "code": "touch.material.update",
                "name": "修改出库",
                "description": "修改原材料出库草稿",
            },
            {
                "code": "touch.material.audit",
                "name": "审核出库",
                "description": "审核原材料出库单",
            },
            {
                "code": "touch.material.reverse_audit",
                "name": "反审核出库",
                "description": "反审核原材料出库单",
            },
            {
                "code": "touch.material.delete",
                "name": "删除出库",
                "description": "作废或删除原材料出库单",
            },
            {
                "code": "touch.material.settings",
                "name": "出库设置",
                "description": "维护触屏端出库默认设置",
            },
        ],
    },
]

ALL_PERMISSION_CODES = [
    permission["code"]
    for module in PERMISSION_MODULES
    for permission in module["permissions"]
]
