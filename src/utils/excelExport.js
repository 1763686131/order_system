/**
 * Excel 导出工具
 * 基于 xlsx 库封装的通用导出功能
 */

import * as XLSX from 'xlsx'

/**
 * 导出数据到 Excel
 * @param {Object} options - 配置项
 * @param {string} options.filename - 文件名（不含扩展名）
 * @param {string} options.sheetName - 工作表名称
 * @param {Array<Array>} options.data - 数据数组（二维数组）
 * @param {Array<Object>} options.merges - 合并单元格配置 [{ s: { r: 0, c: 0 }, e: { r: 0, c: 12 } }]
 * @param {Array<Object>} options.colWidths - 列宽配置 [{ wch: 10 }, { wch: 15 }]
 * @param {Array<Object>} options.rowHeights - 行高配置 [{ hpt: 30 }]
 * @param {Object} options.styles - 样式配置对象
 */
export function exportToExcel(options) {
  const {
    filename = '导出文件',
    sheetName = 'Sheet1',
    data = [],
    merges = [],
    colWidths = [],
    rowHeights = [],
    styles = {}
  } = options

  // 创建工作簿和工作表
  const wb = XLSX.utils.book_new()
  const ws = XLSX.utils.aoa_to_sheet(data)

  // 设置列宽
  if (colWidths.length > 0) {
    ws['!cols'] = colWidths
  }

  // 设置行高
  if (rowHeights.length > 0) {
    ws['!rows'] = rowHeights
  }

  // 合并单元格
  if (merges.length > 0) {
    ws['!merges'] = merges
  }

  // 应用样式
  if (Object.keys(styles).length > 0) {
    applyStylesToWorksheet(ws, data, styles)
  }

  // 添加工作表到工作簿
  XLSX.utils.book_append_sheet(wb, ws, sheetName)

  // 导出文件
  XLSX.writeFile(wb, `${filename}.xlsx`, {
    bookType: 'xlsx',
    type: 'binary',
    cellStyles: true
  })
}

/**
 * 应用样式到工作表
 * @param {Object} ws - 工作表对象
 * @param {Array<Array>} data - 数据数组
 * @param {Object} styles - 样式配置
 */
function applyStylesToWorksheet(ws, data, styles) {
  const range = XLSX.utils.decode_range(ws['!ref'])

  for (let R = range.s.r; R <= range.e.r; ++R) {
    for (let C = range.s.c; C <= range.e.c; ++C) {
      const cellAddress = XLSX.utils.encode_cell({ r: R, c: C })
      if (!ws[cellAddress]) continue

      // 根据行类型应用样式
      const style = getStyleForRow(R, styles, data.length)
      if (style) {
        ws[cellAddress].s = style
      }
    }
  }
}

/**
 * 获取指定行的样式
 * @param {number} rowIndex - 行索引
 * @param {Object} styles - 样式配置对象
 * @param {number} totalRows - 总行数
 * @returns {Object|null}
 */
function getStyleForRow(rowIndex, styles, totalRows) {
  const {
    titleRow = null,
    headerRow = null,
    dataRowStart = null,
    summaryRow = null,
    titleStyle = {},
    headerStyle = {},
    dataStyle = {},
    summaryStyle = {}
  } = styles

  if (titleRow !== null && rowIndex === titleRow) {
    return titleStyle
  } else if (headerRow !== null && rowIndex === headerRow) {
    return headerStyle
  } else if (summaryRow !== null && rowIndex === summaryRow) {
    return summaryStyle
  } else if (dataRowStart !== null && rowIndex >= dataRowStart && rowIndex < totalRows - 1) {
    return dataStyle
  }

  return null
}

/**
 * 预设样式：标题样式
 */
export const TITLE_STYLE = {
  font: { name: '微软雅黑', sz: 16, bold: true },
  alignment: { horizontal: 'center', vertical: 'center' }
}

/**
 * 预设样式：表头样式
 */
export const HEADER_STYLE = {
  font: { name: '微软雅黑', sz: 11, bold: true, color: { rgb: 'FFFFFF' } },
  fill: { fgColor: { rgb: '4472C4' } },
  alignment: { horizontal: 'center', vertical: 'center' },
  border: {
    top: { style: 'thin', color: { rgb: '000000' } },
    bottom: { style: 'thin', color: { rgb: '000000' } },
    left: { style: 'thin', color: { rgb: '000000' } },
    right: { style: 'thin', color: { rgb: '000000' } }
  }
}

/**
 * 预设样式：数据样式
 */
export const DATA_STYLE = {
  font: { name: '微软雅黑', sz: 10 },
  alignment: { horizontal: 'center', vertical: 'center' },
  border: {
    top: { style: 'thin', color: { rgb: 'D0D0D0' } },
    bottom: { style: 'thin', color: { rgb: 'D0D0D0' } },
    left: { style: 'thin', color: { rgb: 'D0D0D0' } },
    right: { style: 'thin', color: { rgb: 'D0D0D0' } }
  }
}

