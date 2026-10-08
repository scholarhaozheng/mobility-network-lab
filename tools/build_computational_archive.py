"""Build a deterministic computational ZIP from explicitly listed repository files."""
from pathlib import Path
from datetime import datetime
from html import unescape
import json,hashlib,zipfile,subprocess,sys,tempfile,re
from urllib.parse import urlsplit,unquote
from check_computational_archive import safe_member
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/downloads'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,o):p.write_text(json.dumps(o,indent=2)+'\n',encoding='utf-8')
def sha(b):return hashlib.sha256(b).hexdigest()
def readme_resources(readme):
 """Read HTML sources and plain or angle-bracket Markdown image destinations."""
 references=[]
 pattern=r'''(?:<img\b[^>]*?\bsrc=["']([^"']+)["']|!\[[^\]]*\]\(\s*(?:<([^>\n]+)>|([^\s)]+)))'''
 for match in re.finditer(pattern,readme,re.IGNORECASE):
  value=unescape(next(group for group in match.groups() if group is not None))
  parsed=urlsplit(value)
  if parsed.scheme or parsed.netloc or not parsed.path:continue
  references.append(unquote(parsed.path))
 return references

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 checkout=read(ROOT/'experiments/checkout-files.json')
 release_id=checkout['releaseId']
 if not re.fullmatch(r'\d{8}-r\d+',release_id):raise ValueError('Invalid checkout release ID: '+release_id)
 release_date=datetime.strptime(release_id[:8],'%Y%m%d')
 source_revision='reproduction-'+release_date.strftime('%Y-%m-%d')+release_id[8:]
 archive_date=(release_date.year,release_date.month,release_date.day,0,0,0)
 paths=checkout['paths']; data={}
 if len(paths)!=len(set(p.casefold() for p in paths)):raise ValueError('Duplicate archive paths')
 for p in paths:
  source=(ROOT/p).resolve()
  if not safe_member(p) or (ROOT/p).is_symlink() or not source.is_relative_to(ROOT.resolve()) or not source.is_file():raise ValueError('Invalid source: '+p)
  if source.stat().st_size>=100*1024*1024:raise ValueError('Archive source exceeds size limit: '+p)
  data[p]=source.read_bytes()
 readme=data['README.md'].decode('utf-8-sig')
 references=readme_resources(readme)
 for resource in references:
  if resource not in data:raise ValueError('README resource is absent from the explicit archive list: '+resource)
 if sum(map(len,data.values()))>512*1024*1024:raise ValueError('Archive expanded size exceeds 512 MiB')
 readme_refresh={'documentationOnly':True,'computationalRecipeRelease':'reproduction-2026-10-04-r14','preservedComputationalCommands':41,'preservedRecoveredRecords':44,'readme':'README.md','imagePositions':len(references),'uniqueLocalImages':len(set(references)),'allReadmeImagesIncluded':True,'exporter':'tools/build_readme_from_homepage.py','scope':checkout['documentationRefreshScope']}
 arc=OUT/'computational-checkout.zip'
 with zipfile.ZipFile(arc,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p,b in sorted(data.items()):
   info=zipfile.ZipInfo(p,date_time=archive_date);info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
   z.writestr(info,b,compresslevel=9)
 if arc.stat().st_size>=100*1024*1024:raise ValueError('Computational archive exceeds the 100 MiB limit')
 manifest={'schema':'mcl_public_computational_archive_v1','releaseId':release_id,'sourceRevision':source_revision,'documentationRefresh':readme_refresh,'archive':arc.name,'sha256':sha(arc.read_bytes()),'bytes':arc.stat().st_size,'files':[{'path':p,'source':p,'sha256':sha(b),'bytes':len(b)} for p,b in sorted(data.items())]}
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
  assert (check['commands_checked'],check['unique_files_checked'],check['recovered_records_checked'])==(41,200,44)
  output=Path(td)/'query-run'
  for action in ('run','verify'):
   command=[sys.executable,'-B',str(target/'tools/mcl_recovered.py'),action,'TOOL-CITY-EVIDENCE-QUERY','--run' if action=='verify' else '--output',str(output)]
   execution=subprocess.run(command,cwd=target,capture_output=True,text=True,check=True,timeout=180)
  smoke=read(output/'verification.json');assert smoke['success'] and smoke['optimizer_calls']==0
  smoke.update({'record':'TOOL-CITY-EVIDENCE-QUERY','source':'freshly extracted public archive','execution':'fresh query followed by independent CSV verification through the common CLI','runReceiptExitCode':read(output/'entry-run.json')['exit_code'],'verifyReceiptExitCode':read(output/'entry-verify.json')['exit_code'],'python':sys.version.split()[0]})
 note={'issue':'Boston native returned-point checker expected the unshipped complete historical driver hash 0a054ab078d46a8b74fa257336a65275564c38cc3e60e5c4d8cb9c412a87a22a.','correction':'Require the already-public AST-isolated mathematical builder, the same artifact required by the controller and actually executed in the archived rank-26/rank-52 receipt.','shippedSource':'algorithms/path_compression/diagnostic_l3/source/build_alm_model_levels.py','actualSha256':sha((ROOT/'algorithms/path_compression/diagnostic_l3/source/build_alm_model_levels.py').read_bytes()),'receipt':'experiments/verification/boston-native-l3-ranks26-52.json','numericalEquationChange':False}
 report={'schema':'mcl_publication_validation_v1','status':'PASS','releaseId':release_id,'sourceRevision':manifest['sourceRevision'],'archive':manifest['archive'],'archiveSha256':manifest['sha256'],'archiveBytes':manifest['bytes'],'members':len(data),'documentationRefresh':readme_refresh,'safeExtraction':True,'everyMemberMatchesPublicRepositorySource':True,'checkoutIntegrity':check,'nativeSourceIdentityCorrection':note,'publicationSmoke':'docs/reproduction/publication-smoke.json','recoveredValidation':'docs/reproduction/recovered-validation.json','extractedArchiveSmoke':smoke,'scope':'Integrity validation of every exact public download member, including the original 41 commands and all supplemental recovered entries, plus a fresh public-table query and independent verification from the extracted ZIP. Historical runs and inspections are recorded separately. This documentation release runs no solver or experiment, and does not certify complete raw-source city pipelines.'}
 write(ROOT/'docs/reproduction/publication-validation.json',report)
 write(OUT/'downloads.json',{'schema':'mcl_public_computational_downloads_v1','releaseId':release_id,'sourceRevision':manifest['sourceRevision'],'combined':{'filename':arc.name,'bytes':manifest['bytes'],'sha256':manifest['sha256'],'files':len(data),'manifest':'computational-checkout.manifest.json'}})
 print(json.dumps({'status':'PASS','members':len(data),'readmeImages':len(set(references)),'archiveBytes':manifest['bytes'],'sha256':manifest['sha256'],'commands':check['commands_checked'],'pinnedFiles':check['unique_files_checked'],'recoveredRecords':check.get('recovered_records_checked'),'extractedArchiveSmoke':smoke['success']},indent=2))
if __name__=='__main__':main()
