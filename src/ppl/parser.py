import re
from .ast import *

def clean_lines(text):
    lines=[]
    for number, raw in enumerate(text.splitlines(),1):
        raw=raw.split('#',1)[0].rstrip()
        if raw.strip():
            indent=len(raw)-len(raw.lstrip(' ')); lines.append((number,indent,raw.strip()))
    return lines

class Parser:
    def __init__(self,text): self.lines=clean_lines(text); self.i=0
    def error(self,msg):
        n=self.lines[self.i][0] if self.i<len(self.lines) else 'EOF'; raise SyntaxError(f'Line {n}: {msg}')
    def parse(self):
        p=Program()
        while self.i<len(self.lines):
            _,indent,line=self.lines[self.i]
            if indent!=0: self.error('Top-level declaration must not be indented')
            if line.startswith('APP '): p.app=AppDecl(line[4:].strip()); self.i+=1
            elif line.startswith('INPUT '): p.inputs.append(self.parse_input())
            elif line.startswith('MODEL_POLICY '): p.model_policies.append(self.parse_policy())
            elif line.startswith('AGENT '): p.agents.append(self.parse_agent())
            elif line.startswith('WORKFLOW '): p.workflows.append(self.parse_workflow())
            else: self.error(f'Unexpected line: {line}')
        return p
    def parse_input(self):
        _,parent,line=self.lines[self.i]; name=line[6:].strip(); self.i+=1; fields=[]
        while self.i<len(self.lines) and self.lines[self.i][1]>parent:
            _,_,line=self.lines[self.i]
            if ':' not in line: self.error(f'Expected field declaration, got: {line}')
            n,t=map(str.strip,line.split(':',1)); fields.append(InputField(n,t)); self.i+=1
        return InputDecl(name,fields)
    def parse_policy(self):
        _,parent,line=self.lines[self.i]; name=line[len('MODEL_POLICY '):].strip(); self.i+=1
        vals={}
        while self.i<len(self.lines) and self.lines[self.i][1]>parent:
            _,_,line=self.lines[self.i]
            if ':' in line:
                k,v=map(str.strip,line.split(':',1)); vals[k.lower()]=v
            self.i+=1
        return ModelPolicyDecl(name, vals.get('reasoning','reasoning-default'), vals.get('classification','classification-default'), vals.get('extraction','extraction-default'), int(vals.get('max_retries','1')), vals.get('fallback','fallback-default'))
    def parse_agent(self):
        _,parent,line=self.lines[self.i]; name=line[6:].strip(); self.i+=1; agent=AgentDecl(name)
        while self.i<len(self.lines) and self.lines[self.i][1]>parent:
            _,indent,line=self.lines[self.i]
            if line.startswith('INPUT '): agent.input_name=line[6:].strip(); self.i+=1
            elif line.startswith('CLASSIFY '): agent.operations.append(self.parse_classify(indent))
            elif line=='EXTRACT': agent.operations.append(self.parse_extract(indent))
            elif line=='REASON': agent.operations.append(self.parse_reason(indent))
            elif line=='OUTPUT': agent.outputs=self.parse_output(indent)
            else: self.error(f'Unexpected AGENT statement: {line}')
        return agent
    def parse_classify(self,op_indent):
        _,_,line=self.lines[self.i]; target=line[len('CLASSIFY '):].strip(); self.i+=1; cats=[]
        while self.i<len(self.lines) and self.lines[self.i][1]>op_indent:
            _,_,line=self.lines[self.i]; cats.append(line); self.i+=1
        return ClassifyOp(target,cats)
    def parse_extract(self,op_indent):
        self.i+=1; fields=[]; schema={}
        while self.i<len(self.lines) and self.lines[self.i][1]>op_indent:
            _,_,line=self.lines[self.i]; n,t=self._typed(line); fields.append(n); schema[n]=t; self.i+=1
        return ExtractOp(fields,schema)
    def parse_reason(self,op_indent):
        self.i+=1; instructions=[]; consider=[]; schema={}
        while self.i<len(self.lines) and self.lines[self.i][1]>op_indent:
            _,indent,line=self.lines[self.i]
            if line.lower()=='consider:':
                self.i+=1
                while self.i<len(self.lines) and self.lines[self.i][1]>indent:
                    _,_,c=self.lines[self.i]; consider.append(c); self.i+=1
            elif line.lower()=='output:':
                self.i+=1
                while self.i<len(self.lines) and self.lines[self.i][1]>indent:
                    _,_,o=self.lines[self.i]; n,t=self._typed(o); schema[n]=t; self.i+=1
            else: instructions.append(line); self.i+=1
        return ReasonOp(' '.join(instructions).strip(),consider,schema)
    def parse_output(self,op_indent):
        self.i+=1; fields=[]
        while self.i<len(self.lines) and self.lines[self.i][1]>op_indent:
            _,_,line=self.lines[self.i]; fields.append(line); self.i+=1
        return fields
    def _typed(self,line):
        if ':' in line:
            n,t=map(str.strip,line.split(':',1)); return n,t
        return line,'TEXT'
    def parse_workflow(self):
        _,parent,line=self.lines[self.i]; name=line[9:].strip(); self.i+=1; return WorkflowDecl(name,self.parse_steps(parent))
    def parse_steps(self,parent_indent):
        steps=[]
        while self.i<len(self.lines) and self.lines[self.i][1]>parent_indent:
            _,indent,line=self.lines[self.i]
            if line.startswith('RECEIVE '): steps.append(ReceiveStep(line[8:].strip())); self.i+=1
            elif line.startswith('RUN '): steps.append(RunStep(line[4:].strip())); self.i+=1
            elif line.startswith('IF '): steps.append(self.parse_if(indent))
            elif line.startswith('RETURN '): steps.append(ReturnStep(self.parse_value(line[7:].strip()))); self.i+=1
            else: self.error(f'Unexpected WORKFLOW statement: {line}')
        return steps
    def parse_if(self,indent):
        condition=self.parse_condition(self.lines[self.i][2]); self.i+=1; then_steps=self.parse_steps(indent); else_if=[]; else_steps=[]
        while self.i<len(self.lines) and self.lines[self.i][1]==indent:
            line=self.lines[self.i][2]
            if line.startswith('ELSE IF '): c=self.parse_condition(line[8:].strip()); self.i+=1; else_if.append((c,self.parse_steps(indent)))
            elif line=='ELSE': self.i+=1; else_steps=self.parse_steps(indent); break
            else: break
        return IfStep(condition,then_steps,else_if,else_steps)
    def parse_condition(self,text):
        m=re.match(r'(.+?)\s*(>=|<=|==|!=|>|<)\s*(.+)$',text)
        if not m: self.error(f'Invalid condition: {text}')
        return Condition(m.group(1).strip(),m.group(2),self.parse_value(m.group(3).strip()))
    def parse_value(self,value):
        if len(value)>=2 and value[0]==value[-1] and value[0] in "\"'": return value[1:-1]
        try: return int(value)
        except ValueError:
            try: return float(value)
            except ValueError: return value

def parse(text): return Parser(text).parse()
