"""Census and execute annotation-derived CLARITY alternatives. No inference.

SQLGlot is used for scoped AST binding and structural invariants. Source SQL is
patched only at bound identifier spans. Semantic claims remain annotation-
conditional; complete executable/type-screened references are not human gold.
"""
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
from itertools import product,combinations
import argparse,csv,hashlib,json,math,sqlite3,sys,time
import sqlglot
from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope,Scope

HERE=Path(__file__).resolve().parent
from replay_config import annotations_root, spider_databases, bird_databases, output_dir
from frozen_protocol import PROTOCOL_SHA256
DATA=annotations_root()
SPIDER=spider_databases()
BIRD=bird_databases()
OUT=output_dir();OUT.mkdir(parents=True,exist_ok=True)
MAX_VARIANTS=256;MAX_ROWS=50_000;MAX_CELLS=500_000;TIMEOUT=5

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def dumps(x):return json.dumps(x,sort_keys=True,ensure_ascii=False)
def digest(x):return hashlib.sha256(dumps(x).encode()).hexdigest()
def quote(s):return '"'+s.replace('"','""')+'"'
def cell(x):
 if x is None:return ['null']
 if isinstance(x,int):return ['number',str(x),'1']
 if isinstance(x,float):
  if math.isfinite(x):
   f=Fraction(x);return ['number',str(f.numerator),str(f.denominator)]
  return ['nonfinite',str(x)]
 if isinstance(x,bytes):return ['blob',x.hex()]
 return ['text',x]
def type_family(t):
 t=(t or '').upper()
 if 'INT' in t:return 'numeric'
 if any(w in t for w in ['CHAR','CLOB','TEXT']):return 'text'
 if not t or 'BLOB' in t:return 'blob_or_untyped'
 return 'numeric'
def db_path(dataset,db):
 p=(SPIDER if dataset=='spider' else BIRD)/db/(db+'.sqlite')
 return p
CONNS={};SCHEMAS={};SQL_CACHE={};STORAGE_CACHE={};DB_RECORDS={}
def connection(ds,db):
 key=(ds,db)
 if key not in CONNS:
  p=db_path(ds,db)
  if not p.exists():raise FileNotFoundError(str(p))
  c=sqlite3.connect(p.resolve().as_uri()+'?mode=ro',uri=True)
  c.execute('PRAGMA query_only=ON');CONNS[key]=c
  DB_RECORDS[key]={'dataset':ds,'db_id':db,'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':sha(p),'author_snapshot_identity_verified':False}
 return CONNS[key]
def schema(ds,db):
 key=(ds,db)
 if key not in SCHEMAS:
  c=connection(ds,db);tables=c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
  SCHEMAS[key]={name.lower():{'name':name,'columns':{r[1].lower():{'name':r[1],'declared_type':r[2],'family':type_family(r[2])} for r in c.execute('PRAGMA table_info('+quote(name)+')')}} for (name,) in tables}
 return SCHEMAS[key]
def arm_timeout(c):
 deadline=time.monotonic()+TIMEOUT
 c.set_progress_handler(lambda:int(time.monotonic()>deadline),10_000)
def storage(ds,db,table,col):
 key=(ds,db,table,col)
 if key not in STORAGE_CACHE:
  c=connection(ds,db);arm_timeout(c)
  try:
   rr=c.execute('SELECT typeof('+quote(col)+'), COUNT(*) FROM '+quote(table)+' WHERE '+quote(col)+' IS NOT NULL GROUP BY typeof('+quote(col)+')').fetchall()
   STORAGE_CACHE[key]={'ok':True,'nonnull_storage_classes':dict(rr)}
  except Exception as e:STORAGE_CACHE[key]={'ok':False,'error':type(e).__name__+': '+str(e)}
 return STORAGE_CACHE[key]
