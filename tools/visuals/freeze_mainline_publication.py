"""Record this local presentation increment without modifying old receipts."""
from pathlib import Path
import json
from freeze_hk10_publication import build_record
from check_hk10_publication import CURRENT_RECEIPT,RECEIPT,LOCAL_INSTRUCTION,sha,validate

def main():
    root=Path(__file__).resolve().parents[2]
    record=build_record(root)
    record['publication_instruction']=LOCAL_INSTRUCTION
    record['previous_presentation_receipt_sha256']=sha(root/RECEIPT)
    record['remote_write_authorized']=False
    record['change_scope']='Local Ann Arbor ChoiceFW, Chicago ADMM116 and old Urbana T4 update. Six other city articles, 19-row comparison and historical HK evidence retained.'
    (root/CURRENT_RECEIPT).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    result=validate(root)
    print(json.dumps({'status':result['status'],'checks':result['checks'],'errors':result['errors']}))
    return bool(result['errors'])
if __name__=='__main__':raise SystemExit(main())
