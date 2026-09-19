"""Permission catalog used by auth schema, API responses, and UI metadata."""

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
]

ALL_PERMISSION_CODES = [
    permission["code"]
    for module in PERMISSION_MODULES
    for permission in module["permissions"]
]