def execute(ds,db,sql):
 key=(ds,db,sql)
 if key in SQL_CACHE:return dict(SQL_CACHE[key])
 start=time.monotonic();c=connection(ds,db);arm_timeout(c)
 try:
  cur=c.execute(sql);names=[r[0] for r in cur.description];rows=[];n=0
  while True:
   chunk=cur.fetchmany(1000)
   if not chunk:break
   n+=len(chunk)
   if n>MAX_ROWS or n*len(names)>MAX_CELLS:raise OverflowError('complete_result_cap_exceeded')
   rows.extend(chunk)
  encoded=[dumps([cell(x) for x in r]) for r in rows]
  bag=Counter(encoded)
  preview=[[x if x is None or isinstance(x,(int,float)) else {'type':type(x).__name__,'sha256':digest(cell(x))} for x in r] for r in rows[:3]]
  result={'ok':True,'row_count':len(rows),'column_count':len(names),'columns':names,'ordered_signature':digest(encoded),'bag_signature':digest(sorted(bag.items())),'set_signature':digest(sorted(bag)),
          'empty':not rows,'all_null':bool(rows) and all(x is None for r in rows for x in r),'scalar_zero':len(rows)==1 and len(names)==1 and isinstance(rows[0][0],(int,float)) and rows[0][0]==0,'numeric_or_hashed_preview':preview,'elapsed_seconds':time.monotonic()-start}
 except Exception as e:
  result={'ok':False,'error':type(e).__name__+': '+str(e),'elapsed_seconds':time.monotonic()-start,'failure_class':'result_cap' if isinstance(e,OverflowError) else 'timeout' if 'interrupted' in str(e).lower() else 'execution_or_fetch'}
 SQL_CACHE[key]=result;return dict(result)

class Unresolved(Exception):pass
def parse(s):
 rr=sqlglot.parse(s,read='sqlite')
 if len(rr)!=1 or not isinstance(rr[0],exp.Query):raise Unresolved('not_one_readonly_query')
 if any(isinstance(x,exp.Anonymous) and x.name.lower() in ['load_extension','readfile','writefile'] for x in rr[0].walk()):raise Unresolved('external_function')
 return rr[0]
def scope_columns(tree):
 scopes=list(traverse_scope(tree));mapnode={}
 for si,sc in enumerate(scopes):
  for col in sc.columns:
   nearest=col.find_ancestor(exp.Select)
   if nearest is sc.expression:mapnode[id(col)]=(sc,si)
 return scopes,mapnode
def resolve(sc,col,sch,depth=0):
 if depth>10:raise Unresolved('scope_recursion')
 source={k.lower():v for k,v in sc.sources.items()}
 name=col.name.lower();qual=col.table.lower()
 if qual:
  if qual not in source:
   if sc.parent:return resolve(sc.parent,col,sch,depth+1)
   raise Unresolved('unknown_qualifier')
  s=source[qual]
  if not isinstance(s,exp.Table):raise Unresolved('derived_source_lineage_unresolved')
  table=s.name.lower()
  if table not in sch or name not in sch[table]['columns']:raise Unresolved('column_not_in_bound_table')
  return table,qual,depth>0
 matches=[];unknown=False
 for alias,s in source.items():
  if isinstance(s,exp.Table) and s.name.lower() in sch and name in sch[s.name.lower()]['columns']:matches.append((s.name.lower(),alias))
  elif isinstance(s,Scope):
   if '*' in s.expression.named_selects or name in [x.lower() for x in s.expression.named_selects]:unknown=True
 if len(matches)==1 and not unknown:return *matches[0],False
 if not matches and not unknown and sc.parent:return resolve(sc.parent,col,sch,depth+1)
 raise Unresolved('ambiguous_or_unknown_unqualified_column')
def fingerprint(tree,indices,facet_ids):
 t=tree.copy();cols=list(t.find_all(exp.Column))
 for idx in indices:
  cols[idx].set('this',exp.Identifier(this='__FACET_'+str(facet_ids[idx])+'__',quoted=False))
  cols[idx].set('table',exp.Identifier(this='__BOUND_RELATION__',quoted=False))
 return [{k:v for k,v in r.items() if k!='m'} for r in t.dump()]
