/**
 * Excel 导出工具
 * 基于 xlsx-js-style 封装数据和单元格样式导出
 */

import XLSX from 'xlsx-js-style'

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
    applyStylesToWorksheet(ws, styles)
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
 * @param {Object} styles - 样式配置
 */
function applyStylesToWorksheet(ws, styles) {
  if (!ws['!ref']) return

  const range = XLSX.utils.decode_range(ws['!ref'])
  const defaultStyle = styles.defaultStyle || {}
  const hasDefaultStyle = Object.keys(defaultStyle).length > 0

  for (let R = range.s.r; R <= range.e.r; ++R) {
    const rowStyle = getStyleForRow(R, styles)
    if (!rowStyle && !hasDefaultStyle) continue

    const style = {
      ...defaultStyle,
      ...rowStyle,
      font: { ...defaultStyle.font, ...rowStyle?.font },
      alignment: { ...defaultStyle.alignment, ...rowStyle?.alignment },
      border: { ...defaultStyle.border, ...rowStyle?.border }
    }
    for (let C = range.s.c; C <= range.e.c; ++C) {
      const cellAddress = XLSX.utils.encode_cell({ r: R, c: C })
      // 合并区域和空白格也需要实体单元格，才能保存完整的外边框。
      if (!ws[cellAddress]) ws[cellAddress] = { t: 's', v: '' }
      ws[cellAddress].s = style
    }
  }
}

/**
 * 获取指定行的样式
 * @param {number} rowIndex - 行索引
 * @param {Object} styles - 样式配置对象
 * @returns {Object|null}
 */
function getStyleForRow(rowIndex, styles) {
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
  } else if (dataRowStart !== null && rowIndex >= dataRowStart) {
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
