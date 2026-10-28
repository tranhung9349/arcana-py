"""Compare the numeric Python port with the pinned JS source on identical pillars."""
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from randomyst.bazi import analyze


def run(count=1000):
    rng = random.Random(20261011)
    cases = [{"gans": [rng.randrange(10) for _ in range(4)], "zhis": [rng.randrange(12) for _ in range(4)]} for _ in range(count)]
    js = '''
const fs=require('fs');
const modulePath=process.argv[1];
const {analyzeNguHanh}=require(modulePath);
const gans=Array.from('甲乙丙丁戊己庚辛壬癸'),zhis=Array.from('子丑寅卯辰巳午未申酉戌亥');
const rows=JSON.parse(fs.readFileSync(0,'utf8')).map(c=>{
const x=analyzeNguHanh({gans:c.gans.map(i=>gans[i]),zhis:c.zhis.map(i=>zhis[i])});
return {dung_than:x.dung_than.ngu_hanh,hy_than:x.hy_than.ngu_hanh,ky_than:x.ky_than.ngu_hanh,strength:x.nhan_dinh.cuong_do,total_support:x.nhan_dinh.diem_tuong_doi.ho_tro,total_oppose:x.nhan_dinh.diem_tuong_doi.khac_che,dieu_hau:x.dieu_hau.can_thiet};
});process.stdout.write(JSON.stringify(rows));
'''
    source = ROOT / 'data/reference/tinix-bazi/phan_tich/ngu_hanh.js'
    result = subprocess.run(['node','-e',js,str(source)],input=json.dumps(cases),text=True,capture_output=True,check=True)
    expected = json.loads(result.stdout)
    mismatches = []
    reasons = set()
    for i,(case,ref) in enumerate(zip(cases,expected)):
        port = analyze(**case)
        reasons.add(port['reason_code'])
        observed = {key:port[key] for key in ref}
        if observed != ref:
            mismatches.append({'index':i,'case':case,'expected':ref,'observed':observed})
    return {'cases':count,'mismatches':mismatches,'decision_branches_covered':sorted(reasons),
            'comparison_scope':'Same supplied four pillars; not an independent calendar or Bazi correctness proof',
            'source_commit':'80ff4463d0397c1b11db76f38d880255f55558bc',
            'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'port_sha256':hashlib.sha256((ROOT/'randomyst/bazi.py').read_bytes()).hexdigest()}

if __name__=='__main__':
    result=run()
    target=ROOT/'docs/research/bazi_python_port_validation.json'
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(bool(result['mismatches']))