def contains(parent,node):return parent is not None and any(x is node for x in parent.walk())
def literal_value(node,sch):
 if isinstance(node,exp.Literal):return ['string' if node.is_string else 'numeric',node.this]
 if isinstance(node,exp.Column) and not node.table and node.this.args.get('quoted') and not any(node.name.lower() in t['columns'] for t in sch.values()):return ['string',node.name]
 return None
def contradictions(tree,sch):
 found=[]
 for sc in traverse_scope(tree):
  where=sc.expression.args.get('where')
  if not where:continue
  atoms=[]
  def flatten(x):
   if isinstance(x,exp.And):flatten(x.this);flatten(x.expression)
   elif not isinstance(x,exp.Or):atoms.append(x)
  flatten(where.this);seen={}
  for atom in atoms:
   if not isinstance(atom,exp.EQ):continue
   left,right=atom.this,atom.expression
   if not isinstance(left,exp.Column):left,right=right,left
   if not isinstance(left,exp.Column):continue
   lv=literal_value(right,sch)
   if lv is None:continue
   try:table,alias,_=resolve(sc,left,sch)
   except Unresolved:continue
   key=(table,alias,left.name.lower())
   if key in seen and seen[key]!=lv:found.append({'binding':list(key),'reason':'different_literal_equalities_in_same_AND_scope'})
   seen[key]=lv
 return found

