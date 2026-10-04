"""Build a deterministic computational ZIP from explicitly listed repository files."""
from pathlib import Path
import json,hashlib,zipfile,subprocess,sys,tempfile,re
from urllib.parse import urlsplit,unquote
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/downloads'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,o):p.write_text(json.dumps(o,indent=2)+'\n',encoding='utf-8')
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 paths=read(ROOT/'experiments/checkout-files.json')['paths']; data={}
 for p in paths:
  source=(ROOT/p).resolve()
  if not source.is_relative_to(ROOT.resolve()) or not source.is_file():raise ValueError('Invalid source: '+p)
  data[p]=source.read_bytes()
 readme=data['README.md'].decode('utf-8-sig')
 references=[]
 for match in re.finditer(r'''(?:src=["']([^"']+)["']|!\[[^\]]*\]\(([^)]+)\))''',readme):
  value=match.group(1) or match.group(2)
  parsed=urlsplit(value)
  if parsed.scheme or parsed.netloc or not parsed.path:continue
  resource=unquote(parsed.path)
  if resource not in data:raise ValueError('README resource is absent from the explicit archive list: '+resource)
  references.append(resource)
 readme_refresh={'documentationOnly':True,'computationalRecipeRelease':'reproduction-2026-10-04-r14','preservedComputationalCommands':41,'preservedRecoveredRecords':44,'readme':'README.md','imagePositions':len(references),'uniqueLocalImages':len(set(references)),'allReadmeImagesIncluded':True,'exporter':'tools/build_readme_from_homepage.py','scope':'README and reproduction navigation are synchronized with the homepage. The reader catalog uses one evidence-backed status and a static fallback; all prior archive members and figure sources are retained. Computational recipes, pinned code, numeric receipts, and their r14 immutable links are unchanged.'}
 arc=OUT/'computational-checkout.zip'
 with zipfile.ZipFile(arc,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p,b in sorted(data.items()):
   info=zipfile.ZipInfo(p,date_time=(2026,10,4,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
   z.writestr(info,b,compresslevel=9)
 manifest={'schema':'mcl_public_computational_archive_v1','releaseId':'20261004-r18.1','sourceRevision':'reproduction-2026-10-04-r18.1','documentationRefresh':readme_refresh,'archive':arc.name,'sha256':sha(arc.read_bytes()),'bytes':arc.stat().st_size,'files':[{'path':p,'source':p,'sha256':sha(b),'bytes':len(b)} for p,b in sorted(data.items())]}
 write(OUT/'computational-checkout.manifest.json',manifest)
 with tempfile.TemporaryDirectory(prefix='mcl-release-') as td:
  target=Path(td)/'checkout';target.mkdir()
  with zipfile.ZipFile(arc) as z:
   assert z.testzip() is None
   assert set(z.namelist())==set(data)
   for m in manifest['files']:
    assert sha(z.read(m['path']))==m['sha256']
    assert (target/m['path']).resolve().is_relative_to(target.resolve())
   z.extractall(target)
  r=subprocess.run([sys.executable,'-B',str(target/'tools/mcl_reproduction_check.py')],cwd=target,capture_output=True,text=True,check=True)
  check=json.loads(r.stdout);assert check['status']=='PASS'
  output=Path(td)/'query-run'
  for action in ('run','verify'):
   command=[sys.executable,'-B',str(target/'tools/mcl_recovered.py'),action,'TOOL-CITY-EVIDENCE-QUERY','--run' if action=='verify' else '--output',str(output)]
   execution=subprocess.run(command,cwd=target,capture_output=True,text=True,check=True,timeout=180)
  smoke=read(output/'verification.json');assert smoke['success']
  smoke.update({'record':'TOOL-CITY-EVIDENCE-QUERY','source':'freshly extracted public archive','execution':'fresh query followed by independent CSV verification through the common CLI','runReceiptExitCode':read(output/'entry-run.json')['exit_code'],'verifyReceiptExitCode':read(output/'entry-verify.json')['exit_code'],'python':sys.version.split()[0]})
 note={'issue':'Boston native returned-point checker expected the unshipped complete historical driver hash 0a054ab078d46a8b74fa257336a65275564c38cc3e60e5c4d8cb9c412a87a22a.','correction':'Require the already-public AST-isolated mathematical builder, the same artifact required by the controller and actually executed in the archived rank-26/rank-52 receipt.','shippedSource':'algorithms/path_compression/diagnostic_l3/source/build_alm_model_levels.py','actualSha256':sha((ROOT/'algorithms/path_compression/diagnostic_l3/source/build_alm_model_levels.py').read_bytes()),'receipt':'experiments/verification/boston-native-l3-ranks26-52.json','numericalEquationChange':False}
 report={'schema':'mcl_publication_validation_v1','status':'PASS','releaseId':'20261004-r18.1','sourceRevision':manifest['sourceRevision'],'archive':manifest['archive'],'archiveSha256':manifest['sha256'],'archiveBytes':manifest['bytes'],'members':len(data),'documentationRefresh':readme_refresh,'safeExtraction':True,'everyMemberMatchesPublicRepositorySource':True,'checkoutIntegrity':check,'nativeSourceIdentityCorrection':note,'publicationSmoke':'docs/reproduction/publication-smoke.json','recoveredValidation':'docs/reproduction/recovered-validation.json','extractedArchiveSmoke':smoke,'scope':'Integrity validation of every exact public download member, including the original 41 commands and all supplemental recovered entries, plus a fresh public-table query and independent verification from the extracted ZIP. Other lightweight city runs and historical inspections are recorded separately; this packaging check does not rerun every solver or certify complete raw-source city pipelines.'}
 write(ROOT/'docs/reproduction/publication-validation.json',report)
 write(OUT/'downloads.json',{'schema':'mcl_public_computational_downloads_v1','releaseId':'20261004-r18.1','sourceRevision':manifest['sourceRevision'],'combined':{'filename':arc.name,'bytes':manifest['bytes'],'sha256':manifest['sha256'],'files':len(data),'manifest':'computational-checkout.manifest.json'}})
 print(json.dumps({'status':'PASS','members':len(data),'readmeImages':len(set(references)),'archiveBytes':manifest['bytes'],'sha256':manifest['sha256'],'commands':check['commands_checked'],'pinnedFiles':check['unique_files_checked'],'recoveredRecords':check.get('recovered_records_checked'),'extractedArchiveSmoke':smoke['success']},indent=2))
if __name__=='__main__':main()
