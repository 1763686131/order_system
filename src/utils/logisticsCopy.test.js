import assert from 'node:assert/strict'
import test from 'node:test'
import {
  formatLogisticsOrderForCopy,
  LOGISTICS_COPY_EDITOR_KEY
} from './logisticsCopy.js'

const fieldsFor = template => [{
  key: LOGISTICS_COPY_EDITOR_KEY,
  name: '复制内容',
  template,
  enabled: true
}]

const order = {
  order_goods: [
    { goods_name: 'A1商品', spec: 'B1规格', quantity: 'C1数量', unit: '袋' },
    { goods_name: 'A2商品', spec: 'B2规格', quantity: 'C2数量', unit: '组' }
  ]
}

test('first goods name does not include its specification', () => {
  assert.equal(
    formatLogisticsOrderForCopy(order, {
      fields: fieldsFor('@goodsName / @spec / @unit')
    }),
    'A1商品 / B1规格 / 袋'
  )
})

test('row separators align goods, specs and quantities by item', () => {
  const template = '商品明细：\n@allGoods | @allSpecs | @allQuantity\n结束'
  assert.equal(
    formatLogisticsOrderForCopy(order, { fields: fieldsFor(template) }),
    '商品明细：\nA1商品  B1规格  C1数量\nA2商品  B2规格  C2数量\n结束'
  )
})

test('all units align with each item even when their units differ', () => {
  assert.equal(
    formatLogisticsOrderForCopy(order, {
      fields: fieldsFor('@allGoods | @allSpecs | @allQuantity | @allUnits')
    }),
    'A1商品  B1规格  C1数量  袋\nA2商品  B2规格  C2数量  组'
  )
})

test('templates without row separators keep aggregated variables', () => {
  assert.equal(
    formatLogisticsOrderForCopy(order, {
      fields: fieldsFor('@allGoods @allSpecs @allQuantity @allUnits')
    }),
    'A1商品、A2商品 B1规格、B2规格 C1数量、C2数量 袋、组'
  )
})

test('missing specs keep other values aligned with their item', () => {
  const missingSpec = {
    order_goods: [
      { goods_name: 'A1商品', quantity: 1 },
      { goods_name: 'A2商品', spec: 'B2规格', quantity: 2 }
    ]
  }
  assert.equal(
    formatLogisticsOrderForCopy(missingSpec, {
      fields: fieldsFor('@allGoods | @allSpecs | @allQuantity')
    }),
    'A1商品    1\nA2商品  B2规格  2'
  )
})

test('row layout falls back to aggregated values without item details', () => {
  assert.equal(
    formatLogisticsOrderForCopy(
      { goods_name: '单件商品', goods_spec: '单件规格', goods_quantity: 3 },
      { fields: fieldsFor('@allGoods | @allSpecs | @allQuantity') }
    ),
    '单件商品  单件规格  3'
  )
})

test('joiner appends ASCII text to variables without extending their names', () => {
  const withWeight = { goods_weight: 50, receiver_name: '张三' }
  assert.equal(
    formatLogisticsOrderForCopy(withWeight, {
      fields: fieldsFor('重量：@goodsWeight～kg / @receiverName ～ 先生 / {goodsWeight}～kg')
    }),
    '重量：50kg / 张三先生 / 50kg'
  )
})

test('joiner works inside per-item rows', () => {
  assert.equal(
    formatLogisticsOrderForCopy(order, {
      fields: fieldsFor('@allGoods | @allSpecs | @allQuantity～kg')
    }),
    'A1商品  B1规格  C1数量kg\nA2商品  B2规格  C2数量kg'
  )
})

test('wave symbols in ordinary text remain visible', () => {
  assert.equal(
    formatLogisticsOrderForCopy({}, { fields: fieldsFor('型号：A～B') }),
    '型号：A～B'
  )
})