def build(ds,r):
 sch=schema(ds,r['db_id']);tree=parse(r['expectedQuery']);scopes,node_scopes=scope_columns(tree);cols=list(tree.find_all(exp.Column))
 selected=r.get('selected_column');terms=r.get('ac_term');raw=r.get('similar_columns')
 if not isinstance(selected,list) or not selected or not isinstance(raw,list):raise Unresolved('missing_annotation_layout')
 k=len(selected)
 if ('multiple' in r['usecase'] and k!=2) or ('single' in r['usecase'] and k!=1):raise Unresolved('facet_count_mismatch')
 groups=[raw] if k==1 else raw
 if len(groups)!=k or not all(isinstance(g,list) and g and all(isinstance(x,(str,int,float)) for x in g) for g in groups):raise Unresolved('candidate_group_layout')
 targets=[];indices=[];fid={};flags=[];kinds=[]
 for fi,(target,grp) in enumerate(zip(selected,groups)):
  value=None
  if isinstance(target,str):name=target
  elif isinstance(target,list) and len(target)==2 and isinstance(target[0],str):name=target[0];value=str(target[1])
  else:raise Unresolved('selected_target_layout')
  nn=name.lower();matches=[]
  for ci,col in enumerate(cols):
   if col.name.lower()!=nn:continue
   if id(col) not in node_scopes:raise Unresolved('target_scope_missing')
   sc,si=node_scopes[id(col)];table,alias,corr=resolve(sc,col,sch)
   matches.append((ci,col,table,alias,si,corr))
  if not matches:raise Unresolved('selected_column_not_found')
  tables={x[2] for x in matches}
  if len(tables)!=1:raise Unresolved('selected_table_identity_lost')
  table=next(iter(tables));catalog=sch[table]['columns'];candidate=[str(x) for x in grp]
  if value is not None and candidate and candidate[0]==value:candidate=candidate[1:]
  if not candidate or not all(x.lower() in catalog for x in candidate):raise Unresolved('value_layout_or_candidate_table_membership_unresolved' if r['usecase'].startswith('value') else 'candidate_not_in_selected_table')
  normalized=list(dict.fromkeys([nn]+[x.lower() for x in candidate]))
  if len(normalized)<2:raise Unresolved('less_than_two_column_readings')
  meta=[catalog[x] for x in normalized]
  if len({x['family'] for x in meta})>1:flags.append('declared_type_family_mismatch')
  if any(x['family']=='blob_or_untyped' for x in meta):flags.append('untyped_or_blob_domain')
  if len({(x[3],x[4]) for x in matches})>1:flags.append('multiple_relation_instances_or_scopes')
  if any(x[5] for x in matches):flags.append('correlated_binding')
  spans=[]
  for ci,col,_,alias,si,corr in matches:
   if ci in fid:raise Unresolved('overlapping_selected_bindings')
   start=col.this.meta.get('start');end=col.this.meta.get('end')
   if start is None or end is None:raise Unresolved('identifier_span_unavailable')
   if start<0 or end>=len(r['expectedQuery']):raise Unresolved('identifier_span_invalid')
   spans.append({'column_index':ci,'start':start,'end':end,'scope_id':si,'relation_alias':alias,'source_was_qualified':bool(col.table),'correlated':corr,'source_token':r['expectedQuery'][start:end+1]})
   indices.append(ci);fid[ci]=fi
   if any(contains(p,col) for p in tree.expressions if isinstance(tree,exp.Select)):flags.append('projected_output_affected')
   if col.find_ancestor(exp.Join):flags.append('join_key_affected')
  targets.append({'facet':fi,'selected_column':name,'selected_value':value,'table':sch[table]['name'],'source_table_key':table,'source_column_key':nn,'candidates':[catalog[x]['name'] for x in normalized],'candidate_type_families':{catalog[x]['name']:catalog[x]['family'] for x in normalized},'spans':spans,'source_group_contains_selected':nn in [str(x).lower() for x in grp]})
  kinds.append('value_category_column_readings' if r['usecase'].startswith('value') else 'column_readings')
 if not isinstance(terms,list) or len(terms)!=k:flags.append('pivot_layout_unresolved')
 elif len({str(t).strip().lower() for t in terms})!=len(terms):flags.append('repeated_pivot_terms')
 if tree.args.get('limit') or tree.args.get('offset'):flags.append('limit_or_offset_requires_selection_validation')
 if isinstance(tree,exp.SetOperation):flags.append('set_operation_output_contract_requires_validation')
 if any(isinstance(n,(exp.Limit,exp.Offset)) and n is not tree.args.get('limit') and n is not tree.args.get('offset') for n in tree.walk()):flags.append('nested_limit_or_offset_requires_selection_validation')
 if tree.args.get('order'):flags.append('outer_order_requires_tie_validation')
 if any(isinstance(n,exp.Anonymous) and n.name.lower() in ['random','randomblob'] or isinstance(n,(exp.CurrentDate,exp.CurrentTimestamp,exp.CurrentTime)) or isinstance(n,exp.Literal) and n.is_string and n.this.lower() in ['now','localtime'] for n in tree.walk()):flags.append('nondeterministic_or_clock_expression')
 total=math.prod(len(t['candidates']) for t in targets)
 if total>MAX_VARIANTS:raise Unresolved('variant_product_cap')
 original_mask=fingerprint(tree,indices,fid);variants=[];seen={}
 for choices in product(*[t['candidates'] for t in targets]):
  collisions=len({(t['source_table_key'],c.lower()) for t,c in zip(targets,choices)})<len(targets)
  edits=[]
  for t,c in zip(targets,choices):
   if c.lower()==t['source_column_key']:continue
   for s in t['spans']:
    token=quote(c) if s['source_was_qualified'] else quote(s['relation_alias'])+'.'+quote(c)
    edits.append((s['start'],s['end'],token))
  sql=r['expectedQuery']
  for start,end,c in sorted(edits,reverse=True):sql=sql[:start]+c+sql[end+1:]
  a=parse(sql)
  if fingerprint(a,indices,fid)!=original_mask:raise Unresolved('nonfacet_AST_change')
  _,new_scopes=scope_columns(a);new_cols=list(a.find_all(exp.Column))
  for t in targets:
   for s in t['spans']:
    col=new_cols[s['column_index']]
    if id(col) not in new_scopes:raise Unresolved('derived_target_scope_missing')
    table,alias,corr=resolve(new_scopes[id(col)][0],col,sch)
    if table!=t['source_table_key'] or alias!=s['relation_alias']:raise Unresolved('derived_binding_changed')
  conflict=contradictions(a,sch)
  if collisions:flags.append('facet_candidate_collision_product')
  if conflict:flags.append('contradictory_literal_product')
  h=digest(sql)
  if h in seen:
   seen[h]['equivalent_product_choices'].append(list(choices));continue
  v={'sql':sql,'sql_sha256':h,'choices':list(choices),'equivalent_product_choices':[],'facet_collision':collisions,'contradictory_literal_flags':conflict}
  seen[h]=v;variants.append(v)
 profiles=[]
 for t in targets:
  for candidate in t['candidates']:
   p=storage(ds,r['db_id'],t['table'],candidate);family=t['candidate_type_families'][candidate]
   incompatible=[]
   if p['ok']:
    allowed={'integer','real'} if family=='numeric' else {'text'} if family=='text' else set(p['nonnull_storage_classes'])
    incompatible=[x for x in p['nonnull_storage_classes'] if x not in allowed]
    if incompatible:flags.append('runtime_storage_family_anomaly')
   else:flags.append('storage_profile_unresolved')
   profiles.append({'table':t['table'],'column':candidate,'declared_family':family,'profile':p,'incompatible_storage_classes':incompatible})
 return tree,targets,variants,sorted(set(flags)),profiles,total

