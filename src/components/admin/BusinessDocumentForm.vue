<template>
  <section class="business-document-form" :data-document-type="documentType" :data-document-action="action" :aria-label="ui.config.title" :aria-busy="ui.loading">
    <form novalidate @submit.prevent="submitDocument" @wheel="handleNumberWheel">
      <div class="top-info-bar">
        <fieldset class="header-fields" :disabled="fieldsDisabled">
          <h2>{{ ui.config.title }}</h2>
          <label v-if="isPurchase && !ui.savedDocumentId && ui.inboundTypes.length > 1" class="info-group">
            <span>入库类型</span>
            <select :value="ui.inboundType" @change="ui.changeInboundType($event.target.value)">
              <option v-for="type in ui.inboundTypes" :key="type" :value="type">{{ type === 'finished-product' ? '成品' : '原材料' }}</option>
            </select>
          </label>
          <label class="info-group">
            <span>{{ isPurchaseOrder ? '申请门店' : '门店' }}<b v-if="isPurchaseOrder"> *</b></span>
            <select v-model="ui.form.storeId" :disabled="fieldsDisabled || (isPurchase && Boolean(ui.purchaseOrderId))" :ref="element => setFieldRef('storeId', element)" @change="handleStoreChange">
              <option value="">请选择门店</option>
              <option v-for="store in ui.stores" :key="store.id" :value="isSale ? store.id : String(store.id)">{{ store.name }}</option>
            </select>
          </label>
          <label v-if="!isPurchaseOrder && (!isPurchase || isMaterial || ui.purchaseOrderId)" class="info-group">
            <span>{{ ui.config.partyLabel }}</span>
            <input v-if="isPurchase && ui.purchaseOrderId" type="text" :value="ui.form.supplierName || '供应商详见采购申请明细'" readonly />
            <select v-else-if="isPurchase" v-model="ui.form.supplierId" :disabled="fieldsDisabled" :required="!ui.purchaseOrderId && isMaterial" :ref="element => setFieldRef('supplierId', element)" @change="dismissHint('supplierId')">
              <option value="">请选择供应商</option>
              <option v-for="supplier in ui.suppliers" :key="supplier.id" :value="String(supplier.id)">{{ supplier.supplierName || supplier.name }}</option>
            </select>
            <input v-else type="text" autocomplete="off" :ref="setCustomerInputRef" :value="ui.customerDropdownOpen ? ui.customerSearch : ui.selectedCustomerName" placeholder="请选择客户" @focus="ui.openCustomerDropdown" @input="ui.handleCustomerSearchInput" @keydown.escape.prevent="ui.closeCustomerDropdown" />
          </label>
          <label v-if="!isPurchaseOrder" class="info-group">
            <span>仓库</span>
            <select v-model="ui.form.warehouseId" :ref="element => setFieldRef('warehouseId', element)" @change="handleHeaderWarehouseChange">
              <option value="">请选择仓库</option>
              <option v-for="warehouse in ui.filteredWarehouses" :key="warehouse.id" :value="isSale ? warehouse.id : String(warehouse.id)">{{ warehouse.name }}</option>
            </select>
          </label>
          <label class="info-group"><span>{{ ui.config.dateLabel || '单据日期' }}<b v-if="isPurchaseOrder"> *</b></span><input v-model="ui.form[ui.config.dateField]" :ref="element => setFieldRef('documentDate', element)" type="date" @change="ui.onDateChange?.(); dismissHint('documentDate')" /></label>
          <label v-if="isPurchaseOrder" class="info-group"><span>预计到货日期</span><input v-model="ui.form.expectedDate" type="date" @input="ui.onExpectedDateInput()" /></label>
          <label class="info-group"><span>单据编号</span><input v-model="ui.form[ui.config.numberField]" type="text" :readonly="!isSale" :placeholder="isSale ? '单据编号' : '保存后自动生成'" /></label>
          <label v-if="isReturn" class="info-group"><span>原订单编号</span><input v-model.trim="ui.form.originalOrderNumber" :ref="element => setFieldRef('originalOrderNumber', element)" type="text" /></label>
        </fieldset>
        <div class="toolbar-actions">
          <label v-if="!isPurchaseOrder" class="tax-toggle"><input v-model="ui.taxEnabled" type="checkbox" :disabled="fieldsDisabled" /><span>含税</span></label>
          <button type="button" class="btn btn-danger" :disabled="fieldsDisabled" @click="confirmation = 'clear'">清空</button>
          <button type="button" class="btn close-button" :disabled="ui.saving" title="关闭" aria-label="关闭" @click="requestClose"><X :size="18" :stroke-width="1.6" aria-hidden="true" /></button>
        </div>
      </div>
      <fieldset :disabled="fieldsDisabled">
        <div v-if="isSale || isPurchase" class="contact-info-bar">
          <template v-if="isSale">
            <label class="info-group"><span>联系人</span><input v-model="ui.form.contactPerson" :ref="element => setFieldRef('contactPerson', element)" type="text" @input="dismissHint('contactPerson')" /></label>
            <label class="info-group"><span>联系电话</span><input v-model="ui.form.contactPhone" :ref="element => setFieldRef('contactPhone', element)" type="tel" @input="dismissHint('contactPhone')" /></label>
            <label class="info-group address-field"><span>联系地址</span><input v-model="ui.form.contactAddress" type="text" /></label>
            <label class="info-group"><span>工程项目</span><input v-model="ui.form.projectName" type="text" /></label>
            <label class="info-group logistics-field"><span>物流服务</span><select v-model="ui.form.logisticsService" @change="dismissHint('logisticsService')"><option v-for="service in ui.logisticsServiceOptions" :key="service" :value="service">{{ service }}</option></select></label>
          </template>
          <template v-else>
            <label class="info-group"><span>检验员</span><input v-model="ui.form.inspector" type="text" /></label>
            <label class="info-group"><span>质检单号</span><input v-model="ui.form.qualityNo" type="text" /></label>
          </template>
        </div>

        <div class="products-table-wrapper">
          <table class="products-table">
            <colgroup>
              <col style="width: 40px" /><col style="width: 54px" /><col v-if="isPurchaseOrder" style="width: 125px" /><col v-if="isPurchaseOrder" style="width: 88px" /><col style="width: 170px" /><col v-if="isPurchaseOrder" style="width: 82px" /><col style="width: 105px" /><col style="width: 55px" />
              <template v-if="!isPurchaseOrder"><col style="width: 130px" /><col style="width: 95px" /><col style="width: 90px" /></template>
              <col style="width: 88px" /><col v-if="isPurchaseOrder" style="width: 125px" /><col style="width: 88px" />
              <template v-if="ui.taxEnabled"><col style="width: 80px" /><col style="width: 110px" /></template>
              <col style="width: 110px" />
              <template v-if="ui.taxEnabled"><col v-if="!isSale" style="width: 100px" /><col style="width: 110px" /></template>
              <template v-if="isPurchase"><col style="width: 140px" /><col style="width: 110px" /></template>
              <col style="width: 110px" />
            </colgroup>
            <thead><tr>
              <th>序号</th><th>操作</th><th v-if="isPurchaseOrder">所属仓库</th><th v-if="isPurchaseOrder">分类</th><th>{{ isPurchaseOrder ? '商品信息' : isMaterial ? '物料信息' : '商品信息' }}<b v-if="isPurchaseOrder"> *</b></th><th v-if="isPurchaseOrder">编码</th><th>规格型号</th><th>单位</th>
              <template v-if="!isPurchaseOrder"><th>所属仓库</th><th>当前库存</th><th>{{ isPurchase ? '应收数量' : '件数' }}</th></template>
              <th :class="{ right: isPurchaseOrder }">{{ isPurchaseOrder ? '采购数量' : isPurchase ? '实收数量' : '数量' }}<b v-if="isPurchaseOrder"> *</b></th>
              <th v-if="isPurchaseOrder">采购供应商<b v-if="ui.auditMode"> *</b></th><th :class="{ right: isPurchaseOrder }">{{ isPurchaseOrder ? '采购单价 (元)' : '单价 (元)' }}<b v-if="isPurchaseOrder && ui.auditMode"> *</b></th>
              <template v-if="ui.taxEnabled"><th>税率 (%)</th><th>含税单价</th></template>
              <th :class="{ right: isPurchaseOrder }">金额 (元)</th><template v-if="ui.taxEnabled"><th v-if="!isSale">税额</th><th>含税金额</th></template>
              <template v-if="isPurchase"><th>批次号</th><th>货位编码</th></template><th>备注信息</th>
            </tr></thead>
            <tbody>
              <tr v-for="(item, index) in ui.form.items" :key="item.key ?? index" :class="{ 'row-focused': ui.focusedRow === index }">
                <td class="center">{{ index + 1 }}</td>
                <td class="center"><template v-if="!isPurchaseOrder || !ui.readOnly"><button class="btn-icon" type="button" title="在下方插入一行" aria-label="在下方插入一行" @click="ui.addRow(index)"><Plus :size="16" aria-hidden="true" /></button><button class="btn-icon remove" type="button" title="删除此行" aria-label="删除此行" :disabled="isPurchaseOrder && ui.form.items.length === 1" @click="ui.removeRow(index)"><Trash2 :size="15" aria-hidden="true" /></button></template></td>
                <td v-if="isPurchaseOrder">
                  <select v-model="item.warehouseId" class="purchase-cell-select" :ref="element => setFieldRef(`item-warehouse-${index}`, element)" aria-label="所属仓库" @focus="activatePurchaseCell(item, 'warehouse')" @blur="activePurchaseCell = ''" @change="ui.onItemWarehouseChange(item); dismissHint(`item-warehouse-${index}`)">
                    <option value="">{{ purchaseCellPlaceholder(item, 'warehouse', ui.form.storeId ? '请选择仓库' : '请先选择门店') }}</option>
                    <option v-if="item.warehouseId && !ui.filteredWarehouses.some(warehouse => String(warehouse.id) === String(item.warehouseId))" :value="item.warehouseId">{{ item.warehouseName || '历史仓库' }}</option>
                    <option v-for="warehouse in ui.filteredWarehouses" :key="warehouse.id" :value="String(warehouse.id)">{{ warehouse.name }}</option>
                  </select>
                </td>
                <td v-if="isPurchaseOrder">
                  <select v-if="item.warehouseId" v-model="item.categoryId" class="purchase-cell-select" :ref="element => setFieldRef(`item-category-${index}`, element)" aria-label="分类" @focus="activatePurchaseCell(item, 'category')" @blur="activePurchaseCell = ''" @change="ui.onCategoryChange(item); dismissHint(`item-category-${index}`)">
                    <option value="">请选择分类</option>
                    <option v-for="category in ui.categoriesForItem(item)" :key="category.id" :value="String(category.id)">{{ category.name }}</option>
                  </select>
                  <span v-else class="blank-cell"></span>
                </td>
                <td>
                  <input v-if="isPurchaseOrder" v-model="item.goodsName" class="purchase-cell-input" :ref="element => setProductInputRef(index, element)" type="text" autocomplete="off" aria-label="商品" :placeholder="purchaseProductPlaceholder(item)" @focus="activatePurchaseCell(item, 'product'); ui.showProductDropdown(index)" @blur="activePurchaseCell = ''; ui.hideProductDropdown(index)" @input="ui.onProductInput(index); dismissHint(`item-product-${index}`)" @keydown.escape.prevent="ui.closeProductDropdown?.()" />
                  <select v-else-if="isPurchase" v-model="item.productId" class="purchase-cell-select" :ref="element => setProductInputRef(index, element)" :aria-label="isMaterial ? '物料' : '商品'" @focus="activatePurchaseCell(item, 'product')" @blur="activePurchaseCell = ''" @change="ui.onProductChange(item); dismissHint(`item-product-${index}`)">
                    <option value="">{{ purchaseCellPlaceholder(item, 'product', ui.form.storeId ? `请选择${isMaterial ? '物料' : '商品'}` : '请先选择门店') }}</option>
                    <option v-if="item.productId && !ui.products.some(product => String(product.id) === String(item.productId))" :value="item.productId">{{ item.goodsName }}</option>
                    <option v-for="product in ui.productsForItem(item)" :key="product.id" :value="String(product.id)">{{ product.code ? `${product.code} · ` : '' }}{{ product.name }}</option>
                  </select>
                  <input v-else v-model="item.goodsName" :ref="element => setProductInputRef(index, element)" type="text" aria-label="商品" autocomplete="off" @focus="ui.showProductDropdown(index)" @blur="ui.hideProductDropdown(index)" @input="ui.onProductInput(index)" />
                </td>
                <td v-if="isPurchaseOrder" class="muted" :title="item.productCode">{{ item.productCode }}</td>
                <td><input v-model="item[ui.config.specField]" type="text" readonly /></td>
                <td><input v-model="item.unit" type="text" readonly /></td>
                <template v-if="!isPurchaseOrder">
                  <td><select v-if="item.productId" v-model="item.warehouseId" class="purchase-cell-select" :ref="element => setFieldRef(`item-warehouse-${index}`, element)" aria-label="所属仓库" @focus="activatePurchaseCell(item, 'warehouse')" @blur="activePurchaseCell = ''" @change="ui.onItemWarehouseChange(item); dismissHint(`item-warehouse-${index}`)"><option value="">{{ purchaseCellPlaceholder(item, 'warehouse', ui.form.storeId ? '请选择仓库' : '请先选择门店') }}</option><option v-for="warehouse in ui.filteredWarehouses" :key="warehouse.id" :value="String(warehouse.id)">{{ warehouse.name }}</option></select></td>
                  <td class="right">{{ item.productId ? money(item.currentStock) : '' }}</td>
                  <td><input v-if="isPurchase" v-model.number="item.expectedQty" :ref="element => setFieldRef(`item-expected-${index}`, element)" aria-label="应收数量" type="number" min="0" step="0.0001" /><input v-else v-model.number="item.packages" aria-label="件数" type="number" min="0" step="0.01" @input="ui.onPackagesInput(index)" /></td>
                </template>
                <td><input v-if="!isPurchaseOrder || item.productId" v-model.number="item.quantity" :ref="element => setFieldRef(`item-quantity-${index}`, element)" :aria-label="isPurchaseOrder ? '采购数量' : '数量'" type="number" :min="isPurchaseOrder ? '0.0001' : '0'" step="0.0001" :required="isPurchaseOrder" @input="ui.onQuantityInput(index); dismissHint(`item-quantity-${index}`)" /><span v-else class="blank-cell"></span></td>
                <td v-if="isPurchaseOrder">
                  <input v-if="item.productId" :value="ui.supplierDropdownOpen && ui.focusedSupplierRow === index ? ui.supplierSearch : item.supplierName" class="purchase-cell-input" :ref="element => setSupplierInputRef(index, element)" type="text" autocomplete="off" :required="ui.auditMode" aria-label="采购供应商" :placeholder="purchaseCellPlaceholder(item, 'supplier', ui.auditMode ? '请选择采购供应商' : '暂不指定（选填）')" @focus="activatePurchaseCell(item, 'supplier'); ui.openSupplierDropdown(index)" @blur="activePurchaseCell = ''; ui.hideSupplierDropdown(index)" @input="ui.handleSupplierSearchInput(index, $event); dismissHint(`item-supplier-${index}`)" @keydown.escape.prevent="ui.closeSupplierDropdown?.()" />
                  <span v-else class="blank-cell"></span>
                </td>
                <td><input v-if="!isPurchaseOrder || item.productId" v-model.number="item.price" :ref="element => setFieldRef(`item-price-${index}`, element)" :aria-label="isPurchaseOrder ? '采购单价' : '单价'" :required="isPurchaseOrder && ui.auditMode" type="number" min="0" :step="isPurchase ? '0.0001' : '0.01'" @input="ui.onPriceInput(index); dismissHint(`item-price-${index}`)" /><span v-else class="blank-cell"></span></td>
                <template v-if="ui.taxEnabled">
                  <td><input v-if="item.productId" v-model.number="item.taxRate" :ref="element => setFieldRef(`item-tax-${index}`, element)" aria-label="税率" type="number" min="0" max="100" step="0.01" @input="ui.onTaxRateInput(index)" /></td>
                  <td><input v-if="item.productId" v-model.number="item.taxIncludedPrice" aria-label="含税单价" type="number" min="0" step="0.01" @input="ui.onIncludedPriceInput(index)" /></td>
                </template>
                <td class="right"><template v-if="isPurchaseOrder"><input v-if="item.productId" v-model.number="item.amount" :ref="element => setFieldRef(`item-amount-${index}`, element)" aria-label="金额" type="number" min="0" step="0.01" @input="dismissHint(`item-amount-${index}`)" /><span v-else class="blank-cell"></span></template><template v-else>{{ item.productId ? money(item.amount) : '' }}</template></td>
                <template v-if="ui.taxEnabled"><td v-if="!isSale" class="right">{{ item.productId ? money(item.taxAmount) : '' }}</td><td class="right">{{ item.productId ? money(item[ui.config.includedField]) : '' }}</td></template>
                <template v-if="isPurchase"><td><input v-model="item.batchNo" :ref="element => setFieldRef(`item-batch-${index}`, element)" aria-label="批次号" type="text" maxlength="80" /></td><td><input v-model="item.binCode" aria-label="货位编码" type="text" maxlength="80" /></td></template>
                <td><input v-if="!isPurchaseOrder || item.productId" v-model="item.remark" aria-label="行备注" type="text" :maxlength="isPurchaseOrder ? 500 : undefined" /><span v-else class="blank-cell"></span></td>
              </tr>
              <tr class="total-row">
                <td :colspan="isPurchaseOrder ? 8 : 7" class="center">合计</td>
                <td v-if="!isPurchaseOrder" class="right"><input v-if="isSale" v-model.number="ui.totalPackages" aria-label="总件数" type="number" min="0" @input="ui.onTotalPackagesManualInput" /><span v-else>{{ money(ui.totalPackages) }}</span></td>
                <td class="right">{{ isPurchaseOrder && !hasPurchaseOrderItems ? '' : money(ui.totalQuantity) }}</td><td :colspan="isPurchaseOrder ? 2 : ui.taxEnabled ? 3 : 1"></td>
                <td class="right">{{ isPurchaseOrder && !hasPurchaseOrderItems ? '' : money(ui.totalAmount) }}</td><template v-if="ui.taxEnabled"><td v-if="!isSale" class="right">{{ money(ui.totalTaxAmount) }}</td><td class="right">{{ money(ui.totalIncludedAmount) }}</td></template><td :colspan="isPurchase ? 3 : 1"></td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="bottom-info-bar">
          <div class="finance-row-full">
            <label v-if="isSalesDocument && (ui.salesPeople.length || ui.form.salesPerson)" class="info-group salesperson-field">
              <span>业务员</span>
              <span class="salesperson-control">
                <span class="salesperson-sizer" aria-hidden="true">{{ salespersonLabel }}</span>
                <select v-model="ui.form.salesPerson" @change="dismissHint('salesPerson')">
                  <option value="">请选择业务员</option>
                  <option v-if="ui.form.salesPerson && !ui.salesPeople.some(employee => employee.displayName === ui.form.salesPerson)" :value="ui.form.salesPerson">{{ ui.form.salesPerson }}（历史记录）</option>
                  <option v-for="employee in ui.salesPeople" :key="employee.id" :value="employee.displayName">{{ employee.displayName }}</option>
                </select>
              </span>
            </label>
            <label v-if="isSalesDocument" class="info-group"><span>制单人</span><input :value="ui.currentCreatorName" :style="ui.creatorNameStyle" type="text" readonly /></label>
            <label v-if="isPurchaseOrder" class="info-group purchaser-field">
              <span>采购人</span>
              <span class="salesperson-control">
                <span class="salesperson-sizer" aria-hidden="true">{{ purchasePersonLabel }}</span>
                <select v-model="ui.form.purchaser">
                  <option value="">请选择采购人</option>
                  <option v-if="ui.form.purchaser && !ui.purchasePeople.some(employee => employee.displayName === ui.form.purchaser)" :value="ui.form.purchaser">{{ ui.form.purchaser }}（历史记录）</option>
                  <option v-for="employee in ui.purchasePeople" :key="employee.id || employee.username" :value="employee.displayName">{{ employee.displayName }}</option>
                </select>
              </span>
            </label>
            <label v-if="isPurchaseOrder" class="info-group"><span>制单人</span><input :value="ui.currentCreatorName" :style="ui.creatorNameStyle" type="text" readonly /></label>
            <label class="info-group wide"><span>{{ isPurchaseOrder ? '申请备注' : '备注信息' }}</span><input v-model="ui.form[ui.config.remarkField]" type="text" :maxlength="isPurchaseOrder ? 500 : isPurchase ? 200 : 1000" :placeholder="isPurchaseOrder ? '申请用途、交期等补充说明' : undefined" /></label>
            <label v-if="isSalesDocument" class="info-group"><span>包装</span><select v-model="ui.form.packaging" @change="ui.handlePackagingChange?.()"><option v-for="packaging in ui.packagingOptions" :key="packaging" :value="packaging">{{ packaging }}</option><option v-if="isSale" :value="ui.ADD_PACKAGING_VALUE">新增包装...</option></select></label>
            <template v-if="isSale"><label class="info-group"><span>折扣后金额</span><input v-model.number="ui.form.discountAmount" type="number" min="0" step="0.01" /></label><label class="info-group"><span>其他费用</span><input v-model.number="ui.form.otherFees" type="number" min="0" step="0.01" /></label></template>
            <template v-if="isReturn"><label class="info-group"><span>应退金额</span><input v-model.number="ui.form.returnAmount" :ref="element => setFieldRef('returnAmount', element)" type="number" min="0" step="0.01" /></label><label class="info-group"><span>本次退款</span><input v-model.number="ui.form.refundAmount" :ref="element => setFieldRef('refundAmount', element)" type="number" min="0" step="0.01" /></label></template>
            <template v-if="isPurchaseOrder">
              <label class="info-group"><span>付款金额</span><input v-model.number="ui.form.paymentAmount" :ref="element => setFieldRef('paymentAmount', element)" type="number" min="0" step="0.01" /></label>
              <label class="info-group"><span>其它费用</span><input v-model.number="ui.form.otherFees" :ref="element => setFieldRef('otherFees', element)" type="number" min="0" step="0.01" /></label>
            </template>
            <label v-if="isSalesDocument" class="info-group"><span>结算账户</span><select v-model="ui.form.settlementAccount"><option value="">请选择结算账户</option><option v-if="ui.form.settlementAccount && !ui.storeBankAccounts.some(account => (account.value || account.accountName) === ui.form.settlementAccount)" :value="ui.form.settlementAccount">{{ ui.form.settlementAccount }}</option><option v-for="account in ui.storeBankAccounts" :key="account.id" :value="account.value || account.accountName">{{ account.label || account.accountName }}</option></select></label>
            <label v-if="isPurchaseOrder" class="info-group"><span>结算账户</span><select v-model="ui.form.settlementAccount"><option value="">请选择结算账户</option><option v-if="ui.form.settlementAccount && !ui.storeBankAccounts.some(account => (account.value || account.accountName) === ui.form.settlementAccount)" :value="ui.form.settlementAccount">{{ ui.form.settlementAccount }}</option><option v-for="account in ui.storeBankAccounts" :key="account.id" :value="account.value || account.accountName">{{ account.label || account.accountName }}</option></select></label>
          </div>
          <div class="finance-row">
            <template v-if="isSale"><span>客户欠款 <strong>{{ money(ui.customerReceivable) }}</strong></span><span>本单应收 <strong>{{ money(ui.shouldReceive) }}</strong></span><label class="info-group"><span>本次收款</span><input v-model.number="ui.form.currentPayment" type="number" min="0" step="0.01" /></label><span>本单欠款 <strong class="red">{{ money(ui.currentDebt) }}</strong></span></template>
            <template v-else-if="isReturn"><span>商品合计 <strong>{{ money(ui.taxEnabled ? ui.totalIncludedAmount : ui.totalAmount) }}</strong></span><span>核销金额 <strong>{{ money(Number(ui.form.returnAmount || 0) - Number(ui.form.refundAmount || 0)) }}</strong></span><span>本次退款 <strong class="red">{{ money(ui.form.refundAmount) }}</strong></span></template>
            <template v-else-if="isPurchaseOrder"><span class="document-status" :class="`status-${ui.form.status}`">{{ ui.statusLabel }}</span><span>供应商应付 <strong>{{ formatMoney(ui.supplierPayable) }}</strong></span><span>本单应付 <strong>{{ formatMoney(ui.purchaseOrderPayable) }}</strong></span><label class="info-group"><span>本次付款</span><input v-model.number="ui.form.currentPayment" :ref="element => setFieldRef('currentPayment', element)" type="number" min="0" step="0.01" /></label><span>本单应付 <strong class="red">{{ formatMoney(ui.currentPayable) }}</strong></span></template>
            <template v-else><span>入库数量 <strong>{{ money(ui.totalQuantity) }}</strong></span><span>入库金额 <strong>{{ money(ui.totalAmount) }}</strong></span><span v-if="ui.taxEnabled">税额 <strong>{{ money(ui.totalTaxAmount) }}</strong></span><span>价税合计 <strong>{{ money(ui.totalIncludedAmount) }}</strong></span></template>
            <div v-if="isPurchaseOrder && !ui.readOnly" class="document-actions">
              <button class="btn" type="button" @click="requestClose">取消</button>
              <button v-if="!ui.auditMode" class="btn btn-secondary" type="button" @click="submitDocument($event, 'draft')"><Save :size="16" aria-hidden="true" />保存草稿</button>
              <button class="btn btn-primary" type="submit"><Check v-if="ui.auditMode" :size="16" aria-hidden="true" /><Send v-else :size="16" aria-hidden="true" />{{ ui.saving ? (ui.auditMode ? '审核中...' : '保存中...') : (ui.auditMode ? '补充并审核通过' : '提交审核') }}</button>
            </div>
            <button v-else-if="!isPurchaseOrder" class="btn btn-primary save-button" type="submit">{{ ui.saving ? '保存中...' : '保存并打印' }}</button>
          </div>
        </div>
      </fieldset>
      <footer v-if="ui.loading || ui.loadFailed || ui.readOnly" class="document-footer">
        <span v-if="ui.loading" role="status">加载中...</span><span v-else-if="ui.loadFailed" class="red" role="alert">加载失败，请刷新后重试</span><span v-else-if="ui.readOnly">只读 · {{ ui.statusLabel || ui.form.status || '单据详情' }}</span>
        <button v-if="isPurchaseOrder" class="btn" type="button" :disabled="ui.saving" @click="requestClose">返回列表</button>
        <button v-if="ui.config.printType && ui.readOnly && !ui.loading && !ui.loadFailed" class="btn" type="button" @click="ui.openPrint?.()">打印</button>
      </footer>
    </form>

    <Teleport to="body">
      <div v-if="(isSalesDocument || isPurchaseOrder) && ui.activeProductRow && !ui.readOnly" :ref="ui.setProductDropdownRef" class="document-dropdown product-dropdown" :style="ui.productDropdownStyle" @pointerdown.stop @mousedown.prevent>
        <div class="product-option dropdown-heading"><span>编号</span><span>名称</span><span>规格</span><span>单位</span><span>库存</span><span>备注</span></div>
        <button v-for="product in ui.activeProductRow.filteredProducts" :key="product.id" type="button" class="product-option" @click="ui.selectProduct(ui.focusedRow, product)"><span>{{ product.code || '-' }}</span><span>{{ product.name }}</span><span>{{ product.specification || '-' }}</span><span>{{ ui.getUnitName(product.unitId) || product.unit || '-' }}</span><span>{{ money(ui.getProductStock(product, ui.activeProductRow)) }}</span><span :title="product.notes || product.remark">{{ product.notes || product.remark || '-' }}</span></button>
        <div v-if="!ui.activeProductRow.filteredProducts.length" class="dropdown-empty">暂无匹配商品</div>
      </div>
      <div v-if="isSalesDocument && ui.customerDropdownOpen && !ui.readOnly" :ref="ui.setCustomerDropdownRef" class="document-dropdown customer-dropdown" :style="ui.customerDropdownStyle" @pointerdown.stop @mousedown.prevent>
        <button v-for="customer in ui.paginatedCustomers" :key="customer.id" type="button" class="customer-option" @click="ui.selectCustomer(customer)"><strong>{{ customer.customerName || customer.name }}</strong><span>{{ customer.contactPerson || '-' }}</span><span>{{ customer.phone || '-' }}</span></button>
        <div v-if="!ui.paginatedCustomers.length" class="dropdown-empty">暂无匹配客户</div>
        <div v-if="ui.customerTotalPages > 1" class="dropdown-pagination"><button type="button" aria-label="上一页客户" :disabled="ui.customerPage <= 1" @click="ui.changeCustomerPage(ui.customerPage - 1)">&lsaquo;</button><span>{{ ui.customerPage }} / {{ ui.customerTotalPages }}</span><button type="button" aria-label="下一页客户" :disabled="ui.customerPage >= ui.customerTotalPages" @click="ui.changeCustomerPage(ui.customerPage + 1)">&rsaquo;</button></div>
      </div>
      <div v-if="isPurchaseOrder && ui.supplierDropdownOpen && !ui.readOnly" :ref="ui.setSupplierDropdownRef" class="document-dropdown customer-dropdown" :style="ui.supplierDropdownStyle" @pointerdown.stop @mousedown.prevent>
        <button v-for="supplier in ui.paginatedSuppliers" :key="supplier.id" type="button" class="customer-option" @click="ui.selectSupplier(ui.focusedSupplierRow, supplier)"><strong>{{ supplier.supplierName || supplier.name }}</strong><span>{{ supplier.contactPerson || '-' }}</span><span>{{ supplier.phone || '-' }}</span></button>
        <div v-if="!ui.paginatedSuppliers.length" class="dropdown-empty">暂无匹配供应商</div>
        <div v-if="ui.supplierTotalPages > 1" class="dropdown-pagination"><button type="button" aria-label="上一页供应商" :disabled="ui.supplierPage <= 1" @click="ui.changeSupplierPage(ui.supplierPage - 1)">&lsaquo;</button><span>{{ ui.supplierPage }} / {{ ui.supplierTotalPages }}</span><button type="button" aria-label="下一页供应商" :disabled="ui.supplierPage >= ui.supplierTotalPages" @click="ui.changeSupplierPage(ui.supplierPage + 1)">&rsaquo;</button></div>
      </div>
      <div v-if="ui.validationHint?.key" :ref="ui.setValidationHintRef" class="validation-hint" :class="ui.validationHintPlacement" :style="ui.validationHintStyle" role="alert"><TriangleAlert :size="18" aria-hidden="true" /><span><template v-for="(part, index) in validationMessageParts" :key="index"><strong v-if="part.important">{{ part.text }}</strong><template v-else>{{ part.text }}</template></template></span></div>
      <div v-if="ui.notice?.visible" class="page-notice" :class="{ error: ui.notice.type === 'error', 'purchase-order-notice': isPurchaseOrder }" :role="ui.notice.type === 'error' ? 'alert' : 'status'"><template v-if="isPurchaseOrder"><CircleAlert v-if="ui.notice.type === 'error'" :size="19" aria-hidden="true" /><CircleCheck v-else :size="19" aria-hidden="true" /></template>{{ ui.notice.message }}</div>
    </Teleport>
    <CustomModal :visible="Boolean(confirmation)" :title="confirmation === 'clear' ? '确认清空' : '确认关闭'" :message="confirmation === 'clear' ? '确定清空当前填写的数据？' : '确定关闭当前单据？'" @confirm="confirmAction" @cancel="confirmation = ''" />
    <CustomModal :visible="Boolean(ui.showModal)" :title="ui.modalTitle || '操作失败'" :message="ui.modalMessage || ''" :show-cancel="false" type="error" @confirm="ui.closeModal?.()" @cancel="ui.closeModal?.()" />
    <PrintTemplateSelector v-if="ui.config.printType" :visible="ui.printTemplateDialogOpen" :business-type="ui.config.printType" :title="`${ui.config.title}打印`" :document-number="ui.printNumber" @close="ui.closePrintTemplateDialog" @preview="ui.previewSelectedPrintTemplate" @print="ui.printSelectedPrintTemplate" />
    <OrderPrintPreview v-if="ui.config.printType" :visible="ui.printPreviewVisible" :template="ui.selectedPrintTemplate" :variables="ui.printVariables" :printer="ui.selectedPrintPrinter" :auto-print="ui.printPreviewAutoPrint" @close="ui.closePrintPreview" />
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Check, CircleAlert, CircleCheck, Plus, Save, Send, Trash2, TriangleAlert, X } from '@lucide/vue'
import CustomModal from '@/components/CustomModal.vue'
import PrintTemplateSelector from '@/components/print/PrintTemplateSelector.vue'
import OrderPrintPreview from '@/components/print/OrderPrintPreview.vue'
import { DOCUMENT_ACTIONS, DOCUMENT_TYPES, money } from '@/composables/documents/documentModels'
import { useBusinessDocument } from '@/composables/documents/useBusinessDocument'

