import { h, render } from 'vue'
import TableColumnOrderDialog from '../components/common/TableColumnOrderDialog.vue'
import { createResizableColumns } from './resizableColumns.js'
import { createTableColumnLayout } from '../utils/tableColumnLayout.js'

const instances = new WeakMap()

function createTableLayout(table, binding) {
  let value = binding.value
  let host = null
  let dialog = null
  let dialogVisible = false
  const appContext = binding.instance?.$?.appContext
  const resize = createResizableColumns(table, false)

  const renderDialog = () => {
    const vnode = h(TableColumnOrderDialog, {
      visible: dialogVisible,
      columns: dialog.columns,
      defaultColumns: dialog.defaultColumns,
      hiddenKeys: dialog.hiddenKeys,
      'onUpdate:visible': visible => {
        dialogVisible = visible
        renderDialog()
      },
      onApply: (keys, hiddenKeys) => {
        dialog.apply(keys, hiddenKeys)
        dialogVisible = false
        renderDialog()
      }
    })
    vnode.appContext = appContext
    render(vnode, host)
  }

  const prepareUpdate = () => {
    resize.suspend()
    order.restore()
  }

  const sync = nextValue => {
    value = nextValue
    order.sync(value)
    resize.sync(value)
  }

  const order = createTableColumnLayout(table, {
    openDialog: next => {
      dialog = next
      dialogVisible = true
      if (!host) {
        host = table.ownerDocument.createElement('div')
        host.className = 'table-layout-dialog-host'
        table.ownerDocument.body.appendChild(host)
      }
      renderDialog()
    },
    onChange: ({ keys, hiddenKeys }) => {
      prepareUpdate()
      sync(value)
      value?.onReorder?.({ keys, hiddenKeys })
    }
  })

  sync(value)
  return {
    prepareUpdate,
    sync(nextValue) {
      if (dialogVisible) {
        dialogVisible = false
        renderDialog()
      }
      sync(nextValue)
    },
    destroy() {
      resize.destroy()
      order.destroy()
      if (host) {
        render(null, host)
        host.remove()
      }
    }
  }
}

export default {
  mounted(table, binding) {
    instances.set(table, createTableLayout(table, binding))
  },
  beforeUpdate(table) {
    // Vue must always patch the original child order, including v-for fragment anchors.
    instances.get(table)?.prepareUpdate()
  },
  updated(table, binding) {
    instances.get(table)?.sync(binding.value)
  },
  beforeUnmount(table) {
    instances.get(table)?.destroy()
    instances.delete(table)
  }
}