def main():
 arg=argparse.ArgumentParser();arg.add_argument('--dataset',choices=['spider','bird','both'],default='both');args=arg.parse_args()
 inputs=[];intake=[];groups={}
 for ds in ['spider','bird'] if args.dataset=='both' else [args.dataset]:
  p=DATA/ds/'final_data'/f'{ds}_data.jsonl';lines=p.read_text().splitlines();inputs.append({'dataset':ds,'path':str(p),'sha256':sha(p)})
  cats=Counter()
  for line,s in enumerate(lines,1):
   if not s.strip():continue
   r=json.loads(s);cat=r['usecase'].split(' - ')[0];cats[cat]+=1
   if 'ambiguity' not in cat:continue
   key=dumps([r['db_id'],r['question'],r['expectedQuery'],cat,r['ac_term'],r['selected_column'],r['similar_columns']]);h=hashlib.sha256(key.encode()).hexdigest();g=groups.setdefault((ds,h),{'record':r,'lines':[],'styles':Counter(),'key':key})
   g['lines'].append(line);g['styles'][r['usecase'].split(' - ')[1]]+=1
  intake.append({'dataset':ds,'records':sum(cats.values()),'ambiguity_records':sum(n for c,n in cats.items() if 'ambiguity' in c),'outside_agreement_unanswerability_records':sum(n for c,n in cats.items() if 'ambiguity' not in c),'category_records':dict(cats)})
 ledger=[];pairs=[]
 for index,((ds,h),g) in enumerate(groups.items()):
  r=g['record'];case={'bundle_id':ds+'-'+h,'dataset':ds,'source_lines':g['lines'],'first_source_line':g['lines'][0],'conversation_records':len(g['lines']),'styles':dict(g['styles']),'db_id':r['db_id'],'category':r['usecase'].split(' - ')[0],'question':r['question'],'parent_sql':r['expectedQuery'],'ac_term':r['ac_term'],'selected_column':r['selected_column'],'similar_columns':r['similar_columns'],'annotation_key':g['key'],'status':'intake','fixed_output_screened_eligible':False}
  try:
   if not db_path(ds,r['db_id']).exists():raise Unresolved('database_missing')
   parent=execute(ds,r['db_id'],r['expectedQuery']);case['parent_execution']=parent
   if not parent['ok']:case['status']='parent_execution_failed';ledger.append(case);continue
   tree,targets,variants,flags,profiles,total=build(ds,r)
   case.update({'targets':targets,'candidate_product_count':total,'unique_derived_queries':len(variants),'construction_flags':flags,'storage_profiles':profiles,'outer_order_required':bool(tree.args.get('order')),'references':variants,'status':'references_constructed'})
   for v in variants:v['execution']=execute(ds,r['db_id'],v['sql'])
   successes=[v for v in variants if v['execution']['ok']]
   complete=len(successes)==len(variants) and len(variants)>1
   case['all_alternatives_executed']=complete
   case['reference_failures']=len(variants)-len(successes)
   if not complete:case['status']='alternative_execution_incomplete'
   else:case['status']='complete_execution'
   core_flags=list(flags)
   if r['usecase'].startswith('value'):core_flags.append('value_category_outside_primary_column_population')
   if not complete:core_flags.append('incomplete_alternative_execution')
   if len(variants)<2:core_flags.append('one_unique_derived_query')
   # This population is an explicit structural/type screening, not full semantics.
   case['fixed_output_screened_eligible']=not core_flags
   case['fixed_output_exclusion_reasons']=sorted(set(core_flags))
   comparator='ordered_signature' if case['outer_order_required'] else 'bag_signature'
   if complete:
    case['all_alternatives_agree']=len({v['execution'][comparator] for v in variants})==1
    case['all_empty']=all(v['execution']['empty'] for v in variants)
    case['all_null']=all(v['execution']['all_null'] for v in variants)
    case['all_scalar_zero']=all(v['execution']['scalar_zero'] for v in variants)
   else:case['all_alternatives_agree']=None
   pair_count=matching=0
   for i,j in combinations(range(len(variants)),2):
    a,b=variants[i]['execution'],variants[j]['execution']
    if not a['ok'] or not b['ok']:continue
    eq=a[comparator]==b[comparator];pair_count+=1;matching+=eq
    pairs.append({'bundle_id':case['bundle_id'],'dataset':ds,'category':case['category'],'reference_i':i,'reference_j':j,'row_bag_equal':a['bag_signature']==b['bag_signature'],'ordered_list_equal':a['ordered_signature']==b['ordered_signature'],'row_set_equal':a['set_signature']==b['set_signature'],'declared_comparator_equal':eq,'either_empty':a['empty'] or b['empty'],'both_empty':a['empty'] and b['empty'],'fixed_output_screened_eligible':case['fixed_output_screened_eligible']})
   case['executed_pair_count']=pair_count;case['matching_pair_count']=matching;case['any_pair_agrees']=matching>0 if complete else None
  except Unresolved as e:case.update(status='construction_unresolved',construction_reason=str(e),fixed_output_screened_eligible=False)
  except Exception as e:case.update(status='implementation_error',implementation_error=type(e).__name__+': '+str(e),fixed_output_screened_eligible=False)
  ledger.append(case)
  if (index+1)%100==0:print('Processed',index+1,'/',len(groups),'unique SQL executions',len(SQL_CACHE),flush=True)
 (OUT/'bundle-ledger.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in ledger))
 with (OUT/'pair-comparisons.csv').open('w',newline='') as f:
  if pairs:w=csv.DictWriter(f,fieldnames=list(pairs[0]));w.writeheader();w.writerows(pairs)
 manifest={'client_date':'2026-10-05','inputs':inputs,'databases':list(DB_RECORDS.values()),'python':sys.version,'sqlite':sqlite3.sqlite_version,'sqlglot':sqlglot.__version__,'protocol_sha256':PROTOCOL_SHA256,'script_sha256':sha(Path(__file__)),'unique_sql_executions':len(SQL_CACHE),'storage_profiles':len(STORAGE_CACHE),'model_inference':False,'author_snapshot_identity_verified':False,'limits':{'query_timeout_seconds':TIMEOUT,'rows':MAX_ROWS,'cells':MAX_CELLS,'candidate_products':MAX_VARIANTS}}
 (OUT/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 (OUT/'intake.json').write_text(json.dumps(intake,indent=2)+'\n')
 flat=[]
 for c in ledger:
  flat.append({k:c.get(k) for k in ['bundle_id','dataset','first_source_line','db_id','category','conversation_records','status','construction_reason','unique_derived_queries','reference_failures','all_alternatives_executed','fixed_output_screened_eligible','all_alternatives_agree','any_pair_agrees','all_empty','all_null','all_scalar_zero']})
 with (OUT/'bundle-summary.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat)
 print(json.dumps({'bundles':len(ledger),'status':dict(Counter(x['status'] for x in ledger)),'unique_sql_executions':len(SQL_CACHE),'intake':intake},indent=2),flush=True)
 for c in CONNS.values():c.close()
if __name__=='__main__':main()
