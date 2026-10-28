"""Source-linked spot checks, not full-range independent astronomical certification."""
from datetime import datetime,timedelta,timezone
import hashlib,json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import astronomy
from research_tools.legacy_time_engine import jie_for_year

# Published JCST/UTC+9 minute values: NAOJ Reki Yoko 2026 Solar Terms.
# Preserve the table's minute resolution; do not infer exact seconds from it.
REFERENCE=[(1,5,17,23),(2,4,5,2),(3,5,22,59),(4,5,3,40),(5,5,20,49),(6,6,0,48),
           (7,7,10,57),(8,7,20,43),(9,7,23,41),(10,8,15,29),(11,7,18,52),(12,7,11,53)]
SOURCE='https://eco.mtk.nao.ac.jp/koyomi/yoko/2026/rekiyou262.html.en'
rows=[]
for event,ref in zip(jie_for_year(2026),REFERENCE):
    calculated,branch,name,angle=event
    published=datetime(2026,*ref,tzinfo=timezone(timedelta(hours=9))).astimezone(timezone.utc)
    difference=(calculated-published).total_seconds()
    rows.append({'term':name,'target_longitude':angle,'published_jcst':published.astimezone(timezone(timedelta(hours=9))).isoformat(),
                 'calculated_utc':calculated.isoformat(),'difference_from_published_minute_seconds':difference,'within_60_seconds':abs(difference)<60})
max_residual=0
count=0
for year in range(1949,2032):
    for instant,branch,name,angle in jie_for_year(year):
        time=astronomy.Time.Make(instant.year,instant.month,instant.day,instant.hour,instant.minute,instant.second+instant.microsecond/1e6)
        residual=abs((astronomy.SunPosition(time).elon-angle+180)%360-180)
        max_residual=max(max_residual,residual);count+=1
report={'provider':'astronomy-engine-2.1.19','independent_reference_source':SOURCE,'reference_year':2026,'reference_timezone':'UTC+9 JCST',
        'reference_resolution_seconds':60,'independent_spot_checks':rows,'all_12_within_one_minute':all(r['within_60_seconds'] for r in rows),
        'internal_root_checks':count,'internal_root_years':[1949,2031],'max_internal_longitude_residual_degrees':max_residual,
        'full_range_independent_validation':False,'error_bound_seconds':None,'validation_status':'EXPERIMENTAL',
        'limitations':['Root residual is solver consistency, not independent physical accuracy.','NOAA EoT error bound and lunar month/year/leap labels not certified by this audit.'],
        'time_engine_sha256':hashlib.sha256((ROOT/'randomyst/time_engine.py').read_bytes()).hexdigest()}
(ROOT/'docs/research/astronomy_runtime_spot_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='independent_spot_checks'},ensure_ascii=False,indent=2))
raise SystemExit(not report['all_12_within_one_minute'])
