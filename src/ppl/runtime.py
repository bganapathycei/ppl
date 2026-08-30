import time
from .ai_gateway import AIGateway, AIRequest, ModelPolicy
from .model_policy import resolve_policy
from .schema import validate_output

class Runtime:
    def __init__(self, pir, gateway=None):
        self.pir=pir; self.gateway=gateway or AIGateway(); self.context={}; self.trace=[]; self.return_value=None
        self.policies={k: ModelPolicy(**{kk: vv for kk,vv in v.items() if kk!='name'}) for k,v in pir.get('model_policies',{}).items()}
    def run(self,input_data):
        self.context.update(input_data)
        if not self.pir['workflows']: raise RuntimeError('No workflow defined')
        wf=next((w for w in self.pir['workflows'] if w['name']=='Main'),self.pir['workflows'][0]); self._steps(wf['steps'])
        return self.return_value if self.return_value is not None else self.context
    def _steps(self,steps):
        for s in steps:
            if s['operation']=='RECEIVE': self.trace.append(('RECEIVE','D','✓'))
            elif s['operation']=='RUN': self._run_agent(s['name'])
            elif s['operation']=='IF': self._condition(s)
            elif s['operation']=='RETURN': self.return_value=s['value']; self.trace.append(('RETURN','D',str(s['value']))); return
    def _run_agent(self,name):
        agent=next(a for a in self.pir['agents'] if a['name']==name); local=dict(self.context); self.trace.append((f'RUN {name}','D','✓'))
        for op in agent['operations']:
            policy=self.policies.get(agent.get('policy',''),resolve_policy(agent.get('policy')))
            if op['operation']=='CLASSIFY':
                source=self._resolve(op['target'],local); schema=op['schema']; req=AIRequest('CLASSIFY','Classify the input into the allowed categories.',source,schema,op['categories'],policy); response=self.gateway.execute(req)
                validate_output(schema,response.output,op['categories']); local.update(response.output); self._trace_ai('CLASSIFY',response)
            elif op['operation']=='EXTRACT':
                req=AIRequest('EXTRACT','Extract the requested fields.',local.get('incident',{}),op['schema'],[],policy); response=self.gateway.execute(req); validate_output(op['schema'],response.output); local.update(response.output); self._trace_ai('EXTRACT',response)
            elif op['operation']=='REASON':
                req=AIRequest('REASON',op['instruction'],local.get('incident',{}) | {'context':local},op['schema'],[],policy); response=self.gateway.execute(req); validate_output(op['schema'],response.output); local.update(response.output); self._trace_ai('REASON',response)
        self.context.update(local); self.context[name]=dict(local)
    def _trace_ai(self,operation,response):
        self.trace.append((operation,'C',f'model={response.model} latency={response.latency_ms:.2f}ms tokens={response.input_tokens+response.output_tokens} cost=${response.cost_usd:.4f} attempts={response.attempts}'))
    def _condition(self,s):
        if self._eval(s['condition']): self._steps(s['then']); return
        for b in s['else_if']:
            if self._eval(b['condition']): self._steps(b['steps']); return
        self._steps(s['else'])
    def _resolve(self,name,local):
        cur=local
        for part in name.split('.'):
            if isinstance(cur,dict): cur=cur.get(part,'')
            else: return ''
        return cur
    def _eval(self,c):
        left=self._resolve(c['left'],self.context); right=c['right']
        return {'>':left>right,'<':left<right,'>=':left>=right,'<=':left<=right,'==':left==right,'!=':left!=right}[c['operator']]