/**
 * 预设样式：汇总样式
 */
export const SUMMARY_STYLE = {
  font: { name: '微软雅黑', sz: 11, bold: true },
  alignment: { horizontal: 'center', vertical: 'center' },
  fill: { fgColor: { rgb: 'F2F2F2' } },
  border: {
    top: { style: 'medium', color: { rgb: '000000' } },
    bottom: { style: 'medium', color: { rgb: '000000' } },
    left: { style: 'thin', color: { rgb: '000000' } },
    right: { style: 'thin', color: { rgb: '000000' } }
  }
}

/**
 * 运费记录导出（专用函数）
 * @param {Object} params - 参数对象
 */
export function exportFreightRecords(params) {
  const {
    periodText,
    mergedData,
    totalFreight,
    finalBalance,
    getDisplayIndex,
    formatDate,
    getGoodsName,
    getTotalWeight,
    getChannelName,
    getLogisticsNumber,
    getFreightAmountForRow,
    getPaidAmount,
    calculateBalance,
    hasReceipt
  } = params

  // 准备导出数据
  const exportRows = []

  // 添加标题行
  exportRows.push(['运费记录单'])
  exportRows.push([]) // 空行

  // 添加日期信息
  exportRows.push([`日期: ${periodText}`])
  exportRows.push([]) // 空行

  // 添加表头
  const headerRow = [
    '序号', '日期', '客户', '货物信息', '数量 (kg)', '收货地址',
    '渠道', '车牌号/单号', '价格 (¥)', '已支付', '备用金合计', '回单回传', '备注'
  ]
  exportRows.push(headerRow)

  const dataStartRow = exportRows.length // 记录数据开始行号

  // 添加数据行
  mergedData.forEach((item, index) => {
    if (item.itemType === 'order') {
      // 只在第一笔运费时添加完整信息
      if (item.freightCostIndex === 0) {
        const row = [
          getDisplayIndex(index),
          formatDate(item.completed_date),
          item.order_client || '-',
          getGoodsName(item),
          getTotalWeight(item),
          item.receiver_address || '-',
          getChannelName(item),
          getLogisticsNumber(item),
          getFreightAmountForRow(item),
          getPaidAmount(item),
          `¥ ${calculateBalance(index).toFixed(2)}`,
          hasReceipt(item) ? '✓' : '',
          item.remark || ''
        ]
        exportRows.push(row)
      } else {
        // 多笔运费的后续行，只显示运费相关列
        const row = [
          '', '', '', '', '', '',
          getChannelName(item),
          getLogisticsNumber(item),
          getFreightAmountForRow(item),
          getPaidAmount(item),
          '',
          hasReceipt(item) ? '✓' : '',
          item.remark || ''
        ]
        exportRows.push(row)
      }
    } else if (item.itemType === 'fund') {
      // 备用金行
      const row = [
        getDisplayIndex(index),
        formatDate(item.date),
        '备用金转入' + (item.note ? `（${item.note}）` : ''),
        '', '', '', '', '',
        '',
        item.amount >= 0 ? '+ ' + item.amount.toFixed(2) : item.amount.toFixed(2),
        `¥ ${calculateBalance(index).toFixed(2)}`,
        '',
        ''
      ]
      exportRows.push(row)
    }
  })

  // 添加空行和汇总
  exportRows.push([])
  const summaryRow = ['合计', '', '', '', '', '', '', '',
    `¥ ${totalFreight.toFixed(2)}`, '',
    `备用金: ¥ ${finalBalance.toFixed(2)}`, '', '']
  exportRows.push(summaryRow)

  // 导出配置
  exportToExcel({
    filename: `物流对账_${periodText}`,
    sheetName: '运费记录',
    data: exportRows,
    colWidths: [
      { wch: 6 },  // 序号
      { wch: 12 }, // 日期
      { wch: 15 }, // 客户
      { wch: 15 }, // 货物信息
      { wch: 12 }, // 数量
      { wch: 30 }, // 收货地址
      { wch: 12 }, // 渠道
      { wch: 15 }, // 车牌号/单号
      { wch: 12 }, // 价格
      { wch: 12 }, // 已支付
      { wch: 15 }, // 备用金合计
      { wch: 10 }, // 回单回传
      { wch: 20 }  // 备注
    ],
    rowHeights: [
      { hpt: 30 } // 标题行高度
    ],
    merges: [
      { s: { r: 0, c: 0 }, e: { r: 0, c: 12 } } // 合并标题行
    ],
    styles: {
      titleRow: 0,
      headerRow: 4,
      dataRowStart: dataStartRow,
      summaryRow: exportRows.length - 1,
      titleStyle: TITLE_STYLE,
      headerStyle: HEADER_STYLE,
      dataStyle: DATA_STYLE,
      summaryStyle: SUMMARY_STYLE
    }
  })
}
