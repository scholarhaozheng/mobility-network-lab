"""Prepare the reviewed computational material for the public repository."""
from pathlib import Path
import json,re,hashlib,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
REPO='https://github.com/scholarhaozheng/mobility-network-lab'
PUBLIC_REF='reproduction-2026-10-04-r12'
RAW='https://raw.githubusercontent.com/scholarhaozheng/mobility-network-lab/'+PUBLIC_REF+'/'
RELEASE='20261004-r12'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,o):p.write_text(json.dumps(o,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def convert(v):
 if isinstance(v,dict):return {k:convert(x) for k,x in v.items()}
 if isinstance(v,list):return [convert(x) for x in v]
 if not isinstance(v,str):return v
 v=v.replace('/reading/stage4/20261004-r05/site/','').replace('/reading/stage4/20261004-r05/','reproduction/')
 v=v.replace('Public GitHub main does not yet contain these additions.','The registered command and exact inputs are included in this repository release.')
 v=v.replace('in the local review package','in the computational checkout').replace('in the local r05 review bundle','in this computational checkout')
 v=v.replace('The immediate GMNS provider revision and applicable redistribution terms for this converted snapshot must be confirmed before external publication. This does not prevent the verified local frozen-input computation.','The exact immediate GMNS provider revision is not recovered. These are frozen derived benchmark inputs with academic-research use and source attribution retained; see DATA_LICENSES.md and the fixture PROVENANCE.json. Raw-source reconstruction is not certified.')
 return v
inv=convert(read(ROOT/'experiments/inventory.json'))
for e in inv['experiments']:
 if e.get('publicationReviewRequirements'):
  e['publicationReviewRequirements']=['The immediate GMNS provider revision is not recovered. The exact derived input bytes are fixed; academic-research use and upstream attribution are retained in DATA_LICENSES.md and examples/sioux-falls/finite-time-r05/PROVENANCE.json. Raw-source reconstruction is not certified.']
write(ROOT/'experiments/inventory.json',inv)
cat=read(ROOT/'experiments/catalog.json')
cat['data_acquisition']='The computational ZIP or current repository checkout contains every registered frozen input and its SHA-256. Each recipe verifies file identities before execution. Frozen historical per-entry URLs and catalog identities are retained for receipt compatibility; experiments/publication.json adds current acquisition links. Raw-source acquisition is separate. The tap-b helper downloads a hash-pinned upstream source archive only when explicitly invoked.'
cat['publication_manifest']='experiments/publication.json'
write(ROOT/'experiments/catalog.json',cat)
ledger=convert(read(ROOT/'experiments/reproduction-status.json'))
ledger.update(schema='mcl_reproduction_status_v1',releaseVersion=RELEASE,published=True,publicationRef=PUBLIC_REF,publicationRefKind='immutable release tag; numerical file hashes additionally pin content')
for e in ledger['records']:
 e['portalUrl']='reproduce.html#'+e['id']
 if e.get('verifiedCommandId'):e['receiptUrl']='assets/reproduction/verification/'+e['verifiedCommandId']+'.json'
 if e.get('availability'):
  e['availability']['registeredCommandPublished']=bool(e.get('verifiedCommandId'))
  e['availability']['reviewOverlayReady']=False
  e['availability']['repositoryCheckoutReady']=True
  e['availability']['dataAcquisition']='Download the computational checkout or clone the repository; exact registered inputs and source hashes are pinned in experiments/catalog.json. Original upstream acquisition is separate.'
 for f in e.get('data',[]):
  p=f.get('path')
  if p and (ROOT/p).is_file():
   f['downloadUrl']=RAW+p;f['includedInRepository']=True
  f.pop('includedInReviewOverlay',None)
write(ROOT/'experiments/reproduction-status.json',ledger)
write(ROOT/'docs/assets/reproduction/reproduction-status.json',ledger)
# Preserve per-command catalog dictionaries and their receipt identities.
files={}
rt=read(ROOT/'experiments/runtime-setup.json')
for e in cat['experiments']:
 for f in e['files']+rt.get('entries',{}).get(e['id'],{}).get('files',[]):
  p=f['path'];files[p]={'path':p,'sha256':f['sha256'],'downloadUrl':RAW+p,'browseUrl':REPO+'/blob/'+PUBLIC_REF+'/'+p}
write(ROOT/'experiments/publication.json',{'schema':'mcl_computational_publication_v1','releaseId':RELEASE,'baseline':cat['baseline_commit'],'repository':REPO,'repositoryRef':PUBLIC_REF,'refScope':'The release tag fixes this repository snapshot. Verify the SHA-256 identities below and record git rev-parse HEAD for the resolved commit.','verifiedCommands':len(cat['experiments']),'verifiedRecords':ledger['verifiedRecords'],'recordCount':ledger['recordCount'],'files':list(files.values()),'archiveManifest':'docs/downloads/computational-checkout.manifest.json'})
