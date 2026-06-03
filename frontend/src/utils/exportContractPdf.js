const PDF_EXPORT_STYLE_ID = 'contract-pdf-export-styles'
const IMAGE_LOAD_TIMEOUT_MS = 8000

function ensurePdfExportStyles() {
  if (document.getElementById(PDF_EXPORT_STYLE_ID)) return
  const style = document.createElement('style')
  style.id = PDF_EXPORT_STYLE_ID
  style.textContent = `
    body.contract-pdf-exporting .contract-actions {
      display: none !important;
    }
    body.contract-pdf-exporting .page-header,
    body.contract-pdf-exporting .el-alert {
      visibility: hidden !important;
      height: 0 !important;
      margin: 0 !important;
      padding: 0 !important;
      overflow: hidden !important;
    }
    body.contract-pdf-exporting .el-card {
      border: none !important;
      box-shadow: none !important;
    }
    body.contract-pdf-exporting .el-card__body {
      padding: 0 !important;
    }
    body.contract-pdf-exporting .contract-document {
      box-shadow: none !important;
      max-width: 860px !important;
      width: 100% !important;
      margin: 0 auto !important;
      padding: 24px 36px 32px !important;
      background: #fff !important;
    }
    body.contract-pdf-exporting .signature-image {
      max-width: 100% !important;
      max-height: 100px !important;
      object-fit: contain !important;
      display: block !important;
    }
    body.contract-pdf-exporting .signature-area {
      min-height: 100px !important;
      height: auto !important;
    }
  `
  document.head.appendChild(style)
}

function waitForLayout() {
  return new Promise((resolve) => {
    requestAnimationFrame(() => requestAnimationFrame(resolve))
  })
}

/** 等待合同内所有图片（含 base64 签名）加载完成 */
function waitForImages(root) {
  const imgs = [...root.querySelectorAll('img')]
  if (imgs.length === 0) return Promise.resolve()

  return Promise.all(
    imgs.map(
      (img) =>
        new Promise((resolve) => {
          if (img.complete && img.naturalWidth > 0) {
            resolve()
            return
          }
          const done = () => resolve()
          img.addEventListener('load', done, { once: true })
          img.addEventListener('error', done, { once: true })
          setTimeout(done, IMAGE_LOAD_TIMEOUT_MS)
          if (img.src && !img.complete) {
            const current = img.src
            img.src = ''
            img.src = current
          }
        })
    )
  )
}

/**
 * 将合同正文 DOM 导出为 PDF（与详情页所见一致）
 * @param {HTMLElement} sourceElement - ContractDocument 根节点（页面中已渲染）
 * @param {{ filename?: string }} options
 */
export async function exportContractPdf(sourceElement, options = {}) {
  if (!sourceElement) {
    throw new Error('合同内容未加载')
  }

  ensurePdfExportStyles()
  const filename = options.filename || '房屋租赁合同.pdf'

  sourceElement.scrollIntoView({ block: 'start', behavior: 'instant' })
  window.scrollTo(0, 0)
  await waitForImages(sourceElement)
  await waitForLayout()

  document.body.classList.add('contract-pdf-exporting')

  try {
    await waitForLayout()

    const { default: html2canvas } = await import('html2canvas')
    const { jsPDF } = await import('jspdf')

    const canvas = await html2canvas(sourceElement, {
      scale: 2,
      useCORS: true,
      allowTaint: true,
      backgroundColor: '#ffffff',
      logging: false,
      scrollX: 0,
      scrollY: -window.scrollY,
      windowWidth: document.documentElement.clientWidth,
      windowHeight: document.documentElement.clientHeight,
      onclone: (clonedDoc) => {
        clonedDoc.querySelectorAll('.contract-actions').forEach((el) => el.remove())
        const doc = clonedDoc.querySelector('.contract-document')
        if (doc) {
          doc.style.boxShadow = 'none'
          doc.style.maxWidth = '860px'
          doc.style.width = '100%'
          doc.style.background = '#fff'
        }
      },
    })

    const marginMm = 12
    const pdf = new jsPDF({ unit: 'mm', format: 'a4', orientation: 'portrait' })
    const pageWidth = pdf.internal.pageSize.getWidth()
    const pageHeight = pdf.internal.pageSize.getHeight()
    const contentWidth = pageWidth - marginMm * 2
    const contentHeight = pageHeight - marginMm * 2

    const imgData = canvas.toDataURL('image/jpeg', 0.92)
    const imgWidth = contentWidth
    const imgHeight = (canvas.height * imgWidth) / canvas.width

    let heightLeft = imgHeight
    let position = marginMm

    pdf.addImage(imgData, 'JPEG', marginMm, position, imgWidth, imgHeight)
    heightLeft -= contentHeight

    while (heightLeft > 0) {
      pdf.addPage()
      position = heightLeft - imgHeight + marginMm
      pdf.addImage(imgData, 'JPEG', marginMm, position, imgWidth, imgHeight)
      heightLeft -= contentHeight
    }

    pdf.save(filename)
  } finally {
    document.body.classList.remove('contract-pdf-exporting')
  }
}

export function buildContractPdfFilename(contract) {
  const no = contract?.contract_no || contract?.id || 'unknown'
  return `房屋租赁合同_${no}.pdf`
}
