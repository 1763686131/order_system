import assert from 'node:assert/strict'
import test from 'node:test'
import XLSX from 'xlsx-js-style'
import * as Reader from 'xlsx'
import {
  DATA_STYLE,
  TITLE_STYLE,
  exportFreightRecords,
  exportToExcel
} from './excelExport.js'

function captureExport(options, exporter = exportToExcel) {
  const writeFile = XLSX.writeFile
  let captured
  XLSX.writeFile = (workbook, filename, writeOptions) => {
    const bytes = XLSX.write(workbook, { ...writeOptions, type: 'buffer' })
    captured = {
      workbook,
      filename,
      saved: Reader.read(bytes, { type: 'buffer', cellStyles: true, bookFiles: true })
    }
  }
  try {
    exporter(options)
  } finally {
    XLSX.writeFile = writeFile
  }
  assert.ok(captured, 'the export must write a workbook')
  return captured
}

test('plain exports preserve values, column widths, row heights and merges', () => {
  const { filename, saved } = captureExport({
    filename: 'records',
    data: [['Title'], ['Code', 'Amount'], ['0000123', 0]],
    merges: [{ s: { r: 0, c: 0 }, e: { r: 0, c: 1 } }],
    colWidths: [{ wch: 22 }, { wch: 14 }],
    rowHeights: [{ hpt: 36 }]
  })
  const sheet = saved.Sheets.Sheet1
  assert.equal(filename, 'records.xlsx')
  assert.equal(sheet.A3.t, 's')
  assert.equal(sheet.A3.v, '0000123')
  assert.equal(sheet.B3.t, 'n')
  assert.equal(sheet.B3.v, 0)
  assert.equal(sheet['!cols'][0].wch, 22)
  assert.equal(sheet['!rows'][0].hpt, 36)
  assert.equal(sheet['!merges'][0].e.c, 1)
})

test('default styles cover blank cells and merged title edges through the last row', () => {
  const { workbook, saved } = captureExport({
    data: [['Title'], ['Code', 'Amount'], ['0001', 1], ['0002']],
    merges: [{ s: { r: 0, c: 0 }, e: { r: 0, c: 1 } }],
    styles: {
      defaultStyle: {
        ...DATA_STYLE,
        alignment: { ...DATA_STYLE.alignment, wrapText: true }
      },
      titleRow: 0,
      titleStyle: TITLE_STYLE,
      headerRow: 1,
      headerStyle: { font: { bold: true } }
    }
  })
  const sheet = workbook.Sheets.Sheet1
  for (const address of ['A1', 'B1', 'A2', 'B2', 'A3', 'B3', 'A4', 'B4']) {
    assert.equal(sheet[address].s.alignment.horizontal, 'center')
    assert.equal(sheet[address].s.alignment.vertical, 'center')
    assert.equal(sheet[address].s.alignment.wrapText, true)
    for (const edge of ['top', 'bottom', 'left', 'right']) {
      assert.equal(sheet[address].s.border[edge].style, 'thin')
    }
  }
  assert.equal(sheet.A1.s.font.sz, 16)
  assert.equal(sheet.A2.s.font.bold, true)
  assert.equal(sheet.A2.s.font.name, DATA_STYLE.font.name)
  assert.equal(sheet.B1.v, '')
  assert.equal(sheet.B4.v, '')
  const stylesXml = String(saved.files['xl/styles.xml'].content)
  assert.match(stylesXml, /horizontal="center"/)
  assert.match(stylesXml, /vertical="center"/)
  assert.match(stylesXml, /wrapText="true"/)
  assert.match(stylesXml, /style="thin"/)
  assert.match(stylesXml, /<sz val="16"/)
})

test('data row styles include the final row without requiring a summary', () => {
  const { workbook } = captureExport({
    data: [['Amount'], [1], [2]],
    styles: { dataRowStart: 1, dataStyle: DATA_STYLE }
  })
  assert.equal(workbook.Sheets.Sheet1.A2.s.border.top.style, 'thin')
  assert.equal(workbook.Sheets.Sheet1.A3.s.border.top.style, 'thin')
})

test('summary row styles take precedence over data styles and inherit alignment', () => {
  const { workbook } = captureExport({
    data: [['Amount'], [1], [1]],
    styles: {
      defaultStyle: DATA_STYLE,
      dataRowStart: 1,
      dataStyle: { font: { bold: false } },
      summaryRow: 2,
      summaryStyle: { font: { bold: true } }
    }
  })
  const sheet = workbook.Sheets.Sheet1
  assert.equal(sheet.A2.s.font.bold, false)
  assert.equal(sheet.A3.s.font.bold, true)
  assert.equal(sheet.A3.s.alignment.horizontal, 'center')
})

test('empty exports with styles do not decode a missing worksheet range', () => {
  assert.doesNotThrow(() => captureExport({
    data: [],
    styles: { defaultStyle: DATA_STYLE }
  }))
})

test('freight exports remain compatible with the styled writer', () => {
  const { filename, saved } = captureExport({
    periodText: '2026-10-14',
    mergedData: [],
    totalFreight: 0,
    finalBalance: 0
  }, exportFreightRecords)
  assert.ok(filename.endsWith('2026-10-14.xlsx'))
  const sheet = saved.Sheets[saved.SheetNames[0]]
  assert.equal(sheet['!merges'][0].e.c, 12)
  assert.equal(sheet['!rows'][0].hpt, 30)
  assert.equal(saved.Styles.Fonts.some(font => font.sz === 16 && font.bold), true)
})
