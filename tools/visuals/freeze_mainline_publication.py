"""Record this local presentation increment without modifying old receipts."""
from pathlib import Path
import json
from freeze_hk10_publication import build_record
from check_hk10_publication import CURRENT_RECEIPT,RECEIPT,CURRENT_INSTRUCTION,sha,validate

def main():
    root=Path(__file__).resolve().parents[2]
    record=build_record(root)
    record['publication_instruction']=CURRENT_INSTRUCTION
    record['previous_presentation_receipt_sha256']=sha(root/RECEIPT)
    record['remote_write_authorized']=True
    record['original_quality_instruction']={'date':'2026-10-09','instruction_original':'再做一个版本，图片清晰度不要降低，其他操作可以去做，例如固定图片占位、异步解码，减少滚动重算和页面跳动。然后再统计一下本地模拟较慢电脑的结果','scope':'Retain original image quality and bytes; optimize loading/layout and measure locally; no remote publication requested'}
    record['performance_instruction']={'date':'2026-10-09','instruction_original':'你看看本地的最新提交，然后看看怎么处理和修改一下比较好。网页加载的问题。另外，现在README的排版没有跟上我们网页版的最新排版和格式，麻烦同步一下。','scope':'Local loading and scroll-performance fixes and README synchronization; no remote publication requested'}
    record['change_scope']='Local browser-performance and README synchronization update on top of the released 20261009 edition. Original SVG/PNG/JPEG assets render directly with stable aspect ratios, asynchronous decoding and preloaded original fonts; original scientific assets, figure links, captions, city/method coverage and historical HK evidence are retained. Remote publication is authorized by the maintainer instruction recorded above.'
    (root/CURRENT_RECEIPT).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    result=validate(root)
    print(json.dumps({'status':result['status'],'checks':result['checks'],'errors':result['errors']}))
    return bool(result['errors'])
if __name__=='__main__':raise SystemExit(main())