const props = defineProps({
  documentType: { type: String, required: true, validator: value => Boolean(DOCUMENT_TYPES[value]) },
  action: { type: String, default: 'create', validator: value => DOCUMENT_ACTIONS.includes(value) },
  documentId: { type: Number, default: null },
  purchaseOrderId: { type: Number, default: null },
  printOnOpen: { type: Boolean, default: false },
  productType: { type: String, default: 'finished-product' }
})
const emit = defineEmits(['close'])
const ui = useBusinessDocument(props)
const isSale = computed(() => props.documentType === 'sale')
const isReturn = computed(() => props.documentType === 'sale-return')
const isPurchase = computed(() => props.documentType === 'purchase')
const isPurchaseOrder = computed(() => props.documentType === 'purchase-order')
const hasPurchaseOrderItems = computed(() => isPurchaseOrder.value && ui.form.items.some(item => item.productId))
const activePurchaseCell = ref('')
const activatePurchaseCell = (item, field) => { activePurchaseCell.value = `${item.key}-${field}` }
const purchaseCellPlaceholder = (item, field, message) => activePurchaseCell.value === `${item.key}-${field}` ? message : ''
const purchaseProductPlaceholder = item => {
  if (activePurchaseCell.value !== `${item.key}-product`) return ''
  if (!ui.form.storeId) return '请先选择门店'
  if (!item.warehouseId) return '请先选择仓库'
  if (ui.categoriesForItem?.(item)?.length && !item.categoryId) return '请先选择分类'
  return '搜索或选择商品'
}
const isMaterial = computed(() => isPurchase.value && ui.form.type !== 'finished-product')
const isSalesDocument = computed(() => isSale.value || isReturn.value)
const formatMoney = value => Number(value || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const fieldsDisabled = computed(() => ui.loading || ui.loadFailed || ui.readOnly || ui.saving)
const salespersonLabel = computed(() => {
  const name = ui.form.salesPerson
  if (!name) return '请选择业务员'
  return ui.salesPeople.some(employee => employee.displayName === name) ? name : `${name}（历史记录）`
})
const purchasePersonLabel = computed(() => {
  const name = ui.form.purchaser
  if (!name) return '请选择采购人'
  return ui.purchasePeople.some(employee => employee.displayName === name) ? name : `${name}（历史记录）`
})
const confirmation = ref('')
const requestClose = () => {
  if (ui.saving) return
  if (ui.readOnly || ui.loadFailed) emit('close')
  else confirmation.value = 'close'
}
const handleNumberWheel = event => {
  if (event.target instanceof HTMLInputElement && event.target.type === 'number') {
    event.preventDefault()
  }
}
const handleStoreChange = () => {
  ui.onStoreChange?.()
  dismissHint('storeId')
}
const handleHeaderWarehouseChange = () => {
  ui.onWarehouseChange?.()
  dismissHint('warehouseId')
}
const validationMessageParts = computed(() => (ui.validationHint?.message || '').split(/(采购数量|采购供应商|采购单价|申请门店|申请日期|实收数量|应收数量|商品数量|原订单编号|单据日期|所属仓库|分类|应退金额|本次退款|总件数|联系(?:人|方式|电话)|供应商|门店|仓库|客户|商品明细|商品|物料|批次号|数量|单价|税率|金额|件数|有效数值|整数|非负数|\d+(?:\.\d+)?)/g).map((text, index) => ({ text, important: index % 2 === 1 })))
const submitDocument = (event, status) => {
  if (fieldsDisabled.value || !ui.validateForm()) return
  const form = event.currentTarget instanceof HTMLFormElement ? event.currentTarget : event.currentTarget.form
  for (const [index, input] of Array.from(form.elements).entries()) {
    if (!input.willValidate || input.validity.valid) continue
    const label = input.getAttribute('aria-label') || input.closest('label')?.querySelector('span')?.textContent.trim() || '输入值'
    let message = `请输入有效的${label}。`
    if (input.validity.rangeUnderflow) message = `${label}不能小于 ${input.min}。`
    else if (input.validity.rangeOverflow) message = `${label}不能大于 ${input.max}。`
    else if (input.validity.stepMismatch) {
      const step = input.step || '1'
      const decimalPlaces = (step.split('.')[1] || '').length
      message = decimalPlaces ? `${label}最多保留 ${decimalPlaces} 位小数。` : `${label}需为整数。`
    }
    const key = `native-input-${index}`
    ui.setValidationFieldRef(key, input)
    ui.showValidationHint(key, message)
    return
  }
  ui.save(status)
}
watch(() => ui.loading, loading => {
  if (!loading && props.printOnOpen && !ui.loadFailed) ui.openPrint?.()
})
const setFieldRef = (key, element) => ui.setValidationFieldRef?.(key, element)
const dismissHint = key => ui.dismissValidationHint?.(key)
const setCustomerInputRef = element => {
  ui.setCustomerInputRef?.(element)
  setFieldRef('customerId', element)
}
const setProductInputRef = (index, element) => {
  ui.setProductInputRef?.(index, element)
  setFieldRef(`item-product-${index}`, element)
}
const setSupplierInputRef = (index, element) => {
  ui.setSupplierInputRef?.(index, element)
  setFieldRef(`item-supplier-${index}`, element)
}
const confirmAction = () => {
  const action = confirmation.value
  confirmation.value = ''
  if (action === 'clear') ui.clearForm()
  else {
    ui.discardDraft?.()
    emit('close')
  }
}
defineExpose({ ui })
</script>

<style scoped>
.business-document-form, .business-document-form * { box-sizing: border-box; letter-spacing: 0; }
.business-document-form { color: #17212b; background: #fff; border: 1px solid #e3e8ec; border-radius: 6px; font-size: 13px; }
form, fieldset { margin: 0; padding: 0; border: 0; min-width: 0; }
.top-info-bar, .contact-info-bar, .finance-row-full, .finance-row { display: flex; align-items: center; flex-wrap: wrap; gap: 12px; padding: 12px 14px; border-bottom: 1px solid #e3e8ec; }
.top-info-bar h2 { margin: 0 4px 0 0; font-size: 17px; white-space: nowrap; }
.header-fields { display: contents; }
.contact-info-bar { background: #fbfcfc; }
.info-group { display: flex; align-items: center; min-width: 0; gap: 7px; }
.info-group > span { flex: none; color: #5c6975; font-size: 12px; white-space: nowrap; }
input, select, button { font: inherit; }
.info-group input, .info-group select { width: 142px; min-width: 0; height: 34px; padding: 0 9px; border: 1px solid #d4dde3; border-radius: 4px; color: #17212b; background: #fff; }
.top-info-bar .info-group > span, .contact-info-bar .info-group > span, .top-info-bar .tax-toggle { color: #46535f; font-size: 14px; font-weight: 600; }
.top-info-bar .info-group input, .top-info-bar .info-group select, .contact-info-bar .info-group input, .contact-info-bar .info-group select { width: 160px; height: 38px; padding: 0 11px; font-size: 14px; }
.contact-info-bar .address-field input { width: 192px; }
.contact-info-bar .logistics-field select { width: 220px; }
.info-group.wide { flex: 1 1 230px; }
.info-group.wide input { width: 100%; }
.info-group.salesperson-field, .info-group.purchaser-field { flex: 0 1 auto; max-width: 100%; }
.info-group > .salesperson-control { position: relative; display: inline-block; min-width: 72px; max-width: 280px; color: #17212b; font-size: 13px; font-weight: 400; }
.salesperson-sizer { display: block; visibility: hidden; height: 34px; padding: 0 32px 0 11px; white-space: nowrap; }
.info-group .salesperson-control select { position: absolute; inset: 0; width: 100%; min-width: 0; padding: 0 28px 0 9px; }
input[type=number] { -moz-appearance: textfield; appearance: textfield; }
input[type=number]::-webkit-inner-spin-button, input[type=number]::-webkit-outer-spin-button { margin: 0; appearance: none; }
input:focus, select:focus { outline: 2px solid #b5e5d8; outline-offset: -1px; }
input[readonly] { background: #f8fafb; color: #64717c; }
.toolbar-actions { margin-left: auto; display: flex; align-items: center; gap: 10px; }
.toolbar-actions .btn { min-height: 38px; font-size: 14px; }
.close-button { width: 38px; padding: 0; }
.tax-toggle { display: flex; align-items: center; gap: 5px; white-space: nowrap; }
.tax-toggle input { accent-color: #159a7c; }
.btn { min-height: 34px; display: inline-flex; align-items: center; justify-content: center; gap: 6px; padding: 0 13px; border: 1px solid #d4dde3; border-radius: 4px; background: #fff; color: #52616c; cursor: pointer; white-space: nowrap; }
.btn:hover { background: #f3f8f6; }
.btn-primary { color: #fff; background: #159a7c; border-color: #159a7c; }
.btn-primary:hover { background: #08755e; }
.btn-danger { color: #b5363e; background: #fff6f6; border-color: #f1cbd0; }
button:disabled { cursor: default; opacity: .5; }
.products-table-wrapper { overflow-x: auto; }
.products-table { width: 100%; table-layout: fixed; border-collapse: collapse; }
.products-table th, .products-table td { height: 43px; padding: 4px 7px; border-bottom: 1px solid #e9eef1; border-right: 1px solid #eef1f3; overflow: hidden; }
.products-table th { font-weight: 600; font-size: 12px; color: #6c7a85; background: #f8fafb; text-align: left; white-space: nowrap; }
.products-table td input, .products-table td select { width: 100%; height: 32px; min-width: 0; border: 1px solid transparent; border-radius: 3px; color: inherit; background: transparent; padding: 0 4px; }
.products-table td { color: #17212b; font-size: 14px; }
.products-table td input[type=number], .products-table td.right { font-weight: 500; font-variant-numeric: tabular-nums; }
.products-table .total-row td { font-weight: 600; }
.products-table td input:hover, .products-table td select:hover { border-color: #d4dde3; }
.products-table td input[type=number] { text-align: right; }
.products-table td input[readonly] { color: #46535f; }
.row-focused { background: #f3fbf8; }
.center { text-align: center; }
.right { text-align: right; font-variant-numeric: tabular-nums; }
.btn-icon { width: 24px; height: 26px; border: 0; border-radius: 3px; color: #08755e; background: transparent; font-size: 20px; cursor: pointer; }
.btn-icon:hover { background: #e6f4ef; }
.btn-icon.remove { color: #b5363e; }
.total-row { background: #f8fafb; font-weight: 600; }
.finance-row-full { border-bottom: 0; }
.finance-row { gap: 22px; background: #fbfcfc; }
.finance-row strong { margin-left: 8px; font-variant-numeric: tabular-nums; color: #08755e; }
.red, .finance-row .red { color: #b5363e; }
.save-button { margin-left: auto; font-weight: 600; }
.document-footer { display: flex; align-items: center; justify-content: flex-end; gap: 10px; padding: 8px 14px; }
.document-footer > span { margin-right: auto; color: #65727e; }
fieldset:disabled .save-button, fieldset:disabled .btn-icon, fieldset:disabled .btn-danger { visibility: hidden; }
.document-dropdown { position: fixed; z-index: 3200; overflow: auto; max-width: calc(100vw - 24px); border: 1px solid #cdd9df; border-radius: 5px; background: #fff; box-shadow: 0 8px 25px #17212b24; color: #17212b; font-size: 12px; box-sizing: border-box; }
.product-option { display: grid; grid-template-columns: 70px 1.6fr 1fr 50px 60px 1fr; align-items: center; width: 100%; min-height: 38px; padding: 7px 10px; border: 0; border-bottom: 1px solid #eef1f3; background: #fff; text-align: left; gap: 8px; cursor: pointer; font: inherit; }
.product-option > span, .customer-option > span, .customer-option > strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.product-option:hover, .customer-option:hover { background: #eaf7f2; }
.dropdown-heading { position: sticky; top: 0; background: #f6f9fa; color: #6c7a85; font-weight: 600; cursor: default; }
.customer-option { display: grid; grid-template-columns: 1.2fr 1fr 1fr; width: 100%; min-height: 38px; padding: 8px 10px; gap: 8px; border: 0; border-bottom: 1px solid #eef1f3; background: #fff; text-align: left; cursor: pointer; font: inherit; }
.dropdown-empty { padding: 20px; color: #7b8892; text-align: center; }
.dropdown-pagination { display: flex; justify-content: center; align-items: center; gap: 14px; padding: 7px; }
.dropdown-pagination button { width: 28px; height: 28px; border: 1px solid #d4dde3; border-radius: 4px; background: #fff; cursor: pointer; }
.validation-hint { position: fixed; z-index: 4000; display: flex; align-items: center; gap: 8px; max-width: min(360px, calc(100vw - 24px)); padding: 9px 12px; border: 1px solid #cbd2d8; border-radius: 4px; background: #fff; color: #17212b; font-size: 14px; line-height: 1.5; box-shadow: 0 3px 10px #17212b26; box-sizing: border-box; overflow-wrap: anywhere; }
.validation-hint > svg { flex: none; color: #d97706; }
.validation-hint strong { color: #dc2626; font-weight: 600; }
.validation-hint::before { content: ''; position: absolute; left: var(--hint-arrow-left, 20px); width: 10px; height: 10px; background: #fff; transform: translateX(-50%) rotate(45deg); }
.validation-hint.below::before { top: -6px; border-top: 1px solid #cbd2d8; border-left: 1px solid #cbd2d8; }
.validation-hint.above::before { bottom: -6px; border-right: 1px solid #cbd2d8; border-bottom: 1px solid #cbd2d8; }
.page-notice { position: fixed; z-index: 4500; top: 78px; left: 50%; max-width: calc(100vw - 24px); transform: translateX(-50%); padding: 11px 18px; background: #ecf9f3; color: #08755e; border: 1px solid #b5e5d8; border-radius: 5px; box-shadow: 0 6px 20px #17212b18; }
.page-notice.error { background: #fff; color: #b5363e; border-color: #d4dde3; }
.business-document-form[data-document-type="purchase-order"] { min-width: 0; margin: 20px; border-color: #e2e8f0; border-radius: 7px; }
.business-document-form[data-document-type="purchase-order"] .top-info-bar,
.business-document-form[data-document-type="purchase-order"] .finance-row-full,
.business-document-form[data-document-type="purchase-order"] .finance-row { padding: 14px 20px; }
.business-document-form[data-document-type="purchase-order"] b { color: #dc3545; }
.business-document-form[data-document-type="purchase-order"] .products-table { min-width: 0; width: 100%; }
.business-document-form[data-document-type="purchase-order"] .products-table td { font-size: 12px; }
.business-document-form[data-document-type="purchase-order"] .products-table td input,
.business-document-form[data-document-type="purchase-order"] .products-table td select { height: 28px; }
.business-document-form[data-document-type="purchase-order"] .products-table td .purchase-cell-select,
.business-document-form[data-document-type="purchase"] .products-table td .purchase-cell-select { appearance: none; padding-right: 20px; background-image: none; }
.business-document-form[data-document-type="purchase-order"] .products-table td .purchase-cell-select:focus,
.business-document-form[data-document-type="purchase"] .products-table td .purchase-cell-select:focus { border-color: #0f9f78; background-color: #fff; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6'%3E%3Cpath d='M0 0h10L5 6z' fill='%23172033'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 5px center; background-size: 10px 6px; }
.business-document-form[data-document-type="purchase-order"] .products-table tbody tr:not(.total-row):hover { background: #f4fbf8; }
.business-document-form[data-document-type="purchase-order"] .products-table th.right { text-align: right; }
.business-document-form[data-document-type="purchase-order"] .muted { color: #596579; text-overflow: ellipsis; white-space: nowrap; }
.business-document-form[data-document-type="purchase-order"] .blank-cell { display: block; min-height: 28px; }
.business-document-form[data-document-type="purchase-order"] .info-group input { height: 38px; }
.business-document-form[data-document-type="purchase-order"] .btn { min-height: 38px; border-radius: 5px; font-size: 13px; font-weight: 600; }
.business-document-form[data-document-type="purchase-order"] .btn-primary { background: #0f9f78; border-color: #0f9f78; }
.business-document-form[data-document-type="purchase-order"] .btn-primary:hover:not(:disabled) { background: #08745a; border-color: #08745a; }
.business-document-form[data-document-type="purchase-order"] .btn-secondary { color: #08745a; background: #e9f8f3; border-color: #a9e5d2; }
.business-document-form[data-document-type="purchase-order"] button:focus-visible { outline: 2px solid #0f9f78; outline-offset: 2px; }
.btn-icon { display: inline-flex; align-items: center; justify-content: center; padding: 0; vertical-align: middle; }
.document-actions { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; margin-left: auto; }
.document-status { display: inline-flex; align-items: center; min-height: 25px; padding: 3px 9px; border-radius: 999px; background: #f1f2f4; color: #596579; font-size: 12px; font-weight: 600; }
.document-status.status-pending, .document-status.status-partial { background: #fff3df; color: #a4510b; }
.document-status.status-approved { background: #e7f5f8; color: #16647a; }
.document-status.status-completed { background: #eaf8f1; color: #13734f; }
.document-status.status-cancelled { color: #b4232f; }
.page-notice.purchase-order-notice { top: 24px; display: flex; align-items: center; gap: 9px; min-height: 44px; max-width: min(520px, calc(100vw - 32px)); color: #172033; background: #fff; border-color: #dfe5ec; border-radius: 6px; font-size: 13px; font-weight: 600; line-height: 1.5; overflow-wrap: anywhere; box-shadow: 0 10px 30px #0f172a29; }
.purchase-order-notice svg { flex: none; color: #0f9f78; }
.purchase-order-notice.error svg { color: #dc3545; }
@media (max-width: 780px) {
  .business-document-form[data-document-type="purchase-order"] { margin: 12px; }
  .business-document-form[data-document-type="purchase-order"] .top-info-bar,
  .business-document-form[data-document-type="purchase-order"] .finance-row-full,
  .business-document-form[data-document-type="purchase-order"] .finance-row { gap: 10px; padding: 12px; }
  .business-document-form[data-document-type="purchase-order"] .top-info-bar h2 { flex-basis: 100%; }
  .business-document-form[data-document-type="purchase-order"] .info-group { flex: 1 1 240px; }
  .business-document-form[data-document-type="purchase-order"] .info-group input,
  .business-document-form[data-document-type="purchase-order"] .info-group select { flex: 1; width: 0; }
  .business-document-form[data-document-type="purchase-order"] .toolbar-actions { width: 100%; justify-content: flex-end; }
  .business-document-form[data-document-type="purchase-order"] .finance-row > .document-status { flex-basis: auto; }
  .document-actions { width: 100%; justify-content: flex-end; }
}
@media (max-width: 700px) {
  .top-info-bar, .contact-info-bar, .finance-row-full, .finance-row { gap: 10px; padding: 10px; }
  .top-info-bar h2 { flex-basis: 100%; }
  .info-group { flex: 1 1 240px; }
  .info-group input, .info-group select { flex: 1; width: 0; }
  .top-info-bar .info-group input, .top-info-bar .info-group select, .contact-info-bar .info-group input, .contact-info-bar .info-group select { width: 0; }
  .info-group .salesperson-control select { flex: none; width: 100%; }
  .salesperson-control { max-width: min(280px, calc(100vw - 100px)); }
  .toolbar-actions { width: 100%; justify-content: flex-end; }
  .finance-row > span { flex-basis: 100%; }
  .save-button { width: 100%; }
  .product-option { grid-template-columns: 50px 1.5fr 1fr 40px 45px; gap: 5px; padding: 6px; }
  .product-option > span:last-child { display: none; }
}
</style>
