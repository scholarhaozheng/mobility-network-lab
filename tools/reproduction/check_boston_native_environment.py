"""Read-only check of the Boston native Windows environment; no solve or install."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix',type=Path,required=True)
    parser.add_argument('--manifest',type=Path,default=Path(__file__).resolve().parents[2]/'environments/boston-native-manifest.json')
    args=parser.parse_args();prefix=args.prefix.resolve();manifest=json.loads(args.manifest.read_text(encoding='utf-8'))
    checks=[{'name':'windows_platform','pass':os.name=='nt'}]
    installed={}
    for p in (prefix/'conda-meta').glob('*.json'):
        item=json.loads(p.read_text(encoding='utf-8'));installed[item['name']]=item
    for expected in manifest['condaPackages']:
        actual=installed.get(expected['name'],{})
        checks.append({'name':'conda:'+expected['name'],'pass':all(actual.get(k)==expected[k] for k in ['version','build','sha256'])})
    python=prefix/'python.exe';ipopt=prefix/manifest['nativeExecutable']['relativePath']
    checks += [{'name':'native_python_exists','pass':python.is_file()}, {'name':'ipopt_executable_hash','pass':ipopt.is_file() and sha(ipopt)==manifest['nativeExecutable']['sha256']}]
    details={}
    if python.is_file() and ipopt.is_file():
        env=os.environ.copy();env['PATH']=os.pathsep.join([str(prefix/'Library/bin'),str(prefix/'Scripts'),str(prefix),env.get('PATH','')]);env['PYTHONDONTWRITEBYTECODE']='1'
        probe='import json,sys,importlib.metadata as m; import numpy as np,scipy.sparse as sp,pyomo.environ as pyo; x=pyo.ConcreteModel(); x.v=pyo.Var(initialize=1); print(json.dumps({"python":".".join(map(str,sys.version_info[:3])),"packages":{n:m.version(n) for n in ["numpy","scipy","Pyomo","ply"]},"numeric_imports":float((sp.eye(2) @ np.ones(2)).sum())==2 and pyo.value(x.v)==1}))'
        p=subprocess.run([str(python),'-B','-c',probe],env=env,capture_output=True,text=True,timeout=30)
        checks.append({'name':'native_modules_import','pass':p.returncode==0})
        if p.returncode==0:
            details=json.loads(p.stdout);required={'numpy':'2.0.2',**{x['name']:x['version'] for x in manifest['pipWheels']}}
            checks.append({'name':'python_version','pass':details['python']==manifest['pythonVersion']})
            checks.append({'name':'pip_and_numpy_versions','pass':details['packages']==required})
            checks.append({'name':'numerical_library_loading','pass':details['numeric_imports'] is True})
        v=subprocess.run([str(ipopt),'-v'],env=env,capture_output=True,text=True,timeout=30)
        checks.append({'name':'ipopt_version_command','pass':v.returncode==0 and manifest['nativeExecutable']['version'] in (v.stdout+v.stderr)})
        details['ipopt_version_output']=(v.stdout+v.stderr).strip()
    result={'success':all(c['pass'] for c in checks),'checks':checks,'details':details,'optimizer_calls':0,'environment_installation_performed':False,'clean_environment_creation_verified':False,'scope':'Checks an installed prefix against the recovered exact native package identities and required imports. It does not create an environment or solve a model.'}
    print(json.dumps(result,indent=2));return 0 if result['success'] else 2

if __name__=='__main__':
    raise SystemExit(main())
